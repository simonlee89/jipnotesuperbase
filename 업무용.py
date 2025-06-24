from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
import os
import json

# PostgreSQL 관련 모듈은 배포 환경에서만 import
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

# 데이터베이스 초기화
def init_db():
    print("=== 업무용 DB 초기화 시작 ===")
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        print(f"업무용 DB 연결 성공 - 타입: {db_type}")
        
        # 기존 테이블에 보증보험 칼럼이 없으면 추가
        try:
            if db_type == 'postgresql':
                cursor.execute("ALTER TABLE office_links ADD COLUMN IF NOT EXISTS guarantee_insurance BOOLEAN DEFAULT FALSE")
                cursor.execute("ALTER TABLE office_links ADD COLUMN IF NOT EXISTS is_checked BOOLEAN DEFAULT FALSE")
            else:
                cursor.execute("PRAGMA table_info(office_links)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'guarantee_insurance' not in columns:
                    cursor.execute("ALTER TABLE office_links ADD COLUMN guarantee_insurance BOOLEAN DEFAULT 0")
                if 'is_checked' not in columns:
                    cursor.execute("ALTER TABLE office_links ADD COLUMN is_checked INTEGER DEFAULT 0")
            conn.commit()
        except Exception as e:
            print(f"칼럼 추가 중 오류 (무시 가능): {e}")
            conn.rollback()
        
        if db_type == 'postgresql':
            # PostgreSQL용 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS office_links (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    added_by TEXT NOT NULL,
                    date_added TEXT NOT NULL,
                    rating INTEGER DEFAULT 5,
                    liked BOOLEAN DEFAULT FALSE,
                    disliked BOOLEAN DEFAULT FALSE,
                    memo TEXT DEFAULT '',
                    customer_name TEXT DEFAULT '000',
                    move_in_date TEXT DEFAULT '',
                    management_site_id TEXT DEFAULT NULL,
                    guarantee_insurance BOOLEAN DEFAULT FALSE,
                    is_checked BOOLEAN DEFAULT FALSE
                )
            ''')
            print("PostgreSQL office_links 테이블 생성 완료")
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_info (
                    id INTEGER PRIMARY KEY,
                    customer_name TEXT DEFAULT '000',
                    move_in_date TEXT DEFAULT ''
                )
            ''')
            print("PostgreSQL customer_info 테이블 생성 완료")
            
            # 기본 고객 정보 삽입 (ON CONFLICT로 중복 방지)
            cursor.execute('''
                INSERT INTO customer_info (id, customer_name, move_in_date) 
                VALUES (1, '프리미엄등록', '') 
                ON CONFLICT (id) DO NOTHING
            ''')
        else:
            # SQLite용 테이블 생성 (기존 코드)
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
                    is_checked INTEGER DEFAULT 0
                )
            ''')
            print("SQLite office_links 테이블 생성 완료")
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_info (
                    id INTEGER PRIMARY KEY,
                    customer_name TEXT DEFAULT '000',
                    move_in_date TEXT DEFAULT ''
                )
            ''')
            print("SQLite customer_info 테이블 생성 완료")
            
            cursor.execute('INSERT OR IGNORE INTO customer_info (id, customer_name, move_in_date) VALUES (1, "프리미엄등록", "")')
        
        conn.commit()
        conn.close()
        print("=== 업무용 DB 초기화 완료 ===")
        
    except Exception as e:
        print(f"=== 업무용 DB 초기화 실패: {e} ===")
        raise

# 데이터베이스 연결 함수
def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if database_url and PSYCOPG2_AVAILABLE:
        # PostgreSQL 연결
        conn = psycopg2.connect(database_url)
        return conn, 'postgresql'
    else:
        # SQLite 연결 (업무용 전용)
        conn = sqlite3.connect('/data/integrated.db')
        return conn, 'sqlite'

app = Flask(__name__)

# Railway에서 gunicorn 실행 시에도 DB 초기화가 되도록 앱 생성 직후 호출
init_db()

