from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from web_app import db
from web_app.api import (
    search_code, get_file_content, update_file_content, 
    delete_file, manage_file_tag, get_code_statistics
)
import json
import os

# CRUD 관련 추가 기능 구현
code_crud = Blueprint('code_crud', __name__)

@code_crud.route('/api/file/<int:file_id>', methods=['GET'])
def api_get_file(file_id):
    """API: 파일 정보 및 내용 조회"""
    code_info, content = get_file_content(file_id)
    
    if not code_info:
        return jsonify({
            'success': False,
            'message': '파일을 찾을 수 없습니다.'
        }), 404
    
    return jsonify({
        'success': True,
        'file': code_info,
        'content': content
    })

@code_crud.route('/api/file/<int:file_id>', methods=['PUT'])
def api_update_file(file_id):
    """API: 파일 내용 업데이트"""
    data = request.get_json()
    content = data.get('content', '')
    
    success, message = update_file_content(file_id, content)
    
    return jsonify({
        'success': success,
        'message': message
    }), 200 if success else 400

@code_crud.route('/api/file/<int:file_id>', methods=['DELETE'])
def api_delete_file(file_id):
    """API: 파일 삭제"""
    success, message = delete_file(file_id)
    
    return jsonify({
        'success': success,
        'message': message
    }), 200 if success else 400

@code_crud.route('/api/file/<int:file_id>/tag', methods=['POST'])
def api_manage_tag(file_id):
    """API: 태그 관리"""
    data = request.get_json()
    action = data.get('action')
    tag_name = data.get('tag_name')
    
    if not tag_name or action not in ['add', 'remove']:
        return jsonify({
            'success': False,
            'message': '유효하지 않은 요청입니다.'
        }), 400
    
    success, message = manage_file_tag(file_id, tag_name, action)
    
    return jsonify({
        'success': success,
        'message': message
    }), 200 if success else 400

@code_crud.route('/batch', methods=['GET'])
def batch_operations():
    """일괄 작업 페이지"""
    return render_template('code/batch.html', title='일괄 작업')

@code_crud.route('/api/batch/tag', methods=['POST'])
def api_batch_tag():
    """API: 일괄 태그 관리"""
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    action = data.get('action')
    tag_name = data.get('tag_name')
    
    if not file_ids or not tag_name or action not in ['add', 'remove']:
        return jsonify({
            'success': False,
            'message': '유효하지 않은 요청입니다.'
        }), 400
    
    results = []
    for file_id in file_ids:
        success, message = manage_file_tag(file_id, tag_name, action)
        results.append({
            'file_id': file_id,
            'success': success,
            'message': message
        })
    
    return jsonify({
        'success': True,
        'results': results
    })

@code_crud.route('/api/batch/delete', methods=['POST'])
def api_batch_delete():
    """API: 일괄 삭제"""
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    
    if not file_ids:
        return jsonify({
            'success': False,
            'message': '유효하지 않은 요청입니다.'
        }), 400
    
    results = []
    for file_id in file_ids:
        success, message = delete_file(file_id)
        results.append({
            'file_id': file_id,
            'success': success,
            'message': message
        })
    
    return jsonify({
        'success': True,
        'results': results
    })

@code_crud.route('/export', methods=['GET'])
def export_page():
    """데이터 내보내기 페이지"""
    return render_template('code/export.html', title='데이터 내보내기')

@code_crud.route('/api/export', methods=['POST'])
def api_export():
    """API: 데이터 내보내기"""
    data = request.get_json()
    format_type = data.get('format', 'csv')
    query = data.get('query', '')
    suitable_only = data.get('suitable_only', False)
    min_quality = data.get('min_quality')
    
    if min_quality:
        min_quality = float(min_quality)
    
    # 코드 검색
    results = search_code(
        query=query,
        suitable_only=suitable_only,
        min_quality=min_quality,
        limit=1000  # 내보내기는 더 많은 결과를 허용
    )
    
    # 내보내기 디렉토리 확인
    export_dir = os.path.join('collected_code', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # 파일명 생성
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"code_export_{timestamp}.{format_type}"
    filepath = os.path.join(export_dir, filename)
    
    # 내보내기 형식에 따라 처리
    if format_type == 'csv':
        import csv
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 헤더 작성
            writer.writerow(['ID', '파일명', '저장소', '품질 점수', '코드 라인', '적합성', '태그', '로컬 경로'])
            # 데이터 작성
            for item in results:
                writer.writerow([
                    item['id'],
                    item['name'],
                    item['repo_name'],
                    item.get('quality_score', 'N/A'),
                    item.get('code_lines', 0),
                    'Yes' if item.get('is_suitable', False) else 'No',
                    ', '.join(item.get('tags', [])),
                    item['local_path']
                ])
    elif format_type == 'json':
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
    else:
        return jsonify({
            'success': False,
            'message': f'지원하지 않는 형식: {format_type}'
        }), 400
    
    # 상대 경로 반환
    relative_path = os.path.join('exports', filename)
    
    return jsonify({
        'success': True,
        'message': f'{len(results)}개 항목이 {format_type} 형식으로 내보내기 되었습니다.',
        'file_path': relative_path,
        'file_name': filename
    })

@code_crud.route('/download/<path:filename>')
def download_file(filename):
    """내보내기 파일 다운로드"""
    from flask import send_from_directory
    
    # 보안을 위해 경로 검증
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    return send_from_directory('collected_code', filename, as_attachment=True)
