import unittest
import os
import sys
import tempfile
import shutil
from flask import Flask

# 테스트 환경 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web_app import app as flask_app

class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        """테스트 환경 설정"""
        self.app = flask_app.test_client()
        self.app_context = flask_app.app_context()
        self.app_context.push()
        
        # 테스트용 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """테스트 환경 정리"""
        self.app_context.pop()
        
        # 테스트용 임시 디렉토리 삭제
        shutil.rmtree(self.test_dir)
    
    def test_main_page(self):
        """메인 페이지 테스트"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'GitHub \xed\x8c\x8c\xec\x9d\xb4\xec\x8d\xac \xec\xbd\x94\xeb\x93\x9c \xea\xb4\x80\xeb\xa6\xac', response.data)  # "GitHub 파이썬 코드 관리" 텍스트 확인
    
    def test_about_page(self):
        """소개 페이지 테스트"""
        response = self.app.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xec\x8b\x9c\xec\x8a\xa4\xed\x85\x9c \xec\x86\x8c\xea\xb0\x9c', response.data)  # "시스템 소개" 텍스트 확인
    
    def test_crawler_index(self):
        """크롤러 관리 페이지 테스트"""
        response = self.app.get('/crawler/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xed\x81\xac\xeb\xa1\xa4\xeb\x9f\xac \xea\xb4\x80\xeb\xa6\xac', response.data)  # "크롤러 관리" 텍스트 확인
    
    def test_crawler_new(self):
        """새 크롤링 작업 페이지 테스트"""
        response = self.app.get('/crawler/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xec\x83\x88 \xed\x81\xac\xeb\xa1\xa4\xeb\xa7\x81 \xec\x9e\x91\xec\x97\x85', response.data)  # "새 크롤링 작업" 텍스트 확인
    
    def test_crawler_status(self):
        """크롤링 상태 페이지 테스트"""
        response = self.app.get('/crawler/status')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xed\x81\xac\xeb\xa1\xa4\xeb\xa7\x81 \xec\x83\x81\xed\x83\x9c', response.data)  # "크롤링 상태" 텍스트 확인
    
    def test_code_index(self):
        """코드 목록 페이지 테스트"""
        response = self.app.get('/code/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xec\xbd\x94\xeb\x93\x9c \xeb\xaa\xa9\xeb\xa1\x9d', response.data)  # "코드 목록" 텍스트 확인
    
    def test_code_stats(self):
        """코드 통계 페이지 테스트"""
        response = self.app.get('/code/stats')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xec\xbd\x94\xeb\x93\x9c \xed\x86\xb5\xea\xb3\x84', response.data)  # "코드 통계" 텍스트 확인
    
    def test_batch_operations(self):
        """일괄 작업 페이지 테스트"""
        response = self.app.get('/code_crud/batch')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xec\x9d\xbc\xea\xb4\x84 \xec\x9e\x91\xec\x97\x85', response.data)  # "일괄 작업" 텍스트 확인
    
    def test_export_page(self):
        """데이터 내보내기 페이지 테스트"""
        response = self.app.get('/code_crud/export')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xeb\x8d\xb0\xec\x9d\xb4\xed\x84\xb0 \xeb\x82\xb4\xeb\xb3\xb4\xeb\x82\xb4\xea\xb8\xb0', response.data)  # "데이터 내보내기" 텍스트 확인
    
    def test_api_stats(self):
        """API: 코드 통계 테스트"""
        response = self.app.get('/code/api/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertIn('repository_count', data)
        self.assertIn('file_count', data)
        self.assertIn('suitable_file_count', data)
        self.assertIn('average_quality_score', data)
    
    def test_api_list(self):
        """API: 코드 목록 테스트"""
        response = self.app.get('/code/api/list')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertIsInstance(data, list)
    
    def test_api_crawler_status(self):
        """API: 크롤링 상태 테스트"""
        response = self.app.get('/crawler/api/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertIn('current_job', data)
        self.assertIn('history', data)

if __name__ == '__main__':
    unittest.main()