# 고객 정보 조회 함수 (새로 추가)
def get_customer_info(management_site_id):
    """management_site_id로 고객 정보를 조회하는 함수"""
    print(f"[DEBUG] get_customer_info 호출됨 - management_site_id: {management_site_id}")
    customer_name = None
    move_in_date = ''
    
    # 여러 경로에서 DB 파일 찾기
    db_paths = ['/data/integrated.db', 'integrated.db', './integrated.db']
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"[DEBUG] DB 파일 찾음: {db_path}")
            try:
                system_conn = sqlite3.connect(db_path)
                system_cursor = system_conn.cursor()
                
                # 먼저 테이블 존재 확인
                system_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employee_customers'")
                if not system_cursor.fetchone():
                    print(f"[DEBUG] employee_customers 테이블이 없음: {db_path}")
                    system_conn.close()
                    continue
                
                system_cursor.execute('''
                    SELECT customer_name, move_in_date 
                    FROM employee_customers 
                    WHERE management_site_id = ?
                ''', (management_site_id,))
                customer_data = system_cursor.fetchone()
                print(f"[DEBUG] {db_path} 조회 결과: {customer_data}")
                system_conn.close()
                
                if customer_data:
                    customer_name = customer_data[0] if customer_data[0] else '고객'
                    move_in_date = customer_data[1] if customer_data[1] else ''
                    print(f"[DEBUG] 고객 정보 찾음 - 이름: {customer_name}, 입주일: {move_in_date}")
                    return customer_name, move_in_date, True
                    
            except sqlite3.Error as e:
                print(f"[DEBUG] {db_path} 조회 실패: {e}")
                continue
        else:
            print(f"[DEBUG] DB 파일 없음: {db_path}")

    print(f"[DEBUG] 고객 정보를 찾을 수 없음: {management_site_id}")
    return None, '', False

@app.route('/')
def index():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    # 고객 정보 가져오기
    cursor.execute('SELECT customer_name, move_in_date FROM customer_info WHERE id = 1')
    customer_info = cursor.fetchone()
    
    if db_type == 'postgresql':
        customer_name = customer_info[0] if customer_info else '프리미엄등록'
        move_in_date = customer_info[1] if customer_info else ''
    else:
        customer_name = customer_info[0] if customer_info else '프리미엄등록'
        move_in_date = customer_info[1] if customer_info else ''
    
    conn.close()
    
    return render_template('업무용_index.html', customer_name=customer_name, move_in_date=move_in_date)

