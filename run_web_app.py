import os
import sys
import time

# 🔧 상위 디렉토리를 PYTHONPATH에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 🛠 실행 파일 경로 출력
print(f"🚀 run_web_app.py 실행됨 @ {os.path.abspath(__file__)}")

# 🧩 Flask 앱 임포트
try:
    from web_app import app, db
    print("✅ Flask 앱 임포트 성공")
except Exception as e:
    print("❌ Flask 앱 임포트 실패:", e)
    raise

# 🛠 데이터베이스 테이블 생성
try:
    with app.app_context():
        db.create_all()  # 데이터베이스 테이블 생성
        print("📌 데이터베이스 테이블이 생성되었습니다.")
except Exception as e:
    print("❌ 데이터베이스 테이블 생성 중 오류:", e)

# 🛤 라우트 목록 출력
print("\n📌 현재 등록된 라우트 목록:")
time.sleep(0.5)
try:
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint:30} → {rule.rule}")
except Exception as e:
    print("❌ 라우트 출력 중 오류:", e)

# 🛰 Flask 서버 실행
print("\n🚀 Flask 서버 시작 중...\n")
app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
