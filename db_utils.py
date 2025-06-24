import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    환경변수에 따라 PostgreSQL 또는 SQLite 연결을 반환합니다.
    PostgreSQL 연결 실패 시 SQLite로 폴백합니다.
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # PostgreSQL 연결 시도
        try:
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            logger.info("PostgreSQL 연결 성공")
            return conn, 'postgresql'
        except Exception as e:
            logger.error(f"PostgreSQL 연결 실패: {e}")
            logger.info("SQLite로 폴백합니다.")
            # PostgreSQL 실패 시 SQLite로 폴백
    
    # SQLite 연결 (로컬 개발용 또는 PostgreSQL 실패 시 폴백)
    db_paths = ['/data/integrated.db', 'integrated.db', './integrated.db']
    for db_path in db_paths:
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            logger.info(f"SQLite 연결 성공: {db_path}")
            return conn, 'sqlite'
    
    # 기본 SQLite 파일 생성
    conn = sqlite3.connect('integrated.db')
    conn.row_factory = sqlite3.Row
    logger.info("새 SQLite DB 생성: integrated.db")
    return conn, 'sqlite'

def init_database():
    """
    데이터베이스 테이블을 초기화합니다.
    관리자페이지와 동일한 구조로 생성합니다.
    """
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'postgresql':
            # PostgreSQL용 테이블 생성 (관리자페이지 구조와 동일)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    employee_id VARCHAR(100) UNIQUE NOT NULL,
                    employee_name VARCHAR(100) NOT NULL,
                    team VARCHAR(100) NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    created_date TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
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
            
            # 추가 테이블들
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS links (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    platform VARCHAR(50),
                    added_by VARCHAR(100),
                    date_added VARCHAR(50),
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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS office_links (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    platform VARCHAR(50) NOT NULL,
                    added_by VARCHAR(100) NOT NULL,
                    date_added VARCHAR(50) NOT NULL,
                    rating INTEGER DEFAULT 5,
                    liked BOOLEAN DEFAULT FALSE,
                    disliked BOOLEAN DEFAULT FALSE,
                    memo TEXT DEFAULT '',
                    customer_name VARCHAR(100) DEFAULT '000',
                    move_in_date VARCHAR(50) DEFAULT '',
                    management_site_id VARCHAR(50) DEFAULT NULL,
                    guarantee_insurance BOOLEAN DEFAULT FALSE,
                    is_checked BOOLEAN DEFAULT FALSE,
                    unchecked_likes_work INTEGER DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT FALSE
                )
            ''')
            
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
            
        else:
            # SQLite용 테이블 생성 (관리자페이지 구조와 동일)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT UNIQUE NOT NULL,
                    employee_name TEXT NOT NULL,
                    team TEXT NOT NULL,
                    password TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
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
                    FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
                )
            ''')
            
            # 추가 테이블들
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
                    is_checked INTEGER DEFAULT 0
                )
            ''')
            
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
                    is_deleted INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS guarantee_insurance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    link_id INTEGER,
                    management_site_id TEXT,
                    employee_id TEXT,
                    action TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (link_id) REFERENCES office_links (id)
                )
            ''')
        
        conn.commit()
        logger.info(f"{db_type} 데이터베이스 테이블 초기화 완료")
        
        # 테이블 목록 확인
        if db_type == 'postgresql':
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"생성된 테이블: {tables}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        return False

def execute_query(query, params=None, fetch=False):
    """
    공통 쿼리 실행 함수
    """
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    try:
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
            return dict(result)
        return None
        
    except Exception as e:
        logger.error(f"고객 정보 조회 실패: {e}")
        return None 