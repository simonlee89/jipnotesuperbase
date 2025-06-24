import sqlite3

# integrated.db 연결
conn = sqlite3.connect('integrated.db')
cursor = conn.cursor()

print("=== employee_customers 테이블 확인 ===")
try:
    cursor.execute('SELECT * FROM employee_customers LIMIT 5')
    customers = cursor.fetchall()
    if customers:
        print(f"고객 수: {len(customers)}")
        for customer in customers:
            print(f"ID: {customer[0]}, 직원ID: {customer[1]}, management_site_id: {customer[2]}, 고객명: {customer[3]}")
    else:
        print("고객 데이터가 없습니다.")
except Exception as e:
    print(f"테이블 조회 오류: {e}")

print("\n=== 테이블 목록 확인 ===")
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("테이블 목록:", [table[0] for table in tables])
except Exception as e:
    print(f"테이블 목록 조회 오류: {e}")

conn.close() 