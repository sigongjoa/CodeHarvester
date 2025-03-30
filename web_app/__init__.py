# web_app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# db 객체는 여기서만 정의하고
db = SQLAlchemy()

# Flask 애플리케이션 초기화
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../collected_code/code_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db를 app에 바인딩
db.init_app(app)

# Blueprint 등록
from web_app.routes.main import main as main_blueprint
app.register_blueprint(main_blueprint)

from web_app.routes.crawler import crawler as crawler_blueprint
app.register_blueprint(crawler_blueprint, url_prefix='/crawler')

from web_app.routes.code import code as code_blueprint
app.register_blueprint(code_blueprint, url_prefix='/code')

from web_app.routes.code_crud import code_crud as code_crud_blueprint
app.register_blueprint(code_crud_blueprint, url_prefix='/code_crud')

# 라우트 목록 출력
print("📌 현재 등록된 라우트 목록:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint:30} → {rule.rule}")
