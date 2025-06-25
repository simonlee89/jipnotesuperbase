import os
import sqlite3
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
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
    """
    데이터베이스 테이블을 초기화합니다.
    PostgreSQL과 SQLite 모두 완벽하게 지원하는 구조로 생성합니다.
    """
    try:
        logger.info("=== 데이터베이스 초기화 시작 ===")
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        logger.info(f"DB 타입: {db_type}")
        
        if db_type == 'postgresql':
            # PostgreSQL용 테이블 생성 - 완벽한 구조
            logger.info("PostgreSQL 테이블 생성 중...")
            
            # 1. employees 테이블 - 직원 정보
            cursor.execute('''
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
                )
            ''')
            logger.info("✅ employees 테이블 생성")
            
            # 2. employee_customers 테이블 - 고객 정보 (완벽한 구조)
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
                    created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    budget_min VARCHAR(100),
                    budget_max VARCHAR(100),
                    preferred_area TEXT,
                    special_requirements TEXT,
                    contact_preference VARCHAR(50) DEFAULT 'phone'
                )
            ''')
            logger.info("✅ employee_customers 테이블 생성")
            
            # 3. links 테이블 - 주거용 매물 링크 (완벽한 구조)
            cursor.execute('''
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
                )
            ''')
            logger.info("✅ links 테이블 생성")
            
            # 4. office_links 테이블 - 업무용 매물 링크 (완벽한 구조)
            cursor.execute('''
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
                )
            ''')
            logger.info("✅ office_links 테이블 생성")
            
            # 5. guarantee_insurance_log 테이블 - 보증보험 로그 (완벽한 구조)
            cursor.execute('''
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
                )
            ''')
            logger.info("✅ guarantee_insurance_log 테이블 생성")
            
            # 6. customer_info 테이블 - 기본 고객 정보 (완벽한 구조)
            cursor.execute('''
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
            ''')
            logger.info("✅ customer_info 테이블 생성")
            
            # 기본 고객 정보 삽입
            cursor.execute('''
                INSERT INTO customer_info (id, customer_name, move_in_date) 
                VALUES (1, '제일좋은집 찾아드릴분', '') 
                ON CONFLICT (id) DO NOTHING
            ''')
            
            # 인덱스 생성 (신 구조에 맞게)
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_employees_name ON employees(name);",
                "CREATE INDEX IF NOT EXISTS idx_employees_role ON employees(role);",
                "CREATE INDEX IF NOT EXISTS idx_employee_customers_employee_id ON employee_customers(employee_id);",
                "CREATE INDEX IF NOT EXISTS idx_employee_customers_management_site_id ON employee_customers(management_site_id);",
                "CREATE INDEX IF NOT EXISTS idx_links_management_site_id ON links(management_site_id);",
                "CREATE INDEX IF NOT EXISTS idx_links_added_by ON links(added_by);",
                "CREATE INDEX IF NOT EXISTS idx_links_guarantee_insurance ON links(guarantee_insurance);",
                "CREATE INDEX IF NOT EXISTS idx_office_links_management_site_id ON office_links(management_site_id);",
                "CREATE INDEX IF NOT EXISTS idx_office_links_added_by ON office_links(added_by);",
                "CREATE INDEX IF NOT EXISTS idx_office_links_guarantee_insurance ON office_links(guarantee_insurance);"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            logger.info("✅ PostgreSQL 인덱스 생성 완료")
            
        else:
            # SQLite용 테이블 생성 - 호환 가능한 구조
            logger.info("SQLite 테이블 생성 중...")
            
            # 1. employees 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT UNIQUE NOT NULL,
                    employee_name TEXT NOT NULL,
                    team TEXT NOT NULL,
                    password TEXT NOT NULL DEFAULT '1234',
                    created_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    last_login TEXT,
                    phone TEXT,
                    email TEXT,
                    role TEXT DEFAULT '직원'
                )
            ''')
            logger.info("✅ employees 테이블 생성")
            
            # 2. employee_customers 테이블
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
                    created_date TEXT NOT NULL,
                    last_updated TEXT,
                    budget_min TEXT,
                    budget_max TEXT,
                    preferred_area TEXT,
                    special_requirements TEXT,
                    contact_preference TEXT DEFAULT 'phone'
                )
            ''')
            logger.info("✅ employee_customers 테이블 생성")
            
            # 3. links 테이블
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
                    residence_extra TEXT DEFAULT '',
                    created_at TEXT,
                    updated_at TEXT,
                    view_count INTEGER DEFAULT 0,
                    price TEXT,
                    area TEXT,
                    room_type TEXT,
                    floor_info TEXT,
                    deposit TEXT,
                    monthly_rent TEXT
                )
            ''')
            logger.info("✅ links 테이블 생성")
            
            # 4. office_links 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS office_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    added_by TEXT NOT NULL,
                    date_added TEXT NOT NULL,
                    rating INTEGER DEFAULT 5,
                    liked INTEGER DEFAULT 0,
                    disliked INTEGER DEFAULT 0,
                    memo TEXT DEFAULT '',
                    customer_name TEXT DEFAULT '000',
                    move_in_date TEXT DEFAULT '',
                    management_site_id TEXT DEFAULT NULL,
                    guarantee_insurance INTEGER DEFAULT 0,
                    is_checked INTEGER DEFAULT 0,
                    unchecked_likes_work INTEGER DEFAULT 0,
                    is_deleted INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    view_count INTEGER DEFAULT 0,
                    office_type TEXT,
                    office_size TEXT,
                    monthly_fee TEXT,
                    deposit_amount TEXT,
                    utilities_included INTEGER DEFAULT 0,
                    parking_available INTEGER DEFAULT 0,
                    elevator_available INTEGER DEFAULT 0
                )
            ''')
            logger.info("✅ office_links 테이블 생성")
            
            # 5. guarantee_insurance_log 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS guarantee_insurance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    link_id INTEGER,
                    management_site_id TEXT,
                    employee_id TEXT,
                    action TEXT,
                    timestamp TEXT,
                    table_type TEXT DEFAULT 'office_links',
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')
            logger.info("✅ guarantee_insurance_log 테이블 생성")
            
            # 6. customer_info 테이블
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_info (
                    id INTEGER PRIMARY KEY,
                    customer_name TEXT DEFAULT '제일좋은집 찾아드릴분',
                    move_in_date TEXT DEFAULT '',
                    phone TEXT,
                    email TEXT,
                    preferred_contact TEXT DEFAULT 'phone',
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            logger.info("✅ customer_info 테이블 생성")
            
            # 기본 고객 정보 삽입
            cursor.execute('INSERT OR IGNORE INTO customer_info (id, customer_name, move_in_date) VALUES (1, "제일좋은집 찾아드릴분", "")')
        
        conn.commit()
        logger.info(f"✅ {db_type} 데이터베이스 테이블 초기화 완료")
        
        # 테이블 목록 확인
        if db_type == 'postgresql':
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"생성된 테이블: {tables}")
        
        cursor.close()
        conn.close()
        logger.info("=== 데이터베이스 초기화 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        return False

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
    """
    관리 사이트 ID로 고객 정보를 조회합니다.
    """
    try:
        logger.info(f"고객 정보 조회 시작: {management_site_id}")
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'postgresql':
            query = '''
                SELECT ec.*, e.employee_name, e.team
                FROM employee_customers ec
                LEFT JOIN employees e ON ec.employee_id = e.employee_id
                WHERE ec.management_site_id = %s
            '''
        else:
            query = '''
                SELECT ec.*, e.employee_name, e.team
                FROM employee_customers ec
                LEFT JOIN employees e ON ec.employee_id = e.employee_id
                WHERE ec.management_site_id = ?
            '''
        
        cursor.execute(query, (management_site_id,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            logger.info(f"✅ 고객 정보 조회 성공: {result['customer_name'] if 'customer_name' in result else 'N/A'}")
            return dict(result)
        else:
            logger.warning(f"❌ 고객 정보 없음: {management_site_id}")
            return None
        
    except Exception as e:
        logger.error(f"❌ 고객 정보 조회 실패: {e}")
        return None 