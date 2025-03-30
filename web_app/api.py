from flask import jsonify, request
import sys
import os
import json
import time
import threading
import sqlite3
from datetime import datetime

# 기존 크롤러 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from github_crawler import GitHubPythonCrawler
from code_filter import CodeQualityFilter
from code_storage import CodeStorageManager

# 크롤링 작업 상태 저장
crawling_jobs = []
current_job = None

def get_db_connection():
    """데이터베이스 연결 생성"""
    conn = sqlite3.connect('collected_code/code_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def crawl_repository(repo_url, max_files):
    """특정 저장소 URL에서 크롤링"""
    global current_job
    
    job_id = len(crawling_jobs) + 1
    job = {
        'id': job_id,
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'query': repo_url,
        'status': 'in_progress',
        'files_downloaded': 0
    }
    
    current_job = job
    crawling_jobs.append(job)
    
    try:
        # GitHub URL에서 사용자명과 저장소명 추출
        parts = repo_url.strip('/').split('/')
        if len(parts) < 5 or parts[2] != 'github.com':
            raise ValueError("유효한 GitHub 저장소 URL이 아닙니다.")
        
        username = parts[3]
        repo_name = parts[4]
        
        # 크롤링 실행
        crawler = GitHubPythonCrawler(output_dir="collected_code")
        downloaded_files = crawler.crawl_repository(username, repo_name, max_files_per_repo=max_files)
        
        # 필터링 실행
        filter_instance = CodeQualityFilter(metadata_file="collected_code/metadata.json")
        suitable, unsuitable = filter_instance.filter_code()
        
        # 작업 상태 업데이트
        job['status'] = 'completed'
        job['files_downloaded'] = len(downloaded_files)
        job['suitable_files'] = suitable
        job['unsuitable_files'] = unsuitable
        job['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 데이터베이스 동기화
        storage = CodeStorageManager(base_dir="collected_code")
        storage.import_from_metadata()
        
        current_job = None
        return job
    
    except Exception as e:
        # 오류 발생 시 작업 상태 업데이트
        job['status'] = 'failed'
        job['error'] = str(e)
        job['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_job = None
        raise

def crawl_by_query(query, max_repos, max_files):
    """검색 쿼리로 크롤링"""
    global current_job
    
    job_id = len(crawling_jobs) + 1
    job = {
        'id': job_id,
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'query': query,
        'status': 'in_progress',
        'files_downloaded': 0
    }
    
    current_job = job
    crawling_jobs.append(job)
    
    try:
        # 크롤링 실행
        crawler = GitHubPythonCrawler(output_dir="collected_code")
        downloaded_files = crawler.crawl(
            query=query,
            max_repos=max_repos,
            max_files_per_repo=max_files
        )
        
        # 필터링 실행
        filter_instance = CodeQualityFilter(metadata_file="collected_code/metadata.json")
        suitable, unsuitable = filter_instance.filter_code()
        
        # 작업 상태 업데이트
        job['status'] = 'completed'
        job['files_downloaded'] = len(downloaded_files)
        job['suitable_files'] = suitable
        job['unsuitable_files'] = unsuitable
        job['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 데이터베이스 동기화
        storage = CodeStorageManager(base_dir="collected_code")
        storage.import_from_metadata()
        
        current_job = None
        return job
    
    except Exception as e:
        # 오류 발생 시 작업 상태 업데이트
        job['status'] = 'failed'
        job['error'] = str(e)
        job['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_job = None
        raise

def get_crawling_status():
    """크롤링 작업 상태 조회"""
    return {
        'current_job': current_job if current_job else {},  # ✅ None 방지
        'history': crawling_jobs[-10:] if crawling_jobs else []
    }

def get_code_statistics():
    """코드 통계 정보 조회"""
    try:
        conn = get_db_connection()
        
        # 기본 통계
        stats = {}
        
        # 저장소 수
        cursor = conn.execute("SELECT COUNT(DISTINCT id) FROM repositories")
        stats['repository_count'] = cursor.fetchone()[0]
        
        # 파일 수
        cursor = conn.execute("SELECT COUNT(id) FROM files")
        stats['file_count'] = cursor.fetchone()[0]
        
        # 적합한 파일 수
        cursor = conn.execute("SELECT COUNT(id) FROM files WHERE is_suitable = 1")
        stats['suitable_file_count'] = cursor.fetchone()[0]
        
        # 평균 품질 점수
        cursor = conn.execute("SELECT AVG(quality_score) FROM files WHERE quality_score IS NOT NULL")
        avg_quality = cursor.fetchone()[0]
        stats['average_quality_score'] = avg_quality if avg_quality else 0
        
        # 저장소별 파일 수
        cursor = conn.execute("""
            SELECT r.name, COUNT(f.id) as file_count
            FROM repositories r
            JOIN files f ON r.id = f.repo_id
            GROUP BY r.id
            ORDER BY file_count DESC
            LIMIT 10
        """)
        stats['repositories'] = [{'name': row['name'], 'file_count': row['file_count']} for row in cursor.fetchall()]
        
        # 품질 점수 분포
        stats['quality_distribution'] = [0, 0, 0, 0, 0]  # 0-2, 2-4, 4-6, 6-8, 8-10
        cursor = conn.execute("SELECT quality_score FROM files WHERE quality_score IS NOT NULL")
        for row in cursor.fetchall():
            score = row['quality_score']
            if score < 2:
                stats['quality_distribution'][0] += 1
            elif score < 4:
                stats['quality_distribution'][1] += 1
            elif score < 6:
                stats['quality_distribution'][2] += 1
            elif score < 8:
                stats['quality_distribution'][3] += 1
            else:
                stats['quality_distribution'][4] += 1
        
        # 태그 분포
        cursor = conn.execute("""
            SELECT t.name, COUNT(ft.file_id) as count
            FROM tags t
            JOIN file_tags ft ON t.id = ft.tag_id
            GROUP BY t.id
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['tags'] = [{'name': row['name'], 'count': row['count']} for row in cursor.fetchall()]
        
        conn.close()
        return stats
    
    except Exception as e:
        print(f"통계 정보 조회 오류: {str(e)}")
        return {
            'repository_count': 0,
            'file_count': 0,
            'suitable_file_count': 0,
            'average_quality_score': 0,
            'repositories': [],
            'quality_distribution': [0, 0, 0, 0, 0],
            'tags': []
        }

def search_code(query=None, suitable_only=False, min_quality=None, limit=100):
    """코드 검색"""
    storage = CodeStorageManager(base_dir="collected_code")
    results = storage.search_files(
        query=query,
        suitable_only=suitable_only,
        min_quality=min_quality,
        limit=limit
    )
    
    # 태그 정보 추가
    for item in results:
        item['tags'] = storage.get_file_tags(item['id'])
    
    return results

def get_file_content(file_id):
    """파일 내용 조회"""
    storage = CodeStorageManager(base_dir="collected_code")
    results = storage.search_files(limit=100)
    
    file_info = None
    for item in results:
        if item['id'] == file_id:
            file_info = item
            break
    
    if not file_info:
        return None, "파일을 찾을 수 없습니다."
    
    try:
        with open(file_info['local_path'], 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return file_info, content
    except Exception as e:
        return file_info, f"파일 내용을 읽을 수 없습니다: {str(e)}"

def update_file_content(file_id, content):
    """파일 내용 업데이트"""
    storage = CodeStorageManager(base_dir="collected_code")
    results = storage.search_files(limit=100)
    
    file_info = None
    for item in results:
        if item['id'] == file_id:
            file_info = item
            break
    
    if not file_info:
        return False, "파일을 찾을 수 없습니다."
    
    try:
        with open(file_info['local_path'], 'w', encoding='utf-8') as f:
            f.write(content)
        return True, "파일이 성공적으로 업데이트되었습니다."
    except Exception as e:
        return False, f"파일 업데이트 중 오류 발생: {str(e)}"

def delete_file(file_id):
    """파일 삭제"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 파일 정보 조회
        cursor.execute("SELECT local_path FROM files WHERE id = ?", (file_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "파일을 찾을 수 없습니다."
        
        local_path = result['local_path']
        
        # 파일 태그 삭제
        cursor.execute("DELETE FROM file_tags WHERE file_id = ?", (file_id,))
        
        # 파일 정보 삭제
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        
        conn.commit()
        conn.close()
        
        # 실제 파일 삭제
        if os.path.exists(local_path):
            os.remove(local_path)
        
        return True, "파일이 성공적으로 삭제되었습니다."
    except Exception as e:
        return False, f"파일 삭제 중 오류 발생: {str(e)}"

def manage_file_tag(file_id, tag_name, action):
    """파일 태그 관리"""
    storage = CodeStorageManager(base_dir="collected_code")
    
    try:
        if action == 'add':
            storage.add_tag(file_id, tag_name)
            return True, f"태그 '{tag_name}'이(가) 추가되었습니다."
        elif action == 'remove':
            storage.remove_tag(file_id, tag_name)
            return True, f"태그 '{tag_name}'이(가) 제거되었습니다."
        else:
            return False, "유효하지 않은 작업입니다."
    except Exception as e:
        return False, f"태그 관리 중 오류 발생: {str(e)}"
