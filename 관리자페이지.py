from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import uuid
from datetime import datetime
import os
import requests
import time

# 환경변수에서 사이트 URL 가져오기 (Railway 배포용)
RESIDENCE_SITE_URL = os.environ.get('RESIDENCE_SITE_URL', 'http://localhost:5000')
BUSINESS_SITE_URL = os.environ.get('BUSINESS_SITE_URL', 'http://localhost:5001')

def init_admin_db():
    """관리자 데이터베이스 초기화"""
    print("=== DB 초기화 시작 ===")
    try:
        conn = sqlite3.connect('/data/integrated.db')
        cursor = conn.cursor()
        print("DB 연결 성공: /data/integrated.db")
        
        # 직원 테이블 생성 (팀 컬럼 추가)
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
        print("employees 테이블 생성 완료")
        
        # 기존 테이블에 team 컬럼이 없다면 추가
        try:
            cursor.execute('ALTER TABLE employees ADD COLUMN team TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            # 컬럼이 이미 존재하면 무시
            pass
        
        # 직원별 고객 관리 테이블 생성
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
        print("employee_customers 테이블 생성 완료")
        
        # 기존 테이블에 누락된 컬럼 추가
        try:
            cursor.execute('ALTER TABLE employee_customers ADD COLUMN loan_info TEXT')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE employee_customers ADD COLUMN parking TEXT')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE employee_customers ADD COLUMN pets TEXT')
        except sqlite3.OperationalError:
            pass
        
        # 주거용 매물 링크 테이블 생성 (links)
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
        print("links 테이블 생성 완료")
        
        # 업무용 매물 링크 테이블 생성 (office_links)
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
        print("office_links 테이블 생성 완료")
        
        # 보증보험 로그 테이블 생성
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
        print("guarantee_insurance_log 테이블 생성 완료")
        
        # links 테이블에 누락된 컬럼들 추가
        try:
            cursor.execute('ALTER TABLE links ADD COLUMN guarantee_insurance INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE links ADD COLUMN is_deleted INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE links ADD COLUMN is_checked INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        # office_links 테이블에 누락된 컬럼들 추가
        try:
            cursor.execute('ALTER TABLE office_links ADD COLUMN is_deleted INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE office_links ADD COLUMN unchecked_likes_work INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        conn.close()
        print("=== DB 초기화 완료 ===")
        
    except Exception as e:
        print(f"=== DB 초기화 실패: {e} ===")
        raise

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 세션용 비밀키

# Railway에서 gunicorn 실행 시에도 DB 초기화가 되도록 앱 생성 직후 호출
try:
    init_admin_db()
    print("✅ 관리자 DB 초기화 성공")
except Exception as e:
    print(f"❌ 관리자 DB 초기화 실패: {e}")
    # 실패해도 앱은 계속 실행

@app.route('/')
def index():
    """메인 페이지 - 로그인 또는 직원 관리"""
    if 'employee_id' in session:
        return redirect(url_for('employee_dashboard'))
    elif 'is_admin' in session:
        return redirect(url_for('admin_panel'))
    return render_template('admin_main.html')

@app.route('/login', methods=['POST'])
def login():
    """직원 로그인"""
    data = request.get_json()
    employee_id = data.get('employee_id')
    password = data.get('password')
    
    conn = sqlite3.connect('/data/integrated.db')
    cursor = conn.cursor()
    cursor.execute('SELECT employee_name FROM employees WHERE employee_id = ? AND password = ? AND is_active = 1', 
                   (employee_id, password))
    employee = cursor.fetchone()
    conn.close()
    
    if employee:
        session['employee_id'] = employee_id
        session['employee_name'] = employee[0]
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '아이디 또는 비밀번호가 잘못되었습니다.'})

