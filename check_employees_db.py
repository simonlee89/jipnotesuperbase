#!/usr/bin/env python3
"""
PostgreSQL employees 테이블 상태 확인 스크립트
"""
import os
from db_utils import get_db_connection

def check_employees_table():
    """employees 테이블 상태 상세 확인"""
    try:
        print("=== 🔍 employees 테이블 상태 확인 ===")
        
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        print(f"DB 타입: {db_type}")
        
        # 1. 테이블 구조 확인
        if db_type == 'postgresql':
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'employees' 
                ORDER BY ordinal_position
            """)
        else:
            cursor.execute("PRAGMA table_info(employees)")
        
        columns = cursor.fetchall()
        print(f"\n📊 테이블 구조 ({len(columns)}개 컬럼):")
        for col in columns:
            if db_type == 'postgresql':
                print(f"  - {col[0]} ({col[1]}) NULL:{col[2]} DEFAULT:{col[3]}")
            else:
                print(f"  - {col[1]} ({col[2]}) NULL:{'NO' if col[3] else 'YES'} DEFAULT:{col[4]}")
        
        # 2. 데이터 개수 확인
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        print(f"\n📈 총 직원 수: {count}명")
        
        # 3. 실제 데이터 확인
        if count > 0:
            cursor.execute("SELECT id, name, email, department, position, created_at, role FROM employees ORDER BY id")
            employees = cursor.fetchall()
            
            print(f"\n👥 직원 목록:")
            for emp in employees:
                print(f"  ID:{emp[0]} | 이름:'{emp[1]}' | 이메일:'{emp[2]}' | 부서:'{emp[3]}' | 직책:'{emp[4]}' | 생성일:{emp[5]} | 역할:{emp[6]}")
        else:
            print("\n❌ 직원 데이터가 없습니다!")
        
        # 4. 특정 이름으로 검색 테스트
        test_names = ['admin', 'test', '관리자', '직원']
        print(f"\n🔍 테스트 이름 검색:")
        for name in test_names:
            if db_type == 'postgresql':
                cursor.execute("SELECT id, name FROM employees WHERE name = %s", (name,))
            else:
                cursor.execute("SELECT id, name FROM employees WHERE name = ?", (name,))
            result = cursor.fetchone()
            if result:
                print(f"  ✅ '{name}' 찾음: ID={result[0]}")
            else:
                print(f"  ❌ '{name}' 없음")
        
        conn.close()
        print("\n=== ✅ 확인 완료 ===")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_employees_table() 