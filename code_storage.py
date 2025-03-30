#!/usr/bin/env python3
"""
데이터 저장 및 관리 모듈

GitHub에서 수집한 파이썬 코드와 메타데이터를 저장하고 관리하는 기능을 제공합니다.
코드 검색, 필터링, 업데이트 기능을 포함합니다.
"""

import os
import json
import shutil
import sqlite3
from datetime import datetime
import pandas as pd

class CodeStorageManager:
    """파이썬 코드 저장 및 관리 클래스"""
    
    def __init__(self, base_dir="collected_code", db_file="code_database.db"):
        """
        코드 저장 관리자 초기화
        
        Args:
            base_dir (str): 기본 디렉토리 경로
            db_file (str): 데이터베이스 파일 경로
        """
        self.base_dir = base_dir
        self.metadata_file = os.path.join(base_dir, "metadata.json")
        self.db_file = os.path.join(base_dir, db_file)
        
        # 기본 디렉토리 생성
        os.makedirs(base_dir, exist_ok=True)
        
        # 데이터베이스 초기화
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 저장소 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                full_name TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                description TEXT,
                stars INTEGER,
                forks INTEGER,
                license TEXT,
                created_at TEXT,
                updated_at TEXT,
                added_at TEXT
            )
            ''')
            
            # 파일 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_id INTEGER,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                url TEXT NOT NULL,
                local_path TEXT NOT NULL,
                quality_score REAL,
                code_lines INTEGER,
                is_suitable INTEGER,
                unsuitable_reason TEXT,
                complexity_avg REAL,
                complexity_max INTEGER,
                function_count INTEGER,
                downloaded_at TEXT,
                FOREIGN KEY (repo_id) REFERENCES repositories (id),
                UNIQUE (repo_id, path)
            )
            ''')
            
            # 태그 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            ''')
            
            # 파일-태그 관계 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_tags (
                file_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (file_id, tag_id),
                FOREIGN KEY (file_id) REFERENCES files (id),
                FOREIGN KEY (tag_id) REFERENCES tags (id)
            )
            ''')
            
            conn.commit()
            conn.close()
            print("데이터베이스 초기화 완료")
            
        except Exception as e:
            print(f"데이터베이스 초기화 오류: {str(e)}")
    
    def import_from_metadata(self):
        """
        메타데이터 파일에서 데이터베이스로 데이터 가져오기
        
        Returns:
            tuple: (가져온 저장소 수, 가져온 파일 수)
        """
        if not os.path.exists(self.metadata_file):
            print(f"메타데이터 파일이 존재하지 않습니다: {self.metadata_file}")
            return 0, 0
            
        try:
            # 메타데이터 로드
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            repo_count = 0
            file_count = 0
            
            # 저장소 및 파일 정보 가져오기
            for item in metadata:
                # 저장소 정보 추출
                repo_name = item.get('repo_name')
                repo_full_name = item.get('repo_full_name')
                
                if not repo_full_name:
                    continue
                    
                # 저장소 정보 삽입 또는 업데이트
                cursor.execute('''
                INSERT OR IGNORE INTO repositories 
                (name, full_name, url, stars, license, added_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    repo_name,
                    repo_full_name,
                    item.get('repo_url'),
                    item.get('repo_stars', 0),
                    item.get('repo_license'),
                    datetime.now().isoformat()
                ))
                
                if cursor.rowcount > 0:
                    repo_count += 1
                
                # 저장소 ID 가져오기
                cursor.execute('SELECT id FROM repositories WHERE full_name = ?', (repo_full_name,))
                repo_id = cursor.fetchone()[0]
                
                # 파일 정보 삽입 또는 업데이트
                cursor.execute('''
                INSERT OR IGNORE INTO files 
                (repo_id, name, path, url, local_path, quality_score, code_lines, 
                is_suitable, unsuitable_reason, complexity_avg, complexity_max, 
                function_count, downloaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    repo_id,
                    item.get('file_name'),
                    item.get('file_path'),
                    item.get('file_url'),
                    item.get('local_path'),
                    item.get('quality_score'),
                    item.get('code_lines'),
                    1 if item.get('is_suitable') else 0,
                    item.get('unsuitable_reason'),
                    item.get('complexity', {}).get('avg_complexity'),
                    item.get('complexity', {}).get('max_complexity'),
                    item.get('complexity', {}).get('function_count'),
                    item.get('downloaded_at', datetime.now().isoformat())
                ))
                
                if cursor.rowcount > 0:
                    file_count += 1
            
            conn.commit()
            conn.close()
            
            print(f"메타데이터 가져오기 완료: {repo_count}개 저장소, {file_count}개 파일")
            return repo_count, file_count
            
        except Exception as e:
            print(f"메타데이터 가져오기 오류: {str(e)}")
            return 0, 0
    
    def export_to_metadata(self):
        """
        데이터베이스에서 메타데이터 파일로 데이터 내보내기
        
        Returns:
            int: 내보낸 파일 수
        """
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 저장소 및 파일 정보 조회
            cursor.execute('''
            SELECT 
                r.name as repo_name, 
                r.full_name as repo_full_name,
                r.url as repo_url,
                r.stars as repo_stars,
                r.license as repo_license,
                f.name as file_name,
                f.path as file_path,
                f.url as file_url,
                f.local_path,
                f.quality_score,
                f.code_lines,
                f.is_suitable,
                f.unsuitable_reason,
                f.complexity_avg,
                f.complexity_max,
                f.function_count,
                f.downloaded_at
            FROM files f
            JOIN repositories r ON f.repo_id = r.id
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # 메타데이터 형식으로 변환
            metadata = []
            for row in rows:
                item = dict(row)
                
                # 복잡도 정보 추가
                item['complexity'] = {
                    'avg_complexity': item.pop('complexity_avg'),
                    'max_complexity': item.pop('complexity_max'),
                    'function_count': item.pop('function_count')
                }
                
                # 불리언 값 변환
                item['is_suitable'] = bool(item['is_suitable'])
                
                metadata.append(item)
            
            # 메타데이터 파일 저장
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
                
            print(f"메타데이터 내보내기 완료: {len(metadata)}개 파일")
            return len(metadata)
            
        except Exception as e:
            print(f"메타데이터 내보내기 오류: {str(e)}")
            return 0
    
    def add_tag(self, file_id, tag_name):
        """
        파일에 태그 추가
        
        Args:
            file_id (int): 파일 ID
            tag_name (str): 태그 이름
            
        Returns:
            bool: 성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 태그 추가 또는 ID 가져오기
            cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag_name,))
            cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            tag_id = cursor.fetchone()[0]
            
            # 파일-태그 관계 추가
            cursor.execute('INSERT OR IGNORE INTO file_tags (file_id, tag_id) VALUES (?, ?)', 
                          (file_id, tag_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"태그 추가 오류: {str(e)}")
            return False
    
    def remove_tag(self, file_id, tag_name):
        """
        파일에서 태그 제거
        
        Args:
            file_id (int): 파일 ID
            tag_name (str): 태그 이름
            
        Returns:
            bool: 성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 태그 ID 가져오기
            cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            result = cursor.fetchone()
            
            if result:
                tag_id = result[0]
                
                # 파일-태그 관계 제거
                cursor.execute('DELETE FROM file_tags WHERE file_id = ? AND tag_id = ?', 
                              (file_id, tag_id))
                
                conn.commit()
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"태그 제거 오류: {str(e)}")
            return False
    
    def get_file_tags(self, file_id):
        """
        파일의 태그 목록 가져오기
        
        Args:
            file_id (int): 파일 ID
            
        Returns:
            list: 태그 이름 목록
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT t.name 
            FROM tags t
            JOIN file_tags ft ON t.id = ft.tag_id
            WHERE ft.file_id = ?
            ''', (file_id,))
            
            tags = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return tags
            
        except Exception as e:
            print(f"태그 목록 가져오기 오류: {str(e)}")
            return []
    
    def search_files(self, query=None, tags=None, min_quality=None, 
                    suitable_only=False, limit=100):
        """
        파일 검색
        
        Args:
            query (str, optional): 검색어
            tags (list, optional): 태그 목록
            min_quality (float, optional): 최소 품질 점수
            suitable_only (bool, optional): 적합한 파일만 검색
            limit (int, optional): 최대 결과 수
            
        Returns:
            list: 검색 결과 목록
        """
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 기본 쿼리
            sql = '''
            SELECT 
                f.id, f.name, f.path, f.local_path, f.quality_score, 
                f.code_lines, f.is_suitable, r.full_name as repo_name
            FROM files f
            JOIN repositories r ON f.repo_id = r.id
            '''
            
            conditions = []
            params = []
            
            # 검색어 조건
            if query:
                conditions.append('''
                (f.name LIKE ? OR f.path LIKE ? OR r.name LIKE ? OR r.full_name LIKE ?)
                ''')
                params.extend([f'%{query}%'] * 4)
            
            # 태그 조건
            if tags:
                placeholders = ', '.join(['?'] * len(tags))
                sql += f'''
                JOIN file_tags ft ON f.id = ft.file_id
                JOIN tags t ON ft.tag_id = t.id
                '''
                conditions.append(f't.name IN ({placeholders})')
                params.extend(tags)
            
            # 품질 점수 조건
            if min_quality is not None:
                conditions.append('f.quality_score >= ?')
                params.append(min_quality)
            
            # 적합성 조건
            if suitable_only:
                conditions.append('f.is_suitable = 1')
            
            # 조건 추가
            if conditions:
                sql += ' WHERE ' + ' AND '.join(conditions)
            
            # 그룹화 및 정렬
            sql += ' GROUP BY f.id ORDER BY f.quality_score DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            # 태그 정보 추가
            for result in results:
                result['tags'] = self.get_file_tags(result['id'])
                result['is_suitable'] = bool(result['is_suitable'])
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"파일 검색 오류: {str(e)}")
            return []
    
    def get_statistics(self):
        """
        데이터 통계 정보 가져오기
        
        Returns:
            dict: 통계 정보
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 저장소 수
            cursor.execute('SELECT COUNT(*) FROM repositories')
            repo_count = cursor.fetchone()[0]
            
            # 파일 수
            cursor.execute('SELECT COUNT(*) FROM files')
            file_count = cursor.fetchone()[0]
            
            # 적합한 파일 수
            cursor.execute('SELECT COUNT(*) FROM files WHERE is_suitable = 1')
            suitable_count = cursor.fetchone()[0]
            
            # 태그 수
            cursor.execute('SELECT COUNT(*) FROM tags')
            tag_count = cursor.fetchone()[0]
            
            # 평균 품질 점수
            cursor.execute('SELECT AVG(quality_score) FROM files')
            avg_quality = cursor.fetchone()[0]
            
            # 평균 코드 라인 수
            cursor.execute('SELECT AVG(code_lines) FROM files')
            avg_lines = cursor.fetchone()[0]
            
            # 라이센스 분포
            cursor.execute('''
            SELECT license, COUNT(*) as count
            FROM repositories
            GROUP BY license
            ORDER BY count DESC
            ''')
            licenses = {row[0] if row[0] else 'Unknown': row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'repository_count': repo_count,
                'file_count': file_count,
                'suitable_file_count': suitable_count,
                'tag_count': tag_count,
                'average_quality_score': round(avg_quality, 2) if avg_quality else 0,
                'average_code_lines': round(avg_lines, 2) if avg_lines else 0,
                'license_distribution': licenses
            }
            
        except Exception as e:
            print(f"통계 정보 가져오기 오류: {str(e)}")
            return {}
    
    def export_to_csv(self, output_file="code_data.csv"):
        """
        데이터를 CSV 파일로 내보내기
        
        Args:
            output_file (str): 출력 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_file)
            
            # 데이터 쿼리
            query = '''
            SELECT 
                r.name as repo_name, 
                r.full_name as repo_full_name,
                r.url as repo_url,
                r.stars as repo_stars,
                r.license as repo_license,
                f.name as file_name,
                f.path as file_path,
                f.url as file_url,
                f.local_path,
                f.quality_score,
                f.code_lines,
                f.is_suitable,
                f.unsuitable_reason,
                f.complexity_avg,
                f.complexity_max,
                f.function_count,
                f.downloaded_at
            FROM files f
            JOIN repositories r ON f.repo_id = r.id
            '''
            
            # pandas로 데이터 로드
            df = pd.read_sql_query(query, conn)
            
            # CSV 파일로 저장
            output_path = os.path.join(self.base_dir, output_file)
            df.to_csv(output_path, index=False)
            
            conn.close()
            print(f"CSV 파일 내보내기 완료: {output_path}")
            return True
            
        except Exception as e:
            print(f"CSV 파일 내보내기 오류: {str(e)}")
            return False
    
    def backup_data(self, backup_dir=None):
        """
        데이터 백업
        
        Args:
            backup_dir (str, optional): 백업 디렉토리 경로
            
        Returns:
            str: 백업 디렉토리 경로
        """
        try:
            # 백업 디렉토리 설정
            if backup_dir is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(self.base_dir, f"backup_{timestamp}")
            
            os.makedirs(backup_dir, exist_ok=True)
            
            # 데이터베이스 파일 백업
            if os.path.exists(self.db_file):
                shutil.copy2(self.db_file, os.path.join(backup_dir, os.path.basename(self.db_file)))
            
            # 메타데이터 파일 백업
            if os.path.exists(self.metadata_file):
                shutil.copy2(self.metadata_file, os.path.join(backup_dir, os.path.basename(self.metadata_file)))
            
            print(f"데이터 백업 완료: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            print(f"데이터 백업 오류: {str(e)}")
            return None

# 테스트 코드
if __name__ == "__main__":
    # 코드 저장 관리자 인스턴스 생성
    storage = CodeStorageManager()
    
    # 메타데이터에서 데이터베이스로 가져오기
    storage.import_from_metadata()
    
    # 통계 정보 출력
    stats = storage.get_statistics()
    print("데이터 통계:")
    for key, value in stats.items():
        print(f"- {key}: {value}")
