#!/usr/bin/env python3
"""
Railway PostgreSQL 직접 테스트 및 데이터 추가 스크립트
"""

import psycopg2
import sys
from datetime import datetime

# Railway DATABASE_URL
DATABASE_URL = "postgresql://postgres:lAnQSPxyBfubqMtRXAZGviaVvtjsXbEw@postgres.railway.internal:5432/railway"

def test_postgresql_connection():
    """PostgreSQL 연결 테스트"""
    try:
        print("🔄 Railway PostgreSQL 연결 시도...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("✅ PostgreSQL 연결 성공!")
        
        # 테이블 목록 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"\n📋 생성된 테이블들: {[table[0] for table in tables]}")
        
        return conn, cursor
        
    except Exception as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        return None, None

def check_employees_data(cursor):
    """employees 테이블 데이터 확인"""
    try:
        print("\n🔍 employees 테이블 데이터 확인...")
        
        # 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'employees' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print("📊 employees 테이블 구조:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        # 데이터 개수 확인
        cursor.execute("SELECT COUNT(*) FROM employees;")
        count = cursor.fetchone()[0]
        print(f"\n👥 현재 직원 수: {count}명")
        
        # 모든 직원 데이터 조회
        cursor.execute("SELECT * FROM employees LIMIT 10;")
        employees = cursor.fetchall()
        if employees:
            print("📝 현재 직원 목록:")
            for emp in employees:
                print(f"  - {emp}")
        else:
            print("⚠️ 직원 데이터가 없습니다!")
            
        return count > 0
        
    except Exception as e:
        print(f"❌ employees 데이터 확인 실패: {e}")
        return False

def add_test_employees(cursor, conn):
    """테스트 직원들 추가"""
    try:
        print("\n➕ 테스트 직원들 추가...")
        
        test_employees = [
            ('admin', 'admin@company.com', '관리부', '관리자', 'admin'),
            ('관리자', 'manager@company.com', '관리부', '부장', 'manager'),
            ('직원1', 'emp1@company.com', '영업부', '대리', 'employee'),
            ('직원2', 'emp2@company.com', '마케팅부', '주임', 'employee'),
            ('테스트직원', 'test@company.com', '개발부', '사원', 'employee'),
            ('김철수', 'kim@company.com', '영업부', '과장', 'employee'),
            ('이영희', 'lee@company.com', '인사부', '대리', 'employee'),
            ('박민수', 'park@company.com', '재무부', '주임', 'employee')
        ]
        
        current_time = datetime.now()
        
        for name, email, department, position, role in test_employees:
            try:
                cursor.execute("""
                    INSERT INTO employees (name, email, department, position, created_at, last_login, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        email = EXCLUDED.email,
                        department = EXCLUDED.department,
                        position = EXCLUDED.position,
                        role = EXCLUDED.role;
                """, (name, email, department, position, current_time, current_time, role))
                print(f"  ✅ {name} 추가/업데이트 완료")
            except Exception as e:
                print(f"  ❌ {name} 추가 실패: {e}")
        
        conn.commit()
        print("💾 모든 변경사항 저장 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 직원 추가 실패: {e}")
        conn.rollback()

def check_other_tables(cursor):
    """다른 테이블들 상태 확인"""
    try:
        print("\n🔍 다른 테이블들 상태 확인...")
        
        tables_to_check = ['links', 'office_links', 'customer_info', 'guarantee_insurance_log', 'employee_customers']
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"  📊 {table}: {count}개 레코드")
            except Exception as e:
                print(f"  ❌ {table} 확인 실패: {e}")
                
    except Exception as e:
        print(f"❌ 테이블 상태 확인 실패: {e}")

def test_employee_login(cursor):
    """직원 로그인 테스트"""
    try:
        print("\n🔐 직원 로그인 테스트...")
        
        test_names = ['admin', '관리자', '직원1', '테스트직원']
        
        for name in test_names:
            cursor.execute("SELECT name, email, department, role FROM employees WHERE name = %s;", (name,))
            result = cursor.fetchone()
            if result:
                print(f"  ✅ {name}: {result}")
            else:
                print(f"  ❌ {name}: 찾을 수 없음")
                
    except Exception as e:
        print(f"❌ 로그인 테스트 실패: {e}")

def main():
    """메인 함수"""
    print("🚀 Railway PostgreSQL 직접 테스트 시작")
    print("=" * 50)
    
    # PostgreSQL 연결
    conn, cursor = test_postgresql_connection()
    if not conn:
        sys.exit(1)
    
    try:
        # 직원 데이터 확인
        has_employees = check_employees_data(cursor)
        
        # 직원이 없으면 테스트 직원들 추가
        if not has_employees:
            add_test_employees(cursor, conn)
            
            # 다시 확인
            print("\n🔄 직원 추가 후 재확인...")
            check_employees_data(cursor)
        
        # 다른 테이블들 상태 확인
        check_other_tables(cursor)
        
        # 직원 로그인 테스트
        test_employee_login(cursor)
        
        print("\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("🔌 데이터베이스 연결 종료")

if __name__ == "__main__":
    main() 