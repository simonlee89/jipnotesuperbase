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
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # PostgreSQL 연결
        try:
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            logger.info("PostgreSQL 연결 성공")
            return conn, 'postgresql'
        except Exception as e:
            logger.error(f"PostgreSQL 연결 실패: {e}")
            raise
    else:
        # SQLite 연결 (로컬 개발용)
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
    """
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if db_type == 'postgresql':
            # PostgreSQL용 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    department VARCHAR(100),
                    position VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employee_customers (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER REFERENCES employees(id),
                    management_site_id VARCHAR(50) UNIQUE NOT NULL,
                    customer_name VARCHAR(200) NOT NULL,
                    customer_type VARCHAR(50) DEFAULT 'general',
                    site_url VARCHAR(500),
                    residence_extra TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # SQLite용 테이블 생성 (기존 코드)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    department TEXT,
                    position TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employee_customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER,
                    management_site_id TEXT UNIQUE NOT NULL,
                    customer_name TEXT NOT NULL,
                    customer_type TEXT DEFAULT 'general',
                    site_url TEXT,
                    residence_extra TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees (id)
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
        
        return True
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

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
    query = '''
        SELECT ec.*, e.name as employee_name, e.email as employee_email
        FROM employee_customers ec
        LEFT JOIN employees e ON ec.employee_id = e.id
        WHERE ec.management_site_id = %s
    '''
    
    conn, db_type = get_db_connection()
    if db_type == 'sqlite':
        query = query.replace('%s', '?')
    
    try:
        result = execute_query(query, (management_site_id,), fetch=True)
        return result[0] if result else None
    except Exception as e:
        logger.error(f"고객 정보 조회 실패: {e}")
        return None 