@app.route('/admin-login', methods=['POST'])
def admin_login():
    """관리자 로그인"""
    data = request.get_json()
    admin_id = data.get('admin_id')
    admin_password = data.get('admin_password')
    
    # 관리자 계정 하드코딩 (실제 환경에서는 환경변수나 DB에서 관리)
    ADMIN_ID = 'admin'
    ADMIN_PASSWORD = 'ejxkqdnjs1emd'
    
    if admin_id == ADMIN_ID and admin_password == ADMIN_PASSWORD:
        session['is_admin'] = True
        session['admin_id'] = admin_id
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '관리자 아이디 또는 비밀번호가 잘못되었습니다.'})

@app.route('/logout')
def logout():
    """로그아웃"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def employee_dashboard():
    """직원 대시보드"""
    # 관리자도 직원 대시보드 접근 가능
    if 'employee_id' not in session and 'is_admin' not in session:
        return redirect(url_for('index'))
    
    # 관리자인 경우 관리자 이름으로 표시
    if 'is_admin' in session:
        employee_name = '관리자'
    else:
        employee_name = session.get('employee_name', '직원')
    
    return render_template('employee_dashboard.html', 
                         employee_name=employee_name,
                         residence_site_url=RESIDENCE_SITE_URL,
                         business_site_url=BUSINESS_SITE_URL)

@app.route('/admin')
def admin_panel():
    """관리자 패널 (직원 관리)"""
    # 관리자 권한 확인
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    # DB에서 보증보험 매물 리스트 조회 (links 테이블 기준)
    conn = sqlite3.connect('/data/integrated.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT l.id, l.url, l.platform, l.added_by, l.date_added, l.memo
        FROM links l
        WHERE l.guarantee_insurance = 1 AND (l.is_deleted = 0 OR l.is_deleted IS NULL)
        ORDER BY l.id DESC
    ''')
    guarantee_list = cursor.fetchall()
    conn.close()

    return render_template('admin_panel.html', 
                         guarantee_list=guarantee_list,
                         residence_site_url=RESIDENCE_SITE_URL,
                         business_site_url=BUSINESS_SITE_URL)

@app.route('/admin/guarantee-delete/<int:id>', methods=['POST'])
def guarantee_delete(id):
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    conn = sqlite3.connect('/data/integrated.db')
    cursor = conn.cursor()
    # guarantee_insurance 값을 0으로 변경 (삭제 대신)
    cursor.execute('UPDATE links SET guarantee_insurance = 0 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/guarantee-edit/<int:id>', methods=['POST'])
def guarantee_edit(id):
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    memo = request.form.get('memo', '')
    conn = sqlite3.connect('/data/integrated.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE office_links SET memo = ? WHERE id = ?', (memo, id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

# 직원 관리 API
@app.route('/api/employees', methods=['GET', 'POST'])
def manage_employees():
    if request.method == 'GET':
        # 직원 목록 조회 (팀 정보 포함)
        conn = sqlite3.connect('/data/integrated.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, employee_id, employee_name, team, created_date, is_active 
            FROM employees 
            ORDER BY created_date DESC
        ''')
        employees = cursor.fetchall()
        conn.close()
        
        employee_list = []
        for emp in employees:
            employee_list.append({
                'id': emp[0],
                'employee_id': emp[1],
                'employee_name': emp[2],
                'team': emp[3] if emp[3] else '',
                'created_date': emp[4],
                'is_active': emp[5]
            })
        
        return jsonify(employee_list)
    
    elif request.method == 'POST':
        # 새 직원 추가 (팀 정보 포함)
        data = request.get_json()
        employee_id = data.get('employee_id')
        employee_name = data.get('employee_name')
        team = data.get('team', '')
        password = data.get('password', '1234')  # 기본 비밀번호
        
        if not employee_id or not employee_name:
            return jsonify({'success': False, 'message': '직원아이디와 이름을 입력해주세요.'})
        
        if not team:
            return jsonify({'success': False, 'message': '팀을 입력해주세요.'})
        
        try:
            conn = sqlite3.connect('/data/integrated.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO employees (employee_id, employee_name, team, password, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (employee_id, employee_name, team, password, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'message': '이미 존재하는 직원 아이디입니다.'})

@app.route('/api/employees/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    """직원 삭제 (비활성화)"""
    conn = sqlite3.connect('/data/integrated.db')
    cursor = conn.cursor()
    # 직원 id로 employee_id 조회
    cursor.execute('SELECT employee_id FROM employees WHERE id = ?', (emp_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'})
    employee_id_value = result[0]
    # 1. 해당 직원이 등록한 보증보험 guarantee_insurance=1 → 0으로 변경
    cursor.execute('UPDATE office_links SET guarantee_insurance = 0 WHERE added_by = ? AND guarantee_insurance = 1', (employee_id_value,))
    # 2. 직원 비활성화
    cursor.execute('UPDATE employees SET is_active = 0 WHERE id = ?', (emp_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/employees/<int:emp_id>/reset-password', methods=['PUT'])
def reset_employee_password(emp_id):
    """직원 비밀번호 재설정"""
    data = request.get_json()
    new_password = data.get('new_password', '1234')  # 기본 비밀번호
    
    conn = sqlite3.connect('/data/integrated.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE employees SET password = ? WHERE id = ?', (new_password, emp_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'})
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '비밀번호가 재설정되었습니다.'})

def hide_links_by_employee(employee_id, db_path='/data/integrated.db'):
    """해당 직원이 등록한 보증보험 매물을 모두 숨김 처리 (ID/문자열 모두 포함)"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # added_by가 employee_id(숫자) 또는 str(employee_id)(문자열)인 경우 모두 포함
        cursor.execute("""
            UPDATE office_links
            SET is_deleted = 1
            WHERE guarantee_insurance = 1
            AND (added_by = ? OR added_by = ?)
        """, (employee_id, str(employee_id)))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"보증보험 매물 숨기기 실패: {e}")
        return False

