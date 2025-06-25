#!/usr/bin/env python3
"""
Railway PostgreSQL 컬럼 추가 및 구조 수정 스크립트
"""
import os

def fix_postgresql_columns():
    """PostgreSQL에서 누락된 컬럼들을 추가"""
    try:
        print("=== 🔧 PostgreSQL 컬럼 수정 시작 ===")
        
        # PostgreSQL 모듈 import
        try:
            import psycopg2
        except ImportError:
            print("❌ psycopg2 모듈이 설치되지 않음")
            return
        
        # DATABASE_URL 환경변수 사용
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL 환경변수가 설정되지 않음")
            return
        
        print(f"🔗 DB 연결: {database_url[:50]}...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 1. employees 테이블 구조 확인 및 수정
        print("\n📊 employees 테이블 수정 중...")
        
        # 현재 컬럼 확인
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'employees'
        """)
        employee_columns = [row[0] for row in cursor.fetchall()]
        print(f"현재 employees 컬럼: {employee_columns}")
        
        # 구 구조인지 확인
        if 'employee_id' in employee_columns and 'employee_name' in employee_columns:
            print("🔄 구 구조를 신 구조로 변환 중...")
            
            # 데이터 백업
            cursor.execute("SELECT * FROM employees")
            old_data = cursor.fetchall()
            print(f"백업된 데이터: {len(old_data)}개")
            
            # 테이블 재생성
            cursor.execute("DROP TABLE employees")
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
            print("✅ employees 신 테이블 생성")
            
            # 데이터 복원
            for old_row in old_data:
                employee_name = old_row[2] if len(old_row) > 2 else old_row[1]
                created_date = old_row[5] if len(old_row) > 5 else 'NOW()'
                
                cursor.execute('''
                    INSERT INTO employees (name, email, department, position, created_at, role)
                    VALUES (%s, '', '', '', %s, 'employee')
                ''', (employee_name, created_date))
            
            print(f"✅ 데이터 복원 완료: {len(old_data)}개")
        
        elif 'name' not in employee_columns:
            print("❌ employees 테이블 구조가 이상함. 재생성합니다.")
            cursor.execute("DROP TABLE IF EXISTS employees")
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
            print("✅ employees 테이블 재생성")
        
        # 2. employee_customers 테이블 컬럼 추가
        print("\n📊 employee_customers 테이블 수정 중...")
        
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'employee_customers'
        """)
        customer_columns = [row[0] for row in cursor.fetchall()]
        print(f"현재 employee_customers 컬럼: {customer_columns}")
        
        # 누락된 컬럼들 추가
        missing_columns = [
            ('phone', 'VARCHAR(50)'),
            ('inquiry_date', 'VARCHAR(50)'),
            ('move_in_date', 'VARCHAR(50)'),
            ('amount', 'VARCHAR(100)'),
            ('room_count', 'VARCHAR(50)'),
            ('location', 'VARCHAR(200)'),
            ('loan_info', 'TEXT'),
            ('parking', 'VARCHAR(50)'),
            ('pets', 'VARCHAR(50)'),
            ('progress_status', 'VARCHAR(50) DEFAULT \'진행중\''),
            ('memo', 'TEXT'),
            ('created_date', 'TIMESTAMP DEFAULT NOW()')
        ]
        
        for col_name, col_type in missing_columns:
            if col_name not in customer_columns:
                try:
                    cursor.execute(f'ALTER TABLE employee_customers ADD COLUMN {col_name} {col_type}')
                    print(f"  ✅ {col_name} 컬럼 추가")
                except Exception as e:
                    print(f"  ❌ {col_name} 추가 실패: {e}")
        
        # 3. 테스트 직원 추가
        print("\n👥 테스트 직원 추가 중...")
        cursor.execute("SELECT COUNT(*) FROM employees")
        emp_count = cursor.fetchone()[0]
        
        if emp_count == 0:
            test_employees = [
                ('admin', 'admin'),
                ('관리자', 'admin'),
                ('직원1', 'employee'),
                ('직원2', 'employee'),
                ('테스트직원', 'employee')
            ]
            
            for name, role in test_employees:
                cursor.execute('''
                    INSERT INTO employees (name, email, department, position, role)
                    VALUES (%s, '', '', '', %s)
                ''', (name, role))
                print(f"  ✅ '{name}' 추가")
        
        # 4. 최종 확인
        print("\n📋 최종 확인:")
        cursor.execute("SELECT id, name, role FROM employees")
        employees = cursor.fetchall()
        print(f"employees 테이블: {len(employees)}명")
        for emp in employees:
            print(f"  - ID:{emp[0]} | 이름:'{emp[1]}' | 역할:{emp[2]}")
        
        cursor.execute("SELECT COUNT(*) FROM employee_customers")
        customer_count = cursor.fetchone()[0]
        print(f"employee_customers 테이블: {customer_count}명")
        
        conn.commit()
        conn.close()
        
        print("\n=== ✅ PostgreSQL 컬럼 수정 완료 ===")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_postgresql_columns() 