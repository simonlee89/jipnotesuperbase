#!/usr/bin/env python3
"""
PostgreSQL 데이터베이스 컬럼 구조 완벽 정리 스크립트
치타처럼 빠르게 모든 누락된 컬럼을 추가합니다!

실행 방법:
python postgresql_column_fix.py

주의사항:
- Railway PostgreSQL 환경에서만 실행됩니다
- 기존 데이터는 보존됩니다
- 안전한 ALTER TABLE 문을 사용합니다
"""

import os
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.error("❌ psycopg2 모듈이 없습니다. PostgreSQL에 연결할 수 없습니다.")
    exit(1)

def get_postgres_connection():
    """PostgreSQL 연결"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url or not PSYCOPG2_AVAILABLE:
        raise Exception("PostgreSQL 환경이 아닙니다.")
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise Exception(f"PostgreSQL 연결 실패: {e}")

def safe_add_column(cursor, table_name, column_name, column_definition):
    """안전하게 컬럼 추가"""
    try:
        # 컬럼 존재 여부 확인
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        
        if cursor.fetchone():
            logger.info(f"⚠️  {table_name}.{column_name} 이미 존재함 - 건너뜀")
            return False
        
        # 컬럼 추가
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        cursor.execute(sql)
        logger.info(f"✅ {table_name}.{column_name} 추가 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ {table_name}.{column_name} 추가 실패: {e}")
        return False

def create_safe_index(cursor, index_name, table_name, columns):
    """안전하게 인덱스 생성"""
    try:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})")
        logger.info(f"✅ 인덱스 {index_name} 생성 완료")
        return True
    except Exception as e:
        logger.error(f"❌ 인덱스 {index_name} 생성 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("🔥 PostgreSQL 컬럼 구조 완벽 정리 시작!")
    logger.info("치타처럼 빠르게 작업합니다...")
    logger.info("=" * 60)
    
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # 현재 테이블 목록 확인
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 기존 테이블: {existing_tables}")
        
        added_columns = 0
        
        # 1. employees 테이블 컬럼 추가
        logger.info("\n📋 employees 테이블 컬럼 추가 중...")
        employee_columns = [
            ("last_login", "TIMESTAMP"),
            ("phone", "VARCHAR(50)"),
            ("email", "VARCHAR(200)"),
            ("role", "VARCHAR(50) DEFAULT '직원'")
        ]
        
        for col_name, col_def in employee_columns:
            if safe_add_column(cursor, "employees", col_name, col_def):
                added_columns += 1
        
        # 2. employee_customers 테이블 컬럼 추가
        logger.info("\n👥 employee_customers 테이블 컬럼 추가 중...")
        customer_columns = [
            ("phone", "VARCHAR(50)"),
            ("inquiry_date", "VARCHAR(50)"),
            ("move_in_date", "VARCHAR(50)"),
            ("amount", "VARCHAR(100)"),
            ("room_count", "VARCHAR(50)"),
            ("location", "VARCHAR(200)"),
            ("loan_info", "TEXT"),
            ("parking", "VARCHAR(50)"),
            ("pets", "VARCHAR(50)"),
            ("budget_min", "VARCHAR(100)"),
            ("budget_max", "VARCHAR(100)"),
            ("preferred_area", "TEXT"),
            ("special_requirements", "TEXT"),
            ("contact_preference", "VARCHAR(50) DEFAULT 'phone'")
        ]
        
        for col_name, col_def in customer_columns:
            if safe_add_column(cursor, "employee_customers", col_name, col_def):
                added_columns += 1
        
        # 3. links 테이블 컬럼 추가 (주거용 매물)
        logger.info("\n🏠 links 테이블 컬럼 추가 중...")
        links_columns = [
            ("residence_extra", "TEXT DEFAULT ''"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("view_count", "INTEGER DEFAULT 0"),
            ("price", "VARCHAR(100)"),
            ("area", "VARCHAR(50)"),
            ("room_type", "VARCHAR(50)"),
            ("floor_info", "VARCHAR(50)"),
            ("deposit", "VARCHAR(100)"),
            ("monthly_rent", "VARCHAR(100)")
        ]
        
        for col_name, col_def in links_columns:
            if safe_add_column(cursor, "links", col_name, col_def):
                added_columns += 1
        
        # 4. office_links 테이블 컬럼 추가 (업무용 매물)
        logger.info("\n💼 office_links 테이블 컬럼 추가 중...")
        office_columns = [
            ("customer_name", "VARCHAR(100) DEFAULT '000'"),
            ("move_in_date", "VARCHAR(50) DEFAULT ''"),
            ("management_site_id", "VARCHAR(50)"),
            ("is_checked", "INTEGER DEFAULT 0"),
            ("unchecked_likes_work", "INTEGER DEFAULT 0"),
            ("is_deleted", "INTEGER DEFAULT 0"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("view_count", "INTEGER DEFAULT 0"),
            ("office_type", "VARCHAR(50)"),
            ("office_size", "VARCHAR(50)"),
            ("monthly_fee", "VARCHAR(100)"),
            ("deposit_amount", "VARCHAR(100)"),
            ("utilities_included", "BOOLEAN DEFAULT FALSE"),
            ("parking_available", "BOOLEAN DEFAULT FALSE"),
            ("elevator_available", "BOOLEAN DEFAULT FALSE")
        ]
        
        for col_name, col_def in office_columns:
            if safe_add_column(cursor, "office_links", col_name, col_def):
                added_columns += 1
        
        # 5. guarantee_insurance_log 테이블 컬럼 추가
        logger.info("\n📋 guarantee_insurance_log 테이블 컬럼 추가 중...")
        log_columns = [
            ("table_type", "VARCHAR(20) DEFAULT 'office_links'"),
            ("details", "TEXT"),
            ("ip_address", "VARCHAR(45)"),
            ("user_agent", "TEXT")
        ]
        
        for col_name, col_def in log_columns:
            if safe_add_column(cursor, "guarantee_insurance_log", col_name, col_def):
                added_columns += 1
        
        # 6. customer_info 테이블 컬럼 추가
        logger.info("\n📞 customer_info 테이블 컬럼 추가 중...")
        
        # customer_info 테이블이 없으면 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_info (
                id INTEGER PRIMARY KEY,
                customer_name VARCHAR(200) DEFAULT '제일좋은집 찾아드릴분',
                move_in_date VARCHAR(50) DEFAULT '',
                phone VARCHAR(50),
                email VARCHAR(200),
                preferred_contact VARCHAR(20) DEFAULT 'phone',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ customer_info 테이블 생성/확인 완료")
        
        # 기본 데이터 삽입
        cursor.execute("""
            INSERT INTO customer_info (id, customer_name, move_in_date) 
            VALUES (1, '제일좋은집 찾아드릴분', '') 
            ON CONFLICT (id) DO NOTHING
        """)
        
        info_columns = [
            ("phone", "VARCHAR(50)"),
            ("email", "VARCHAR(200)"),
            ("preferred_contact", "VARCHAR(20) DEFAULT 'phone'"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for col_name, col_def in info_columns:
            if safe_add_column(cursor, "customer_info", col_name, col_def):
                added_columns += 1
        
        # 7. 성능 최적화 인덱스 생성
        logger.info("\n🚀 성능 최적화 인덱스 생성 중...")
        
        indexes = [
            ("idx_employees_employee_id", "employees", "employee_id"),
            ("idx_employees_team", "employees", "team"),
            ("idx_employees_last_login", "employees", "last_login"),
            ("idx_employee_customers_employee_id", "employee_customers", "employee_id"),
            ("idx_employee_customers_management_site_id", "employee_customers", "management_site_id"),
            ("idx_employee_customers_progress_status", "employee_customers", "progress_status"),
            ("idx_links_management_site_id", "links", "management_site_id"),
            ("idx_links_added_by", "links", "added_by"),
            ("idx_links_guarantee_insurance", "links", "guarantee_insurance"),
            ("idx_links_is_deleted", "links", "is_deleted"),
            ("idx_links_liked", "links", "liked"),
            ("idx_office_links_management_site_id", "office_links", "management_site_id"),
            ("idx_office_links_added_by", "office_links", "added_by"),
            ("idx_office_links_guarantee_insurance", "office_links", "guarantee_insurance"),
            ("idx_office_links_is_deleted", "office_links", "is_deleted"),
            ("idx_office_links_liked", "office_links", "liked"),
            ("idx_guarantee_log_management_site_id", "guarantee_insurance_log", "management_site_id"),
            ("idx_guarantee_log_employee_id", "guarantee_insurance_log", "employee_id"),
            ("idx_guarantee_log_timestamp", "guarantee_insurance_log", "timestamp")
        ]
        
        created_indexes = 0
        for idx_name, table_name, columns in indexes:
            if create_safe_index(cursor, idx_name, table_name, columns):
                created_indexes += 1
        
        # 8. 데이터 정리 및 기본값 설정
        logger.info("\n🧹 데이터 정리 및 기본값 설정 중...")
        
        cleanup_queries = [
            # employees 테이블 기본값 설정
            "UPDATE employees SET role = '직원' WHERE role IS NULL",
            "UPDATE employees SET is_active = TRUE WHERE is_active IS NULL",
            
            # employee_customers 테이블 기본값 설정
            "UPDATE employee_customers SET progress_status = '진행중' WHERE progress_status IS NULL",
            "UPDATE employee_customers SET contact_preference = 'phone' WHERE contact_preference IS NULL",
            "UPDATE employee_customers SET created_date = CURRENT_TIMESTAMP WHERE created_date IS NULL",
            "UPDATE employee_customers SET last_updated = CURRENT_TIMESTAMP WHERE last_updated IS NULL",
            
            # links 테이블 기본값 설정
            "UPDATE links SET residence_extra = '' WHERE residence_extra IS NULL",
            "UPDATE links SET is_deleted = 0 WHERE is_deleted IS NULL",
            "UPDATE links SET is_checked = 0 WHERE is_checked IS NULL",
            "UPDATE links SET guarantee_insurance = 0 WHERE guarantee_insurance IS NULL",
            "UPDATE links SET view_count = 0 WHERE view_count IS NULL",
            "UPDATE links SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL",
            "UPDATE links SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL",
            
            # office_links 테이블 기본값 설정
            "UPDATE office_links SET customer_name = '000' WHERE customer_name IS NULL",
            "UPDATE office_links SET move_in_date = '' WHERE move_in_date IS NULL",
            "UPDATE office_links SET is_deleted = 0 WHERE is_deleted IS NULL",
            "UPDATE office_links SET is_checked = 0 WHERE is_checked IS NULL",
            "UPDATE office_links SET unchecked_likes_work = 0 WHERE unchecked_likes_work IS NULL",
            "UPDATE office_links SET guarantee_insurance = 0 WHERE guarantee_insurance IS NULL",
            "UPDATE office_links SET view_count = 0 WHERE view_count IS NULL",
            "UPDATE office_links SET utilities_included = FALSE WHERE utilities_included IS NULL",
            "UPDATE office_links SET parking_available = FALSE WHERE parking_available IS NULL",
            "UPDATE office_links SET elevator_available = FALSE WHERE elevator_available IS NULL",
            "UPDATE office_links SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL",
            "UPDATE office_links SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL",
            
            # guarantee_insurance_log 테이블 기본값 설정
            "UPDATE guarantee_insurance_log SET table_type = 'office_links' WHERE table_type IS NULL",
            "UPDATE guarantee_insurance_log SET timestamp = CURRENT_TIMESTAMP WHERE timestamp IS NULL"
        ]
        
        updated_rows = 0
        for query in cleanup_queries:
            try:
                cursor.execute(query)
                rows = cursor.rowcount
                if rows > 0:
                    updated_rows += rows
                    logger.info(f"✅ 데이터 정리: {rows}개 행 업데이트")
            except Exception as e:
                logger.warning(f"⚠️  데이터 정리 쿼리 실행 중 오류: {e}")
        
        # 커밋
        conn.commit()
        
        # 최종 결과 출력
        logger.info("\n" + "=" * 60)
        logger.info("🎉 PostgreSQL 컬럼 구조 완벽 정리 완료!")
        logger.info("=" * 60)
        logger.info(f"📊 총 추가된 컬럼: {added_columns}개")
        logger.info(f"🚀 생성된 인덱스: {created_indexes}개")
        logger.info(f"🧹 정리된 데이터: {updated_rows}개 행")
        logger.info("=" * 60)
        
        # 최종 테이블 구조 확인
        logger.info("📋 최종 테이블 구조:")
        
        for table in ['employees', 'employee_customers', 'links', 'office_links', 'guarantee_insurance_log', 'customer_info']:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table,))
            
            columns = cursor.fetchall()
            logger.info(f"\n🔹 {table} ({len(columns)}개 컬럼):")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                logger.info(f"   - {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        cursor.close()
        conn.close()
        
        logger.info("\n🔥 치타처럼 빠른 작업 완료!")
        logger.info("이제 3개 애플리케이션이 완벽하게 동기화되었습니다.")
        
    except Exception as e:
        logger.error(f"❌ 치명적 오류: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 성공: PostgreSQL 컬럼 구조가 완벽하게 정리되었습니다!")
        exit(0)
    else:
        print("\n❌ 실패: 오류가 발생했습니다.")
        exit(1) 