@app.route('/api/employees/<int:emp_id>/permanent-delete', methods=['DELETE'])
def permanent_delete_employee(emp_id):
    """직원 완전 삭제 (비활성화된 직원만, 모든 매물 숨김 처리 포함)"""
    conn = sqlite3.connect('/data/integrated.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_active, employee_id FROM employees WHERE id = ?', (emp_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'})
    if result[0] == 1:
        conn.close()
        return jsonify({'success': False, 'message': '활성 상태인 직원은 완전 삭제할 수 없습니다. 먼저 비활성화해주세요.'})
    employee_id_value = result[1]

    # 1. 해당 직원이 등록한 보증보험 링크 id 목록 조회
    cursor.execute('SELECT id FROM office_links WHERE added_by = ?', (employee_id_value,))
    link_ids = [row[0] for row in cursor.fetchall()]

    # 2. guarantee_insurance_log에서 해당 링크 로그 삭제
    for link_id in link_ids:
        cursor.execute('DELETE FROM guarantee_insurance_log WHERE link_id = ?', (link_id,))

    # 3. office_links 테이블에서 해당 직원의 모든 매물 삭제 (guarantee_insurance=0 포함)
    cursor.execute('DELETE FROM office_links WHERE added_by = ?', (employee_id_value,))

    # 기존 고객/직원 삭제
    cursor.execute('DELETE FROM employee_customers WHERE employee_id = ?', (employee_id_value,))
    cursor.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '직원이 완전히 삭제(숨김) 처리되었고, 해당 직원의 모든 매물도 삭제되었습니다.'})

@app.route('/api/employees/<int:emp_id>/activate', methods=['PUT'])
def activate_employee(emp_id):
    """직원 활성화"""
    conn = sqlite3.connect('/data/integrated.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE employees SET is_active = 1 WHERE id = ?', (emp_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'})
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '직원이 활성화되었습니다.'})

