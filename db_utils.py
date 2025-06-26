import os
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# PostgreSQL 모듈 import
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
    logger.info("psycopg2 모듈 사용 가능")
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.error("psycopg2 모듈을 찾을 수 없음 - PostgreSQL 연결 불가")
    raise Exception("PostgreSQL 연결을 위해 psycopg2 모듈이 필요합니다")

def get_db_connection():
    """
    PostgreSQL 연결을 반환합니다.
    Railway 환경에서는 DATABASE_URL 환경변수를 사용합니다.
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise Exception("DATABASE_URL 환경변수가 설정되지 않았습니다")
    
    if not PSYCOPG2_AVAILABLE:
        raise Exception("psycopg2 모듈이 설치되지 않았습니다")
    
    try:
        logger.info("PostgreSQL 연결 시도")
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        
        # 연결 테스트
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        
        logger.info("✅ PostgreSQL 연결 성공")
        return conn, 'postgresql'
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL 연결 실패: {e}")
        raise Exception(f"PostgreSQL 연결 실패: {e}")

def dict_from_row(row):
    """데이터베이스 row 객체를 Python 딕셔너리로 변환합니다."""
    if row:
        return dict(row)
    return None

def init_database():
    """DB 연결을 가져오고, 모든 테이블이 존재하는지 확인 및 생성"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    logger.info(f"DB 타입: {db_type}")

    logger.info("PostgreSQL 테이블 생성 (필요시)...")
    try:
        create_all_tables_postgres(cursor) # IF NOT EXISTS로 생성
        logger.info("✅ PostgreSQL 테이블 생성 확인 완료.")
    except Exception as e:
        logger.error(f"PostgreSQL 테이블 생성 실패: {e}")
        conn.rollback()
        raise
        
    logger.info("=== 데이터베이스 초기화/확인 완료 ===")
    conn.commit()
    conn.close()

def create_all_tables_postgres(cursor):
    """PostgreSQL용 모든 테이블 생성 쿼리 실행 (IF NOT EXISTS 사용)"""
    # 1. employees
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) UNIQUE NOT NULL,
            email VARCHAR(200) NOT NULL DEFAULT '',
            team VARCHAR(100) NOT NULL DEFAULT '',
            position VARCHAR(100) NOT NULL DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            last_login TIMESTAMP,
            role VARCHAR(50) NOT NULL DEFAULT 'employee',
            status VARCHAR(20) NOT NULL DEFAULT 'active'
        )
    ''')
    # 2. employee_customers
    cursor.execute('''
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
            created_date TIMESTAMP NOT NULL
        )
    ''')
    # 3. links
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL,
            platform VARCHAR(50),
            added_by VARCHAR(100),
            date_added TIMESTAMP,
            rating INTEGER DEFAULT 0,
            liked BOOLEAN DEFAULT FALSE,
            disliked BOOLEAN DEFAULT FALSE,
            memo TEXT,
            management_site_id VARCHAR(50),
            guarantee_insurance BOOLEAN DEFAULT FALSE,
            is_deleted BOOLEAN DEFAULT FALSE,
            is_checked BOOLEAN DEFAULT FALSE
        )
    ''')
    # 4. office_links
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS office_links (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL,
            platform VARCHAR(50),
            added_by VARCHAR(100),
            date_added TIMESTAMP,
            rating INTEGER DEFAULT 0,
            liked BOOLEAN DEFAULT FALSE,
            disliked BOOLEAN DEFAULT FALSE,
            memo TEXT,
            management_site_id VARCHAR(50),
            guarantee_insurance BOOLEAN DEFAULT FALSE,
            is_deleted BOOLEAN DEFAULT FALSE,
            unchecked_likes_work INTEGER DEFAULT 0
        )
    ''')
    # 5. guarantee_insurance_log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guarantee_insurance_log (
            id SERIAL PRIMARY KEY,
            link_id INTEGER,
            management_site_id VARCHAR(50),
            employee_id VARCHAR(50),
            action VARCHAR(100),
            timestamp TIMESTAMP
        )
    ''')



def ensure_all_columns():
    """
    모든 테이블에 대해 누락된 컬럼이 있는지 확인하고 추가합니다.
    (기존에 있던 ensure_X_column 함수들을 통합하고 개선)
    """
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        table_definitions = {
            'employees': {
                'id': 'SERIAL PRIMARY KEY',
                'name': 'VARCHAR(200) UNIQUE NOT NULL',
                'email': 'VARCHAR(200) NOT NULL DEFAULT \'\'',
                'team': 'VARCHAR(100) NOT NULL DEFAULT \'\'',
                'position': 'VARCHAR(100) NOT NULL DEFAULT \'\'',
                'created_at': 'TIMESTAMP NOT NULL DEFAULT NOW()',
                'last_login': 'TIMESTAMP',
                'role': 'VARCHAR(50) NOT NULL DEFAULT \'employee\'',
                'status': 'VARCHAR(20) NOT NULL DEFAULT \'active\''
            },

            'office_links': {
                'is_deleted': 'BOOLEAN DEFAULT FALSE',
                'unchecked_likes_work': 'INTEGER DEFAULT 0'
            }
        }
        
        for table_name, columns_to_check in table_definitions.items():
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,))
            existing_columns = [row[0] for row in cursor.fetchall()]

            for col_name, col_type in columns_to_check.items():
                if col_name not in existing_columns:
                    logger.info(f"'{table_name}' 테이블에 '{col_name}' 컬럼 추가 중...")
                    cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN "{col_name}" {col_type}')
                    logger.info(f"✅ '{col_name}' 컬럼 추가 완료")

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("=== 컬럼 구조 확인 및 수정 완료 ===")
        
    except Exception as e:
        # 테이블이 아직 존재하지 않는 경우 등 오류는 무시하고 계속 진행
        logger.warning(f"컬럼 구조 확인 중 오류 발생 (무시 가능): {e}")

def execute_query(query, params=None, fetch=False):
    """
    공통 쿼리 실행 함수 (PostgreSQL 전용)
    """
    try:
        conn, _ = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            result = [dict(row) for row in cursor.fetchall()]
            return result
        else:
            conn.commit()
            return cursor.rowcount
            
    except Exception as e:
        logger.error(f"쿼리 실행 실패: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def get_customer_info(management_site_id):
    """management_site_id로 고객 정보를 조회하고, 상세한 디버깅 로그를 남깁니다."""
    print(f"🕵️  [get_customer_info] 고객 정보 조회 시도: management_site_id='{management_site_id}'")
    if not management_site_id:
        print("❌ [get_customer_info] management_site_id가 제공되지 않았습니다.")
        return None

    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        print(f"ℹ️  [get_customer_info] DB 타입: {db_type}")

        query = "SELECT * FROM employee_customers WHERE management_site_id = %s"
        
        print(f"执行 [get_customer_info] 쿼리: {query} (파라미터: {management_site_id})")
        cursor.execute(query, (management_site_id,))
        customer = cursor.fetchone()
        
        conn.close()

        if customer:
            print(f"✅ [get_customer_info] 고객 정보 조회 성공: {dict(customer)}")
            return dict(customer)
        else:
            print(f"🤷 [get_customer_info] 해당 ID의 고객을 찾을 수 없습니다: '{management_site_id}'")
            return None
    except Exception as e:
        print(f"🚨 [get_customer_info] DB 조회 중 심각한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None 