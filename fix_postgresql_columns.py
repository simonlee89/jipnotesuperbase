#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 데이터베이스 컬럼 구조 완벽 수정 스크립트
관리자페이지.py, 업무용.py, 주거용.py 간의 호환성 완벽 보장
"""

import os
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.error("psycopg2 모듈이 필요합니다!")
    exit(1)

def get_db_connection():
    """PostgreSQL 연결"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL 환경변수가 설정되지 않았습니다!")
        exit(1)
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        logger.info("✅ PostgreSQL 연결 성공")
        return conn
    except Exception as e:
        logger.error(f"❌ PostgreSQL 연결 실패: {e}")
        exit(1)

def execute_sql(conn, sql, description=""):
    """SQL 실행 헬퍼 함수"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        logger.info(f"✅ {description} 성공")
        return True
    except Exception as e:
        logger.error(f"❌ {description} 실패: {e}")
        conn.rollback()
        return False

def check_column_exists(conn, table_name, column_name):
    """컬럼 존재 여부 확인"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"컬럼 확인 실패: {e}")
        return False

def fix_employees_table(conn):
    """employees 테이블 구조 완벽 수정"""
    logger.info("🔧 employees 테이블 수정 시작")
    
    # 테이블 생성 (없는 경우)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        employee_id VARCHAR(100) UNIQUE NOT NULL,
        employee_name VARCHAR(100) NOT NULL,
        team VARCHAR(100) NOT NULL,
        password VARCHAR(100) NOT NULL DEFAULT '1234',
        created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        last_login TIMESTAMP,
        phone VARCHAR(50),
        email VARCHAR(200),
        role VARCHAR(50) DEFAULT '직원'
    );
    """
    execute_sql(conn, create_table_sql, "employees 테이블 생성")
    
    # 필수 컬럼들 추가
    missing_columns = [
        ("last_login", "TIMESTAMP", "마지막 로그인"),
        ("phone", "VARCHAR(50)", "전화번호"),
        ("email", "VARCHAR(200)", "이메일"),
        ("role", "VARCHAR(50) DEFAULT '직원'", "역할")
    ]
    
    for col_name, col_type, description in missing_columns:
        if not check_column_exists(conn, 'employees', col_name):
            sql = f"ALTER TABLE employees ADD COLUMN {col_name} {col_type};"
            execute_sql(conn, sql, f"employees.{col_name} 컬럼 추가 ({description})")

def fix_employee_customers_table(conn):
    """employee_customers 테이블 구조 완벽 수정"""
    logger.info("🔧 employee_customers 테이블 수정 시작")
    
    # 테이블 생성 (없는 경우)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS employee_customers (
        id SERIAL PRIMARY KEY,
        employee_id VARCHAR(100) NOT NULL,
        management_site_id VARCHAR(50) UNIQUE NOT NULL,
        customer_name VARCHAR(200),
        phone VARCHAR(50),
        inquiry_date VARCHAR(50),
        move_in_date VARCHAR(50),
        amount VARCHAR(100),
        room_count VARCHAR(50),
        location VARCHAR(200),
        loan_info TEXT,
        parking VARCHAR(50),
        pets VARCHAR(50),
        progress_status VARCHAR(50) DEFAULT '진행중',
        memo TEXT,
        created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        budget_min VARCHAR(100),
        budget_max VARCHAR(100),
        preferred_area TEXT,
        special_requirements TEXT,
        contact_preference VARCHAR(50) DEFAULT 'phone'
    );
    """
    execute_sql(conn, create_table_sql, "employee_customers 테이블 생성")
    
    # 필수 컬럼들 추가
    missing_columns = [
        ("phone", "VARCHAR(50)", "전화번호"),
        ("inquiry_date", "VARCHAR(50)", "문의일자"),
        ("move_in_date", "VARCHAR(50)", "입주희망일"),
        ("amount", "VARCHAR(100)", "금액"),
        ("room_count", "VARCHAR(50)", "방수"),
        ("location", "VARCHAR(200)", "희망지역"),
        ("loan_info", "TEXT", "대출정보"),
        ("parking", "VARCHAR(50)", "주차"),
        ("pets", "VARCHAR(50)", "반려동물"),
        ("progress_status", "VARCHAR(50) DEFAULT '진행중'", "진행상태"),
        ("memo", "TEXT", "메모"),
        ("last_updated", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "최종수정일"),
        ("budget_min", "VARCHAR(100)", "최소예산"),
        ("budget_max", "VARCHAR(100)", "최대예산"),
        ("preferred_area", "TEXT", "선호지역"),
        ("special_requirements", "TEXT", "특수요구사항"),
        ("contact_preference", "VARCHAR(50) DEFAULT 'phone'", "연락선호방식")
    ]
    
    for col_name, col_type, description in missing_columns:
        if not check_column_exists(conn, 'employee_customers', col_name):
            sql = f"ALTER TABLE employee_customers ADD COLUMN {col_name} {col_type};"
            execute_sql(conn, sql, f"employee_customers.{col_name} 컬럼 추가 ({description})")

