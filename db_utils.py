import os
import sqlite3
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# PostgreSQL 모듈은 선택적으로 import (배포 환경에서만)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
    logger.info("psycopg2 모듈 사용 가능")
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 모듈을 찾을 수 없음 - SQLite만 사용")

def get_db_connection():
    """
    환경변수에 따라 PostgreSQL 또는 SQLite 연결을 반환합니다.
    Railway 환경에서는 PostgreSQL만 사용하고, 로컬에서는 SQLite 사용합니다.
    """
    database_url = os.environ.get('DATABASE_URL')
    
    # PostgreSQL 연결 시도 (Railway 환경)
    if database_url and PSYCOPG2_AVAILABLE:
        try:
            logger.info("PostgreSQL 연결 시도 (Railway 환경)")
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
            # Railway 환경에서 PostgreSQL 실패 시 예외 발생 (폴백 없음)
            raise Exception(f"PostgreSQL 연결 실패: {e}")
    
    # 로컬 개발 환경 - SQLite 사용
    logger.info("SQLite 연결 시도 (로컬 환경)")
    
    # 여러 경로에서 DB 파일 찾기
    db_paths = [
        '/data/integrated.db',  # Railway persistent volume (사용 안함)
        'integrated.db',        # 현재 디렉토리
        './integrated.db',      # 명시적 현재 디렉토리
    ]
    
    for db_path in db_paths:
        try:
            if os.path.exists(db_path):
                logger.info(f"DB 파일 발견: {db_path}")
                conn = sqlite3.connect(db_path, timeout=30)
                conn.row_factory = sqlite3.Row
                
                # 연결 테스트
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                
                logger.info(f"✅ SQLite 연결 성공: {db_path}")
                return conn, 'sqlite'
        except Exception as e:
            logger.error(f"SQLite 연결 실패 ({db_path}): {e}")
            continue
    
    # 모든 경로에서 실패하면 새 DB 생성 (로컬 환경용)
    try:
        db_path = 'integrated.db'  # 로컬에서만 새 DB 생성
        logger.info(f"새 SQLite DB 생성: {db_path}")
        
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        
        # 연결 테스트
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        
        logger.info(f"✅ 새 SQLite DB 생성 성공: {db_path}")
        return conn, 'sqlite'
        
    except Exception as e:
        logger.error(f"❌ SQLite DB 생성 실패: {e}")
        raise Exception(f"모든 DB 연결 시도 실패: {e}")

