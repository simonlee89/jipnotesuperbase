#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway PostgreSQL 테이블 구조 완전 수정 스크립트
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_postgresql_connection():
    """PostgreSQL 연결 생성"""
    try:
        # Railway 환경변수에서 DB URL 가져오기
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL 환경변수가 설정되지 않았습니다.")
        
        # PostgreSQL 연결
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        logger.info("✅ PostgreSQL 연결 성공")
        return conn
    except Exception as e:
        logger.error(f"❌ PostgreSQL 연결 실패: {e}")
        raise

def fix_employees_table(cursor):
    """employees 테이블 구조 수정"""
    logger.info("🔧 employees 테이블 구조 수정 시작...")
    
    try:
        # 1. 현재 컬럼 확인
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'employees' AND table_schema = 'public'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 현재 employees 컬럼: {existing_columns}")
        
        # 2. 필요한 컬럼들 추가 (없는 경우에만)
        required_columns = {
            'employee_id': 'VARCHAR(50)',
            'employee_name': 'VARCHAR(100)',
            'team': 'VARCHAR(100) DEFAULT \'\'',
            'password': 'VARCHAR(255)',
            'is_active': 'BOOLEAN DEFAULT TRUE',
            'role': 'VARCHAR(50) DEFAULT \'employee\'',
            'email': 'VARCHAR(255)',
            'department': 'VARCHAR(100)',
            'position': 'VARCHAR(100)',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'last_login': 'TIMESTAMP',
            'created_date': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE employees ADD COLUMN {column_name} {column_type}")
                    logger.info(f"✅ {column_name} 컬럼 추가 성공")
                except Exception as e:
                    logger.warning(f"⚠️ {column_name} 컬럼 추가 실패: {e}")
        
        # 3. 테스트 직원들 추가
        test_employees = [
            ('admin', 'admin', '', 'admin123', True, 'admin', 'admin@company.com', 'IT', 'Administrator'),
            ('관리자', '관리자', '', 'admin123', True, 'admin', 'manager@company.com', 'Management', 'Manager'),
            ('직원1', '직원1', '', 'emp123', True, 'employee', 'emp1@company.com', 'Sales', 'Sales Rep'),
            ('직원2', '직원2', '', 'emp123', True, 'employee', 'emp2@company.com', 'Sales', 'Sales Rep'),
            ('테스트직원', '테스트직원', '', 'test123', True, 'employee', 'test@company.com', 'Test', 'Tester'),
            ('김철수', '김철수', '', 'kim123', True, 'employee', 'kim@company.com', 'Marketing', 'Marketer'),
            ('이영희', '이영희', '', 'lee123', True, 'employee', 'lee@company.com', 'HR', 'HR Specialist'),
            ('박민수', '박민수', '', 'park123', True, 'employee', 'park@company.com', 'Finance', 'Accountant')
        ]
        
        for emp in test_employees:
            try:
                # 중복 체크
                cursor.execute("SELECT COUNT(*) FROM employees WHERE employee_id = %s OR name = %s", (emp[0], emp[1]))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO employees 
                        (employee_id, employee_name, team, password, is_active, role, email, department, position, name)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, emp + (emp[1],))  # name 컬럼에도 employee_name과 같은 값 입력
                    logger.info(f"✅ 직원 추가: {emp[1]}")
            except Exception as e:
                logger.warning(f"⚠️ 직원 {emp[1]} 추가 실패: {e}")
        
        logger.info("✅ employees 테이블 구조 수정 완료")
        
    except Exception as e:
        logger.error(f"❌ employees 테이블 수정 실패: {e}")
        raise

def fix_employee_customers_table(cursor):
    """employee_customers 테이블 구조 수정"""
    logger.info("🔧 employee_customers 테이블 구조 수정 시작...")
    
    try:
        # 현재 컬럼 확인
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'employee_customers' AND table_schema = 'public'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 현재 employee_customers 컬럼: {existing_columns}")
        
        # 필요한 컬럼들 추가
        required_columns = {
            'phone': 'VARCHAR(20)',
            'inquiry_date': 'DATE',
            'move_in_date': 'DATE',
            'contract_status': 'VARCHAR(50) DEFAULT \'대기중\'',
            'notes': 'TEXT',
            'last_contact': 'TIMESTAMP',
            'priority': 'INTEGER DEFAULT 1',
            'source': 'VARCHAR(100)',
            'budget_min': 'INTEGER',
            'budget_max': 'INTEGER',
            'preferred_area': 'VARCHAR(200)',
            'room_type': 'VARCHAR(50)',
            'special_requirements': 'TEXT'
        }
        
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE employee_customers ADD COLUMN {column_name} {column_type}")
                    logger.info(f"✅ employee_customers.{column_name} 컬럼 추가 성공")
                except Exception as e:
                    logger.warning(f"⚠️ employee_customers.{column_name} 컬럼 추가 실패: {e}")
        
        logger.info("✅ employee_customers 테이블 구조 수정 완료")
        
    except Exception as e:
        logger.error(f"❌ employee_customers 테이블 수정 실패: {e}")

