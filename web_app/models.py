# web_app/models.py

from web_app import db  # db는 __init__.py에서 이미 초기화된 객체

# 예시 모델
class CodeFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repo_name = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(255))
    local_path = db.Column(db.String(255))
    file_url = db.Column(db.String(255))
    quality_score = db.Column(db.Float)
    downloaded_at = db.Column(db.DateTime)