def init_database():
    """DB 연결을 가져오고, 모든 테이블이 존재하는지 확인 및 생성"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    logger.info(f"DB 타입: {db_type}")

    if db_type == 'postgresql':
        logger.info("PostgreSQL 테이블 생성 (필요시)...")
        try:
            create_all_tables_postgres(cursor) # IF NOT EXISTS로 생성
            logger.info("✅ PostgreSQL 테이블 생성 확인 완료.")
        except Exception as e:
            logger.error(f"PostgreSQL 테이블 생성 실패: {e}")
            conn.rollback()
    else: # SQLite
        logger.info("SQLite 테이블 생성 (필요시)...")
        try:
            create_all_tables_sqlite(cursor)
            logger.info("✅ SQLite 테이블 생성 확인 완료.")
        except Exception as e:
            logger.error(f"SQLite 테이블 생성 실패: {e}")
            conn.rollback()
        
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
            department VARCHAR(100) NOT NULL DEFAULT '',
            position VARCHAR(100) NOT NULL DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            last_login TIMESTAMP,
            role VARCHAR(50) NOT NULL DEFAULT 'employee'
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
            is_checked BOOLEAN DEFAULT FALSE,
            residence_extra TEXT
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
    # 6. customer_info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_info (
            id SERIAL PRIMARY KEY,
            customer_name VARCHAR(200) DEFAULT '제일좋은집 찾아드릴분',
            move_in_date VARCHAR(50) DEFAULT '',
            phone VARCHAR(50),
            email VARCHAR(200),
            preferred_contact VARCHAR(20) DEFAULT 'phone',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

def create_all_tables_sqlite(cursor):
    """SQLite용 모든 테이블 생성 쿼리 실행"""
    # 1. employees
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL DEFAULT '',
            department TEXT NOT NULL DEFAULT '',
            position TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            last_login TEXT,
            role TEXT NOT NULL DEFAULT 'employee'
        )
    ''')
    # 2. employee_customers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee_customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            management_site_id TEXT UNIQUE NOT NULL,
            customer_name TEXT,
            phone TEXT,
            inquiry_date TEXT,
            move_in_date TEXT,
            amount TEXT,
            room_count TEXT,
            location TEXT,
            loan_info TEXT,
            parking TEXT,
            pets TEXT,
            progress_status TEXT DEFAULT '진행중',
            memo TEXT,
            created_date TEXT NOT NULL
        )
    ''')
    # 3. links
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            platform TEXT,
            added_by TEXT,
            date_added TEXT,
            rating INTEGER DEFAULT 0,
            liked INTEGER DEFAULT 0,
            disliked INTEGER DEFAULT 0,
            memo TEXT,
            management_site_id TEXT,
            guarantee_insurance INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            is_checked INTEGER DEFAULT 0,
            residence_extra TEXT
        )
    ''')
    # 4. office_links
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS office_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            platform TEXT,
            added_by TEXT,
            date_added TEXT,
            rating INTEGER DEFAULT 0,
            liked INTEGER DEFAULT 0,
            disliked INTEGER DEFAULT 0,
            memo TEXT,
            management_site_id TEXT,
            guarantee_insurance INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            unchecked_likes_work INTEGER DEFAULT 0
        )
    ''')
    # 5. guarantee_insurance_log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guarantee_insurance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INTEGER,
            management_site_id TEXT,
            employee_id TEXT,
            action TEXT,
            timestamp TEXT
        )
    ''')
    # 6. customer_info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT DEFAULT '제일좋은집 찾아드릴분',
            move_in_date TEXT DEFAULT '',
            phone TEXT,
            email TEXT,
            preferred_contact TEXT DEFAULT 'phone',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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
                'id': ('SERIAL PRIMARY KEY' if db_type == 'postgresql' else 'INTEGER PRIMARY KEY AUTOINCREMENT'),
                'name': ('VARCHAR(200) UNIQUE NOT NULL' if db_type == 'postgresql' else 'TEXT UNIQUE NOT NULL'),
                'email': ('VARCHAR(200) NOT NULL DEFAULT \'\'' if db_type == 'postgresql' else 'TEXT NOT NULL DEFAULT \'\''),
                'department': ('VARCHAR(100) NOT NULL DEFAULT \'\'' if db_type == 'postgresql' else 'TEXT NOT NULL DEFAULT \'\''),
                'position': ('VARCHAR(100) NOT NULL DEFAULT \'\'' if db_type == 'postgresql' else 'TEXT NOT NULL DEFAULT \'\''),
                'created_at': ('TIMESTAMP NOT NULL DEFAULT NOW()' if db_type == 'postgresql' else 'TEXT NOT NULL'),
                'last_login': ('TIMESTAMP' if db_type == 'postgresql' else 'TEXT'),
                'role': ('VARCHAR(50) NOT NULL DEFAULT \'employee\'' if db_type == 'postgresql' else 'TEXT NOT NULL DEFAULT \'employee\'')
            },
            'links': {
                'residence_extra': ('TEXT DEFAULT \'\'' if db_type == 'postgresql' else 'TEXT DEFAULT \'\'')
            },
            'office_links': {
                'is_deleted': 'INTEGER DEFAULT 0',
                'unchecked_likes_work': 'INTEGER DEFAULT 0'
            }
        }
        
        for table_name, columns_to_check in table_definitions.items():
            if db_type == 'postgresql':
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s
                """, (table_name,))
                existing_columns = [row[0] for row in cursor.fetchall()]
            else: # sqlite
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_columns = [row[1] for row in cursor.fetchall()]

            for col_name, col_type in columns_to_check.items():
                if col_name not in existing_columns:
                    logger.info(f"'{table_name}' 테이블에 '{col_name}' 컬럼 추가 중...")
                    if db_type == 'postgresql':
                        cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN "{col_name}" {col_type}')
                    else: # sqlite
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
    공통 쿼리 실행 함수
    """
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            if db_type == 'postgresql':
                result = [dict(row) for row in cursor.fetchall()]
            else:
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

        if db_type == 'postgresql':
            query = "SELECT * FROM employee_customers WHERE management_site_id = %s"
        else: # sqlite
            query = "SELECT * FROM employee_customers WHERE management_site_id = ?"
        
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