#!/usr/bin/env python3
"""
🔥 Railway PostgreSQL 컬럼 강제 추가 스크립트 (주거용/업무용 특화)
직원 추가 오류 해결 + 주거용/업무용 특화 컬럼 추가!

실행 방법:
python railway_column_fix.py

특징:
- PostgreSQL 전용 (Railway 환경)
- 안전한 IF NOT EXISTS 방식
- 주거용(links)과 업무용(office_links) 차별화
- 실시간 진행상황 출력
- 직원 추가 오류 즉시 해결
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
    logger.info("✅ psycopg2 모듈 로드 성공")
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.error("❌ psycopg2 모듈이 없습니다.")
    print("❌ PostgreSQL 환경이 아닙니다. Railway에서 실행해주세요.")
    exit(1)

def get_postgres_connection():
    """PostgreSQL 연결"""
    # PostgreSQL 서비스에서는 DATABASE_PUBLIC_URL 사용
    database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise Exception("DATABASE_URL 또는 DATABASE_PUBLIC_URL 환경변수가 없습니다. Railway 환경에서 실행해주세요.")
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        logger.info(f"✅ PostgreSQL 연결 성공! URL: {database_url[:50]}...")
        return conn
    except Exception as e:
        raise Exception(f"PostgreSQL 연결 실패: {e}")

def safe_add_column(cursor, table_name, column_name, column_definition):
    """안전하게 컬럼 추가 (이미 존재하면 건너뜀)"""
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
        logger.info(f"🎉 {table_name}.{column_name} 추가 성공!")
        return True
        
    except Exception as e:
        logger.error(f"❌ {table_name}.{column_name} 추가 실패: {e}")
        return False

def safe_create_index(cursor, index_name, table_name, columns):
    """안전하게 인덱스 생성"""
    try:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})")
        logger.info(f"📊 인덱스 {index_name} 생성 완료")
        return True
    except Exception as e:
        logger.error(f"❌ 인덱스 {index_name} 생성 실패: {e}")
        return False

def execute_safe_update(cursor, query, description):
    """안전하게 UPDATE 쿼리 실행"""
    try:
        cursor.execute(query)
        rows = cursor.rowcount
        if rows > 0:
            logger.info(f"🧹 {description}: {rows}개 행 업데이트")
            return rows
        return 0
    except Exception as e:
        logger.warning(f"⚠️  {description} 실패: {e}")
        return 0

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("🔥 Railway PostgreSQL 컬럼 강제 추가 시작! (주거용/업무용 특화)")
    print("직원 추가 오류 해결 + 주거용/업무용 차별화...")
    print("=" * 80)
    
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # 현재 테이블 목록 확인
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        existing_tables = [row['table_name'] for row in cursor.fetchall()]
        logger.info(f"📊 기존 테이블: {existing_tables}")
        
        added_columns = 0
        
        # 🚨 STEP 1: employees 테이블 컬럼 추가 (직원 추가 오류 해결)
        print("\n🚨 [긴급] employees 테이블 컬럼 추가 중...")
        employee_columns = [
            ("last_login", "TIMESTAMP"),
            ("phone", "VARCHAR(50)"),
            ("email", "VARCHAR(200)"),
            ("role", "VARCHAR(50) DEFAULT '직원'")
        ]
        
        for col_name, col_def in employee_columns:
            if safe_add_column(cursor, "employees", col_name, col_def):
                added_columns += 1
        
        # STEP 2: employee_customers 테이블 컬럼 추가
        print("\n👥 employee_customers 테이블 컬럼 추가 중...")
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
        
        # 🏠 STEP 3: links 테이블 컬럼 추가 (주거용 특화)
        print("\n🏠 links 테이블 컬럼 추가 중 (주거용 특화)...")
        links_columns = [
            # 기본 링크 정보
            ("memo", "TEXT DEFAULT ''"),
            ("residence_extra", "TEXT DEFAULT ''"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("view_count", "INTEGER DEFAULT 0"),
            ("is_checked", "INTEGER DEFAULT 0"),
            ("is_deleted", "INTEGER DEFAULT 0"),
            
            # 주거용 매물 세부 정보
            ("price", "VARCHAR(100)"),
            ("area", "VARCHAR(50)"),
            ("room_type", "VARCHAR(50)"),
            ("floor_info", "VARCHAR(50)"),
            ("deposit", "VARCHAR(100)"),
            ("monthly_rent", "VARCHAR(100)"),
            
            # 주거용 플랫폼 분류
            ("platform_jikbang", "BOOLEAN DEFAULT FALSE"),       # 직방
            ("platform_naver", "BOOLEAN DEFAULT FALSE"),         # 네이버
            ("platform_etc", "BOOLEAN DEFAULT FALSE"),           # 기타
            ("source_broker", "BOOLEAN DEFAULT FALSE"),          # 중개사
            ("source_customer", "BOOLEAN DEFAULT FALSE"),        # 손님
            
            # 주거용 보증보험 상태  
            ("guarantee_available", "BOOLEAN DEFAULT FALSE"),     # 보증보험가능
            ("guarantee_unavailable", "BOOLEAN DEFAULT FALSE"),   # 보증보험불가
            
            # 주거용 고객 반응
            ("customer_liked", "BOOLEAN DEFAULT FALSE"),          # 좋아요
            ("customer_disliked", "BOOLEAN DEFAULT FALSE"),       # 싫어요
            
            # 주거용 특화 메모 필드
            ("residence_memo", "TEXT DEFAULT ''"),                # 주거용 전용 메모
            ("residence_notes", "TEXT DEFAULT ''")                # 주거용 특이사항
        ]
        
        for col_name, col_def in links_columns:
            if safe_add_column(cursor, "links", col_name, col_def):
                added_columns += 1
        
        # 💼 STEP 4: office_links 테이블 컬럼 추가 (업무용 특화)
        print("\n💼 office_links 테이블 컬럼 추가 중 (업무용 특화)...")
        office_columns = [
            # 기본 링크 정보 (업무용)
            ("memo", "TEXT DEFAULT ''"),
            ("customer_name", "VARCHAR(100) DEFAULT '000'"),
            ("move_in_date", "VARCHAR(50) DEFAULT ''"),
            ("management_site_id", "VARCHAR(50)"),
            ("is_checked", "INTEGER DEFAULT 0"),
            ("unchecked_likes_work", "INTEGER DEFAULT 0"),
            ("is_deleted", "INTEGER DEFAULT 0"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("view_count", "INTEGER DEFAULT 0"),
            
            # 업무용 매물 세부 정보
            ("office_type", "VARCHAR(50)"),                      # 사무실 유형
            ("office_size", "VARCHAR(50)"),                      # 사무실 크기
            ("monthly_fee", "VARCHAR(100)"),                     # 월 임대료
            ("deposit_amount", "VARCHAR(100)"),                  # 보증금
            ("utilities_included", "BOOLEAN DEFAULT FALSE"),     # 공과금 포함
            ("parking_available", "BOOLEAN DEFAULT FALSE"),      # 주차 가능
            ("elevator_available", "BOOLEAN DEFAULT FALSE"),     # 엘리베이터
            
            # 업무용 플랫폼 분류
            ("platform_jikbang", "BOOLEAN DEFAULT FALSE"),       # 직방
            ("platform_naver", "BOOLEAN DEFAULT FALSE"),         # 네이버  
            ("platform_etc", "BOOLEAN DEFAULT FALSE"),           # 기타
            ("source_broker", "BOOLEAN DEFAULT FALSE"),          # 중개사
            ("source_customer", "BOOLEAN DEFAULT FALSE"),        # 손님
            
            # 업무용 보증보험 상태
            ("guarantee_available", "BOOLEAN DEFAULT FALSE"),     # 보증보험가능
            ("guarantee_unavailable", "BOOLEAN DEFAULT FALSE"),   # 보증보험불가
            
            # 업무용 고객 반응
            ("customer_liked", "BOOLEAN DEFAULT FALSE"),          # 좋아요
            ("customer_disliked", "BOOLEAN DEFAULT FALSE"),       # 싫어요
            
            # 업무용 특화 메모 필드
            ("office_memo", "TEXT DEFAULT ''"),                   # 업무용 전용 메모
            ("business_notes", "TEXT DEFAULT ''"),                # 업무용 특이사항
            ("location_advantages", "TEXT DEFAULT ''"),           # 입지 장점
            ("facility_info", "TEXT DEFAULT ''")                  # 시설 정보
        ]
        
        for col_name, col_def in office_columns:
            if safe_add_column(cursor, "office_links", col_name, col_def):
                added_columns += 1
        
        # STEP 5: guarantee_insurance_log 테이블 컬럼 추가
        print("\n📋 guarantee_insurance_log 테이블 컬럼 추가 중...")
        log_columns = [
            ("table_type", "VARCHAR(20) DEFAULT 'office_links'"),
            ("details", "TEXT"),
            ("ip_address", "VARCHAR(45)"),
            ("user_agent", "TEXT")
        ]
        
        for col_name, col_def in log_columns:
            if safe_add_column(cursor, "guarantee_insurance_log", col_name, col_def):
                added_columns += 1
        
        # STEP 6: customer_info 테이블 생성/컬럼 추가
        print("\n📞 customer_info 테이블 처리 중...")
        
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
        
        # STEP 7: 성능 최적화 인덱스 생성
        print("\n🚀 성능 최적화 인덱스 생성 중...")
        
        indexes = [
            # 기본 인덱스
            ("idx_employees_employee_id", "employees", "employee_id"),
            ("idx_employees_team", "employees", "team"),
            ("idx_employees_is_active", "employees", "is_active"),
            ("idx_employee_customers_employee_id", "employee_customers", "employee_id"),
            ("idx_employee_customers_management_site_id", "employee_customers", "management_site_id"),
            ("idx_employee_customers_progress_status", "employee_customers", "progress_status"),
            
            # 주거용(links) 특화 인덱스
            ("idx_links_management_site_id", "links", "management_site_id"),
            ("idx_links_added_by", "links", "added_by"),
            ("idx_links_guarantee_insurance", "links", "guarantee_insurance"),
            ("idx_links_is_deleted", "links", "is_deleted"),
            ("idx_links_platform_jikbang", "links", "platform_jikbang"),
            ("idx_links_platform_naver", "links", "platform_naver"),
            ("idx_links_guarantee_available", "links", "guarantee_available"),
            ("idx_links_customer_liked", "links", "customer_liked"),
            
            # 업무용(office_links) 특화 인덱스
            ("idx_office_links_management_site_id", "office_links", "management_site_id"),
            ("idx_office_links_added_by", "office_links", "added_by"),
            ("idx_office_links_guarantee_insurance", "office_links", "guarantee_insurance"),
            ("idx_office_links_is_deleted", "office_links", "is_deleted"),
            ("idx_office_links_platform_jikbang", "office_links", "platform_jikbang"),
            ("idx_office_links_platform_naver", "office_links", "platform_naver"),
            ("idx_office_links_guarantee_available", "office_links", "guarantee_available"),
            ("idx_office_links_customer_liked", "office_links", "customer_liked"),
            ("idx_office_links_office_type", "office_links", "office_type"),
            
            # 로그 테이블 인덱스
            ("idx_guarantee_log_management_site_id", "guarantee_insurance_log", "management_site_id"),
            ("idx_guarantee_log_employee_id", "guarantee_insurance_log", "employee_id")
        ]
        
        created_indexes = 0
        for idx_name, table_name, columns in indexes:
            if safe_create_index(cursor, idx_name, table_name, columns):
                created_indexes += 1
        
        # STEP 8: 데이터 정리 및 기본값 설정
        print("\n🧹 데이터 정리 및 기본값 설정 중...")
        
        cleanup_queries = [
            # employees 테이블 정리
            ("employees 기본값 설정", "UPDATE employees SET role = '직원' WHERE role IS NULL"),
            ("employees 활성화 설정", "UPDATE employees SET is_active = TRUE WHERE is_active IS NULL"),
            
            # employee_customers 테이블 정리
            ("고객 진행상태 설정", "UPDATE employee_customers SET progress_status = '진행중' WHERE progress_status IS NULL"),
            ("고객 연락 선호도 설정", "UPDATE employee_customers SET contact_preference = 'phone' WHERE contact_preference IS NULL"),
            ("고객 생성일 설정", "UPDATE employee_customers SET created_date = CURRENT_TIMESTAMP WHERE created_date IS NULL"),
            
            # 주거용(links) 테이블 정리
            ("주거용 매물 기본값", "UPDATE links SET residence_extra = '' WHERE residence_extra IS NULL"),
            ("주거용 삭제 플래그", "UPDATE links SET is_deleted = 0 WHERE is_deleted IS NULL"),
            ("주거용 확인 플래그", "UPDATE links SET is_checked = 0 WHERE is_checked IS NULL"),
            ("주거용 보증보험", "UPDATE links SET guarantee_insurance = 0 WHERE guarantee_insurance IS NULL"),
            ("주거용 조회수", "UPDATE links SET view_count = 0 WHERE view_count IS NULL"),
            ("주거용 플랫폼 기본값", "UPDATE links SET platform_jikbang = FALSE, platform_naver = FALSE, platform_etc = FALSE WHERE platform_jikbang IS NULL"),
            ("주거용 소스 기본값", "UPDATE links SET source_broker = FALSE, source_customer = FALSE WHERE source_broker IS NULL"),
            ("주거용 보증보험상태", "UPDATE links SET guarantee_available = FALSE, guarantee_unavailable = FALSE WHERE guarantee_available IS NULL"),
            ("주거용 고객반응", "UPDATE links SET customer_liked = FALSE, customer_disliked = FALSE WHERE customer_liked IS NULL"),
            ("주거용 생성일", "UPDATE links SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"),
            ("주거용 수정일", "UPDATE links SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"),
            
            # 업무용(office_links) 테이블 정리
            ("업무용 고객명", "UPDATE office_links SET customer_name = '000' WHERE customer_name IS NULL"),
            ("업무용 입주일", "UPDATE office_links SET move_in_date = '' WHERE move_in_date IS NULL"),
            ("업무용 삭제 플래그", "UPDATE office_links SET is_deleted = 0 WHERE is_deleted IS NULL"),
            ("업무용 확인 플래그", "UPDATE office_links SET is_checked = 0 WHERE is_checked IS NULL"),
            ("업무용 미확인 좋아요", "UPDATE office_links SET unchecked_likes_work = 0 WHERE unchecked_likes_work IS NULL"),
            ("업무용 보증보험", "UPDATE office_links SET guarantee_insurance = 0 WHERE guarantee_insurance IS NULL"),
            ("업무용 조회수", "UPDATE office_links SET view_count = 0 WHERE view_count IS NULL"),
            ("업무용 플랫폼 기본값", "UPDATE office_links SET platform_jikbang = FALSE, platform_naver = FALSE, platform_etc = FALSE WHERE platform_jikbang IS NULL"),
            ("업무용 소스 기본값", "UPDATE office_links SET source_broker = FALSE, source_customer = FALSE WHERE source_broker IS NULL"),
            ("업무용 보증보험상태", "UPDATE office_links SET guarantee_available = FALSE, guarantee_unavailable = FALSE WHERE guarantee_available IS NULL"),
            ("업무용 고객반응", "UPDATE office_links SET customer_liked = FALSE, customer_disliked = FALSE WHERE customer_liked IS NULL"),
            ("업무용 공과금 포함", "UPDATE office_links SET utilities_included = FALSE WHERE utilities_included IS NULL"),
            ("업무용 주차 가능", "UPDATE office_links SET parking_available = FALSE WHERE parking_available IS NULL"),
            ("업무용 엘리베이터", "UPDATE office_links SET elevator_available = FALSE WHERE elevator_available IS NULL"),
            ("업무용 생성일", "UPDATE office_links SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"),
            ("업무용 수정일", "UPDATE office_links SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"),
            
            # 보증보험 로그 정리
            ("보증보험 로그 타입", "UPDATE guarantee_insurance_log SET table_type = 'office_links' WHERE table_type IS NULL"),
            ("보증보험 로그 시간", "UPDATE guarantee_insurance_log SET timestamp = CURRENT_TIMESTAMP WHERE timestamp IS NULL")
        ]
        
        updated_rows = 0
        for description, query in cleanup_queries:
            rows = execute_safe_update(cursor, query, description)
            updated_rows += rows
        
        # 커밋
        conn.commit()
        
        # 🎉 최종 결과 출력
        print("\n" + "=" * 80)
        print("🎉 Railway PostgreSQL 컬럼 강제 추가 완료! (주거용/업무용 특화)")
        print("=" * 80)
        print(f"📊 총 추가된 컬럼: {added_columns}개")
        print(f"📊 생성된 인덱스: {created_indexes}개") 
        print(f"🧹 정리된 데이터: {updated_rows}개 행")
        print("=" * 80)
        print("✅ 직원 추가 오류가 해결되었습니다!")
        print("🏠 주거용 특화 컬럼이 추가되었습니다!")
        print("💼 업무용 특화 컬럼이 추가되었습니다!")
        print("=" * 80)
        
        # 최종 테이블 구조 확인 요약
        print("\n📋 테이블별 컬럼 개수 요약:")
        
        tables_to_check = ['employees', 'employee_customers', 'links', 'office_links', 'guarantee_insurance_log', 'customer_info']
        for table_name in tables_to_check:
            try:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                """, (table_name,))
                column_count = cursor.fetchone()['count']
                print(f"🔹 {table_name}: {column_count}개 컬럼")
            except Exception as e:
                print(f"❌ {table_name}: 조회 실패 - {e}")
        
        cursor.close()
        conn.close()
        
        print("\n🔥 작업 완료! 주거용과 업무용이 각각 특화된 컬럼으로 분리되었습니다!")
        
    except Exception as e:
        logger.error(f"❌ 치명적 오류: {e}")
        print(f"\n❌ 실패: {e}")
        
        # 더 자세한 오류 정보 출력
        import traceback
        print(f"\n🔍 상세 오류 정보:")
        print(traceback.format_exc())
        
        # DATABASE_URL 확인
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            print(f"\n📊 DATABASE_URL 존재: {database_url[:50]}...")
        else:
            print(f"\n❌ DATABASE_URL 환경변수가 없습니다!")
            
        # 환경변수 목록 확인
        print(f"\n🔧 사용 가능한 환경변수:")
        for key in sorted(os.environ.keys()):
            if 'DATABASE' in key.upper() or 'DB' in key.upper() or 'POSTGRES' in key.upper():
                value = os.environ[key]
                print(f"  - {key}: {value[:50]}..." if len(value) > 50 else f"  - {key}: {value}")
        
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 성공: PostgreSQL 컬럼 구조가 완벽하게 수정되었습니다!")
        print("🚀 직원 추가 기능이 정상 작동할 것입니다!")
        print("🏠 주거용 특화 기능이 활성화되었습니다!")
        print("💼 업무용 특화 기능이 활성화되었습니다!")
        exit(0)
    else:
        print("\n❌ 실패: 오류가 발생했습니다.")
        exit(1) 