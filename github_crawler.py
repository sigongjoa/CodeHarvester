#!/usr/bin/env python3
"""
GitHub 파이썬 코드 크롤러

GitHub에서 파이썬 코드를 검색하고 다운로드하는 모듈입니다.
학습용으로 적합한 코드를 필터링하는 기능을 포함합니다.
"""

import os
import base64
import time
import json
from datetime import datetime
from github import Github, RateLimitExceededException
import requests
from dotenv import load_dotenv
import os
from code_filter import CodeQualityFilter

load_dotenv()  # ⬅️ .env 파일을 읽어서 os.environ 에 등록
token = os.getenv("GITHUB_TOKEN") 
print(f"[DEBUG] Loaded token: {token}")

class GitHubPythonCrawler:
    """GitHub에서 파이썬 코드를 크롤링하는 클래스"""
    
    def __init__(self, token=None, output_dir="collected_code"):
        """
        크롤러 초기화
        
        Args:
            token (str, optional): GitHub API 토큰. 없으면 제한된 API 사용
            output_dir (str, optional): 수집된 코드를 저장할 디렉토리
        """
        self.github = Github(token) if token else Github()
        self.output_dir = output_dir
        self.metadata_file = os.path.join(output_dir, "metadata.json")
        self.quality_filter = CodeQualityFilter(metadata_file=self.metadata_file)
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 메타데이터 파일 초기화
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
                
    
    def search_repositories(self, query="language:python", sort="stars", 
                           order="desc", max_results=10):
        """
        GitHub에서 파이썬 저장소 검색
        
        Args:
            query (str): 검색 쿼리
            sort (str): 정렬 기준 (stars, forks, updated)
            order (str): 정렬 순서 (desc, asc)
            max_results (int): 최대 결과 수
            
        Returns:
            list: 검색된 저장소 목록
        """
        print(f"GitHub에서 '{query}' 검색 중...")
        try:
            repositories = self.github.search_repositories(
                query=query, sort=sort, order=order
            )
            
            results = []
            count = 0
            
            for repo in repositories:
                if count >= max_results:
                    break
                
                results.append({
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'url': repo.html_url,
                    'description': repo.description,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'created_at': repo.created_at.isoformat(),
                    'updated_at': repo.updated_at.isoformat(),
                    'license': repo.license.name if repo.license else None
                })
                count += 1
                
            print(f"{len(results)}개의 저장소를 찾았습니다.")
            return results
            
        except RateLimitExceededException:
            reset_time = self.github.get_rate_limit().core.reset
            current_time = datetime.utcnow()
            wait_time = (reset_time - current_time).total_seconds()
            print(f"API 사용량 제한 초과. {wait_time:.0f}초 후에 다시 시도하세요.")
            return []
    
    def get_python_files(self, repo_name, max_files=None):
        """
        저장소에서 모든 파이썬 파일 목록 가져오기
        
        Args:
            repo_name (str): 저장소 이름 (예: 'username/repo')
            max_files (int, optional): 최대 파일 수 (None이면 모든 파일)
            
        Returns:
            list: 파이썬 파일 정보 목록
        """
        print(f"{repo_name} 저장소에서 파이썬 파일 검색 중...")
        try:
            repo = self.github.get_repo(repo_name)
            contents = repo.get_contents("")
            python_files = []
            
            # 디렉토리를 탐색하는 동안 발생할 수 있는 API 제한을 관리하기 위한 변수
            api_calls = 0
            last_api_call_time = time.time()
            
            while contents:
                if max_files is not None and len(python_files) >= max_files:
                    break
                    
                file_content = contents.pop(0)
                
                # API 호출 관리
                api_calls += 1
                if api_calls % 10 == 0:  # 10번의 API 호출마다
                    current_time = time.time()
                    elapsed = current_time - last_api_call_time
                    if elapsed < 2:  # 2초 이내에 10번의 호출이 있었다면
                        sleep_time = 2 - elapsed
                        print(f"API 호출 제한 방지를 위해 {sleep_time:.2f}초 대기 중...")
                        time.sleep(sleep_time)
                    last_api_call_time = time.time()
                
                try:
                    if file_content.type == "dir":
                        # 디렉토리일 경우 추가 콘텐츠 가져오기
                        print(f"디렉토리 탐색 중: {file_content.path}")
                        try:
                            dir_contents = repo.get_contents(file_content.path)
                            # 리스트인 경우와 단일 객체인 경우 모두 처리
                            if isinstance(dir_contents, list):
                                contents.extend(dir_contents)
                            else:
                                contents.append(dir_contents)
                        except Exception as e:
                            print(f"디렉토리 내용 가져오기 오류 ({file_content.path}): {str(e)}")
                    elif file_content.name.endswith(".py"):
                        python_files.append({
                            'name': file_content.name,
                            'path': file_content.path,
                            'url': file_content.html_url,
                            'sha': file_content.sha,
                            'size': file_content.size
                        })
                        print(f"파이썬 파일 발견: {file_content.path}")
                except AttributeError:
                    # 가끔 콘텐츠 객체가 예상된 속성을 갖지 않는 경우가 있음
                    print(f"콘텐츠 객체 처리 중 오류 발생: {str(file_content)}")
            
            print(f"{len(python_files)}개의 파이썬 파일을 찾았습니다.")
            return python_files
            
        except RateLimitExceededException:
            reset_time = self.github.get_rate_limit().core.reset
            current_time = datetime.utcnow()
            wait_time = (reset_time - current_time).total_seconds()
            print(f"API 사용량 제한 초과. {wait_time:.0f}초 후에 다시 시도하세요.")
            return []
        except Exception as e:
            print(f"파일 목록 가져오기 오류: {str(e)}")
            return []
    
    def download_file(self, repo_name, file_path):
        """
        GitHub에서 파일 내용 다운로드
        
        Args:
            repo_name (str): 저장소 이름
            file_path (str): 파일 경로
            
        Returns:
            str: 파일 내용
        """
        try:
            repo = self.github.get_repo(repo_name)
            file_content = repo.get_contents(file_path)
            
            if isinstance(file_content, list):
                return None  # 디렉토리인 경우
            
            # base64로 인코딩된 내용 디코딩
            content = base64.b64decode(file_content.content).decode('utf-8')
            return content
            
        except Exception as e:
            print(f"파일 다운로드 오류 ({repo_name}/{file_path}): {str(e)}")
            return None
    
    def save_file(self, repo_name, file_path, content):
        """
        파일 내용을 로컬에 저장
        
        Args:
            repo_name (str): 저장소 이름
            file_path (str): 파일 경로
            content (str): 파일 내용
            
        Returns:
            str: 저장된 파일 경로
        """
        if content is None:
            return None
            
        # 저장 경로 생성 (원본 디렉토리 구조 유지)
        repo_dir = os.path.join(self.output_dir, repo_name.replace('/', '_'))
        file_dir = os.path.dirname(file_path)
        save_dir = os.path.join(repo_dir, file_dir)
        os.makedirs(save_dir, exist_ok=True)
        
        # 파일 이름 추출 및 저장
        file_name = os.path.basename(file_path)
        save_path = os.path.join(repo_dir, file_path)
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return save_path
        except Exception as e:
            print(f"파일 저장 오류: {str(e)}")
            return None
    
    def update_metadata(self, repo_info, file_info, local_path, quality_score=None):
        """
        메타데이터 업데이트
        
        Args:
            repo_info (dict): 저장소 정보
            file_info (dict): 파일 정보
            local_path (str): 로컬 저장 경로
            quality_score (float, optional): 코드 품질 점수
        """
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # 새 메타데이터 항목 추가
            metadata.append({
                'repo_name': repo_info['name'],
                'repo_full_name': repo_info['full_name'],
                'repo_url': repo_info['url'],
                'repo_stars': repo_info.get('stars', 0),
                'repo_license': repo_info.get('license', None),
                'file_name': file_info['name'],
                'file_path': file_info['path'],
                'file_url': file_info['url'],
                'local_path': local_path,
                'quality_score': quality_score,
                'downloaded_at': datetime.now().isoformat()
            })
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            print(f"메타데이터 업데이트 오류: {str(e)}")
    
    def crawl(self, query="language:python", max_repos=5, max_files_per_repo=None):
        """
        GitHub에서 파이썬 코드 크롤링 실행 + 품질 평가
        
        Args:
            query (str): 검색 쿼리
            max_repos (int): 최대 저장소 수
            max_files_per_repo (int, optional): 저장소당 최대 파일 수 (None이면 모든 파일)
            
        Returns:
            list: 다운로드된 파일 정보 목록
        """
        # 품질 평가 도구 초기화
        quality_filter = CodeQualityFilter(metadata_file=self.metadata_file)

        # 저장소 검색
        repositories = self.search_repositories(query=query, max_results=max_repos)
        downloaded_files = []

        for repo in repositories:
            print(f"\n저장소 처리 중: {repo['full_name']}")
            python_files = self.get_python_files(repo['full_name'], max_files=max_files_per_repo)

            for file_info in python_files:
                time.sleep(0.5)  # API 제한 방지

                content = self.download_file(repo['full_name'], file_info['path'])
                if content:
                    local_path = self.save_file(repo['full_name'], file_info['path'], content)
                    if local_path:
                        # ✅ 품질 분석 수행
                        quality_score = quality_filter.evaluate_code_quality(local_path)
                        code_lines = quality_filter.count_code_lines(local_path)
                        complexity_info = quality_filter.check_code_complexity(local_path)
                        is_suitable, reason = quality_filter.is_suitable_for_learning(local_path, repo)

                        # 메타데이터 저장
                        self.update_metadata(
                            repo_info=repo,
                            file_info=file_info,
                            local_path=local_path,
                            quality_score=quality_score
                        )

                        # 👉 메타데이터에 부가 정보 직접 추가
                        with open(self.metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        if metadata:
                            metadata[-1]['code_lines'] = code_lines
                            metadata[-1]['complexity'] = complexity_info
                            metadata[-1]['is_suitable'] = is_suitable
                            metadata[-1]['unsuitable_reason'] = None if is_suitable else reason
                            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                                json.dump(metadata, f, indent=2)

                        downloaded_files.append({
                            'repo': repo['full_name'],
                            'file': file_info['path'],
                            'local_path': local_path
                        })
                        print(f"파일 다운로드 및 품질 분석 완료: {file_info['path']}")

        print(f"\n총 {len(downloaded_files)}개의 파일을 다운로드했습니다.")
        return downloaded_files

    def crawl_repository(self, username, repo_name, max_files_per_repo=None):
        """
        특정 GitHub 저장소에서 모든 파이썬 파일을 크롤링하고 저장

        Args:
            username (str): 사용자 이름
            repo_name (str): 저장소 이름
            max_files_per_repo (int, optional): 최대 파일 수 (None이면 모든 파일)
        """
        full_name = f"{username}/{repo_name}"
        print(f"🔍 저장소 {full_name} 에서 코드 크롤링 중...")

        # 저장소 정보 가져오기 (상세 정보 추가)
        try:
            repo = self.github.get_repo(full_name)
            repo_info = {
                'name': repo.name,
                'full_name': repo.full_name,
                'url': repo.html_url,
                'description': repo.description,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'created_at': repo.created_at.isoformat() if repo.created_at else '',
                'updated_at': repo.updated_at.isoformat() if repo.updated_at else '',
                'license': repo.license.name if repo.license else None
            }
        except Exception as e:
            print(f"저장소 정보 가져오기 오류: {str(e)}")
            # 기본 정보로 대체
            repo_info = {
                'name': repo_name,
                'full_name': full_name,
                'url': f"https://github.com/{full_name}",
                'description': '',
                'stars': 0,
                'forks': 0,
                'created_at': '',
                'updated_at': '',
                'license': None
            }

        python_files = self.get_python_files(full_name, max_files=max_files_per_repo)
        downloaded_files = []
        total_files = len(python_files)
        
        print(f"총 {total_files}개의 파이썬 파일을 발견했습니다. 다운로드를 시작합니다...")

        for i, file_info in enumerate(python_files):
            try:
                # 진행 상황 표시
                print(f"\r진행 중: {i+1}/{total_files} ({(i+1)/total_files*100:.1f}%)", end="")
                
                # API 제한 방지를 위한 간격 조절
                if i > 0 and i % 10 == 0:
                    time.sleep(2)
                
                content = self.download_file(full_name, file_info['path'])
                if content:
                    local_path = self.save_file(full_name, file_info['path'], content)
                    if local_path:
                        # 품질 분석 수행 (선택적)
                        try:
                            quality_filter = CodeQualityFilter(metadata_file=self.metadata_file)
                            quality_score = quality_filter.evaluate_code_quality(local_path)
                            code_lines = quality_filter.count_code_lines(local_path)
                            complexity_info = quality_filter.check_code_complexity(local_path)
                            is_suitable, reason = quality_filter.is_suitable_for_learning(local_path, repo_info)
                        except Exception as e:
                            print(f"\n품질 분석 오류 ({file_info['path']}): {str(e)}")
                            quality_score = None
                            code_lines = 0
                            complexity_info = {}
                            is_suitable = None
                            reason = f"분석 오류: {str(e)}"
                        
                        # 메타데이터 업데이트
                        self.update_metadata(repo_info, file_info, local_path, quality_score)
                        
                        # 품질 분석 정보 추가
                        with open(self.metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        if metadata:
                            metadata[-1]['code_lines'] = code_lines
                            metadata[-1]['complexity'] = complexity_info
                            metadata[-1]['is_suitable'] = is_suitable
                            metadata[-1]['unsuitable_reason'] = None if is_suitable else reason
                            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                                json.dump(metadata, f, indent=2)
                        
                        downloaded_files.append({
                            'repo': full_name,
                            'file': file_info['path'],
                            'local_path': local_path
                        })
            except Exception as e:
                print(f"\n파일 처리 중 오류 발생 ({file_info['path']}): {str(e)}")

        print(f"\n✅ 저장소 크롤링 완료: {len(downloaded_files)}개의 파일 다운로드됨")
        return downloaded_files

# 테스트 코드
if __name__ == "__main__":
    # 크롤러 인스턴스 생성
    crawler = GitHubPythonCrawler(output_dir="collected_code")
    
    # 전체 저장소 크롤링 (max_files_per_repo=None으로 모든 파일 가져오기)
    crawler.crawl(query="language:python stars:>1000", max_repos=1, max_files_per_repo=None)
    
    # 또는 특정 저장소의 모든 파이썬 파일 크롤링
    # crawler.crawl_repository("username", "repo_name", max_files_per_repo=None)