@app.route('/customer/<management_site_id>')
def customer_site(management_site_id):
    """고객별 매물 사이트 페이지"""
    print(f"[ROUTE] 고객 사이트 접근 - management_site_id: {management_site_id}")
    print(f"[ROUTE] 현재 작업 디렉토리: {os.getcwd()}")
    print(f"[ROUTE] /data 디렉토리 존재: {os.path.exists('/data')}")
    
    # 디렉토리 내용 확인
    try:
        if os.path.exists('/data'):
            files = os.listdir('/data')
            print(f"[ROUTE] /data 디렉토리 파일들: {files}")
        else:
            print(f"[ROUTE] /data 디렉토리가 존재하지 않음")
    except Exception as e:
        print(f"[ROUTE] /data 디렉토리 읽기 오류: {e}")
    
    # 고객 정보 조회
    customer_name, move_in_date, found = get_customer_info(management_site_id)
    
    if not found:
        print(f"[ROUTE] 고객 정보를 찾을 수 없음: {management_site_id}")
        
        # DB 상태 상세 확인
        debug_db_info = ""
        try:
            import sqlite3
            conn = sqlite3.connect('/data/integrated.db')
            cursor = conn.cursor()
            
            # 테이블 목록 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            debug_db_info += f"<strong>DB 테이블 목록:</strong><br>"
            debug_db_info += "<br>".join([f"- {t[0]}" for t in tables]) + "<br><br>"
            
            # employee_customers 테이블 스키마 확인
            try:
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='employee_customers';")
                schema = cursor.fetchone()
                if schema:
                    debug_db_info += f"<strong>employee_customers 테이블 스키마:</strong><br><code>{schema[0]}</code><br><br>"
                else:
                    debug_db_info += "<strong>❌ employee_customers 테이블이 존재하지 않습니다!</strong><br><br>"
            except Exception as e:
                debug_db_info += f"스키마 조회 오류: {e}<br><br>"
            
            # 고객 목록 조회
            try:
                cursor.execute('SELECT management_site_id, customer_name FROM employee_customers LIMIT 10')
                all_customers = cursor.fetchall()
                debug_db_info += f"<strong>고객 목록:</strong><br>"
                if all_customers:
                    debug_db_info += "<br>".join([f"ID: {c[0]}, 이름: {c[1]}" for c in all_customers])
                else:
                    debug_db_info += "고객 데이터가 없습니다."
            except Exception as e:
                debug_db_info += f"고객 조회 오류: {e}"
            
            conn.close()
        except Exception as e:
            debug_db_info = f"DB 연결 오류: {e}"
        
        # 404 대신 디버깅 정보를 포함한 에러 페이지 반환
        return f"""
        <html><head><title>디버깅 정보</title></head><body>
        <h1>🔍 디버깅 정보</h1>
        <p><strong>찾는 Management Site ID:</strong> {management_site_id}</p>
        <p><strong>현재 디렉토리:</strong> {os.getcwd()}</p>
        <p><strong>/data 존재:</strong> {os.path.exists('/data')}</p>
        <p><strong>파일 목록:</strong> {os.listdir('/data') if os.path.exists('/data') else 'N/A'}</p>
        <hr>
        <h2>📊 DB 상태 정보</h2>
        <div>{debug_db_info}</div>
        <hr>
        <p style="color:red; font-size:18px;"><strong>❌ 결론:</strong> 고객 정보를 찾을 수 없습니다.</p>
        <hr>
        <p><strong>🔧 해결 방법:</strong></p>
        <ol>
        <li><a href="/force-init-db" target="_blank">DB 강제 초기화</a> 실행</li>
        <li>관리자페이지에서 고객 다시 등록</li>
        </ol>
        </body></html>
        """, 404
    else:
        print(f"[ROUTE] 고객 정보 조회 성공 - 이름: {customer_name}, 입주일: {move_in_date}")
    
    # 미확인 좋아요 is_checked=0 → 1로 일괄 갱신
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    if db_type == 'postgresql':
        cursor.execute('UPDATE office_links SET is_checked = TRUE, unchecked_likes_work = 0 WHERE management_site_id = %s AND liked = TRUE AND is_checked = FALSE', (management_site_id,))
    else:
        cursor.execute('UPDATE office_links SET is_checked = 1, unchecked_likes_work = 0 WHERE management_site_id = ? AND liked = 1 AND is_checked = 0', (management_site_id,))
    conn.commit()
    conn.close()
    
    print(f"[ROUTE] 템플릿 렌더링 시작")
    return render_template('업무용_index.html', 
                         customer_name=customer_name, 
                         move_in_date=move_in_date,
                         management_site_id=management_site_id)

@app.route('/api/customer_info', methods=['GET', 'POST'])
def customer_info():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    # URL에서 management_site_id 파라미터 확인
    management_site_id = request.args.get('management_site_id')
    
    # 고객별 사이트인 경우 고객 존재 여부 확인
    if management_site_id:
        _, _, found = get_customer_info(management_site_id)
        if not found:
            conn.close()
            return jsonify({'success': False, 'error': '고객 정보를 찾을 수 없습니다. 삭제되었거나 존재하지 않는 고객입니다.'}), 404
    
    if request.method == 'POST':
        data = request.json
        customer_name = data.get('customer_name', '프리미엄등록')
        move_in_date = data.get('move_in_date', '')
        
        if db_type == 'postgresql':
            cursor.execute('UPDATE customer_info SET customer_name = %s, move_in_date = %s WHERE id = 1', 
                          (customer_name, move_in_date))
        else:
            cursor.execute('UPDATE customer_info SET customer_name = ?, move_in_date = ? WHERE id = 1', 
                          (customer_name, move_in_date))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    
    else:
        cursor.execute('SELECT customer_name, move_in_date FROM customer_info WHERE id = 1')
        info = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'customer_name': info[0] if info else '프리미엄등록',
            'move_in_date': info[1] if info else ''
        })

