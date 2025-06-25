#!/usr/bin/env python3
"""
Railway PostgreSQL employees 테이블 구조 수정 스크립트
"""
import os
from datetime import datetime

def fix_railway_employees():
    """Railway PostgreSQL employees 테이블 구조 확인 및 수정"""
    try:
        print("=== 🚂 Railway PostgreSQL employees 테이블 수정 ===")
        
        # PostgreSQL 모듈 import
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            print("❌ psycopg2 모듈이 설치되지 않음")
            return
        
        # Railway DATABASE_URL 사용
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL 환경변수가 설정되지 않음")
            return
        
        print(f"🔗 DB 연결: {database_url[:50]}...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 1. 현재 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'employees'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ employees 테이블이 존재하지 않음")
            # 새 테이블 생성
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
            print("✅ 새 employees 테이블 생성 완료")
        else:
            print(f"📊 현재 테이블 구조 ({len(columns)}개 컬럼):")
            column_names = []
            for col in columns:
                column_names.append(col[0])
                print(f"  - {col[0]} ({col[1]}) NULL:{col[2]} DEFAULT:{col[3]}")
            
            # 구조 확인
            is_old_structure = 'employee_id' in column_names and 'employee_name' in column_names
            is_new_structure = 'name' in column_names and 'email' in column_names
            
            if is_new_structure:
                print("✅ 이미 신 구조입니다.")
            elif is_old_structure:
                print("🔄 구 구조를 신 구조로 변환합니다.")
                
                # 기존 데이터 백업
                cursor.execute("SELECT * FROM employees")
                old_employees = cursor.fetchall()
                print(f"기존 직원 데이터: {len(old_employees)}명")
                
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
                print("✅ 신 테이블 생성 완료")
                
                # 기존 데이터 변환
                for old_emp in old_employees:
                    # 구 구조에서 필요한 값 추출
                    employee_name = old_emp[2] if len(old_emp) > 2 else old_emp[1]
                    created_date = old_emp[5] if len(old_emp) > 5 else datetime.now()
                    
                    cursor.execute('''
                        INSERT INTO employees (name, email, department, position, created_at, role)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (employee_name, '', '', '', created_date, 'employee'))
                
                print(f"✅ 기존 데이터 {len(old_employees)}명 변환 완료")
            else:
                print("❌ 알 수 없는 구조, 신 테이블로 재생성")
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
                print("✅ 신 테이블 생성 완료")
        
        # 2. 테스트 직원 추가
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("👥 테스트 직원 추가 중...")
            test_employees = [
                ('admin', 'admin'),
                ('관리자', 'admin'),
                ('직원1', 'employee'),
                ('직원2', 'employee'),
                ('테스트직원', 'employee')
            ]
            
            for name, role in test_employees:
                cursor.execute('''
                    INSERT INTO employees (name, email, department, position, created_at, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (name, '', '', '', datetime.now(), role))
                print(f"  ✅ '{name}' 추가")
        
        # 3. 최종 확인
        cursor.execute("SELECT id, name, role FROM employees ORDER BY id")
        employees = cursor.fetchall()
        
        print(f"\n📋 최종 직원 목록 ({len(employees)}명):")
        for emp in employees:
            print(f"  - ID:{emp[0]} | 이름:'{emp[1]}' | 역할:{emp[2]}")
        
        conn.commit()
        conn.close()
        
        print("\n=== ✅ Railway employees 테이블 수정 완료 ===")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_railway_employees() 