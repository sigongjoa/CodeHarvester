# GitHub 파이썬 코드 크롤링 및 웹 관리 시스템

이 시스템은 GitHub에서 파이썬 코드를 자동으로 수집하고, 코드 품질을 평가하여 학습용으로 적합한 코드만 필터링한 후, 웹 인터페이스를 통해 효율적으로 관리할 수 있는 기능을 제공합니다.

## 주요 기능

- GitHub API를 사용한 파이썬 저장소 검색 및 코드 수집
- 특정 GitHub 저장소 URL 입력을 통한 직접 크롤링
- pylint를 사용한 코드 품질 평가
- 학습용으로 적합한 코드 필터링
- 코드 및 메타데이터 관리 (CRUD 기능)
- 코드 검색, 태그 관리, 통계 조회
- 웹 인터페이스를 통한 편리한 사용
- 데이터 내보내기 및 일괄 작업 기능

## 시스템 구성

- **크롤러 모듈**: GitHub API를 사용하여 파이썬 코드를 크롤링
- **필터 모듈**: 코드 품질을 평가하고 필터링
- **저장소 모듈**: 코드 및 메타데이터를 저장하고 관리
- **웹 인터페이스**: 사용자 친화적인 웹 기반 관리 도구

## 설치 방법

### 요구 사항

- Python 3.6 이상
- pip (Python 패키지 관리자)
- Git

### 설치 단계

1. 저장소 클론:
   ```bash
   git clone https://github.com/yourusername/github_python_crawler.git
   cd github_python_crawler
   ```

2. 필요한 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```

3. 데이터 저장 디렉토리 생성:
   ```bash
   mkdir -p collected_code/exports
   ```

## 실행 방법

### 웹 애플리케이션 실행

```bash
python run_web_app.py
```

웹 애플리케이션은 기본적으로 http://localhost:5000 에서 접근할 수 있습니다.

### 테스트 실행

```bash
python test_web_app.py
```

## 사용 방법

### 1. 크롤링 작업 시작

1. 웹 브라우저에서 http://localhost:5000 접속
2. "크롤러 관리" 메뉴 선택
3. "새 크롤링 작업 시작" 버튼 클릭
4. 검색 쿼리 입력 또는 GitHub 저장소 URL 입력
5. 크롤링 옵션 설정 (최대 저장소 수, 최대 파일 수 등)
6. "크롤링 시작" 버튼 클릭

### 2. 크롤링 상태 확인

1. "크롤러 관리" 메뉴에서 "크롤링 상태" 탭 선택
2. 현재 진행 중인 크롤링 작업과 최근 완료된 작업 확인

### 3. 코드 관리

1. "코드 목록" 메뉴 선택
2. 수집된 코드 목록 확인
3. 검색 및 필터링 기능을 사용하여 원하는 코드 찾기
4. 코드 클릭하여 상세 내용 확인
5. 코드 편집, 태그 추가/제거, 삭제 등의 작업 수행

### 4. 통계 확인

1. "코드 통계" 메뉴 선택
2. 저장소별 파일 수, 품질 점수 분포, 태그 분포 등의 통계 확인

### 5. 일괄 작업

1. "일괄 작업" 메뉴 선택
2. 여러 파일 선택 후 태그 추가/제거 또는 일괄 삭제 작업 수행

### 6. 데이터 내보내기

1. "데이터 내보내기" 메뉴 선택
2. 내보내기 형식(CSV, JSON) 선택
3. 필터링 옵션 설정
4. "내보내기 시작" 버튼 클릭
5. 생성된 파일 다운로드

## API 문서

### 크롤러 API

- `GET /crawler/api/status`: 크롤링 작업 상태 조회
- `POST /crawler/api/start`: 검색 쿼리로 크롤링 작업 시작
- `POST /crawler/api/start_url`: 저장소 URL로 크롤링 작업 시작

### 코드 API

- `GET /code/api/list`: 코드 목록 조회
- `GET /code/api/stats`: 코드 통계 정보 조회
- `GET /code_crud/api/file/<file_id>`: 파일 정보 및 내용 조회
- `PUT /code_crud/api/file/<file_id>`: 파일 내용 업데이트
- `DELETE /code_crud/api/file/<file_id>`: 파일 삭제
- `POST /code_crud/api/file/<file_id>/tag`: 태그 관리
- `POST /code_crud/api/batch/tag`: 일괄 태그 관리
- `POST /code_crud/api/batch/delete`: 일괄 삭제
- `POST /code_crud/api/export`: 데이터 내보내기

## 시스템 구조

```
github_python_crawler/
├── github_crawler.py      # GitHub 크롤러 모듈
├── code_filter.py         # 코드 품질 필터 모듈
├── code_storage.py        # 코드 저장소 모듈
├── manager.py             # 명령줄 관리 모듈
├── run_web_app.py         # 웹 애플리케이션 실행 스크립트
├── test_web_app.py        # 웹 애플리케이션 테스트
├── collected_code/        # 수집된 코드 저장 디렉토리
│   ├── exports/           # 내보내기 파일 저장 디렉토리
│   └── ...
└── web_app/               # 웹 애플리케이션
    ├── __init__.py        # 애플리케이션 초기화
    ├── api.py             # API 함수
    ├── routes/            # 라우트 모듈
    │   ├── main.py        # 메인 라우트
    │   ├── crawler.py     # 크롤러 관리 라우트
    │   ├── code.py        # 코드 관리 라우트
    │   └── code_crud.py   # 코드 CRUD 라우트
    ├── static/            # 정적 파일
    │   ├── css/           # CSS 파일
    │   ├── js/            # JavaScript 파일
    │   └── img/           # 이미지 파일
    └── templates/         # HTML 템플릿
        ├── base.html      # 기본 템플릿
        ├── index.html     # 메인 페이지
        ├── about.html     # 소개 페이지
        ├── crawler/       # 크롤러 관련 템플릿
        └── code/          # 코드 관련 템플릿
```

## 문제 해결

### 크롤링이 작동하지 않는 경우

1. GitHub API 요청 제한에 도달했을 수 있습니다. 잠시 후 다시 시도하세요.
2. 인터넷 연결을 확인하세요.
3. 로그 파일을 확인하여 오류 메시지를 확인하세요.

### 웹 애플리케이션이 시작되지 않는 경우

1. 필요한 모든 패키지가 설치되어 있는지 확인하세요.
2. 포트 5000이 이미 사용 중인지 확인하세요.
3. 로그 파일을 확인하여 오류 메시지를 확인하세요.

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 기여 방법

1. 이 저장소를 포크합니다.
2. 새 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`).
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 생성합니다.
