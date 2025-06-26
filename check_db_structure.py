import db_utils
import json

def check_database_structure():
    """데이터베이스 구조와 고객 데이터 확인"""
    print("=" * 60)
    print("📊 데이터베이스 구조 확인")
    print("=" * 60)
    
    try:
        conn, db_type = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        print(f"\n✅ DB 타입: {db_type}")
        
        # employee_customers 테이블 구조 확인
        print("\n📋 employee_customers 테이블 구조:")
        if db_type == 'postgresql':
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'employee_customers' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (NULL 허용: {col[2]})")
        else:
            cursor.execute("PRAGMA table_info(employee_customers)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]}: {col[2]} (NULL 허용: {'YES' if col[3] == 0 else 'NO'})")
        
        # 고객 데이터 샘플 확인
        print("\n👥 고객 데이터 샘플 (최근 5명):")
        cursor.execute("""
            SELECT id, customer_name, management_site_id, employee_id, created_date 
            FROM employee_customers 
            ORDER BY id DESC 
            LIMIT 5
        """)
        customers = cursor.fetchall()
        
        if customers:
            for customer in customers:
                if db_type == 'postgresql':
                    print(f"\n  ID: {customer['id']}")
                    print(f"  이름: {customer['customer_name']}")
                    print(f"  Management Site ID: {customer['management_site_id']}")
                    print(f"  담당 직원: {customer['employee_id']}")
                    print(f"  생성일: {customer['created_date']}")
                else:
                    print(f"\n  ID: {customer[0]}")
                    print(f"  이름: {customer[1]}")
                    print(f"  Management Site ID: {customer[2]}")
                    print(f"  담당 직원: {customer[3]}")
                    print(f"  생성일: {customer[4]}")
        else:
            print("  ❌ 고객 데이터가 없습니다.")
        
        # management_site_id가 NULL인 고객 확인
        print("\n⚠️  management_site_id가 NULL인 고객:")
        cursor.execute("""
            SELECT id, customer_name, employee_id 
            FROM employee_customers 
            WHERE management_site_id IS NULL OR management_site_id = ''
        """)
        null_customers = cursor.fetchall()
        
        if null_customers:
            for customer in null_customers:
                if db_type == 'postgresql':
                    print(f"  - ID: {customer['id']}, 이름: {customer['customer_name']}, 담당: {customer['employee_id']}")
                else:
                    print(f"  - ID: {customer[0]}, 이름: {customer[1]}, 담당: {customer[2]}")
        else:
            print("  ✅ 모든 고객이 management_site_id를 가지고 있습니다.")
        
        # 직원 목록 확인
        print("\n👔 직원 목록:")
        cursor.execute("SELECT id, name, role FROM employees ORDER BY id")
        employees = cursor.fetchall()
        
        if employees:
            for emp in employees:
                if db_type == 'postgresql':
                    print(f"  - ID: {emp['id']}, 이름: {emp['name']}, 역할: {emp['role']}")
                else:
                    print(f"  - ID: {emp[0]}, 이름: {emp[1]}, 역할: {emp[2]}")
        else:
            print("  ❌ 직원 데이터가 없습니다.")
        
        conn.close()
        print("\n" + "=" * 60)
        print("✅ 데이터베이스 확인 완료")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_structure() 