def fix_links_and_office_links_tables(cursor):
    """links와 office_links 테이블 구조 수정"""
    logger.info("🔧 links/office_links 테이블 구조 수정 시작...")
    
    try:
        # links 테이블 수정
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'links' AND table_schema = 'public'
        """)
        links_columns = [row[0] for row in cursor.fetchall()]
        
        # office_links 테이블 수정
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'office_links' AND table_schema = 'public'
        """)
        office_links_columns = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"📊 현재 links 컬럼: {links_columns}")
        logger.info(f"📊 현재 office_links 컬럼: {office_links_columns}")
        
        # 공통 필요 컬럼들
        common_columns = {
            'is_deleted': 'BOOLEAN DEFAULT FALSE',
            'unchecked_likes_work': 'INTEGER DEFAULT 0',
            'view_count': 'INTEGER DEFAULT 0',
            'last_viewed': 'TIMESTAMP',
            'tags': 'TEXT',
            'priority': 'INTEGER DEFAULT 1',
            'notes': 'TEXT'
        }
        
        # links 테이블에 컬럼 추가
        for column_name, column_type in common_columns.items():
            if column_name not in links_columns:
                try:
                    cursor.execute(f"ALTER TABLE links ADD COLUMN {column_name} {column_type}")
                    logger.info(f"✅ links.{column_name} 컬럼 추가 성공")
                except Exception as e:
                    logger.warning(f"⚠️ links.{column_name} 컬럼 추가 실패: {e}")
        
        # office_links 테이블에 컬럼 추가
        for column_name, column_type in common_columns.items():
            if column_name not in office_links_columns:
                try:
                    cursor.execute(f"ALTER TABLE office_links ADD COLUMN {column_name} {column_type}")
                    logger.info(f"✅ office_links.{column_name} 컬럼 추가 성공")
                except Exception as e:
                    logger.warning(f"⚠️ office_links.{column_name} 컬럼 추가 실패: {e}")
        
        logger.info("✅ links/office_links 테이블 구조 수정 완료")
        
    except Exception as e:
        logger.error(f"❌ links/office_links 테이블 수정 실패: {e}")

def create_indexes(cursor):
    """인덱스 생성"""
    logger.info("🔧 인덱스 생성 시작...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_employees_employee_id ON employees(employee_id)",
        "CREATE INDEX IF NOT EXISTS idx_employees_name ON employees(name)",
        "CREATE INDEX IF NOT EXISTS idx_employees_role ON employees(role)",
        "CREATE INDEX IF NOT EXISTS idx_employee_customers_employee_id ON employee_customers(employee_id)",
        "CREATE INDEX IF NOT EXISTS idx_employee_customers_phone ON employee_customers(phone)",
        "CREATE INDEX IF NOT EXISTS idx_links_customer_name ON links(customer_name)",
        "CREATE INDEX IF NOT EXISTS idx_office_links_customer_name ON office_links(customer_name)",
        "CREATE INDEX IF NOT EXISTS idx_links_is_deleted ON links(is_deleted)",
        "CREATE INDEX IF NOT EXISTS idx_office_links_is_deleted ON office_links(is_deleted)"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            logger.info(f"✅ 인덱스 생성 성공: {index_sql.split('ON')[1].strip()}")
        except Exception as e:
            logger.warning(f"⚠️ 인덱스 생성 실패: {e}")

def main():
    """메인 실행 함수"""
    try:
        logger.info("🚀 PostgreSQL 테이블 구조 수정 시작...")
        
        # PostgreSQL 연결
        conn = get_postgresql_connection()
        cursor = conn.cursor()
        
        # 각 테이블 구조 수정
        fix_employees_table(cursor)
        fix_employee_customers_table(cursor)
        fix_links_and_office_links_tables(cursor)
        create_indexes(cursor)
        
        # 최종 확인
        cursor.execute("SELECT COUNT(*) FROM employees")
        emp_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT employee_id, employee_name, role FROM employees LIMIT 5")
        sample_employees = cursor.fetchall()
        
        logger.info(f"✅ 모든 작업 완료!")
        logger.info(f"📊 총 직원 수: {emp_count}명")
        logger.info(f"📋 샘플 직원들:")
        for emp in sample_employees:
            logger.info(f"  - ID:{emp[0]} | 이름:{emp[1]} | 역할:{emp[2]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 전체 작업 실패: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 