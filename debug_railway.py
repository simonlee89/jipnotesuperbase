import sqlite3
import os

print("=== Railway 디버깅 스크립트 ===")

# 환경 확인
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"환경변수 DATABASE_URL: {os.environ.get('DATABASE_URL', 'None')}")

# 파일 존재 확인
db_paths = ['/data/integrated.db', 'integrated.db', './integrated.db']
for path in db_paths:
    if os.path.exists(path):
        print(f"✅ {path} 존재함")
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute('SELECT count(*) FROM employee_customers')
            count = cursor.fetchone()[0]
            print(f"   고객 수: {count}")
            
            cursor.execute('SELECT management_site_id, customer_name FROM employee_customers LIMIT 3')
            customers = cursor.fetchall()
            for customer in customers:
                print(f"   - {customer[0]}: {customer[1]}")
            conn.close()
        except Exception as e:
            print(f"   ❌ DB 연결 오류: {e}")
    else:
        print(f"❌ {path} 없음")

print("\n=== /data 디렉토리 확인 ===")
if os.path.exists('/data'):
    print("✅ /data 디렉토리 존재")
    try:
        files = os.listdir('/data')
        print(f"   파일 목록: {files}")
    except Exception as e:
        print(f"   ❌ 디렉토리 읽기 오류: {e}")
else:
    print("❌ /data 디렉토리 없음") 