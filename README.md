# CodeHarvester (or your chosen name)

🧠 GitHub에서 파이썬 코드를 자동 수집하고, 품질을 분석해 학습에 적합한 코드를 선별하는 웹 기반 시스템입니다.

## 기능
- GitHub 검색 쿼리 또는 저장소 URL 기반 코드 크롤링
- pylint + radon 기반 품질 분석
- 학습용 코드 필터링
- Flask 기반 대시보드로 코드/통계 확인

## 사용법
1. `.env` 파일에 GitHub 토큰 설정
2. `pip install -r requirements.txt`
3. `python run_web_app.py` 실행
4. 웹에서 크롤링 관리

## 예시 화면
스크린샷 추가 예정...


### todo

1. 깃헙의 모든 파일에 대해서 크롤링(현재는 원하는 수만 가져오도록 되어 있음)  
2. 각 코드에 대해서 graph로 표현을 가능하도록 만듬  