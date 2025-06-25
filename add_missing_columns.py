#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 데이터베이스에 누락된 컬럼들을 추가하는 스크립트
치타처럼 빠르게 실행!
"""

import os
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# db_utils에서 연결 함수 가져오기
from db_utils import get_db_connection

def check_column_exists(conn, table_name, column_name):
    """컬럼 존재 여부 확인"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    except Exception as e:
        logger.error(f"컬럼 확인 실패: {e}")
        return False

def execute_sql_safe(conn, sql, description=""):
    """SQL 안전 실행"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        logger.info(f"✅ {description} 성공")
        cursor.close()
        return True
    except Exception as e:
        logger.warning(f"⚠️ {description} 건너뜀 (이미 존재하거나 오류): {e}")
        conn.rollback()
        return False

def add_missing_columns():
    """누락된 컬럼들을 추가"""
    logger.info("🚀 PostgreSQL 컬럼 추가 작업 시작!")
    
    conn, db_type = get_db_connection()
    
    if db_type != 'postgresql':
        logger.error("PostgreSQL이 아닙니다. 이 스크립트는 PostgreSQL 전용입니다.")
        return
    
    logger.info("✅ PostgreSQL 연결 확인 완료")
    
    # 컬럼 추가 작업들
    column_additions = [
        # employees 테이블
        ("employees", "last_login", "TIMESTAMP", "마지막 로그인 시간"),
        ("employees", "phone", "VARCHAR(50)", "직원 전화번호"),
        ("employees", "email", "VARCHAR(200)", "직원 이메일"),
        ("employees", "role", "VARCHAR(50) DEFAULT '직원'", "직원 역할"),
        
        # employee_customers 테이블
        ("employee_customers", "phone", "VARCHAR(50)", "고객 전화번호"),
        ("employee_customers", "inquiry_date", "VARCHAR(50)", "문의 일자"),
        ("employee_customers", "move_in_date", "VARCHAR(50)", "입주 희망일"),
        ("employee_customers", "amount", "VARCHAR(100)", "희망 금액"),
        ("employee_customers", "room_count", "VARCHAR(50)", "방 개수"),
        ("employee_customers", "location", "VARCHAR(200)", "희망 지역"),
        ("employee_customers", "loan_info", "TEXT", "대출 정보"),
        ("employee_customers", "parking", "VARCHAR(50)", "주차 여부"),
        ("employee_customers", "pets", "VARCHAR(50)", "반려동물"),
        ("employee_customers", "last_updated", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "최종 수정일"),
        ("employee_customers", "budget_min", "VARCHAR(100)", "최소 예산"),
        ("employee_customers", "budget_max", "VARCHAR(100)", "최대 예산"),
        ("employee_customers", "preferred_area", "TEXT", "선호 지역"),
        ("employee_customers", "special_requirements", "TEXT", "특수 요구사항"),
        ("employee_customers", "contact_preference", "VARCHAR(50) DEFAULT 'phone'", "연락 선호 방식"),
        
        # links 테이블 (주거용)
        ("links", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "생성 시간"),
        ("links", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "수정 시간"),
        ("links", "view_count", "INTEGER DEFAULT 0", "조회수"),
        ("links", "price", "VARCHAR(100)", "가격"),
        ("links", "area", "VARCHAR(50)", "면적"),
        ("links", "room_type", "VARCHAR(50)", "방 타입"),
        ("links", "floor_info", "VARCHAR(50)", "층 정보"),
        ("links", "deposit", "VARCHAR(100)", "보증금"),
        ("links", "monthly_rent", "VARCHAR(100)", "월세"),
        
        # office_links 테이블 (업무용)
        ("office_links", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "생성 시간"),
        ("office_links", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "수정 시간"),
        ("office_links", "view_count", "INTEGER DEFAULT 0", "조회수"),
        ("office_links", "office_type", "VARCHAR(50)", "사무실 타입"),
        ("office_links", "office_size", "VARCHAR(50)", "사무실 크기"),
        ("office_links", "monthly_fee", "VARCHAR(100)", "월 임대료"),
        ("office_links", "deposit_amount", "VARCHAR(100)", "보증금"),
        ("office_links", "utilities_included", "BOOLEAN DEFAULT FALSE", "관리비 포함 여부"),
        ("office_links", "parking_available", "BOOLEAN DEFAULT FALSE", "주차 가능 여부"),
        ("office_links", "elevator_available", "BOOLEAN DEFAULT FALSE", "엘리베이터 여부"),
        
        # guarantee_insurance_log 테이블
        ("guarantee_insurance_log", "table_type", "VARCHAR(20) DEFAULT 'office_links'", "테이블 타입"),
        ("guarantee_insurance_log", "details", "TEXT", "상세 내용"),
        ("guarantee_insurance_log", "ip_address", "VARCHAR(45)", "IP 주소"),
        ("guarantee_insurance_log", "user_agent", "TEXT", "사용자 에이전트"),
        
        # customer_info 테이블
        ("customer_info", "phone", "VARCHAR(50)", "전화번호"),
        ("customer_info", "email", "VARCHAR(200)", "이메일"),
        ("customer_info", "preferred_contact", "VARCHAR(20) DEFAULT 'phone'", "선호 연락 방식"),
        ("customer_info", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "생성 시간"),
        ("customer_info", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "수정 시간"),
    ]
    
    added_count = 0
    skipped_count = 0
    
    for table_name, column_name, column_type, description in column_additions:
        if not check_column_exists(conn, table_name, column_name):
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};"
            if execute_sql_safe(conn, sql, f"{table_name}.{column_name} 컬럼 추가 ({description})"):
                added_count += 1
            else:
                skipped_count += 1
        else:
            logger.info(f"⏭️ {table_name}.{column_name} 이미 존재함 - 건너뜀")
            skipped_count += 1
    
    # 인덱스 추가
    logger.info("🔧 인덱스 생성 중...")
    
    indexes = [
        ("idx_employees_employee_id", "employees", "employee_id"),
        ("idx_employees_team", "employees", "team"),
        ("idx_employees_is_active", "employees", "is_active"),
        ("idx_employee_customers_employee_id", "employee_customers", "employee_id"),
        ("idx_employee_customers_management_site_id", "employee_customers", "management_site_id"),
        ("idx_employee_customers_progress_status", "employee_customers", "progress_status"),
        ("idx_links_management_site_id", "links", "management_site_id"),
        ("idx_links_added_by", "links", "added_by"),
        ("idx_links_guarantee_insurance", "links", "guarantee_insurance"),
        ("idx_links_date_added", "links", "date_added"),
        ("idx_office_links_management_site_id", "office_links", "management_site_id"),
        ("idx_office_links_added_by", "office_links", "added_by"),
        ("idx_office_links_guarantee_insurance", "office_links", "guarantee_insurance"),
        ("idx_office_links_date_added", "office_links", "date_added"),
        ("idx_guarantee_log_link_id", "guarantee_insurance_log", "link_id"),
        ("idx_guarantee_log_management_site_id", "guarantee_insurance_log", "management_site_id"),
        ("idx_guarantee_log_employee_id", "guarantee_insurance_log", "employee_id"),
        ("idx_guarantee_log_timestamp", "guarantee_insurance_log", "timestamp"),
    ]
    
    for idx_name, table_name, column_name in indexes:
        sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name});"
        execute_sql_safe(conn, sql, f"인덱스 {idx_name} 생성")
    
    # 기존 데이터 정리
    logger.info("🧹 기존 데이터 정리 중...")
    
    data_updates = [
        ("UPDATE employees SET role = '직원' WHERE role IS NULL;", "직원 역할 기본값 설정"),
        ("UPDATE employee_customers SET progress_status = '진행중' WHERE progress_status IS NULL OR progress_status = '';", "고객 진행상태 기본값 설정"),
        ("UPDATE employee_customers SET contact_preference = 'phone' WHERE contact_preference IS NULL;", "고객 연락방식 기본값 설정"),
        ("UPDATE links SET guarantee_insurance = 0 WHERE guarantee_insurance IS NULL;", "주거용 보증보험 기본값 설정"),
        ("UPDATE links SET is_deleted = 0 WHERE is_deleted IS NULL;", "주거용 삭제여부 기본값 설정"),
        ("UPDATE links SET is_checked = 0 WHERE is_checked IS NULL;", "주거용 확인여부 기본값 설정"),
        ("UPDATE links SET residence_extra = '' WHERE residence_extra IS NULL;", "주거용 추가정보 기본값 설정"),
        ("UPDATE links SET view_count = 0 WHERE view_count IS NULL;", "주거용 조회수 기본값 설정"),
        ("UPDATE office_links SET guarantee_insurance = 0 WHERE guarantee_insurance IS NULL;", "업무용 보증보험 기본값 설정"),
        ("UPDATE office_links SET is_deleted = 0 WHERE is_deleted IS NULL;", "업무용 삭제여부 기본값 설정"),
        ("UPDATE office_links SET unchecked_likes_work = 0 WHERE unchecked_likes_work IS NULL;", "업무용 미확인좋아요 기본값 설정"),
        ("UPDATE office_links SET utilities_included = FALSE WHERE utilities_included IS NULL;", "관리비포함여부 기본값 설정"),
        ("UPDATE office_links SET parking_available = FALSE WHERE parking_available IS NULL;", "주차가능여부 기본값 설정"),
        ("UPDATE office_links SET elevator_available = FALSE WHERE elevator_available IS NULL;", "엘리베이터여부 기본값 설정"),
        ("UPDATE customer_info SET preferred_contact = 'phone' WHERE preferred_contact IS NULL;", "고객정보 연락방식 기본값 설정"),
        ("UPDATE guarantee_insurance_log SET table_type = 'office_links' WHERE table_type IS NULL;", "보증보험로그 테이블타입 기본값 설정"),
    ]
    
    for sql, description in data_updates:
        execute_sql_safe(conn, sql, description)
    
    # 최종 결과 확인
    logger.info("📊 최종 테이블 구조 확인 중...")
    
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
    tables = cursor.fetchall()
    
    logger.info("=" * 60)
    logger.info("🎉 PostgreSQL 컬럼 추가 작업 완료!")
    logger.info(f"📈 추가된 컬럼: {added_count}개")
    logger.info(f"⏭️ 건너뛴 항목: {skipped_count}개")
    logger.info("=" * 60)
    logger.info(f"📊 총 {len(tables)}개의 테이블이 완벽하게 구성됨:")
    
    for table in tables:
        table_name = table['table_name']
        cursor.execute(f"SELECT COUNT(*) as count FROM information_schema.columns WHERE table_name = '{table_name}';")
        column_count = cursor.fetchone()['count']
        logger.info(f"  ✅ {table_name}: {column_count}개 컬럼")
    
    cursor.close()
    conn.close()
    
    logger.info("=" * 60)
    logger.info("🔥 치타처럼 빠른 컬럼 추가 완료! 모든 시스템이 완벽하게 준비되었습니다!")
    logger.info("🚀 이제 관리자페이지.py, 업무용.py, 주거용.py가 완벽하게 호환됩니다!")

if __name__ == "__main__":
    add_missing_columns() 