# 직원별 고객 관리 API
@app.route('/api/customers', methods=['GET', 'POST'])
def manage_customers():
    # 관리자 또는 직원만 접근 가능
    if 'employee_id' not in session and 'is_admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # 관리자는 모든 고객 조회, 직원은 자신의 고객만 조회
    if 'is_admin' in session:
        employee_id = None  # 관리자는 모든 고객 조회
    else:
        employee_id = session['employee_id']
    
    if request.method == 'GET':
        # 해당 직원의 고객 목록 조회
        conn = sqlite3.connect('/data/integrated.db')
        cursor = conn.cursor()
        
        if employee_id:  # 직원인 경우
            cursor.execute('''
                SELECT id, management_site_id, customer_name, phone, inquiry_date, 
                       move_in_date, amount, room_count, location, loan_info, parking, 
                       pets, progress_status, memo, employee_id
                FROM employee_customers 
                WHERE employee_id = ?
                ORDER BY inquiry_date DESC
            ''', (employee_id,))
        else:  # 관리자인 경우 모든 고객 조회
            cursor.execute('''
                SELECT id, management_site_id, customer_name, phone, inquiry_date, 
                       move_in_date, amount, room_count, location, loan_info, parking, 
                       pets, progress_status, memo, employee_id
                FROM employee_customers 
                ORDER BY inquiry_date DESC
            ''')
        
        customers = cursor.fetchall()
        conn.close()
        
        customer_list = []
        for customer in customers:
            management_site_id = customer[1]
            unchecked_likes_jug = get_unchecked_likes_count(management_site_id, '/data/integrated.db', mode='residence')
            unchecked_likes_work = get_unchecked_likes_count(management_site_id, '/data/integrated.db', mode='work')
            customer_list.append({
                'id': customer[0],
                'management_site_id': customer[1],
                'customer_name': customer[2],
                'phone': customer[3],
                'inquiry_date': customer[4],
                'move_in_date': customer[5],
                'amount': customer[6],
                'room_count': customer[7],
                'location': customer[8],
                'loan_info': customer[9] if len(customer) > 9 else None,
                'parking': customer[10] if len(customer) > 10 else None,
                'pets': customer[11] if len(customer) > 11 else None,
                'progress_status': customer[12] if len(customer) > 12 else customer[9],
                'memo': customer[13] if len(customer) > 13 else customer[10],
                'employee_id': customer[14] if len(customer) > 14 else employee_id,
                'residence_url': f'{RESIDENCE_SITE_URL}/customer/{customer[1]}',
                'business_url': f'{BUSINESS_SITE_URL}/customer/{customer[1]}',
                'unchecked_likes_jug': unchecked_likes_jug,
                'unchecked_likes_work': unchecked_likes_work
            })
        
        return jsonify(customer_list)
    
    elif request.method == 'POST':
        # 새 고객 추가
        data = request.get_json()
        management_site_id = str(uuid.uuid4())[:8]
        
        # 관리자가 추가하는 경우 직원 ID를 지정할 수 있음
        if 'is_admin' in session and data.get('employee_id'):
            add_employee_id = data.get('employee_id')
        elif 'is_admin' in session:
            add_employee_id = 'admin'  # 관리자가 직접 추가
        else:
            add_employee_id = employee_id
        
        try:
            conn = sqlite3.connect('/data/integrated.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO employee_customers (
                    employee_id, management_site_id, customer_name, phone, inquiry_date,
                    move_in_date, amount, room_count, location, loan_info, parking, pets,
                    progress_status, memo, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                add_employee_id, management_site_id, data.get('customer_name'), data.get('phone'),
                data.get('inquiry_date'), data.get('move_in_date'), data.get('amount'),
                data.get('room_count'), data.get('location'), data.get('loan_info'),
                data.get('parking'), data.get('pets'), data.get('progress_status', '진행중'),
                data.get('memo'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'management_site_id': management_site_id})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/customers/<int:customer_id>', methods=['PUT', 'DELETE'])
