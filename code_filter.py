#!/usr/bin/env python3
"""
코드 품질 필터

GitHub에서 수집한 파이썬 코드의 품질을 평가하고 필터링하는 모듈입니다.
학습용으로 적합한 코드를 선별하는 기능을 제공합니다.
"""

import os
import json
import re
import subprocess
from pylint import lint
from pylint.reporters.text import TextReporter
from io import StringIO

class CodeQualityFilter:
    """파이썬 코드 품질을 평가하고 필터링하는 클래스"""
    
    def __init__(self, metadata_file="collected_code/metadata.json"):
        """
        코드 품질 필터 초기화
        
        Args:
            metadata_file (str): 메타데이터 파일 경로
        """
        self.metadata_file = metadata_file
        self.min_quality_score = 6.0  # 최소 품질 점수 (0-10)
        self.min_code_lines = 10      # 최소 코드 라인 수
        self.max_code_lines = 1000    # 최대 코드 라인 수
        self.allowed_licenses = [     # 학습용으로 허용된 라이센스 목록
            "MIT License", 
            "Apache License 2.0",
            "BSD License",
            "GNU General Public License v3.0",
            "GNU Lesser General Public License v3.0",
            None  # 라이센스 정보가 없는 경우도 포함
        ]
    
    def load_metadata(self):
        """
        메타데이터 로드
        
        Returns:
            list: 메타데이터 목록
        """
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"메타데이터 로드 오류: {str(e)}")
            return []
    
    def save_metadata(self, metadata):
        """
        메타데이터 저장
        
        Args:
            metadata (list): 메타데이터 목록
        """
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"메타데이터 저장 오류: {str(e)}")
    
    def evaluate_code_quality(self, file_path):
        """
        pylint를 사용하여 코드 품질 평가
        
        Args:
            file_path (str): 파이썬 파일 경로
            
        Returns:
            float: 품질 점수 (0-10)
        """
        if not os.path.exists(file_path):
            print(f"파일이 존재하지 않습니다: {file_path}")
            return 0.0
            
        # pylint 출력을 캡처하기 위한 StringIO 객체
        pylint_output = StringIO()
        reporter = TextReporter(pylint_output)
        
        try:
            # pylint 실행
            lint.Run([
                '--disable=C0111',  # 문서화 경고 비활성화
                '--disable=C0103',  # 이름 규칙 경고 비활성화
                file_path
            ], reporter=reporter, exit=False)
            
            # 결과에서 점수 추출
            output = pylint_output.getvalue()
            match = re.search(r'Your code has been rated at ([-\d.]+)/10', output)
            
            if match:
                score = float(match.group(1))
                # 음수 점수를 0으로 처리
                return max(0.0, score)
            else:
                print(f"품질 점수를 찾을 수 없습니다: {file_path}")
                return 0.0
                
        except Exception as e:
            print(f"코드 품질 평가 오류: {str(e)}")
            return 0.0
    
    def count_code_lines(self, file_path):
        """
        파이썬 파일의 코드 라인 수 계산 (주석 및 빈 줄 제외)
        
        Args:
            file_path (str): 파이썬 파일 경로
            
        Returns:
            int: 코드 라인 수
        """
        if not os.path.exists(file_path):
            return 0
            
        try:
            # 주석 및 빈 줄을 제외한 라인 수 계산
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            code_lines = 0
            in_multiline_comment = False
            
            for line in lines:
                line = line.strip()
                
                # 빈 줄 건너뛰기
                if not line:
                    continue
                    
                # 멀티라인 주석 처리
                if '"""' in line or "'''" in line:
                    # 한 줄에 멀티라인 주석이 시작되고 끝나는 경우
                    if line.count('"""') == 2 or line.count("'''") == 2:
                        continue
                    
                    in_multiline_comment = not in_multiline_comment
                    continue
                
                # 멀티라인 주석 내부 건너뛰기
                if in_multiline_comment:
                    continue
                
                # 한 줄 주석 건너뛰기
                if line.startswith('#'):
                    continue
                
                code_lines += 1
                
            return code_lines
            
        except Exception as e:
            print(f"코드 라인 수 계산 오류: {str(e)}")
            return 0
    
    def check_license_compatibility(self, license_name):
        """
        라이센스 호환성 확인
        
        Args:
            license_name (str): 라이센스 이름
            
        Returns:
            bool: 학습용으로 사용 가능한지 여부
        """
        if license_name in self.allowed_licenses:
            return True
        
        # 부분 일치 확인 (예: "MIT"가 "MIT License"에 포함됨)
        for allowed_license in self.allowed_licenses:
            if allowed_license and license_name and allowed_license in license_name:
                return True
        
        return False
    
    def check_code_complexity(self, file_path):
        """
        코드 복잡도 확인
        
        Args:
            file_path (str): 파이썬 파일 경로
            
        Returns:
            dict: 복잡도 정보
        """
        try:
            # radon 패키지가 설치되어 있지 않으면 설치
            try:
                import radon
            except ImportError:
                subprocess.run(["pip3", "install", "radon"], check=True)
                
            # 순환 복잡도 계산
            result = subprocess.run(
                ["radon", "cc", file_path, "--json"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout:
                complexity_data = json.loads(result.stdout)
                
                if complexity_data and file_path in complexity_data:
                    functions = complexity_data[file_path]
                    
                    # 평균 복잡도 계산
                    if functions:
                        total_complexity = sum(func['complexity'] for func in functions)
                        avg_complexity = total_complexity / len(functions)
                        
                        return {
                            'avg_complexity': avg_complexity,
                            'function_count': len(functions),
                            'max_complexity': max(func['complexity'] for func in functions)
                        }
            
            # 기본값 반환
            return {
                'avg_complexity': 0,
                'function_count': 0,
                'max_complexity': 0
            }
            
        except Exception as e:
            print(f"코드 복잡도 확인 오류: {str(e)}")
            return {
                'avg_complexity': 0,
                'function_count': 0,
                'max_complexity': 0
            }
    
    def is_suitable_for_learning(self, file_path, metadata_item):
        """
        코드가 학습용으로 적합한지 확인
        
        Args:
            file_path (str): 파이썬 파일 경로
            metadata_item (dict): 메타데이터 항목
            
        Returns:
            tuple: (적합 여부, 이유)
        """
        # 파일 존재 확인
        if not os.path.exists(file_path):
            return False, "파일이 존재하지 않음"
        
        # 라이센스 확인
        license_name = metadata_item.get('repo_license')
        if not self.check_license_compatibility(license_name):
            return False, f"라이센스 호환성 문제 ({license_name})"
        
        # 코드 라인 수 확인
        code_lines = self.count_code_lines(file_path)
        if code_lines < self.min_code_lines:
            return False, f"코드 라인 수 부족 ({code_lines} < {self.min_code_lines})"
        if code_lines > self.max_code_lines:
            return False, f"코드 라인 수 초과 ({code_lines} > {self.max_code_lines})"
        
        # 코드 품질 평가
        quality_score = self.evaluate_code_quality(file_path)
        if quality_score < self.min_quality_score:
            return False, f"품질 점수 미달 ({quality_score:.1f} < {self.min_quality_score})"
        
        # 모든 조건 통과
        return True, "학습용으로 적합함"
    
    def filter_code(self):
        """
        수집된 코드를 필터링하고 메타데이터 업데이트
        
        Returns:
            tuple: (적합한 파일 수, 부적합한 파일 수)
        """
        metadata = self.load_metadata()
        
        suitable_count = 0
        unsuitable_count = 0
        
        for item in metadata:
            file_path = item.get('local_path')
            
            if not file_path:
                continue
                
            # 학습 적합성 확인
            is_suitable, reason = self.is_suitable_for_learning(file_path, item)
            
            # 품질 점수 계산
            quality_score = self.evaluate_code_quality(file_path)
            
            # 메타데이터 업데이트
            item['quality_score'] = round(quality_score, 2)
            item['code_lines'] = self.count_code_lines(file_path)
            item['is_suitable'] = is_suitable
            item['unsuitable_reason'] = None if is_suitable else reason
            
            # 복잡도 정보 추가
            complexity_info = self.check_code_complexity(file_path)
            item['complexity'] = complexity_info
            
            # 카운터 업데이트
            if is_suitable:
                suitable_count += 1
            else:
                unsuitable_count += 1
        
        # 업데이트된 메타데이터 저장
        self.save_metadata(metadata)
        
        print(f"필터링 완료: 적합한 파일 {suitable_count}개, 부적합한 파일 {unsuitable_count}개")
        return suitable_count, unsuitable_count
    
    def get_suitable_files(self):
        """
        학습용으로 적합한 파일 목록 반환
        
        Returns:
            list: 적합한 파일 메타데이터 목록
        """
        metadata = self.load_metadata()
        return [item for item in metadata if item.get('is_suitable', False)]
    
    def get_unsuitable_files(self):
        """
        학습용으로 부적합한 파일 목록 반환
        
        Returns:
            list: 부적합한 파일 메타데이터 목록
        """
        metadata = self.load_metadata()
        return [item for item in metadata if not item.get('is_suitable', False)]

# 테스트 코드
if __name__ == "__main__":
    # 코드 품질 필터 인스턴스 생성
    filter = CodeQualityFilter()
    
    # 필터링 실행
    suitable, unsuitable = filter.filter_code()
    
    print(f"적합한 파일: {suitable}개")
    print(f"부적합한 파일: {unsuitable}개")