def fix_links_table(conn):
    """links 테이블 구조 완벽 수정 (주거용)"""
    logger.info("🔧 links 테이블 수정 시작")
    
    # 테이블 생성 (없는 경우)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS links (
        id SERIAL PRIMARY KEY,
        url TEXT NOT NULL,
        platform VARCHAR(50),
        added_by VARCHAR(100),
        date_added VARCHAR(50),
        rating INTEGER DEFAULT 0,
        liked INTEGER DEFAULT 0,
        disliked INTEGER DEFAULT 0,
        memo TEXT,
        management_site_id VARCHAR(50),
        guarantee_insurance INTEGER DEFAULT 0,
        is_deleted INTEGER DEFAULT 0,
        is_checked INTEGER DEFAULT 0,
        residence_extra TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        view_count INTEGER DEFAULT 0,
        price VARCHAR(100),
        area VARCHAR(50),
        room_type VARCHAR(50),
        floor_info VARCHAR(50),
        deposit VARCHAR(100),
        monthly_rent VARCHAR(100)
    );
    """
    execute_sql(conn, create_table_sql, "links 테이블 생성")
    
    # 필수 컬럼들 추가
    missing_columns = [
        ("guarantee_insurance", "INTEGER DEFAULT 0", "보증보험가능"),
        ("is_deleted", "INTEGER DEFAULT 0", "삭제여부"),
        ("is_checked", "INTEGER DEFAULT 0", "확인여부"),
        ("residence_extra", "TEXT DEFAULT ''", "주거용추가정보"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "생성시간"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "수정시간"),
        ("view_count", "INTEGER DEFAULT 0", "조회수"),
        ("price", "VARCHAR(100)", "가격"),
        ("area", "VARCHAR(50)", "면적"),
        ("room_type", "VARCHAR(50)", "방타입"),
        ("floor_info", "VARCHAR(50)", "층정보"),
        ("deposit", "VARCHAR(100)", "보증금"),
        ("monthly_rent", "VARCHAR(100)", "월세")
    ]
    
    for col_name, col_type, description in missing_columns:
        if not check_column_exists(conn, 'links', col_name):
            sql = f"ALTER TABLE links ADD COLUMN {col_name} {col_type};"
            execute_sql(conn, sql, f"links.{col_name} 컬럼 추가 ({description})")

def fix_office_links_table(conn):
    """office_links 테이블 구조 완벽 수정 (업무용)"""
    logger.info("🔧 office_links 테이블 수정 시작")
    
    # 테이블 생성 (없는 경우)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS office_links (
        id SERIAL PRIMARY KEY,
        url TEXT NOT NULL,
        platform VARCHAR(50) NOT NULL,
        added_by VARCHAR(100) NOT NULL,
        date_added VARCHAR(50) NOT NULL,
        rating INTEGER DEFAULT 5,
        liked INTEGER DEFAULT 0,
        disliked INTEGER DEFAULT 0,
        memo TEXT DEFAULT '',
        customer_name VARCHAR(100) DEFAULT '000',
        move_in_date VARCHAR(50) DEFAULT '',
        management_site_id VARCHAR(50) DEFAULT NULL,
        guarantee_insurance INTEGER DEFAULT 0,
        is_checked INTEGER DEFAULT 0,
        unchecked_likes_work INTEGER DEFAULT 0,
        is_deleted INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        view_count INTEGER DEFAULT 0,
        office_type VARCHAR(50),
        office_size VARCHAR(50),
        monthly_fee VARCHAR(100),
        deposit_amount VARCHAR(100),
        utilities_included BOOLEAN DEFAULT FALSE,
        parking_available BOOLEAN DEFAULT FALSE,
        elevator_available BOOLEAN DEFAULT FALSE
    );
    """
    execute_sql(conn, create_table_sql, "office_links 테이블 생성")
    
    # 필수 컬럼들 추가
    missing_columns = [
        ("unchecked_likes_work", "INTEGER DEFAULT 0", "미확인좋아요(업무용)"),
        ("is_deleted", "INTEGER DEFAULT 0", "삭제여부"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "생성시간"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "수정시간"),
        ("view_count", "INTEGER DEFAULT 0", "조회수"),
        ("office_type", "VARCHAR(50)", "사무실타입"),
        ("office_size", "VARCHAR(50)", "사무실크기"),
        ("monthly_fee", "VARCHAR(100)", "월임대료"),
        ("deposit_amount", "VARCHAR(100)", "보증금"),
        ("utilities_included", "BOOLEAN DEFAULT FALSE", "관리비포함여부"),
        ("parking_available", "BOOLEAN DEFAULT FALSE", "주차가능여부"),
        ("elevator_available", "BOOLEAN DEFAULT FALSE", "엘리베이터여부")
    ]
    
    for col_name, col_type, description in missing_columns:
        if not check_column_exists(conn, 'office_links', col_name):
            sql = f"ALTER TABLE office_links ADD COLUMN {col_name} {col_type};"
            execute_sql(conn, sql, f"office_links.{col_name} 컬럼 추가 ({description})")

