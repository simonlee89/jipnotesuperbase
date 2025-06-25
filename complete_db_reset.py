#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway PostgreSQL 완전 리셋 및 재구축 스크립트
모든 구 데이터를 삭제하고 새 구조로 완전히 재생성
"""

import os
import psycopg2
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_postgresql_connection():
    """PostgreSQL 연결 생성"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL 환경변수가 설정되지 않았습니다.")
        
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        logger.info("✅ PostgreSQL 연결 성공")
        return conn
    except Exception as e:
        logger.error(f"❌ PostgreSQL 연결 실패: {e}")
        raise

def drop_all_tables(cursor):
    """모든 테이블 완전 삭제"""
    logger.info("🗑️ 모든 테이블 삭제 시작...")
    
    try:
        # 1. 모든 테이블 목록 조회
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        tables = cursor.fetchall()
        
        logger.info(f"📋 발견된 테이블: {[table[0] for table in tables]}")
        
        # 2. 모든 테이블 삭제 (CASCADE로 제약조건 무시)
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                logger.info(f"✅ {table_name} 테이블 삭제")
            except Exception as e:
                logger.warning(f"⚠️ {table_name} 삭제 실패: {e}")
        
        # 3. 시퀀스도 삭제
        cursor.execute("""
            SELECT sequence_name FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        sequences = cursor.fetchall()
        
        for seq in sequences:
            seq_name = seq[0]
            try:
                cursor.execute(f"DROP SEQUENCE IF EXISTS {seq_name} CASCADE")
                logger.info(f"✅ {seq_name} 시퀀스 삭제")
            except Exception as e:
                logger.warning(f"⚠️ {seq_name} 삭제 실패: {e}")
        
        logger.info("🗑️ 모든 테이블 삭제 완료")
        
    except Exception as e:
        logger.error(f"❌ 테이블 삭제 실패: {e}")
        raise

def create_new_tables(cursor):
    """새 테이블 구조로 완전 재생성"""
    logger.info("🏗️ 새 테이블 구조 생성 시작...")
    
    try:
        # 1. employees 테이블 - 완전 새 구조
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
        logger.info("✅ employees 테이블 생성 (신 구조)")
        
        # 2. employee_customers 테이블 - 확장된 구조
        cursor.execute('''
            CREATE TABLE employee_customers (
                id SERIAL PRIMARY KEY,
                employee_id VARCHAR(50) NOT NULL,
                management_site_id VARCHAR(50) UNIQUE NOT NULL,
                customer_name VARCHAR(200),
                phone VARCHAR(20),
                inquiry_date DATE,
                move_in_date DATE,
                amount VARCHAR(100),
                room_count VARCHAR(50),
                location VARCHAR(200),
                loan_info TEXT,
                parking VARCHAR(50),
                pets VARCHAR(50),
                progress_status VARCHAR(50) DEFAULT '진행중',
                memo TEXT,
                created_date TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP DEFAULT NOW(),
                budget_min INTEGER,
                budget_max INTEGER,
                preferred_area VARCHAR(200),
                special_requirements TEXT,
                contact_preference VARCHAR(20) DEFAULT 'phone',
                contract_status VARCHAR(50) DEFAULT '대기중',
                notes TEXT,
                last_contact TIMESTAMP,
                priority INTEGER DEFAULT 1,
                source VARCHAR(100)
            )
        ''')
        logger.info("✅ employee_customers 테이블 생성 (확장 구조)")
        
        # 3. links 테이블 - 주거용 매물
        cursor.execute('''
            CREATE TABLE links (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                platform VARCHAR(100),
                added_by VARCHAR(100),
                date_added TIMESTAMP DEFAULT NOW(),
                rating INTEGER DEFAULT 0,
                liked INTEGER DEFAULT 0,
                disliked INTEGER DEFAULT 0,
                memo TEXT,
                management_site_id VARCHAR(50),
                guarantee_insurance INTEGER DEFAULT 0,
                is_deleted BOOLEAN DEFAULT FALSE,
                is_checked INTEGER DEFAULT 0,
                residence_extra TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                view_count INTEGER DEFAULT 0,
                price VARCHAR(100),
                area VARCHAR(50),
                room_type VARCHAR(50),
                floor_info VARCHAR(50),
                deposit VARCHAR(100),
                monthly_rent VARCHAR(100),
                customer_name VARCHAR(200) DEFAULT '제일좋은집 찾아드릴분',
                move_in_date VARCHAR(50) DEFAULT '',
                unchecked_likes_work INTEGER DEFAULT 0,
                tags TEXT,
                priority INTEGER DEFAULT 1,
                notes TEXT,
                last_viewed TIMESTAMP
            )
        ''')
        logger.info("✅ links 테이블 생성 (주거용)")
        
        # 4. office_links 테이블 - 업무용 매물
        cursor.execute('''
            CREATE TABLE office_links (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                platform VARCHAR(100) NOT NULL,
                added_by VARCHAR(100) NOT NULL,
                date_added TIMESTAMP DEFAULT NOW(),
                rating INTEGER DEFAULT 5,
                liked INTEGER DEFAULT 0,
                disliked INTEGER DEFAULT 0,
                memo TEXT DEFAULT '',
                customer_name VARCHAR(200) DEFAULT '000',
                move_in_date VARCHAR(50) DEFAULT '',
                management_site_id VARCHAR(50) DEFAULT NULL,
                guarantee_insurance INTEGER DEFAULT 0,
                is_checked INTEGER DEFAULT 0,
                unchecked_likes_work INTEGER DEFAULT 0,
                is_deleted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                view_count INTEGER DEFAULT 0,
                office_type VARCHAR(50),
                office_size VARCHAR(50),
                monthly_fee VARCHAR(100),
                deposit_amount VARCHAR(100),
                utilities_included BOOLEAN DEFAULT FALSE,
                parking_available BOOLEAN DEFAULT FALSE,
                elevator_available BOOLEAN DEFAULT FALSE,
                tags TEXT,
                priority INTEGER DEFAULT 1,
                notes TEXT,
                last_viewed TIMESTAMP
            )
        ''')
        logger.info("✅ office_links 테이블 생성 (업무용)")
        
        # 5. guarantee_insurance_log 테이블
        cursor.execute('''
            CREATE TABLE guarantee_insurance_log (
                id SERIAL PRIMARY KEY,
                link_id INTEGER,
                management_site_id VARCHAR(50),
                employee_id VARCHAR(50),
                action VARCHAR(100),
                timestamp TIMESTAMP DEFAULT NOW(),
                table_type VARCHAR(20) DEFAULT 'office_links',
                details TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT
            )
        ''')
        logger.info("✅ guarantee_insurance_log 테이블 생성")
        
        # 6. customer_info 테이블
        cursor.execute('''
            CREATE TABLE customer_info (
                id SERIAL PRIMARY KEY,
                customer_name VARCHAR(200) DEFAULT '제일좋은집 찾아드릴분',
                move_in_date VARCHAR(50) DEFAULT '',
                phone VARCHAR(50),
                email VARCHAR(200),
                preferred_contact VARCHAR(20) DEFAULT 'phone',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        logger.info("✅ customer_info 테이블 생성")
        
        # 기본 고객 정보 삽입
        cursor.execute('''
            INSERT INTO customer_info (id, customer_name, move_in_date) 
            VALUES (1, '제일좋은집 찾아드릴분', '') 
        ''')
        
        logger.info("🏗️ 새 테이블 구조 생성 완료")
        
    except Exception as e:
        logger.error(f"❌ 새 테이블 생성 실패: {e}")
        raise

def create_indexes(cursor):
    """인덱스 생성"""
    logger.info("📊 인덱스 생성 시작...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_employees_name ON employees(name)",
        "CREATE INDEX IF NOT EXISTS idx_employees_role ON employees(role)",
        "CREATE INDEX IF NOT EXISTS idx_employee_customers_employee_id ON employee_customers(employee_id)",
        "CREATE INDEX IF NOT EXISTS idx_employee_customers_management_site_id ON employee_customers(management_site_id)",
        "CREATE INDEX IF NOT EXISTS idx_links_management_site_id ON links(management_site_id)",
        "CREATE INDEX IF NOT EXISTS idx_links_added_by ON links(added_by)",
        "CREATE INDEX IF NOT EXISTS idx_links_is_deleted ON links(is_deleted)",
        "CREATE INDEX IF NOT EXISTS idx_office_links_management_site_id ON office_links(management_site_id)",
        "CREATE INDEX IF NOT EXISTS idx_office_links_added_by ON office_links(added_by)",
        "CREATE INDEX IF NOT EXISTS idx_office_links_is_deleted ON office_links(is_deleted)"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            logger.info(f"✅ 인덱스 생성: {index_sql.split('ON')[1].strip()}")
        except Exception as e:
            logger.warning(f"⚠️ 인덱스 생성 실패: {e}")

def insert_test_data(cursor):
    """테스트 데이터 삽입"""
    logger.info("📝 테스트 데이터 삽입 시작...")
    
    try:
        # 테스트 직원들 추가
        test_employees = [
            ('admin', 'admin@company.com', 'IT', 'Administrator', 'admin'),
            ('관리자', 'manager@company.com', 'Management', 'Manager', 'admin'),
            ('직원1', 'emp1@company.com', 'Sales', 'Sales Rep', 'employee'),
            ('직원2', 'emp2@company.com', 'Sales', 'Sales Rep', 'employee'),
            ('테스트직원', 'test@company.com', 'Test', 'Tester', 'employee'),
            ('김철수', 'kim@company.com', 'Marketing', 'Marketer', 'employee'),
            ('이영희', 'lee@company.com', 'HR', 'HR Specialist', 'employee'),
            ('박민수', 'park@company.com', 'Finance', 'Accountant', 'employee')
        ]
        
        for name, email, dept, pos, role in test_employees:
            cursor.execute('''
                INSERT INTO employees (name, email, department, position, role)
                VALUES (%s, %s, %s, %s, %s)
            ''', (name, email, dept, pos, role))
            logger.info(f"✅ 직원 추가: {name}")
        
        logger.info("📝 테스트 데이터 삽입 완료")
        
    except Exception as e:
        logger.error(f"❌ 테스트 데이터 삽입 실패: {e}")

def main():
    """메인 실행 함수"""
    try:
        logger.info("🚀 PostgreSQL 완전 리셋 시작...")
        
        # PostgreSQL 연결
        conn = get_postgresql_connection()
        cursor = conn.cursor()
        
        # 1. 모든 테이블 삭제
        drop_all_tables(cursor)
        
        # 2. 새 테이블 생성
        create_new_tables(cursor)
        
        # 3. 인덱스 생성
        create_indexes(cursor)
        
        # 4. 테스트 데이터 삽입
        insert_test_data(cursor)
        
        # 5. 최종 확인
        cursor.execute("SELECT COUNT(*) FROM employees")
        emp_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT name, role FROM employees LIMIT 5")
        sample_employees = cursor.fetchall()
        
        logger.info("🎉 PostgreSQL 완전 리셋 성공!")
        logger.info(f"📊 총 직원 수: {emp_count}명")
        logger.info("📋 샘플 직원들:")
        for emp in sample_employees:
            logger.info(f"  - 이름:{emp[0]} | 역할:{emp[1]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 완전 리셋 실패: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 