@app.route('/api/links', methods=['GET', 'POST'])
def links():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    # URL에서 management_site_id 파라미터 확인
    management_site_id = request.args.get('management_site_id')
    
    if request.method == 'POST':
        data = request.json
        url = data.get('url')
        platform = data.get('platform')
        added_by = data.get('added_by', '관리자')  # 기본값 설정
        memo = data.get('memo', '')
        guarantee_insurance = data.get('guarantee_insurance', False)
        
        print(f"[DEBUG] POST /api/links - management_site_id from URL: {management_site_id}")
        print(f"[DEBUG] POST 데이터: url={url}, platform={platform}, added_by={added_by}")
        
        if not url or not platform:
            return jsonify({'success': False, 'error': '필수 정보가 누락되었습니다.'})
        
        date_added = datetime.now().strftime('%Y-%m-%d')
        
        # management_site_id가 있는 경우 고객 존재 여부 확인
        if management_site_id:
            _, _, found = get_customer_info(management_site_id)
            if not found:
                return jsonify({'success': False, 'error': '존재하지 않는 고객입니다.'})
        
        if db_type == 'postgresql':
            cursor.execute('''
                INSERT INTO office_links (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance))
            link_id = cursor.fetchone()[0]
        else:
            cursor.execute('''
                INSERT INTO office_links (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance))
            link_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        print(f"새 링크 추가됨 - ID: {link_id}, 고객: {management_site_id or '기본'}")
        return jsonify({'success': True, 'id': link_id})
    
    else:
        # 필터 파라미터
        platform_filter = request.args.get('platform', 'all')
        user_filter = request.args.get('user', 'all')
        like_filter = request.args.get('like', 'all')
        date_filter = request.args.get('date', '')
        guarantee_filter = request.args.get('guarantee', 'all')
        
        query = 'SELECT * FROM office_links WHERE 1=1'
        params = []
        
        # 고객별 필터링 추가
        if management_site_id:
            print(f"고객별 링크 조회 - management_site_id: {management_site_id}")
            if db_type == 'postgresql':
                query += ' AND management_site_id = %s'
            else:
                query += ' AND management_site_id = ?'
            params.append(management_site_id)
        else:
            # management_site_id가 없으면 기본 링크들만 표시 (NULL 값)
            query += ' AND management_site_id IS NULL'
        
        if platform_filter != 'all':
            if db_type == 'postgresql':
                query += ' AND platform = %s'
            else:
                query += ' AND platform = ?'
            params.append(platform_filter)
        
        if user_filter != 'all':
            if db_type == 'postgresql':
                query += ' AND added_by = %s'
            else:
                query += ' AND added_by = ?'
            params.append(user_filter)
        
        if like_filter == 'liked':
            if db_type == 'postgresql':
                query += ' AND liked = TRUE'
            else:
                query += ' AND liked = 1'
        elif like_filter == 'disliked':
            if db_type == 'postgresql':
                query += ' AND disliked = TRUE'
            else:
                query += ' AND disliked = 1'
        elif like_filter == 'none':
            if db_type == 'postgresql':
                query += ' AND liked = FALSE AND disliked = FALSE'
            else:
                query += ' AND liked = 0 AND disliked = 0'
        
        if date_filter:
            if db_type == 'postgresql':
                query += ' AND date_added = %s'
            else:
                query += ' AND date_added = ?'
            params.append(date_filter)
        
        if guarantee_filter == 'available':
            if db_type == 'postgresql':
                query += ' AND guarantee_insurance = TRUE'
            else:
                query += ' AND guarantee_insurance = 1'
        elif guarantee_filter == 'unavailable':
            if db_type == 'postgresql':
                query += ' AND guarantee_insurance = FALSE'
            else:
                query += ' AND guarantee_insurance = 0'
        
        query += ' ORDER BY id DESC'  # 최신순으로 정렬 (최신이 맨 위)
        
        cursor.execute(query, params)
        links_data = cursor.fetchall()
        
        # 전체 링크 개수 구하기 (번호 계산용)
        total_count = len(links_data)
        
        conn.close()
        
        links_list = []
        for index, link in enumerate(links_data):  # 추가 순서대로 번호 매기기
            # 최신순으로 정렬되어 있으므로, 번호는 역순으로 계산
            link_number = total_count - index
            links_list.append({
                'id': link[0],
                'number': link_number,  # 추가 순서대로 번호 (첫 번째=1, 두 번째=2...)
                'url': link[1],
                'platform': link[2],
                'added_by': link[3],
                'date_added': link[4],
                'rating': link[5],
                'liked': bool(link[6]),
                'disliked': bool(link[7]),
                'memo': link[8] if len(link) > 8 else '',
                'guarantee_insurance': bool(link[12]) if len(link) > 12 else False
            })
        
        print(f"링크 조회 완료 - 총 {len(links_list)}개, 고객: {management_site_id or '기본'}")
        return jsonify(links_list)