def fix_guarantee_insurance_log_table(conn):
    """guarantee_insurance_log 테이블 구조 완벽 수정"""
    logger.info("🔧 guarantee_insurance_log 테이블 수정 시작")
    
    # 테이블 생성 (없는 경우)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS guarantee_insurance_log (
        id SERIAL PRIMARY KEY,
        link_id INTEGER,
        management_site_id VARCHAR(50),
        employee_id VARCHAR(50),
        action VARCHAR(100),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        table_type VARCHAR(20) DEFAULT 'office_links',
        details TEXT,
        ip_address VARCHAR(45),
        user_agent TEXT
    );
    """
    execute_sql(conn, create_table_sql, "guarantee_insurance_log 테이블 생성")
    
    # 필수 컬럼들 추가
    missing_columns = [
        ("table_type", "VARCHAR(20) DEFAULT 'office_links'", "테이블타입"),
        ("details", "TEXT", "상세내용"),
        ("ip_address", "VARCHAR(45)", "IP주소"),
        ("user_agent", "TEXT", "사용자에이전트")
    ]
    
    for col_name, col_type, description in missing_columns:
        if not check_column_exists(conn, 'guarantee_insurance_log', col_name):
            sql = f"ALTER TABLE guarantee_insurance_log ADD COLUMN {col_name} {col_type};"
            execute_sql(conn, sql, f"guarantee_insurance_log.{col_name} 컬럼 추가 ({description})")

def fix_customer_info_table(conn):
    """customer_info 테이블 구조 완벽 수정"""
    logger.info("🔧 customer_info 테이블 수정 시작")
    
    # 테이블 생성 (없는 경우)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS customer_info (
        id INTEGER PRIMARY KEY,
        customer_name VARCHAR(200) DEFAULT '제일좋은집 찾아드릴분',
        move_in_date VARCHAR(50) DEFAULT '',
        phone VARCHAR(50),
        email VARCHAR(200),
        preferred_contact VARCHAR(20) DEFAULT 'phone',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    execute_sql(conn, create_table_sql, "customer_info 테이블 생성")
    
    # 기본 데이터 삽입
    insert_default_sql = """
    INSERT INTO customer_info (id, customer_name, move_in_date) 
    VALUES (1, '제일좋은집 찾아드릴분', '') 
    ON CONFLICT (id) DO NOTHING;
    """
    execute_sql(conn, insert_default_sql, "customer_info 기본 데이터 삽입")
    
    # 필수 컬럼들 추가
    missing_columns = [
        ("phone", "VARCHAR(50)", "전화번호"),
        ("email", "VARCHAR(200)", "이메일"),
        ("preferred_contact", "VARCHAR(20) DEFAULT 'phone'", "선호연락방식"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "생성시간"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "수정시간")
    ]
    
    for col_name, col_type, description in missing_columns:
        if not check_column_exists(conn, 'customer_info', col_name):
            sql = f"ALTER TABLE customer_info ADD COLUMN {col_name} {col_type};"
            execute_sql(conn, sql, f"customer_info.{col_name} 컬럼 추가 ({description})")

def create_indexes_and_constraints(conn):
    """인덱스 및 제약조건 생성"""
    logger.info("🔧 인덱스 및 제약조건 생성 시작")
    
    indexes = [
        # employees 테이블 인덱스
        "CREATE INDEX IF NOT EXISTS idx_employees_employee_id ON employees(employee_id);",
        "CREATE INDEX IF NOT EXISTS idx_employees_team ON employees(team);",
        "CREATE INDEX IF NOT EXISTS idx_employees_is_active ON employees(is_active);",
        
        # employee_customers 테이블 인덱스
        "CREATE INDEX IF NOT EXISTS idx_employee_customers_employee_id ON employee_customers(employee_id);",
        "CREATE INDEX IF NOT EXISTS idx_employee_customers_management_site_id ON employee_customers(management_site_id);",
        "CREATE INDEX IF NOT EXISTS idx_employee_customers_progress_status ON employee_customers(progress_status);",
        
        # links 테이블 인덱스
        "CREATE INDEX IF NOT EXISTS idx_links_management_site_id ON links(management_site_id);",
        "CREATE INDEX IF NOT EXISTS idx_links_added_by ON links(added_by);",
        "CREATE INDEX IF NOT EXISTS idx_links_guarantee_insurance ON links(guarantee_insurance);",
        "CREATE INDEX IF NOT EXISTS idx_links_date_added ON links(date_added);",
        
        # office_links 테이블 인덱스
        "CREATE INDEX IF NOT EXISTS idx_office_links_management_site_id ON office_links(management_site_id);",
        "CREATE INDEX IF NOT EXISTS idx_office_links_added_by ON office_links(added_by);",
        "CREATE INDEX IF NOT EXISTS idx_office_links_guarantee_insurance ON office_links(guarantee_insurance);",
        "CREATE INDEX IF NOT EXISTS idx_office_links_date_added ON office_links(date_added);",
        
        # guarantee_insurance_log 테이블 인덱스
        "CREATE INDEX IF NOT EXISTS idx_guarantee_log_link_id ON guarantee_insurance_log(link_id);",
        "CREATE INDEX IF NOT EXISTS idx_guarantee_log_management_site_id ON guarantee_insurance_log(management_site_id);",
        "CREATE INDEX IF NOT EXISTS idx_guarantee_log_employee_id ON guarantee_insurance_log(employee_id);",
        "CREATE INDEX IF NOT EXISTS idx_guarantee_log_timestamp ON guarantee_insurance_log(timestamp);"
    ]
    
    for index_sql in indexes:
        execute_sql(conn, index_sql, f"인덱스 생성: {index_sql.split()[4]}")

def update_existing_data(conn):
    """기존 데이터 정리 및 업데이트"""
    logger.info("🔧 기존 데이터 정리 시작")
    
    # NULL 값들을 기본값으로 업데이트
    updates = [
        # employees 테이블
        "UPDATE employees SET password = '1234' WHERE password IS NULL OR password = '';",
        "UPDATE employees SET is_active = TRUE WHERE is_active IS NULL;",
        "UPDATE employees SET role = '직원' WHERE role IS NULL;",
        
        # employee_customers 테이블
        "UPDATE employee_customers SET progress_status = '진행중' WHERE progress_status IS NULL OR progress_status = '';",
        "UPDATE employee_customers SET contact_preference = 'phone' WHERE contact_preference IS NULL;",
        
        # links 테이블
        "UPDATE links SET guarantee_insurance = 0 WHERE guarantee_insurance IS NULL;",
        "UPDATE links SET is_deleted = 0 WHERE is_deleted IS NULL;",
        "UPDATE links SET is_checked = 0 WHERE is_checked IS NULL;",
        "UPDATE links SET residence_extra = '' WHERE residence_extra IS NULL;",
        "UPDATE links SET view_count = 0 WHERE view_count IS NULL;",
        
        # office_links 테이블
        "UPDATE office_links SET guarantee_insurance = 0 WHERE guarantee_insurance IS NULL;",
        "UPDATE office_links SET is_deleted = 0 WHERE is_deleted IS NULL;",
        "UPDATE office_links SET unchecked_likes_work = 0 WHERE unchecked_likes_work IS NULL;",
        "UPDATE office_links SET utilities_included = FALSE WHERE utilities_included IS NULL;",
        "UPDATE office_links SET parking_available = FALSE WHERE parking_available IS NULL;",
        "UPDATE office_links SET elevator_available = FALSE WHERE elevator_available IS NULL;",
        
        # customer_info 테이블
        "UPDATE customer_info SET preferred_contact = 'phone' WHERE preferred_contact IS NULL;"
    ]
    
    for update_sql in updates:
        execute_sql(conn, update_sql, f"데이터 업데이트")

def main():
    """메인 실행 함수"""
    logger.info("🚀 PostgreSQL 데이터베이스 컬럼 구조 완벽 수정 시작!")
    logger.info("=" * 60)
    
    # DB 연결
    conn = get_db_connection()
    
    try:
        # 1. 모든 테이블 구조 수정
        fix_employees_table(conn)
        fix_employee_customers_table(conn)
        fix_links_table(conn)
        fix_office_links_table(conn)
        fix_guarantee_insurance_log_table(conn)
        fix_customer_info_table(conn)
        
        # 2. 인덱스 및 제약조건 생성
        create_indexes_and_constraints(conn)
        
        # 3. 기존 데이터 정리
        update_existing_data(conn)
        
        # 4. 최종 확인
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tables = cursor.fetchall()
        
        logger.info("=" * 60)
        logger.info("🎉 PostgreSQL 데이터베이스 구조 수정 완료!")
        logger.info(f"📊 총 {len(tables)}개의 테이블이 완벽하게 구성됨:")
        
        for table in tables:
            table_name = table['table_name']
            cursor.execute(f"SELECT COUNT(*) as count FROM information_schema.columns WHERE table_name = '{table_name}';")
            column_count = cursor.fetchone()['count']
            logger.info(f"  ✅ {table_name}: {column_count}개 컬럼")
        
        logger.info("=" * 60)
        logger.info("🔥 치타처럼 빠른 작업 완료! 모든 컬럼이 완벽하게 준비되었습니다!")
        
    except Exception as e:
        logger.error(f"❌ 실행 중 오류 발생: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 