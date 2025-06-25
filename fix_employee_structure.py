#!/usr/bin/env python3
"""
employees 테이블 구조 통일 및 수정 스크립트
로컬 SQLite와 Railway PostgreSQL 모두 지원
"""
import os
from db_utils import get_db_connection
from datetime import datetime

def fix_employee_structure():
    """employees 테이블 구조를 신 구조로 통일"""
    try:
        print("=== 🔧 employees 테이블 구조 수정 시작 ===")
        
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        print(f"DB 타입: {db_type}")
        
        # 1. 현재 테이블 구조 확인
        if db_type == 'postgresql':
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'employees'
            """)
            columns = [row[0] for row in cursor.fetchall()]
        else:
            cursor.execute("PRAGMA table_info(employees)")
            columns = [row[1] for row in cursor.fetchall()]
        
        print(f"현재 컬럼: {columns}")
        
        # 2. 구 구조인지 신 구조인지 확인
        is_old_structure = 'employee_id' in columns and 'employee_name' in columns
        is_new_structure = 'name' in columns and 'email' in columns
        
        if is_new_structure:
            print("✅ 이미 신 구조입니다. 데이터만 확인합니다.")
            
            # 데이터 확인
            cursor.execute("SELECT COUNT(*) FROM employees")
            count = cursor.fetchone()[0]
            print(f"현재 직원 수: {count}명")
            
            if count == 0:
                print("❌ 직원 데이터가 없습니다. 테스트 직원을 추가합니다.")
                add_test_employees(cursor, db_type)
                conn.commit()
            else:
                cursor.execute("SELECT id, name, role FROM employees")
                employees = cursor.fetchall()
                print("현재 직원 목록:")
                for emp in employees:
                    print(f"  ID:{emp[0]} | 이름:'{emp[1]}' | 역할:{emp[2]}")
        
        elif is_old_structure:
            print("🔄 구 구조를 신 구조로 변환합니다.")
            
            # 기존 데이터 백업
            cursor.execute("SELECT * FROM employees")
            old_employees = cursor.fetchall()
            print(f"기존 직원 데이터: {len(old_employees)}명")
            
            # 구 테이블 삭제 후 신 테이블 생성
            cursor.execute("DROP TABLE employees")
            print("✅ 구 테이블 삭제 완료")
            
            # 신 테이블 생성
            if db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE employees (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        email VARCHAR(200) NOT NULL DEFAULT '',
                        department VARCHAR(100) NOT NULL DEFAULT '',
                        position VARCHAR(100) NOT NULL DEFAULT '',
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        last_login TIMESTAMP,
                        role VARCHAR(50) NOT NULL DEFAULT 'employee'
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE employees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL DEFAULT '',
                        department TEXT NOT NULL DEFAULT '',
                        position TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL,
                        last_login TEXT,
                        role TEXT NOT NULL DEFAULT 'employee'
                    )
                ''')
            print("✅ 신 테이블 생성 완료")
            
            # 기존 데이터 변환 후 삽입
            for old_emp in old_employees:
                # 구 구조: id, employee_id, employee_name, team, password, created_date, is_active
                old_id, employee_id, employee_name, team, password, created_date, is_active = old_emp
                
                # 이름 우선순위: employee_name > employee_id
                final_name = employee_name if employee_name else employee_id
                
                # 신 구조로 변환
                if db_type == 'postgresql':
                    cursor.execute('''
                        INSERT INTO employees (name, email, department, position, created_at, role)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (final_name, '', team or '', '', created_date, 'employee'))
                else:
                    cursor.execute('''
                        INSERT INTO employees (name, email, department, position, created_at, role)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (final_name, '', team or '', '', created_date, 'employee'))
            
            print(f"✅ 기존 데이터 {len(old_employees)}명 변환 완료")
            conn.commit()
        
        else:
            print("❌ 알 수 없는 테이블 구조입니다. 신 테이블을 새로 생성합니다.")
            
            # 테이블 삭제 후 재생성
            cursor.execute("DROP TABLE IF EXISTS employees")
            
            if db_type == 'postgresql':
                cursor.execute('''
                    CREATE TABLE employees (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        email VARCHAR(200) NOT NULL DEFAULT '',
                        department VARCHAR(100) NOT NULL DEFAULT '',
                        position VARCHAR(100) NOT NULL DEFAULT '',
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        last_login TIMESTAMP,
                        role VARCHAR(50) NOT NULL DEFAULT 'employee'
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE employees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL DEFAULT '',
                        department TEXT NOT NULL DEFAULT '',
                        position TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL,
                        last_login TEXT,
                        role TEXT NOT NULL DEFAULT 'employee'
                    )
                ''')
            
            print("✅ 신 테이블 생성 완료")
            add_test_employees(cursor, db_type)
            conn.commit()
        
        conn.close()
        print("\n=== ✅ employees 테이블 구조 수정 완료 ===")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def add_test_employees(cursor, db_type):
    """테스트용 직원 데이터 추가"""
    test_employees = [
        ('admin', 'admin'),
        ('관리자', 'admin'),
        ('직원1', 'employee'),
        ('테스트직원', 'employee')
    ]
    
    current_time = datetime.now()
    
    for name, role in test_employees:
        try:
            if db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO employees (name, email, department, position, created_at, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (name, '', '', '', current_time, role))
            else:
                cursor.execute('''
                    INSERT INTO employees (name, email, department, position, created_at, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, '', '', '', current_time.strftime('%Y-%m-%d %H:%M:%S'), role))
            print(f"  ✅ 테스트 직원 추가: {name} ({role})")
        except Exception as e:
            print(f"  ❌ {name} 추가 실패: {e}")

if __name__ == "__main__":
    fix_employee_structure() 