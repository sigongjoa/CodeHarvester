#!/usr/bin/env python3
"""
관리 인터페이스 모듈

GitHub에서 수집한 파이썬 코드를 관리하기 위한 명령줄 인터페이스를 제공합니다.
코드 검색, 조회, 품질 관리, 태그 관리 등의 기능을 포함합니다.
"""

import os
import sys
import argparse
import json
import textwrap
from tabulate import tabulate
from github_crawler import GitHubPythonCrawler
from code_filter import CodeQualityFilter
from code_storage import CodeStorageManager

class CodeManagementInterface:
    """파이썬 코드 관리 인터페이스 클래스"""
    
    def __init__(self, base_dir="collected_code"):
        """
        관리 인터페이스 초기화
        
        Args:
            base_dir (str): 기본 디렉토리 경로
        """
        self.base_dir = base_dir
        self.crawler = GitHubPythonCrawler(output_dir=base_dir)
        self.filter = CodeQualityFilter(metadata_file=os.path.join(base_dir, "metadata.json"))
        self.storage = CodeStorageManager(base_dir=base_dir)
    
    def setup_parser(self):
        """
        명령줄 인터페이스 파서 설정
        
        Returns:
            argparse.ArgumentParser: 설정된 파서
        """
        parser = argparse.ArgumentParser(
            description='GitHub 파이썬 코드 크롤링 및 관리 시스템',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=textwrap.dedent('''
            사용 예시:
              python manager.py crawl --query "language:python stars:>1000" --max-repos 5
              python manager.py filter
              python manager.py search --query "algorithm" --suitable-only
              python manager.py view --id 1
              python manager.py stats
            ''')
        )
        
        subparsers = parser.add_subparsers(dest='command', help='명령')
        
        # 크롤링 명령
        crawl_parser = subparsers.add_parser('crawl', help='GitHub에서 파이썬 코드 크롤링')
        crawl_parser.add_argument('--query', type=str, default="language:python stars:>1000",
                                help='GitHub 검색 쿼리 (기본값: "language:python stars:>1000")')
        crawl_parser.add_argument('--max-repos', type=int, default=5,
                                help='최대 저장소 수 (기본값: 5)')
        crawl_parser.add_argument('--max-files', type=int, default=10,
                                help='저장소당 최대 파일 수 (기본값: 10)')
        
        # 필터링 명령
        filter_parser = subparsers.add_parser('filter', help='수집된 코드 필터링')
        filter_parser.add_argument('--min-quality', type=float, default=6.0,
                                 help='최소 품질 점수 (기본값: 6.0)')
        filter_parser.add_argument('--min-lines', type=int, default=10,
                                 help='최소 코드 라인 수 (기본값: 10)')
        filter_parser.add_argument('--max-lines', type=int, default=1000,
                                 help='최대 코드 라인 수 (기본값: 1000)')
        
        # 검색 명령
        search_parser = subparsers.add_parser('search', help='코드 검색')
        search_parser.add_argument('--query', type=str, help='검색어')
        search_parser.add_argument('--tags', type=str, help='태그 (쉼표로 구분)')
        search_parser.add_argument('--min-quality', type=float, help='최소 품질 점수')
        search_parser.add_argument('--suitable-only', action='store_true',
                                 help='학습용으로 적합한 코드만 검색')
        search_parser.add_argument('--limit', type=int, default=20,
                                 help='최대 결과 수 (기본값: 20)')
        
        # 파일 조회 명령
        view_parser = subparsers.add_parser('view', help='파일 조회')
        view_parser.add_argument('--id', type=int, required=True, help='파일 ID')
        
        # 태그 관리 명령
        tag_parser = subparsers.add_parser('tag', help='태그 관리')
        tag_parser.add_argument('--id', type=int, required=True, help='파일 ID')
        tag_parser.add_argument('--add', type=str, help='추가할 태그')
        tag_parser.add_argument('--remove', type=str, help='제거할 태그')
        tag_parser.add_argument('--list', action='store_true', help='태그 목록 조회')
        
        # 통계 명령
        subparsers.add_parser('stats', help='데이터 통계 조회')
        
        # 내보내기 명령
        export_parser = subparsers.add_parser('export', help='데이터 내보내기')
        export_parser.add_argument('--format', type=str, choices=['csv', 'json'],
                                 default='csv', help='내보내기 형식 (기본값: csv)')
        export_parser.add_argument('--output', type=str, help='출력 파일 경로')
        
        # 백업 명령
        backup_parser = subparsers.add_parser('backup', help='데이터 백업')
        backup_parser.add_argument('--dir', type=str, help='백업 디렉토리 경로')
        
        # 데이터베이스 동기화 명령
        subparsers.add_parser('sync', help='메타데이터와 데이터베이스 동기화')
        
        return parser
    
    def crawl(self, args):
        """
        GitHub에서 파이썬 코드 크롤링
        
        Args:
            args: 명령줄 인수
        """
        print(f"GitHub에서 파이썬 코드 크롤링 시작 (쿼리: {args.query})")
        
        # 크롤링 실행
        downloaded_files = self.crawler.crawl(
            query=args.query,
            max_repos=args.max_repos,
            max_files_per_repo=args.max_files
        )
        
        print(f"크롤링 완료: {len(downloaded_files)}개 파일 다운로드")
        
        # 데이터베이스 동기화
        self.storage.import_from_metadata()
    
    def filter_code(self, args):
        """
        수집된 코드 필터링
        
        Args:
            args: 명령줄 인수
        """
        print("수집된 코드 필터링 시작")
        
        # 필터 설정 업데이트
        self.filter.min_quality_score = args.min_quality
        self.filter.min_code_lines = args.min_lines
        self.filter.max_code_lines = args.max_lines
        
        # 필터링 실행
        suitable, unsuitable = self.filter.filter_code()
        
        print(f"필터링 완료: 적합한 파일 {suitable}개, 부적합한 파일 {unsuitable}개")
        
        # 데이터베이스 동기화
        self.storage.import_from_metadata()
    
    def search(self, args):
        """
        코드 검색
        
        Args:
            args: 명령줄 인수
        """
        # 태그 목록 변환
        tags = args.tags.split(',') if args.tags else None
        
        # 검색 실행
        results = self.storage.search_files(
            query=args.query,
            tags=tags,
            min_quality=args.min_quality,
            suitable_only=args.suitable_only,
            limit=args.limit
        )
        
        if not results:
            print("검색 결과가 없습니다.")
            return
        
        # 결과 테이블 출력
        table_data = []
        for item in results:
            table_data.append([
                item['id'],
                item['name'],
                item['repo_name'],
                f"{item['quality_score']:.1f}" if item['quality_score'] else 'N/A',
                item['code_lines'],
                '✓' if item['is_suitable'] else '✗',
                ', '.join(item['tags']) if item['tags'] else ''
            ])
        
        headers = ['ID', '파일명', '저장소', '품질 점수', '코드 라인', '적합성', '태그']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print(f"총 {len(results)}개 결과")
    
    def view_file(self, args):
        """
        파일 조회
        
        Args:
            args: 명령줄 인수
        """
        # 파일 정보 검색
        results = self.storage.search_files(limit=1)
        file_info = None
        
        for item in results:
            if item['id'] == args.id:
                file_info = item
                break
        
        if not file_info:
            print(f"ID가 {args.id}인 파일을 찾을 수 없습니다.")
            return
        
        # 파일 정보 출력
        print(f"파일: {file_info['name']}")
        print(f"저장소: {file_info['repo_name']}")
        print(f"품질 점수: {file_info['quality_score']:.1f}" if file_info['quality_score'] else 'N/A')
        print(f"코드 라인: {file_info['code_lines']}")
        print(f"학습 적합성: {'적합' if file_info['is_suitable'] else '부적합'}")
        print(f"태그: {', '.join(file_info['tags']) if file_info['tags'] else '없음'}")
        print(f"로컬 경로: {file_info['local_path']}")
        print("\n--- 파일 내용 ---")
        
        # 파일 내용 출력
        try:
            with open(file_info['local_path'], 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                print(content[:1000] + ('...' if len(content) > 1000 else ''))
        except Exception as e:
            print(f"파일 내용 읽기 오류: {str(e)}")
    
    def manage_tags(self, args):
        """
        태그 관리
        
        Args:
            args: 명령줄 인수
        """
        # 태그 추가
        if args.add:
            if self.storage.add_tag(args.id, args.add):
                print(f"파일 {args.id}에 태그 '{args.add}' 추가 완료")
        
        # 태그 제거
        if args.remove:
            if self.storage.remove_tag(args.id, args.remove):
                print(f"파일 {args.id}에서 태그 '{args.remove}' 제거 완료")
        
        # 태그 목록 조회
        if args.list or (not args.add and not args.remove):
            tags = self.storage.get_file_tags(args.id)
            if tags:
                print(f"파일 {args.id}의 태그: {', '.join(tags)}")
            else:
                print(f"파일 {args.id}에 태그가 없습니다.")
    
    def show_stats(self):
        """데이터 통계 조회"""
        stats = self.storage.get_statistics()
        
        if not stats:
            print("통계 정보를 가져올 수 없습니다.")
            return
        
        print("\n=== 데이터 통계 ===")
        print(f"저장소 수: {stats['repository_count']}")
        print(f"파일 수: {stats['file_count']}")
        print(f"학습용으로 적합한 파일 수: {stats['suitable_file_count']}")
        print(f"태그 수: {stats['tag_count']}")
        print(f"평균 품질 점수: {stats['average_quality_score']:.2f}")
        print(f"평균 코드 라인 수: {stats['average_code_lines']:.1f}")
        
        if stats['license_distribution']:
            print("\n라이센스 분포:")
            for license_name, count in stats['license_distribution'].items():
                print(f"- {license_name}: {count}개")
    
    def export_data(self, args):
        """
        데이터 내보내기
        
        Args:
            args: 명령줄 인수
        """
        if args.format == 'csv':
            output_file = args.output if args.output else "code_data.csv"
            if self.storage.export_to_csv(output_file):
                print(f"CSV 파일로 내보내기 완료: {os.path.join(self.base_dir, output_file)}")
        elif args.format == 'json':
            output_file = args.output if args.output else "code_data.json"
            if self.storage.export_to_metadata():
                print(f"JSON 파일로 내보내기 완료: {self.storage.metadata_file}")
    
    def backup(self, args):
        """
        데이터 백업
        
        Args:
            args: 명령줄 인수
        """
        backup_dir = self.storage.backup_data(args.dir)
        if backup_dir:
            print(f"데이터 백업 완료: {backup_dir}")
    
    def sync_database(self):
        """메타데이터와 데이터베이스 동기화"""
        repo_count, file_count = self.storage.import_from_metadata()
        print(f"메타데이터에서 데이터베이스로 가져오기 완료: {repo_count}개 저장소, {file_count}개 파일")
        
        file_count = self.storage.export_to_metadata()
        print(f"데이터베이스에서 메타데이터로 내보내기 완료: {file_count}개 파일")
    
    def run(self, args=None):
        """
        명령줄 인터페이스 실행
        
        Args:
            args: 명령줄 인수 (None인 경우 sys.argv 사용)
        """
        parser = self.setup_parser()
        args = parser.parse_args(args)
        
        if not args.command:
            parser.print_help()
            return
        
        # 명령 실행
        if args.command == 'crawl':
            self.crawl(args)
        elif args.command == 'filter':
            self.filter_code(args)
        elif args.command == 'search':
            self.search(args)
        elif args.command == 'view':
            self.view_file(args)
        elif args.command == 'tag':
            self.manage_tags(args)
        elif args.command == 'stats':
            self.show_stats()
        elif args.command == 'export':
            self.export_data(args)
        elif args.command == 'backup':
            self.backup(args)
        elif args.command == 'sync':
            self.sync_database()
        else:
            parser.print_help()

# 메인 실행 코드
if __name__ == "__main__":
    try:
        # tabulate 패키지가 설치되어 있지 않으면 설치
        import tabulate
    except ImportError:
        import subprocess
        subprocess.run(["pip3", "install", "tabulate"], check=True)
        import tabulate
    
    # 관리 인터페이스 실행
    interface = CodeManagementInterface()
    interface.run()
