#!/usr/bin/env python3
"""
PostgreSQL 데이터베이스 스키마 업데이트 스크립트
"""

import os
import sys
import logging
from db_utils import get_db_connection

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database_schema():
    """데이터베이스 스키마를 업데이트합니다."""
    
    logger.info("🚀 PostgreSQL 데이터베이스 스키마 업데이트 시작...")
    
    try:
        # 데이터베이스 연결
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        logger.info(f"✅ 데이터베이스 연결 성공 (타입: {db_type})")
        
        # 1. employees 테이블 수정: department를 team으로 변경
        logger.info("1️⃣ employees 테이블의 department 컬럼을 team으로 변경 중...")
        try:
            cursor.execute("ALTER TABLE employees RENAME COLUMN department TO team;")
            logger.info("   ✅ department → team 변경 완료")
        except Exception as e:
            if "does not exist" in str(e).lower():
                logger.info("   ℹ️ department 컬럼이 이미 존재하지 않음 (이미 변경됨)")
            else:
                logger.warning(f"   ⚠️ department → team 변경 중 오류: {e}")
        
        # 2. employees 테이블에 status 필드 추가
        logger.info("2️⃣ employees 테이블에 status 필드 추가 중...")
        try:
            cursor.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';")
            logger.info("   ✅ status 필드 추가 완료")
        except Exception as e:
            logger.warning(f"   ⚠️ status 필드 추가 중 오류: {e}")
        
        # 3. customer_info 테이블 삭제
        logger.info("3️⃣ customer_info 테이블 삭제 중...")
        try:
            cursor.execute("DROP TABLE IF EXISTS customer_info CASCADE;")
            logger.info("   ✅ customer_info 테이블 삭제 완료")
        except Exception as e:
            logger.warning(f"   ⚠️ customer_info 테이블 삭제 중 오류: {e}")
        
        # 4. links 테이블에서 residence_extra 필드 제거
        logger.info("4️⃣ links 테이블에서 residence_extra 필드 제거 중...")
        try:
            cursor.execute("ALTER TABLE links DROP COLUMN IF EXISTS residence_extra;")
            logger.info("   ✅ residence_extra 필드 제거 완료")
        except Exception as e:
            logger.warning(f"   ⚠️ residence_extra 필드 제거 중 오류: {e}")
        
        # 5. 30일 이상된 보증보험 항목 정리
        logger.info("5️⃣ 30일 이상된 보증보험 항목 정리 중...")
        try:
            cursor.execute("""
                UPDATE links 
                SET guarantee_insurance = FALSE 
                WHERE guarantee_insurance = TRUE 
                AND date_added < CURRENT_DATE - INTERVAL '30 days';
            """)
            updated_rows = cursor.rowcount
            logger.info(f"   ✅ {updated_rows}개의 30일 이상된 보증보험 항목 정리 완료")
        except Exception as e:
            logger.warning(f"   ⚠️ 보증보험 항목 정리 중 오류: {e}")
        
        # 6. 인덱스 추가 (성능 향상)
        logger.info("6️⃣ 성능 향상을 위한 인덱스 추가 중...")
        indexes = [
            ("idx_links_guarantee_date", "links(guarantee_insurance, date_added)"),
            ("idx_employee_customers_management_site", "employee_customers(management_site_id)"),
            ("idx_employees_status", "employees(status)")
        ]
        
        for index_name, index_definition in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_definition};")
                logger.info(f"   ✅ 인덱스 {index_name} 생성 완료")
            except Exception as e:
                logger.warning(f"   ⚠️ 인덱스 {index_name} 생성 중 오류: {e}")
        
        # 변경사항 커밋
        conn.commit()
        logger.info("💾 모든 변경사항 커밋 완료")
        
        # 7. 변경사항 확인
        logger.info("7️⃣ 변경사항 확인 중...")
        
        # employees 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'employees'
            ORDER BY ordinal_position;
        """)
        employees_columns = cursor.fetchall()
        logger.info("   📋 employees 테이블 구조:")
        for col in employees_columns:
            logger.info(f"      - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        # customer_info 테이블 존재 여부 확인
        cursor.execute("""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables 
            WHERE table_name = 'customer_info';
        """)
        customer_info_exists = cursor.fetchone()[0]
        logger.info(f"   📋 customer_info 테이블 존재 여부: {'존재함' if customer_info_exists > 0 else '삭제됨'}")
        
        # links 테이블의 residence_extra 필드 존재 여부 확인
        cursor.execute("""
            SELECT COUNT(*) as column_count
            FROM information_schema.columns 
            WHERE table_name = 'links' AND column_name = 'residence_extra';
        """)
        residence_extra_exists = cursor.fetchone()[0]
        logger.info(f"   📋 links.residence_extra 필드 존재 여부: {'존재함' if residence_extra_exists > 0 else '제거됨'}")
        
        cursor.close()
        conn.close()
        
        logger.info("🎉 PostgreSQL 데이터베이스 스키마 업데이트 완료!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 업데이트 중 심각한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("PostgreSQL 데이터베이스 스키마 업데이트 도구")
    logger.info("=" * 60)
    
    # DATABASE_URL 환경변수 확인
    if not os.environ.get('DATABASE_URL'):
        logger.error("❌ DATABASE_URL 환경변수가 설정되지 않았습니다.")
        logger.info("💡 Railway 환경에서 실행하거나, 로컬에서 DATABASE_URL을 설정해주세요.")
        sys.exit(1)
    
    success = update_database_schema()
    
    if success:
        logger.info("✅ 업데이트가 성공적으로 완료되었습니다!")
        sys.exit(0)
    else:
        logger.error("❌ 업데이트 중 오류가 발생했습니다.")
        sys.exit(1) 