def update_delete_customer(customer_id):
    if 'employee_id' not in session and 'is_admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    is_admin = 'is_admin' in session
    employee_id = session.get('employee_id')
    
    if request.method == 'PUT':
        # 고객 정보 수정
        data = request.get_json()
        
        conn = sqlite3.connect('/data/integrated.db')
        cursor = conn.cursor()
        
        # 관리자는 모든 고객 수정 가능, 직원은 자신의 고객만
        if is_admin:
            cursor.execute('SELECT id FROM employee_customers WHERE id = ?', (customer_id,))
        else:
            cursor.execute('SELECT id FROM employee_customers WHERE id = ? AND employee_id = ?', 
                          (customer_id, employee_id))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '권한이 없습니다.'})
        
        # 정보 업데이트
        cursor.execute('''
            UPDATE employee_customers SET
                customer_name = ?, phone = ?, inquiry_date = ?, move_in_date = ?,
                amount = ?, room_count = ?, location = ?, progress_status = ?, memo = ?
            WHERE id = ? AND employee_id = ?
        ''', (
            data.get('customer_name'), data.get('phone'), data.get('inquiry_date'),
            data.get('move_in_date'), data.get('amount'), data.get('room_count'),
            data.get('location'), data.get('progress_status'), data.get('memo'),
            customer_id, employee_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        # 고객 삭제
        conn = sqlite3.connect('/data/integrated.db')
        cursor = conn.cursor()
        
        # management_site_id 조회
        cursor.execute('SELECT management_site_id FROM employee_customers WHERE id = ? AND employee_id = ?', 
                      (customer_id, employee_id))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'message': '권한이 없습니다.'})
        
        management_site_id = result[0]
        
        # 고객 삭제
        cursor.execute('DELETE FROM employee_customers WHERE id = ? AND employee_id = ?', 
                      (customer_id, employee_id))
        conn.commit()
        conn.close()
        
        # 매물 사이트에서도 해당 고객의 링크들 삭제
        delete_customer_links_from_property_db(management_site_id)
        
        return jsonify({'success': True})