@app.route('/api/links/<int:link_id>', methods=['PUT', 'DELETE'])
def update_link(link_id):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    # 링크의 management_site_id 확인
    if db_type == 'postgresql':
        cursor.execute('SELECT management_site_id FROM office_links WHERE id = %s', (link_id,))
    else:
        cursor.execute('SELECT management_site_id FROM office_links WHERE id = ?', (link_id,))
    
    link_result = cursor.fetchone()
    if link_result and link_result[0]:  # management_site_id가 있는 경우
        management_site_id = link_result[0]
        _, _, found = get_customer_info(management_site_id)
        if not found:
            conn.close()
            return jsonify({'success': False, 'error': '삭제된 고객의 링크입니다. 작업을 수행할 수 없습니다.'}), 404
    
    if request.method == 'PUT':
        data = request.json
        action = data.get('action')
        
        if action == 'rating':
            rating = data.get('rating', 5)
            if db_type == 'postgresql':
                cursor.execute('UPDATE office_links SET rating = %s WHERE id = %s', (rating, link_id))
            else:
                cursor.execute('UPDATE office_links SET rating = ? WHERE id = ?', (rating, link_id))
        
        elif action == 'like':
            liked = data.get('liked', False)
            if db_type == 'postgresql':
                if liked:
                    cursor.execute('UPDATE office_links SET liked = TRUE, disliked = FALSE, is_checked = FALSE, unchecked_likes_work = unchecked_likes_work + 1 WHERE id = %s', (link_id,))
                else:
                    cursor.execute('UPDATE office_links SET liked = FALSE, is_checked = FALSE WHERE id = %s', (link_id,))
            else:
                if liked:
                    cursor.execute('UPDATE office_links SET liked = 1, disliked = 0, is_checked = 0, unchecked_likes_work = unchecked_likes_work + 1 WHERE id = ?', (link_id,))
                else:
                    cursor.execute('UPDATE office_links SET liked = 0, is_checked = 0 WHERE id = ?', (link_id,))
        
        elif action == 'dislike':
            disliked = data.get('disliked', False)
            if db_type == 'postgresql':
                cursor.execute('UPDATE office_links SET disliked = %s, liked = %s WHERE id = %s', 
                              (disliked, False, link_id))
            else:
                cursor.execute('UPDATE office_links SET disliked = ?, liked = ? WHERE id = ?', 
                              (disliked, False if disliked else 0, link_id))
        
        elif action == 'memo':
            memo = data.get('memo', '')
            if db_type == 'postgresql':
                cursor.execute('UPDATE office_links SET memo = %s WHERE id = %s', (memo, link_id))
            else:
                cursor.execute('UPDATE office_links SET memo = ? WHERE id = ?', (memo, link_id))
        
        elif action == 'guarantee':
            guarantee_insurance = data.get('guarantee_insurance', False)
            if db_type == 'postgresql':
                cursor.execute('UPDATE office_links SET guarantee_insurance = %s WHERE id = %s', (guarantee_insurance, link_id))
            else:
                cursor.execute('UPDATE office_links SET guarantee_insurance = ? WHERE id = ?', (guarantee_insurance, link_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        if db_type == 'postgresql':
            cursor.execute('DELETE FROM office_links WHERE id = %s', (link_id,))
        else:
            cursor.execute('DELETE FROM office_links WHERE id = ?', (link_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})

@app.route('/api/backup', methods=['GET'])
def backup_data():
    """데이터베이스 내용을 JSON으로 백업"""
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'links': [],
            'customer_info': None
        }
        
        # 링크 데이터 백업
        cursor.execute('SELECT * FROM office_links')
        links = cursor.fetchall()
        
        # 컬럼 이름 가져오기
        if db_type == 'postgresql':
            columns = ['id', 'url', 'platform', 'added_by', 'date_added', 'rating', 'liked', 'disliked', 'memo', 'customer_name', 'move_in_date']
        else:
            cursor.execute("PRAGMA table_info(office_links)")
            columns = [row[1] for row in cursor.fetchall()]
        
        for link in links:
            link_dict = dict(zip(columns, link))
            backup_data['links'].append(link_dict)
        
        # 고객 정보 백업
        cursor.execute('SELECT * FROM customer_info')
        customer = cursor.fetchone()
        if customer:
            if db_type == 'postgresql':
                customer_columns = ['id', 'customer_name', 'move_in_date']
            else:
                cursor.execute("PRAGMA table_info(customer_info)")
                customer_columns = [row[1] for row in cursor.fetchall()]
            backup_data['customer_info'] = dict(zip(customer_columns, customer))
        
        conn.close()
        
        return jsonify(backup_data)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/restore', methods=['POST'])
def restore_data():
    """JSON 백업 데이터로 데이터베이스 복원"""
    try:
        backup_data = request.json
        
        if not backup_data or 'links' not in backup_data:
            return jsonify({'success': False, 'error': '잘못된 백업 데이터입니다.'})
        
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        # 기존 데이터 삭제
        cursor.execute('DELETE FROM office_links')
        cursor.execute('DELETE FROM customer_info')
        
        # 고객 정보 복원
        if backup_data.get('customer_info'):
            customer_info = backup_data['customer_info']
            if db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO customer_info (id, customer_name, move_in_date)
                    VALUES (%s, %s, %s)
                ''', (
                    customer_info.get('id', 1),
                    customer_info.get('customer_name', '제일좋은집 찾아드릴분'),
                    customer_info.get('move_in_date', '')
                ))
            else:
                cursor.execute('''
                    INSERT INTO customer_info (id, customer_name, move_in_date)
                    VALUES (?, ?, ?)
                ''', (
                    customer_info.get('id', 1),
                    customer_info.get('customer_name', '제일좋은집 찾아드릴분'),
                    customer_info.get('move_in_date', '')
                ))
        else:
            # 기본 고객 정보 삽입
            if db_type == 'postgresql':
                cursor.execute('INSERT INTO customer_info (id, customer_name, move_in_date) VALUES (1, %s, %s)', ('제일좋은집 찾아드릴분', ''))
            else:
                cursor.execute('INSERT INTO customer_info (id, customer_name, move_in_date) VALUES (1, "제일좋은집 찾아드릴분", "")')
        
        # 링크 데이터 복원
        for link_data in backup_data['links']:
            if db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO office_links (url, platform, added_by, date_added, rating, liked, disliked, memo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    link_data.get('url', ''),
                    link_data.get('platform', 'other'),
                    link_data.get('added_by', 'unknown'),
                    link_data.get('date_added', datetime.now().strftime('%Y-%m-%d')),
                    link_data.get('rating', 5),
                    link_data.get('liked', False),
                    link_data.get('disliked', False),
                    link_data.get('memo', '')
                ))
            else:
                cursor.execute('''
                    INSERT INTO office_links (url, platform, added_by, date_added, rating, liked, disliked, memo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    link_data.get('url', ''),
                    link_data.get('platform', 'other'),
                    link_data.get('added_by', 'unknown'),
                    link_data.get('date_added', datetime.now().strftime('%Y-%m-%d')),
                    link_data.get('rating', 5),
                    link_data.get('liked', 0),
                    link_data.get('disliked', 0),
                    link_data.get('memo', '')
                ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'{len(backup_data["links"])}개의 링크가 복원되었습니다.'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/cleanup-customer-links/<management_site_id>', methods=['DELETE'])
def cleanup_customer_links(management_site_id):
    """관리자페이지에서 호출하는 고객 링크 정리 API"""
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'postgresql':
            cursor.execute('DELETE FROM office_links WHERE management_site_id = %s', (management_site_id,))
        else:
            cursor.execute('DELETE FROM office_links WHERE management_site_id = ?', (management_site_id,))
            
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"관리자페이지 요청으로 management_site_id {management_site_id} 관련 링크 {deleted_count}개 삭제됨")
        return jsonify({'success': True, 'deleted_count': deleted_count})
    except Exception as e:
        print(f"링크 정리 실패: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/guarantee-insurance-reset', methods=['POST'])
def guarantee_insurance_reset():
    data = request.get_json()
    employee_id = data.get('employee_id')
    if not employee_id:
        return jsonify({'success': False, 'message': 'employee_id 누락'}), 400
    try:
        conn = sqlite3.connect('/data/integrated.db')
        c = conn.cursor()
        c.execute("UPDATE links SET guarantee_insurance = 0 WHERE added_by = ?", (employee_id,))
        affected = c.rowcount
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'affected': affected})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port) 