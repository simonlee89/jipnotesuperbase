from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import uuid
from datetime import datetime
import os
import requests
import time
import db_utils
from psycopg2.extras import RealDictCursor

# 환경변수에서 사이트 URL 가져오기 (Railway 배포용)
RESIDENCE_SITE_URL = os.environ.get('RESIDENCE_SITE_URL', 'http://localhost:5000')
BUSINESS_SITE_URL = os.environ.get('BUSINESS_SITE_URL', 'http://localhost:5001')

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 세션용 비밀키

# Railway에서 gunicorn 실행 시에도 DB 초기화가 되도록 앱 생성 직후 호출
try:
    db_utils.init_database()
    db_utils.ensure_all_columns()
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """직원 로그인 (새로운 테이블 구조에 맞게 수정)"""
    data = request.get_json()
    employee_id = data.get('employee_id')  # 실제로는 name으로 검색
    password = data.get('password')  # password 컬럼이 없으므로 무시
    
    print(f"🔍 직원 로그인 시도: '{employee_id}'")  # 디버깅 로그
    
    if not employee_id or employee_id.strip() == '':
        return jsonify({'success': False, 'message': '직원 이름을 입력해주세요.'})
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
    
        # 새로운 테이블 구조: name으로 검색, password와 is_active 컬럼 없음
        cursor.execute('SELECT id, name, role FROM employees WHERE name = %s', (employee_id,))
        employee = cursor.fetchone()
    
        # 디버깅: 전체 직원 목록 조회
        cursor.execute('SELECT id, name, role FROM employees ORDER BY id')
        all_employees = cursor.fetchall()
        print(f"📋 전체 직원 목록 ({len(all_employees)}명):")
        for emp in all_employees:
            try:
                if isinstance(emp, dict):
                    print(f"  - ID:{emp.get('id')} | 이름:'{emp.get('name')}' | 역할:{emp.get('role')}")
                else:
                    print(f"  - ID:{emp[0]} | 이름:'{emp[1]}' | 역할:{emp[2]}")
            except (KeyError, IndexError) as e:
                print(f"  - 직원 정보 출력 오류: {e}, 데이터: {emp}")
    
        if employee:
            if isinstance(employee, dict):
                employee_name = employee.get('name')
                employee_id_val = employee.get('id')
                employee_role = employee.get('role')
            else:
                employee_name = employee[1]
                employee_id_val = employee[0]
                employee_role = employee[2]

            print(f"✅ 로그인 성공: {employee_name} (ID:{employee_id_val})")
            session['employee_id'] = employee_name # 로그인 시 사용한 이름
            session['employee_name'] = employee_name
            session['employee_role'] = employee_role
            return jsonify({'success': True})
        else:
            print(f"❌ 로그인 실패: '{employee_id}' 직원을 찾을 수 없음")
            
            available_names = []
            for emp in all_employees:
                try:
                    if isinstance(emp, dict):
                        available_names.append(emp.get('name'))
                    else:
                        available_names.append(emp[1])
                except (KeyError, IndexError):
                    continue
            
            return jsonify({
                'success': False, 
                'message': f"'{employee_id}' 직원을 찾을 수 없습니다.\n\n사용 가능한 직원 이름:\n" + "\n".join([f"• {name}" for name in available_names[:10] if name])
            })
    except Exception as e:
        print(f"로그인 중 오류: {e}")
        return jsonify({'success': False, 'message': '로그인 중 서버 오류가 발생했습니다.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin-login', methods=['POST'])
def admin_login():
    """관리자 로그인"""
    data = request.get_json()
    admin_id = data.get('admin_id')
    admin_password = data.get('admin_password')
    
    ADMIN_ID = 'admin'
    ADMIN_PASSWORD = 'ejxkqdnjs1emd'
    
    if admin_id == ADMIN_ID and admin_password == ADMIN_PASSWORD:
        session['is_admin'] = True
        session['admin_id'] = admin_id
        session['employee_name'] = '관리자'
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
    if 'employee_id' not in session and 'is_admin' not in session:
        return redirect(url_for('index'))
    
    employee_name = session.get('employee_name', '직원')
    
    return render_template('employee_dashboard.html', 
                         employee_name=employee_name,
                         residence_site_url=RESIDENCE_SITE_URL,
                         business_site_url=BUSINESS_SITE_URL)

@app.route('/admin')
def admin_panel():
    """관리자 패널 (직원 관리)"""
    if not session.get('is_admin'):
        return redirect(url_for('index'))

    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
    
        cursor.execute('''
            SELECT l.id, l.url, l.platform, l.added_by, l.date_added, l.memo
            FROM links l
            WHERE l.guarantee_insurance = TRUE AND (l.is_deleted = FALSE OR l.is_deleted IS NULL)
            ORDER BY l.id DESC
        ''')
    
        guarantee_list = [db_utils.dict_from_row(row) for row in cursor.fetchall()]

        return render_template('admin_panel.html', 
                             guarantee_list=guarantee_list,
                             residence_site_url=RESIDENCE_SITE_URL,
                             business_site_url=BUSINESS_SITE_URL)
    except Exception as e:
        print(f"보증보험 목록 조회 오류: {e}")
        return "보증보험 목록을 불러오는 중 오류가 발생했습니다.", 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/guarantee-delete/<int:id>', methods=['POST'])
def guarantee_delete(id):
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE links SET guarantee_insurance = FALSE WHERE id = %s', (id,))
        conn.commit()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        if conn: conn.rollback()
        return "삭제 중 오류 발생", 500
    finally:
        if conn: conn.close()

@app.route('/admin/guarantee-edit/<int:id>', methods=['POST'])
def guarantee_edit(id):
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    memo = request.form.get('memo', '')
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE links SET memo = %s WHERE id = %s', (memo, id))
        conn.commit()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        if conn: conn.rollback()
        return "수정 중 오류 발생", 500
    finally:
        if conn: conn.close()

# 직원 관리 API
@app.route('/api/employees', methods=['GET', 'POST'])
def manage_employees():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
            
        if request.method == 'GET':
            cursor.execute('SELECT id, name, created_at, role FROM employees ORDER BY created_at DESC')
            employees = [db_utils.dict_from_row(row) for row in cursor.fetchall()]
            return jsonify(employees)

        if request.method == 'POST':
            data = request.get_json()
            name = data.get('name')
            role = data.get('role', 'employee')
            
            if not name:
                return jsonify({'success': False, 'message': '이름을 입력해야 합니다.'}), 400
            
            cursor.execute("INSERT INTO employees (name, role) VALUES (%s, %s) RETURNING *", (name, role))
            new_employee = db_utils.dict_from_row(cursor.fetchone())
            conn.commit()
            return jsonify({'success': True, 'employee': new_employee})
            
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/employees/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employees WHERE id = %s", (emp_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/customers', methods=['GET', 'POST'])
def manage_customers():
    # 관리자 또는 직원만 접근 가능
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    employee_id = session.get('employee_id')
    if session.get('is_admin'):
        employee_id = 'admin'

    # --- GET 요청: 고객 목록 조회 ---
    if request.method == 'GET':
        conn = None
        try:
            conn, _ = db_utils.get_db_connection()
            cursor = conn.cursor()
        
            if employee_id == 'admin':
                query = "SELECT * FROM employee_customers ORDER BY inquiry_date DESC, id DESC"
                cursor.execute(query)
            else:
                query = "SELECT * FROM employee_customers WHERE employee_id = %s ORDER BY inquiry_date DESC, id DESC"
                cursor.execute(query, (employee_id,))
            
            customers_raw = cursor.fetchall()
            customers_list = [db_utils.dict_from_row(row) for row in customers_raw]
            return jsonify(customers_list)

        except Exception as e:
            print(f"고객 목록 조회 오류: {e}")
            return jsonify({'error': f'고객 목록 조회 실패: {e}'}), 500
        finally:
            if conn:
                conn.close()
        
    # --- POST 요청: 새 고객 추가 ---
    if request.method == 'POST':
        data = request.get_json()
        current_employee_id = session.get('employee_id')
        
        customer_data = {
            'inquiry_date': data.get('inquiry_date'),
            'move_in_date': data.get('move_in_date'),
            'customer_name': data.get('customer_name'),
            'phone': data.get('phone'),
            'amount': data.get('amount'),
            'room_count': data.get('room_count'),
            'location': data.get('location'),
            'loan_info': data.get('loan_info'),
            'parking': data.get('parking'),
            'pets': data.get('pets'),
            'memo': data.get('memo'),
            'progress_status': data.get('progress_status', '진행중'),
            'employee_id': current_employee_id,
            'created_date': datetime.now()
        }
        
        management_site_id = str(uuid.uuid4().hex)[:8]
        
        conn = None
        try:
            conn, _ = db_utils.get_db_connection()
            cursor = conn.cursor()
            
            columns = ', '.join(f'"{k}"' for k in customer_data.keys())
            placeholders = ', '.join(['%s'] * len(customer_data))
            query = f"INSERT INTO employee_customers ({columns}, management_site_id) VALUES ({placeholders}, %s) RETURNING *"
            params = list(customer_data.values()) + [management_site_id]
            
            cursor.execute(query, params)
            new_customer_raw = cursor.fetchone()
            conn.commit()
            
            if not new_customer_raw:
                raise Exception("INSERT 후 새로운 고객 정보를 가져오는데 실패했습니다.")

            new_customer = db_utils.dict_from_row(new_customer_raw)
            return jsonify({'success': True, 'message': '고객이 추가되었습니다.', 'customer': new_customer})

        except Exception as e:
            if conn: conn.rollback()
            return jsonify({'success': False, 'message': f'고객 추가 중 오류 발생: {e}'}), 500
        finally:
            if conn: conn.close()

@app.route('/api/customers/<int:customer_id>', methods=['PUT', 'DELETE'])
def update_delete_customer(customer_id):
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    employee_id = session.get('employee_id')
    if session.get('is_admin'):
        employee_id = 'admin'

    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 권한 확인
        if employee_id != 'admin':
            cursor.execute("SELECT id FROM employee_customers WHERE id = %s AND employee_id = %s", (customer_id, employee_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403

        if request.method == 'PUT':
            data = request.get_json()
            # 여기에 필드 업데이트 로직이 필요하지만, 현재 사용되지 않으므로 pass
            pass
            return jsonify({'success': True})
    
        if request.method == 'DELETE':
            cursor.execute("DELETE FROM employee_customers WHERE id = %s", (customer_id,))
            conn.commit()
            return jsonify({'success': True, 'message': '고객이 삭제되었습니다.'})

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': '작업 중 오류 발생'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/customers/<int:customer_id>/memo', methods=['PUT'])
def update_customer_memo(customer_id):
    data = request.get_json()
    memo = data.get('memo')
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE employee_customers SET memo = %s WHERE id = %s", (memo, customer_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': '메모 업데이트 실패'}), 500
    finally:
        if conn: conn.close()

@app.route('/api/customers/<int:customer_id>/field', methods=['PUT'])
def update_customer_field(customer_id):
    data = request.get_json()
    field, value = list(data.items())[0]

    # 허용된 필드 목록
    allowed_fields = [
        "inquiry_date", "move_in_date", "customer_name", "phone", 
        "amount", "room_count", "location", "loan_info", 
        "parking", "pets", "progress_status"
    ]
    if field not in allowed_fields:
        return jsonify({'success': False, 'error': '허용되지 않은 필드'}), 400

    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        query = f'UPDATE employee_customers SET "{field}" = %s WHERE id = %s'
        cursor.execute(query, (value, customer_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        if conn: conn.rollback()
        print(f"필드 업데이트 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)