@app.route('/api/customers/<int:customer_id>/memo', methods=['PUT'])
def update_customer_memo(customer_id):
    """고객 메모만 업데이트"""
    if 'employee_id' not in session and 'is_admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    is_admin = 'is_admin' in session
    employee_id = session.get('employee_id')
    data = request.get_json()
    memo = data.get('memo', '')
    
    conn = sqlite3.connect('/data/integrated.db')
    cursor = conn.cursor()
    
    # 해당 직원의 고객인지 확인하고 메모 업데이트
    cursor.execute('''
        UPDATE employee_customers SET memo = ?
        WHERE id = ? AND employee_id = ?
    ''', (memo, customer_id, employee_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': '권한이 없습니다.'})
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/customers/<int:customer_id>/field', methods=['PUT'])
def update_customer_field(customer_id):
    """고객 개별 필드 업데이트"""
    if 'employee_id' not in session and 'is_admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    is_admin = 'is_admin' in session
    employee_id = session.get('employee_id')
    data = request.get_json()
    
    conn = sqlite3.connect('/data/integrated.db')
    cursor = conn.cursor()
    
    # 관리자는 모든 고객 수정 가능, 직원은 자신의 고객만
    if is_admin:
        cursor.execute('SELECT * FROM employee_customers WHERE id = ?', (customer_id,))
    else:
        cursor.execute('SELECT * FROM employee_customers WHERE id = ? AND employee_id = ?', 
                      (customer_id, employee_id))
    customer = cursor.fetchone()
    
    if not customer:
        conn.close()
        return jsonify({'success': False, 'message': '권한이 없습니다.'})
    
    # 업데이트 가능한 필드 목록
    allowed_fields = ['customer_name', 'phone', 'inquiry_date', 'move_in_date', 
                     'amount', 'room_count', 'location', 'loan_info', 'parking', 
                     'pets', 'progress_status']
    
    # 업데이트할 필드와 값 확인
    update_fields = []
    update_values = []
    
    for field, value in data.items():
        if field in allowed_fields:
            update_fields.append(f"{field} = ?")
            update_values.append(value)
    
    if not update_fields:
        conn.close()
        return jsonify({'success': False, 'message': '업데이트할 필드가 없습니다.'})
    
    # 업데이트 쿼리 실행
    update_values.extend([customer_id, employee_id])
    query = f'''
        UPDATE employee_customers 
        SET {', '.join(update_fields)}
        WHERE id = ? AND employee_id = ?
    '''
    
    cursor.execute(query, update_values)
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

def get_property_db_connection():
    """매물 사이트와 동일한 DB 연결 방식"""
    # PostgreSQL 관련 모듈은 배포 환경에서만 import
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        PSYCOPG2_AVAILABLE = True
    except ImportError:
        PSYCOPG2_AVAILABLE = False
    
    database_url = os.environ.get('DATABASE_URL')
    if database_url and PSYCOPG2_AVAILABLE:
        # PostgreSQL 연결
        conn = psycopg2.connect(database_url)
        return conn, 'postgresql'
    else:
        # SQLite 연결 (로컬 개발용)
        conn = sqlite3.connect('/data/integrated.db')
        return conn, 'sqlite'

def robust_delete_query(db_path, query, params=()):
    """DB 락이 걸리면 최대 5회까지 재시도하며 안전하게 쿼리 실행"""
    for _ in range(5):
        try:
            conn = sqlite3.connect('/data/integrated.db', timeout=5.0)
            conn.execute('PRAGMA busy_timeout = 5000;')
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                time.sleep(0.5)
            else:
                raise
    print("DB 락으로 인해 쿼리 실패:", query)
    return False

def delete_customer_links_from_property_db(management_site_id):
    """매물 사이트 DB(통합 DB)에서 해당 고객의 링크들과 보증보험 로그까지 robust하게 삭제"""
    try:
        # 0. 먼저 guarantee_insurance를 0으로 업데이트
        robust_delete_query('/data/integrated.db', "UPDATE office_links SET guarantee_insurance = 0 WHERE management_site_id = ?", (management_site_id,))
        # 1. office_links, guarantee_insurance_log robust 삭제
        robust_delete_query('/data/integrated.db', "DELETE FROM office_links WHERE management_site_id = ?", (management_site_id,))
        robust_delete_query('/data/integrated.db', "DELETE FROM guarantee_insurance_log WHERE management_site_id = ?", (management_site_id,))
        # office_links에서 삭제된 id로 guarantee_insurance_log도 추가 삭제 (link_id 기준)
        conn = sqlite3.connect('/data/integrated.db', timeout=5.0)
        conn.execute('PRAGMA busy_timeout = 5000;')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM office_links WHERE management_site_id = ?", (management_site_id,))
        link_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        for link_id in link_ids:
            robust_delete_query('/data/integrated.db', "DELETE FROM guarantee_insurance_log WHERE link_id = ?", (link_id,))
        return True
    except Exception as e:
        print('robust delete 실패:', e)
        return False

def get_unchecked_likes_count(management_site_id, db_path, mode='residence'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if mode == 'residence':
        # 주거용: links 테이블만 카운트
        cursor.execute('SELECT COUNT(*) FROM links WHERE management_site_id = ? AND liked = 1 AND is_checked = 0', (management_site_id,))
        count = cursor.fetchone()[0]
    elif mode == 'work':
        # 업무용: office_links의 unchecked_likes_work만 카운트
        cursor.execute('SELECT SUM(unchecked_likes_work) FROM office_links WHERE management_site_id = ?', (management_site_id,))
        result = cursor.fetchone()[0]
        count = result if result is not None else 0
    else:
        count = 0
    conn.close()
    return count

def ensure_is_deleted_column():
    """office_links 테이블에 is_deleted 컬럼이 없으면 추가 (통합 DB만)"""
    db_path = '/data/integrated.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(office_links)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'is_deleted' not in columns:
            cursor.execute("ALTER TABLE office_links ADD COLUMN is_deleted INTEGER DEFAULT 0")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"{db_path} is_deleted 컬럼 추가 실패: {e}")

def ensure_unchecked_likes_work_column():
    """office_links 테이블에 unchecked_likes_work 컬럼이 없으면 추가 (통합 DB만)"""
    db_path = '/data/integrated.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(office_links)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'unchecked_likes_work' not in columns:
            cursor.execute("ALTER TABLE office_links ADD COLUMN unchecked_likes_work INTEGER DEFAULT 0")
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"{db_path} unchecked_likes_work 컬럼 추가 실패: {e}")

# 서버 시작 시 컬럼 보장
ensure_is_deleted_column()
ensure_unchecked_likes_work_column()

# 숨기기 함수

def hide_link(link_id, db_path='/data/integrated.db'):
    """office_links 테이블에서 해당 id의 매물을 is_deleted=1로 숨김 처리"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE office_links SET is_deleted = 1 WHERE id = ?", (link_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"숨기기 실패: {e}")
        return False

# 보증보험 리스트 조회 쿼리 수정
@app.route('/force-init-db')
def force_init_db():
    """Railway에서 DB 강제 초기화용 엔드포인트"""
    try:
        init_admin_db()
        
        # 테이블 존재 확인
        conn = sqlite3.connect('/data/integrated.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        return f"""
        <h2>✅ DB 초기화 성공!</h2>
        <h3>생성된 테이블:</h3>
        <ul>
        {''.join([f'<li>{table[0]}</li>' for table in tables])}
        </ul>
        <p><a href="/">관리자 페이지로 돌아가기</a></p>
        """
    except Exception as e:
        return f"<h2>❌ DB 초기화 실패: {e}</h2><p><a href='/'>돌아가기</a></p>"

@app.route('/debug-db-status')
def debug_db_status():
    """DB 상태 상세 확인용 디버깅 엔드포인트"""
    try:
        conn = sqlite3.connect('/data/integrated.db')
        cursor = conn.cursor()
        
        debug_info = "<html><head><title>DB 상태 디버깅</title></head><body>"
        debug_info += "<h1>🔍 DB 상태 디버깅 정보</h1>"
        
        # 1. 테이블 목록
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        debug_info += f"<h2>📊 테이블 목록</h2><ul>"
        for table in tables:
            debug_info += f"<li>{table[0]}</li>"
        debug_info += "</ul>"
        
        # 2. employees 테이블 데이터
        try:
            cursor.execute("SELECT * FROM employees LIMIT 10")
            employees = cursor.fetchall()
            debug_info += f"<h2>👥 employees 테이블 ({len(employees)}개)</h2>"
            if employees:
                debug_info += "<table border='1'><tr><th>ID</th><th>Employee ID</th><th>Name</th><th>Team</th><th>Active</th></tr>"
                for emp in employees:
                    debug_info += f"<tr><td>{emp[0]}</td><td>{emp[1]}</td><td>{emp[2]}</td><td>{emp[3]}</td><td>{emp[6]}</td></tr>"
                debug_info += "</table>"
            else:
                debug_info += "<p style='color:red;'>❌ employees 테이블이 비어있습니다!</p>"
        except Exception as e:
            debug_info += f"<p style='color:red;'>employees 조회 오류: {e}</p>"
        
        # 3. employee_customers 테이블 데이터
        try:
            cursor.execute("SELECT * FROM employee_customers LIMIT 10")
            customers = cursor.fetchall()
            debug_info += f"<h2>🏠 employee_customers 테이블 ({len(customers)}개)</h2>"
            if customers:
                debug_info += "<table border='1'><tr><th>ID</th><th>Employee ID</th><th>Management Site ID</th><th>Customer Name</th><th>Status</th></tr>"
                for cust in customers:
                    debug_info += f"<tr><td>{cust[0]}</td><td>{cust[1]}</td><td>{cust[2]}</td><td>{cust[3]}</td><td>{cust[13]}</td></tr>"
                debug_info += "</table>"
            else:
                debug_info += "<p style='color:red;'>❌ employee_customers 테이블이 비어있습니다!</p>"
        except Exception as e:
            debug_info += f"<p style='color:red;'>employee_customers 조회 오류: {e}</p>"
        
        # 4. 특정 management_site_id 검색
        debug_info += "<h2>🔍 특정 ID 검색</h2>"
        test_ids = ['f3a90de4', 'bc612330', '424ee340']
        for test_id in test_ids:
            try:
                cursor.execute("SELECT * FROM employee_customers WHERE management_site_id = ?", (test_id,))
                result = cursor.fetchone()
                if result:
                    debug_info += f"<p style='color:green;'>✅ {test_id}: 찾음 - {result[3]}</p>"
                else:
                    debug_info += f"<p style='color:red;'>❌ {test_id}: 없음</p>"
            except Exception as e:
                debug_info += f"<p style='color:red;'>{test_id} 검색 오류: {e}</p>"
        
        conn.close()
        debug_info += "<hr><p><a href='/'>관리자 페이지로 돌아가기</a></p></body></html>"
        return debug_info
        
    except Exception as e:
        return f"<h2>❌ DB 디버깅 실패: {e}</h2><p><a href='/'>돌아가기</a></p>"

@app.route('/insert-test-data')
def insert_test_data():
    """테스트용 직원과 고객 데이터 직접 삽입"""
    try:
        conn = sqlite3.connect('/data/integrated.db')
        cursor = conn.cursor()
        
        # 1. 테스트 직원 삽입
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO employees (employee_id, employee_name, team, password, created_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('admin', '관리자', '관리팀', 'admin123', current_date, 1))
            print("✅ 테스트 직원 삽입 완료")
        except Exception as e:
            print(f"직원 삽입 오류: {e}")
        
        # 2. 테스트 고객 삽입  
        import uuid
        test_management_id = str(uuid.uuid4())[:8]  # 8자리 ID 생성
        
        try:
            cursor.execute('''
                INSERT INTO employee_customers 
                (employee_id, management_site_id, customer_name, phone, inquiry_date, move_in_date, 
                 amount, room_count, location, progress_status, memo, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('admin', test_management_id, '테스트 고객', '010-1234-5678', current_date, 
                  '2024-12-31', '5억원', '3룸', '서울시 강남구', '진행중', '테스트용 고객입니다', current_date))
            print(f"✅ 테스트 고객 삽입 완료 - ID: {test_management_id}")
        except Exception as e:
            print(f"고객 삽입 오류: {e}")
        
        conn.commit()
        conn.close()
        
        return f"""
        <html><head><title>테스트 데이터 삽입</title></head><body>
        <h2>✅ 테스트 데이터 삽입 완료!</h2>
        <p><strong>생성된 Management Site ID:</strong> <code>{test_management_id}</code></p>
        <hr>
        <h3>🔗 테스트 링크</h3>
        <ul>
        <li><a href="https://web-production-d2f49.up.railway.app/customer/{test_management_id}" target="_blank">주거용 고객 사이트</a></li>
        <li><a href="https://web-production-8db05.up.railway.app/customer/{test_management_id}" target="_blank">업무용 고객 사이트</a></li>
        </ul>
        <hr>
        <p><a href="/debug-db-status">DB 상태 확인</a> | <a href="/">관리자 페이지</a></p>
        </body></html>
        """
        
    except Exception as e:
        return f"<h2>❌ 테스트 데이터 삽입 실패: {e}</h2><p><a href='/'>돌아가기</a></p>"

@app.route('/api/guarantee-list', methods=['GET'])
def get_guarantee_list():
    """보증보험이 가능한 매물 리스트 반환 (관리자+직원용, 숨김 처리 반영)"""
    if not (session.get('is_admin') or session.get('employee_id')):
        return jsonify({'error': 'Unauthorized'}), 401
    conn = sqlite3.connect('/data/integrated.db')
    print('실제 연결된 DB 경로:', '/data/integrated.db')
    cursor = conn.cursor()
    # links 테이블에서 guarantee_insurance=1, is_deleted=0인 링크만 조회, 최신순
    cursor.execute('''
        SELECT l.id, l.url, l.platform, l.added_by, l.date_added, l.rating, l.liked, l.disliked, l.memo, l.management_site_id
        FROM links l
        WHERE l.guarantee_insurance = 1 AND (l.is_deleted = 0 OR l.is_deleted IS NULL)
        ORDER BY l.id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    # 번호는 최신순으로 1부터
    result = []
    for idx, row in enumerate(rows):
        result.append({
            'id': row[0],
            'url': row[1],
            'platform': row[2],
            'added_by': row[3],
            'date_added': row[4],
            'rating': row[5],
            'liked': bool(row[6]),
            'disliked': bool(row[7]),
            'memo': row[8],
            'management_site_id': row[9],
            'number': len(rows) - idx
        })
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=8080) 