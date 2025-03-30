from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from web_app.api import (
    get_code_statistics, search_code, get_file_content, 
    update_file_content, delete_file, manage_file_tag
)

code = Blueprint('code', __name__)

@code.route('/')
def index():
    """코드 목록 페이지"""
    # 검색 매개변수
    query = request.args.get('query', '')
    suitable_only = request.args.get('suitable_only') == 'true'
    min_quality = request.args.get('min_quality', 0)
    if min_quality:
        min_quality = float(min_quality)
    
    # 코드 검색
    results = search_code(
        query=query,
        suitable_only=suitable_only,
        min_quality=min_quality,
        limit=100
    )
    
    return render_template('code/index.html', 
                          title='코드 목록', 
                          codes=results, 
                          query=query, 
                          suitable_only=suitable_only, 
                          min_quality=min_quality)

@code.route('/<int:code_id>')
def view(code_id):
    """코드 상세 조회 페이지"""
    # 파일 정보 및 내용 가져오기
    code_info, content = get_file_content(code_id)
    
    if not code_info:
        flash('코드를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('code.index'))
    
    return render_template('code/view.html', 
                          title=code_info['name'], 
                          code=code_info, 
                          content=content,
                          tags=code_info.get('tags', []))

@code.route('/<int:code_id>/edit', methods=['GET', 'POST'])
def edit(code_id):
    """코드 편집 페이지"""
    if request.method == 'POST':
        # 파일 내용 업데이트
        content = request.form.get('content', '')
        success, message = update_file_content(code_id, content)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('code.view', code_id=code_id))
        else:
            flash(message, 'danger')
    
    # 파일 정보 및 내용 가져오기
    code_info, content = get_file_content(code_id)
    
    if not code_info:
        flash('코드를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('code.index'))
    
    return render_template('code/edit.html', 
                          title=f"편집: {code_info['name']}", 
                          code=code_info, 
                          content=content)

@code.route('/<int:code_id>/delete', methods=['POST'])
def delete(code_id):
    """코드 삭제"""
    success, message = delete_file(code_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('code.index'))

@code.route('/<int:code_id>/tag', methods=['POST'])
def manage_tag(code_id):
    """태그 관리"""
    action = request.form.get('action')
    tag_name = request.form.get('tag_name')
    
    if not tag_name:
        flash('태그 이름을 입력해주세요.', 'warning')
        return redirect(url_for('code.view', code_id=code_id))
    
    success, message = manage_file_tag(code_id, tag_name, action)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('code.view', code_id=code_id))

@code.route('/stats')
def stats():
    """코드 통계"""
    from web_app import db
    from web_app.models import CodeFile  # Move import here
    try:
        # 데이터베이스에서 코드 통계 추출
        repo_count = db.session.query(CodeFile.repo_name).distinct().count()
        file_count = db.session.query(CodeFile.file_name).count()
        suitable_count = db.session.query(CodeFile).filter(CodeFile.quality_score >= 6).count()
        avg_quality = db.session.query(db.func.avg(CodeFile.quality_score)).scalar()

        # 디버깅용 로그 추가
        print(f"repo_count: {repo_count}, file_count: {file_count}, suitable_count: {suitable_count}, avg_quality: {avg_quality}")

        return render_template('code/stats.html', repo_count=repo_count, file_count=file_count,
                               suitable_count=suitable_count, avg_quality=avg_quality)
    except Exception as e:
        print(f"통계 조회 오류: {str(e)}")
        return render_template('code/stats.html', error_message="통계 조회 중 오류가 발생했습니다.")


    

@code.route('/api/list')
def api_list():
    """API: 코드 목록"""
    # 검색 매개변수
    query = request.args.get('query', '')
    suitable_only = request.args.get('suitable_only') == 'true'
    min_quality = request.args.get('min_quality')
    limit = request.args.get('limit', 100, type=int)
    
    if min_quality:
        min_quality = float(min_quality)
    
    # 코드 검색
    results = search_code(
        query=query,
        suitable_only=suitable_only,
        min_quality=min_quality,
        limit=limit
    )
    
    return jsonify(results)

@code.route('/api/stats')
def api_stats():
    """API: 코드 통계"""
    stats = get_code_statistics()
    return jsonify(stats)

