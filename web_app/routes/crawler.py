from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from web_app import db
from web_app.api import (
    crawl_by_query, crawl_repository, get_crawling_status, 
    get_code_statistics, search_code, get_file_content, 
    update_file_content, delete_file, manage_file_tag
)
import threading
import json
from web_app.models import CodeFile
from datetime import datetime
import logging
from flask import flash, redirect, url_for
import threading



logging.basicConfig(level=logging.DEBUG)
crawler = Blueprint('crawler', __name__)


# ✅ 크롤러 대시보드
@crawler.route('/')
def index():
    return render_template('crawler/index.html', title='크롤러 관리')


# ✅ 새 크롤링 작업 시작
@crawler.route('/new', methods=['GET', 'POST'])
def new_crawl():
    if request.method == 'POST':
        query = request.form.get('query', 'language:python stars:>1000')
        max_repos = int(request.form.get('max_repos', 5))
        max_files = int(request.form.get('max_files', 10))

        try:
            thread = threading.Thread(
                target=crawl_by_query,
                args=(query, max_repos, max_files)
            )
            thread.daemon = True
            thread.start()

            flash(f'크롤링 작업이 시작되었습니다. 쿼리: {query}', 'success')
            return redirect(url_for('crawler.status'))
        except Exception as e:
            flash(f'크롤링 작업 시작 중 오류 발생: {str(e)}', 'danger')

    return render_template('crawler/new.html', title='새 크롤링 작업')

    
@crawler.route('/stats')
def stats():
    """통계 페이지"""
    # 여기에서 통계 데이터를 처리하고 렌더링
    return render_template('crawler/stats.html', title="크롤링 통계")

# ✅ 크롤링 상태 확인
@crawler.route('/status')
def status():
    return render_template('crawler/status.html', title='크롤링 상태')


# ✅ API: 쿼리 기반 크롤링 시작
@crawler.route('/api/start', methods=['POST'])
def api_start_crawl():
    data = request.get_json()
    query = data.get('query', 'language:python stars:>1000')
    max_repos = int(data.get('max_repos', 5))
    max_files = int(data.get('max_files', 10))

    try:
        thread = threading.Thread(
            target=crawl_by_query,
            args=(query, max_repos, max_files)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': f'크롤링 작업이 시작되었습니다. 쿼리: {query}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'크롤링 작업 시작 중 오류 발생: {str(e)}'
        }), 500


# ✅ API: URL 기반 크롤링 시작
@crawler.route('/api/start_url', methods=['POST'])
def api_start_url_crawl():
    data = request.get_json()
    repo_url = data.get('repo_url', '')
    max_files = int(data.get('max_files', 10))

    if not repo_url or 'github.com' not in repo_url:
        return jsonify({
            'success': False,
            'message': '유효한 GitHub 저장소 URL을 입력해주세요.'
        }), 400

    try:
        thread = threading.Thread(
            target=crawl_repository,
            args=(repo_url, max_files)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': f'URL 크롤링 작업이 시작되었습니다. URL: {repo_url}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'크롤링 작업 시작 중 오류 발생: {str(e)}'
        }), 500


# ✅ API: 크롤링 상태 조회
@crawler.route('/api/status')
def api_status():
    try:
        status = get_crawling_status()
        return jsonify({ 'success': True, 'data': status })
    except Exception as e:
        return jsonify({ 'success': False, 'message': str(e) }), 500


# ✅ 업로드 페이지 (업로드 전용 템플릿이 필요할 경우)
@crawler.route("/upload", methods=["GET"])
def upload_page():
    return render_template("crawler/upload.html", title="메타데이터 업로드")


# ✅ 로컬 메타데이터 import
@crawler.route('/import', endpoint='import_metadata')
def import_metadata():
    try:
        with open('metadata.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            # downloaded_at 문자열을 datetime 객체로 변환
            downloaded_at_str = item.get("downloaded_at")
            if downloaded_at_str:
                downloaded_at = datetime.fromisoformat(downloaded_at_str)
            else:
                downloaded_at = None  # 값이 없을 경우 None으로 처리

            code = CodeFile(
                repo_name=item.get("repo_name"),
                file_name=item.get("file_name"),
                file_path=item.get("file_path"),
                local_path=item.get("local_path"),
                file_url=item.get("file_url"),
                quality_score=item.get("quality_score"),
                downloaded_at=downloaded_at  # datetime 객체로 저장
            )
            db.session.add(code)

        db.session.commit()
        flash('로컬 메타데이터를 성공적으로 불러왔습니다.', 'success')
    except Exception as e:
        flash(f'메타데이터 불러오기 실패: {str(e)}', 'danger')

    return redirect(url_for('crawler.index'))

@crawler.route('/show_db', endpoint='show_db')
def show_db():
    """DB 내용 출력"""
    try:
        # CodeFile 모델에서 모든 항목을 불러와서 출력
        codes = CodeFile.query.all()
        
        # 터미널에 DB 내용 출력
        for code in codes:
            print(f"Repo Name: {code.repo_name}, File Name: {code.file_name}, Downloaded At: {code.downloaded_at}")
        
        flash('DB 내용을 터미널에 출력했습니다.', 'success')
    except Exception as e:
        flash(f'DB 출력 중 오류 발생: {str(e)}', 'danger')
    
    return redirect(url_for('crawler.index'))


@crawler.route('/crawl_by_url', methods=['POST'])
def crawl_by_url():
    repo_url = request.form.get('repo_url')
    max_files = int(request.form.get('max_files', 10))

    if not repo_url:
        flash('GitHub 저장소 URL을 입력해주세요.', 'warning')
        return redirect(url_for('crawler.new'))

    try:
        threading.Thread(target=crawl_repository, args=(repo_url, max_files)).start()
        flash(f'크롤링을 시작했습니다: {repo_url}', 'info')
        return redirect(url_for('crawler.status'))
    except Exception as e:
        flash(f'크롤링 실패: {str(e)}', 'danger')
        return redirect(url_for('crawler.new'))
