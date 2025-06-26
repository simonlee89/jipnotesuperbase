from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import uuid
from datetime import datetime
import os
import requests
import time
import db_utils
from psycopg2.extras import RealDictCursor

# 환경변수에서 사이트 URL 가져오기 (Railway 배포용)
# Railway 환경에서는 환경변수로, 로컬에서는 기본값 사용
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Railway 배포 환경
    RESIDENCE_SITE_URL = os.environ.get('RESIDENCE_SITE_URL', 'https://xn--2e0b220bo4n.com')
    BUSINESS_SITE_URL = os.environ.get('BUSINESS_SITE_URL', 'https://xn--2e0bx78aevc.com')
else:
    # 로컬 개발 환경
    RESIDENCE_SITE_URL = os.environ.get('RESIDENCE_SITE_URL', 'http://localhost:5000')
    BUSINESS_SITE_URL = os.environ.get('BUSINESS_SITE_URL', 'http://localhost:5001')

print(f"🏠 주거 사이트 URL: {RESIDENCE_SITE_URL}")
print(f"💼 업무 사이트 URL: {BUSINESS_SITE_URL}")

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
    
    # 보증보험 매물 목록 조회
    conn = None
    guarantee_list = []
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.id, l.url, l.platform, l.added_by, l.date_added, l.memo
            FROM links l
            WHERE l.guarantee_insurance = TRUE 
            ORDER BY l.id DESC
            LIMIT 20
        ''')
        
        guarantee_list = [db_utils.dict_from_row(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"보증보험 목록 조회 오류: {e}")
    finally:
        if conn:
            conn.close()
    
    # 디버깅: URL 확인
    print(f"[대시보드] 주거 사이트 URL: {RESIDENCE_SITE_URL}")
    print(f"[대시보드] 업무 사이트 URL: {BUSINESS_SITE_URL}")
    
    return render_template('employee_dashboard.html', 
                         employee_name=employee_name,
                         residence_site_url=RESIDENCE_SITE_URL,
                         business_site_url=BUSINESS_SITE_URL,
                         guarantee_list=guarantee_list)

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
            SELECT l.id, l.url, l.platform, l.added_by, l.date_added, l.memo, l.management_site_id
            FROM links l
            WHERE l.guarantee_insurance = TRUE 
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
            cursor.execute('SELECT id, name, email, team, position, created_at, role, status FROM employees ORDER BY created_at DESC')
            employees_raw = cursor.fetchall()
            print(f"[직원 목록] 조회된 직원 수: {len(employees_raw)}")
            employees = []
            for emp in employees_raw:
                emp_dict = db_utils.dict_from_row(emp)
                # 필드명 통일을 위해 매핑
                emp_dict['employee_id'] = emp_dict.get('name')  # name을 employee_id로 매핑
                emp_dict['employee_name'] = emp_dict.get('name')  # name을 employee_name으로도 매핑
                emp_dict['created_date'] = emp_dict.get('created_at')  # created_at을 created_date로 매핑
                # status가 'active'면 활성, 그 외는 비활성
                emp_dict['is_active'] = emp_dict.get('status', 'active') == 'active'
                employees.append(emp_dict)
                print(f"[직원 목록] 직원: {emp_dict.get('employee_name')} - 활성: {emp_dict['is_active']}")
            print(f"[직원 목록] 최종 응답: {employees}")
            return jsonify(employees)

        if request.method == 'POST':
            print("🔄 직원 추가 요청 받음")
            data = request.get_json()
            print(f"📥 요청 데이터: {data}")
            
            employee_id = data.get('employee_id')  # 실제로는 name으로 사용
            employee_name = data.get('employee_name')
            team = data.get('team', '')
            email = data.get('email', '')
            position = data.get('position', '')
            
            # employee_id와 employee_name 중 하나라도 있으면 name으로 사용
            name = employee_name if employee_name else employee_id
            
            print(f"📝 추출된 데이터 - 이름: '{name}', 팀: '{team}', 이메일: '{email}', 직책: '{position}'")
            
            if not name or name.strip() == '':
                print(f"❌ 이름이 비어있음")
                return jsonify({'success': False, 'message': '이름을 입력해야 합니다.'}), 400
            
            # 중복 이름 체크
            cursor.execute("SELECT id FROM employees WHERE name = %s", (name,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '이미 존재하는 직원 이름입니다.'}), 400
            
            print(f"✅ 직원 추가 중: {name}")
            cursor.execute("""
                INSERT INTO employees (name, email, team, position, created_at, role, status) 
                VALUES (%s, %s, %s, %s, %s, 'employee', 'active') RETURNING *
            """, (name, email, team, position, datetime.now()))
            new_employee_raw = cursor.fetchone()
            new_employee = db_utils.dict_from_row(new_employee_raw)
            
            # 필드명 통일을 위해 매핑
            new_employee['employee_id'] = new_employee.get('name')
            new_employee['employee_name'] = new_employee.get('name')
            new_employee['created_date'] = new_employee.get('created_at')
            new_employee['is_active'] = new_employee.get('status') == 'active'
            
            conn.commit()
            print(f"🎉 직원 추가 성공: {new_employee}")
            return jsonify({'success': True, 'employee': new_employee})
            
    except Exception as e:
        print(f"❌ 직원 추가 오류: {e}")
        if conn: conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/employees/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    """직원 비활성화 (소프트 삭제)"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE employees SET status = 'inactive' WHERE id = %s", (emp_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/employees/<int:emp_id>/activate', methods=['PUT'])
def activate_employee(emp_id):
    """직원 활성화"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE employees SET status = 'active' WHERE id = %s", (emp_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/employees/<int:emp_id>/reset-password', methods=['PUT'])
def reset_employee_password(emp_id):
    """직원 비밀번호 재설정 (더 이상 사용하지 않는 기능)"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # 새로운 스키마에서는 비밀번호 컬럼이 없으므로 성공만 반환
    return jsonify({'success': True, 'message': '새로운 시스템에서는 비밀번호가 필요하지 않습니다.'})

@app.route('/api/employees/<int:emp_id>/permanent-delete', methods=['DELETE'])
def permanent_delete_employee(emp_id):
    """직원 완전 삭제 (비활성 상태인 경우만)"""
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 비활성 상태인지 확인
        cursor.execute("SELECT status FROM employees WHERE id = %s", (emp_id,))
        result = cursor.fetchone()
        if not result or result.get('status') == 'active':
            return jsonify({'success': False, 'message': '활성 상태의 직원은 삭제할 수 없습니다.'}), 400
        
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
            
            # 디버깅: 고객 정보 확인
            print(f"[고객 목록] 총 {len(customers_list)}명의 고객")
            for i, customer in enumerate(customers_list[:3]):  # 처음 3명만 출력
                print(f"  고객 {i+1}: {customer.get('customer_name')} - management_site_id: {customer.get('management_site_id')}")
            
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
        print(f"[고객 추가] 새 management_site_id 생성: {management_site_id}")
        
        conn = None
        try:
            conn, _ = db_utils.get_db_connection()
            cursor = conn.cursor()
            
            columns = ', '.join(f'"{k}"' for k in customer_data.keys())
            placeholders = ', '.join(['%s'] * len(customer_data))
            query = f"INSERT INTO employee_customers ({columns}, management_site_id) VALUES ({placeholders}, %s) RETURNING *"
            params = list(customer_data.values()) + [management_site_id]
            
            print(f"[고객 추가] SQL 쿼리: {query}")
            print(f"[고객 추가] 파라미터 개수: {len(params)}")
            
            cursor.execute(query, params)
            new_customer_raw = cursor.fetchone()
            conn.commit()
            
            if not new_customer_raw:
                raise Exception("INSERT 후 새로운 고객 정보를 가져오는데 실패했습니다.")

            new_customer = db_utils.dict_from_row(new_customer_raw)
            
            # 디버깅: 새 고객 정보 확인
            print(f"[새 고객 추가] 이름: {new_customer.get('customer_name')}")
            print(f"[새 고객 추가] management_site_id: {new_customer.get('management_site_id')}")
            print(f"[새 고객 추가] 전체 데이터: {new_customer}")
            
            # 저장 확인을 위해 다시 조회
            cursor.execute("SELECT management_site_id FROM employee_customers WHERE id = %s", (new_customer.get('id'),))
            verify_result = cursor.fetchone()
            print(f"[새 고객 추가] 저장 확인 - management_site_id: {verify_result}")
            
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

# ==================== 주거용 사이트 라우트 ====================
@app.route('/residence')
def residence_index():
    """주거용 메인 페이지"""
    try:
        # customer_info 테이블 제거로 기본값 사용
        customer_name = '제일좋은집 찾아드릴분'
        move_in_date = ''
        
        employee_id = session.get('employee_id', '')
        return render_template('index.html', customer_name=customer_name, move_in_date=move_in_date, employee_id=employee_id)
        
    except Exception as e:
        print(f"[주거용] 메인 페이지 오류: {e}")
        return f"주거용 사이트 오류: {e}", 500

@app.route('/residence/customer/<management_site_id>')
def residence_customer_site(management_site_id):
    """주거용 고객별 사이트"""
    print(f"[주거ROUTE] 고객 사이트 접근 - management_site_id: {management_site_id}")
    
    # 디버깅: 모든 고객 목록 확인
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, customer_name, management_site_id FROM employee_customers ORDER BY id DESC LIMIT 10")
        all_customers = cursor.fetchall()
        print(f"[주거ROUTE] 최근 고객 10명:")
        for cust in all_customers:
            print(f"  - ID: {cust.get('id')}, 이름: {cust.get('customer_name')}, management_site_id: {cust.get('management_site_id')}")
        conn.close()
    except Exception as e:
        print(f"[주거ROUTE] 고객 목록 조회 오류: {e}")
    
    # 공통 get_customer_info 함수 사용
    customer_info = db_utils.get_customer_info(management_site_id)
    if not customer_info:
        print(f"[주거ROUTE] 고객 정보를 찾을 수 없음: {management_site_id}")
        # 더 자세한 오류 메시지
        return f"""
        <h1>고객 정보를 찾을 수 없습니다</h1>
        <p>요청한 management_site_id: <strong>{management_site_id}</strong></p>
        <p>데이터베이스에서 해당 고객을 찾을 수 없습니다.</p>
        <p><a href="/dashboard">대시보드로 돌아가기</a></p>
        """, 404
    
    customer_name = customer_info.get('customer_name', '고객')
    print(f"[주거ROUTE] 고객 정보 조회 성공 - 이름: {customer_name}")
    
    # 미확인 좋아요 처리
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE links SET is_checked = TRUE WHERE management_site_id = %s AND liked = TRUE AND is_checked = FALSE', (management_site_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"미확인 좋아요 처리 오류: {e}")
    
    return render_template('index.html', 
                         customer_name=customer_name, 
                         move_in_date=customer_info.get('move_in_date', ''),
                         management_site_id=management_site_id)

# ==================== 업무용 사이트 라우트 ====================
@app.route('/business')
def business_index():
    """업무용 메인 페이지"""
    try:
        # customer_info 테이블 제거로 기본값 사용
        customer_name = '프리미엄등록'
        move_in_date = ''
        
        employee_id = session.get('employee_id', '')
        return render_template('업무용_index.html', customer_name=customer_name, move_in_date=move_in_date, employee_id=employee_id)
        
    except Exception as e:
        print(f"[업무용] 메인 페이지 오류: {e}")
        return f"업무용 사이트 오류: {e}", 500

@app.route('/business/customer/<management_site_id>')
def business_customer_site(management_site_id):
    """업무용 고객별 사이트"""
    print(f"[업무ROUTE] 고객 사이트 접근 - management_site_id: {management_site_id}")
    
    # 디버깅: 모든 고객 목록 확인
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, customer_name, management_site_id FROM employee_customers ORDER BY id DESC LIMIT 10")
        all_customers = cursor.fetchall()
        print(f"[업무ROUTE] 최근 고객 10명:")
        for cust in all_customers:
            print(f"  - ID: {cust.get('id')}, 이름: {cust.get('customer_name')}, management_site_id: {cust.get('management_site_id')}")
        conn.close()
    except Exception as e:
        print(f"[업무ROUTE] 고객 목록 조회 오류: {e}")
    
    # 공통 get_customer_info 함수 사용
    customer_info = db_utils.get_customer_info(management_site_id)
    if not customer_info:
        print(f"[업무ROUTE] 고객 정보를 찾을 수 없음: {management_site_id}")
        # 더 자세한 오류 메시지
        return f"""
        <h1>고객 정보를 찾을 수 없습니다</h1>
        <p>요청한 management_site_id: <strong>{management_site_id}</strong></p>
        <p>데이터베이스에서 해당 고객을 찾을 수 없습니다.</p>
        <p><a href="/dashboard">대시보드로 돌아가기</a></p>
        """, 404
    
    customer_name = customer_info.get('customer_name', '고객')
    print(f"[업무ROUTE] 고객 정보 조회 성공 - 이름: {customer_name}")
    
    # 미확인 좋아요 처리 (업무용도 is_checked 사용)
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE office_links SET is_checked = TRUE WHERE management_site_id = %s AND liked = TRUE AND is_checked = FALSE', (management_site_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"미확인 좋아요 처리 오류: {e}")
    
    return render_template('업무용_index.html', 
                         customer_name=customer_name, 
                         move_in_date=customer_info.get('move_in_date', ''),
                         management_site_id=management_site_id)

# ==================== 주거용 API 라우트 ====================
@app.route('/api/links', methods=['GET', 'POST'])
def residence_links():
    """주거용 링크 API"""
    management_site_id = request.args.get('management_site_id')
    
    if request.method == 'POST':
        try:
            conn, _ = db_utils.get_db_connection()
            cursor = conn.cursor()
            
            data = request.json
            url = data.get('url')
            platform = data.get('platform')
            added_by = session.get('employee_id', '중개사')
            memo = data.get('memo', '')
            guarantee_insurance = data.get('guarantee_insurance', False)
            
            if not url or not platform:
                conn.close()
                return jsonify({'success': False, 'error': 'URL과 플랫폼은 필수 입력 항목입니다.'}), 400
            
            date_added = datetime.now().strftime('%Y-%m-%d')
            
            # 고객 정보 검증
            if management_site_id:
                customer_info = db_utils.get_customer_info(management_site_id)
                if not customer_info:
                    conn.close()
                    return jsonify({'success': False, 'error': '존재하지 않는 고객입니다.'}), 404
            
            # DB에 링크 추가 (PostgreSQL)
            cursor.execute('''
                INSERT INTO links (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance))
            result = cursor.fetchone()
            link_id = result['id'] if isinstance(result, dict) else result[0]
            
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'id': link_id})
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # GET 요청
        try:
            conn, _ = db_utils.get_db_connection()
            cursor = conn.cursor()
            
            # 필터 파라미터 처리
            platform_filter = request.args.get('platform', 'all')
            user_filter = request.args.get('user', 'all')
            like_filter = request.args.get('like', 'all')
            date_filter = request.args.get('date', '')
            guarantee_filter = request.args.get('guarantee', 'all')
            
            query = 'SELECT * FROM links WHERE 1=1'
            params = []
            
            # 고객별 필터링
            if management_site_id:
                query += ' AND management_site_id = %s'
                params.append(management_site_id)
            else:
                query += ' AND management_site_id IS NULL'
            
            # 플랫폼 필터
            if platform_filter != 'all':
                query += ' AND platform = %s'
                params.append(platform_filter)
            
            # 사용자 필터
            if user_filter != 'all':
                query += ' AND added_by = %s'
                params.append(user_filter)
            
            # 좋아요 필터
            if like_filter == 'liked':
                query += ' AND liked = TRUE'
            elif like_filter == 'disliked':
                query += ' AND disliked = TRUE'
            
            # 날짜 필터
            if date_filter:
                query += ' AND date_added = %s'
                params.append(date_filter)
            
            # 보증보험 필터
            if guarantee_filter == 'available':
                query += ' AND guarantee_insurance = TRUE'
            elif guarantee_filter == 'unavailable':
                query += ' AND guarantee_insurance = FALSE'
            
            query += ' ORDER BY id DESC'
            cursor.execute(query, params)
            links_data = cursor.fetchall()
            
            conn.close()
            
            # 데이터 형식 변환
            links_list = []
            for idx, link in enumerate(links_data):
                links_list.append({
                    'id': link['id'],
                    'number': len(links_data) - idx,  # 역순 번호
                    'url': link['url'],
                    'platform': link['platform'],
                    'added_by': link['added_by'],
                    'date_added': link['date_added'].strftime('%Y-%m-%d %H:%M') if link.get('date_added') else '',
                    'rating': link['rating'],
                    'liked': bool(link['liked']),
                    'disliked': bool(link['disliked']),
                    'memo': link.get('memo', ''),
                    'guarantee_insurance': bool(link['guarantee_insurance'])
                })
            
            return jsonify(links_list)
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/links/<int:link_id>', methods=['PUT', 'DELETE'])
def update_residence_link(link_id):
    """주거용 링크 수정/삭제"""
    conn, _ = db_utils.get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'PUT':
        data = request.json
        action = data.get('action')
        
        if action == 'rating':
            rating = data.get('rating', 5)
            cursor.execute('UPDATE links SET rating = %s WHERE id = %s', (rating, link_id))
        
        elif action == 'like':
            liked = data.get('liked', False)
            cursor.execute('UPDATE links SET liked = %s, disliked = FALSE, is_checked = FALSE WHERE id = %s', (liked, link_id))
        
        elif action == 'dislike':
            disliked = data.get('disliked', False)
            cursor.execute('UPDATE links SET disliked = %s, liked = FALSE WHERE id = %s', (disliked, link_id))
        
        elif action == 'memo':
            memo = data.get('memo', '')
            cursor.execute('UPDATE links SET memo = %s WHERE id = %s', (memo, link_id))
        
        elif action == 'guarantee':
            guarantee_insurance = data.get('guarantee_insurance', False)
            cursor.execute('UPDATE links SET guarantee_insurance = %s WHERE id = %s', (guarantee_insurance, link_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM links WHERE id = %s', (link_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

# ==================== 업무용 API 라우트 ====================
@app.route('/api/office-links', methods=['GET', 'POST'])
def business_links():
    """업무용 링크 API"""
    management_site_id = request.args.get('management_site_id')
    
    if request.method == 'POST':
        data = request.json
        url = data.get('url')
        platform = data.get('platform')
        added_by = session.get('employee_id', '관리자')
        memo = data.get('memo', '')
        guarantee_insurance = data.get('guarantee_insurance', False)
        
        if not url or not platform:
            return jsonify({'success': False, 'error': '필수 정보가 누락되었습니다.'})
        
        date_added = datetime.now().strftime('%Y-%m-%d')
        
        # management_site_id가 있는 경우 고객 존재 여부 확인
        if management_site_id:
            customer_info = db_utils.get_customer_info(management_site_id)
            if not customer_info:
                return jsonify({'success': False, 'error': '존재하지 않는 고객입니다.'})
        
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO office_links (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        ''', (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance))
        result = cursor.fetchone()
        new_link_id = result['id'] if result and isinstance(result, dict) else (result[0] if result else None)
        
        # 새로 추가된 링크 정보 다시 조회
        cursor.execute('SELECT * FROM office_links WHERE id = %s', (new_link_id,))
        new_link_data = cursor.fetchone()
            
        conn.commit()
        conn.close()

        # PostgreSQL 결과 처리
        response_data = dict(new_link_data)
        response_data['success'] = True  # 프론트엔드가 기대하는 success 필드 추가

        return jsonify(response_data), 201

    else:  # GET 요청
        # 필터 파라미터
        platform_filter = request.args.get('platform', 'all')
        user_filter = request.args.get('user', 'all')
        like_filter = request.args.get('like', 'all')
        date_filter = request.args.get('date', '')
        guarantee_filter = request.args.get('guarantee', 'all')
        
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM office_links WHERE 1=1'
        params = []
        
        # 고객별 필터링 추가
        if management_site_id:
            query += ' AND management_site_id = %s'
            params.append(management_site_id)
        else:
            query += ' AND management_site_id IS NULL'
        
        if platform_filter != 'all':
            query += ' AND platform = %s'
            params.append(platform_filter)
        
        if user_filter != 'all':
            query += ' AND added_by = %s'
            params.append(user_filter)
        
        if like_filter == 'liked':
            query += ' AND liked = TRUE'
        elif like_filter == 'disliked':
            query += ' AND disliked = TRUE'
        elif like_filter == 'none':
            query += ' AND liked = FALSE AND disliked = FALSE'
        
        if date_filter:
            query += ' AND date_added = %s'
            params.append(date_filter)
        
        if guarantee_filter == 'available':
            query += ' AND guarantee_insurance = TRUE'
        elif guarantee_filter == 'unavailable':
            query += ' AND guarantee_insurance = FALSE'
        
        query += ' ORDER BY id DESC'
        
        cursor.execute(query, params)
        links_data = cursor.fetchall()
        conn.close()
        
        # 데이터 접근 방식을 키(컬럼명)로 변경
        links_list = []
        for idx, link in enumerate(links_data):
            links_list.append({
                'id': link['id'],
                'number': len(links_data) - idx,  # 역순 번호
                'url': link['url'],
                'platform': link['platform'],
                'added_by': link['added_by'],
                'date_added': link['date_added'].strftime('%Y-%m-%d %H:%M') if link.get('date_added') else '',
                'rating': link['rating'],
                'liked': bool(link['liked']),
                'disliked': bool(link['disliked']),
                'memo': link.get('memo', ''),
                'guarantee_insurance': bool(link['guarantee_insurance'])
            })
        
        return jsonify(links_list)

@app.route('/api/office-links/<int:link_id>', methods=['PUT', 'DELETE'])
def update_business_link(link_id):
    """업무용 링크 수정/삭제"""
    conn, _ = db_utils.get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'PUT':
        data = request.json
        action = data.get('action')
        
        if action == 'rating':
            rating = data.get('rating', 5)
            cursor.execute('UPDATE office_links SET rating = %s WHERE id = %s', (rating, link_id))
        
        elif action == 'like':
            liked = data.get('liked', False)
            if liked:
                cursor.execute('UPDATE office_links SET liked = TRUE, disliked = FALSE, is_checked = FALSE WHERE id = %s', (link_id,))
            else:
                cursor.execute('UPDATE office_links SET liked = FALSE WHERE id = %s', (link_id,))
        
        elif action == 'dislike':
            disliked = data.get('disliked', False)
            cursor.execute('UPDATE office_links SET disliked = %s, liked = FALSE WHERE id = %s', (disliked, link_id))
        
        elif action == 'memo':
            memo = data.get('memo', '')
            cursor.execute('UPDATE office_links SET memo = %s WHERE id = %s', (memo, link_id))
        
        elif action == 'guarantee':
            guarantee_insurance = data.get('guarantee_insurance', False)
            cursor.execute('UPDATE office_links SET guarantee_insurance = %s WHERE id = %s', (guarantee_insurance, link_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM office_links WHERE id = %s', (link_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/debug/check-customers')
def debug_check_customers():
    """디버깅: employee_customers 테이블 확인"""
    if not session.get('is_admin'):
        return "관리자만 접근 가능합니다.", 403
    
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'employee_customers'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        # 최근 고객 데이터 확인
        cursor.execute("""
            SELECT id, employee_id, customer_name, management_site_id, created_date 
            FROM employee_customers 
            ORDER BY id DESC 
            LIMIT 20
        """)
        customers = cursor.fetchall()
        
        conn.close()
        
        html = """
        <h1>Employee Customers 테이블 디버깅</h1>
        <h2>테이블 구조:</h2>
        <table border="1">
            <tr><th>컬럼명</th><th>데이터타입</th></tr>
        """
        
        for col in columns:
            html += f"<tr><td>{col['column_name']}</td><td>{col['data_type']}</td></tr>"
        
        html += """
        </table>
        <h2>최근 고객 20명:</h2>
        <table border="1">
            <tr><th>ID</th><th>직원ID</th><th>고객명</th><th>Management Site ID</th><th>생성일</th></tr>
        """
        
        for cust in customers:
            html += f"""
            <tr>
                <td>{cust['id']}</td>
                <td>{cust['employee_id']}</td>
                <td>{cust['customer_name']}</td>
                <td><strong>{cust['management_site_id']}</strong></td>
                <td>{cust['created_date']}</td>
            </tr>
            """
        
        html += """
        </table>
        <p><a href="/admin">관리자 페이지로 돌아가기</a></p>
        """
        
        return html
        
    except Exception as e:
        return f"오류 발생: {e}", 500

# ==================== 고객 정보 API 라우트 ====================
@app.route('/api/customer_info', methods=['GET', 'POST'])
def customer_info_api():
    """고객 정보 API - 주거용/업무용 사이트에서 사용"""
    management_site_id = request.args.get('management_site_id')
    
    if request.method == 'GET':
        if not management_site_id:
            return jsonify({'error': 'management_site_id가 필요합니다.'}), 400
        
        customer_info = db_utils.get_customer_info(management_site_id)
        if not customer_info:
            return jsonify({'error': '고객 정보를 찾을 수 없습니다.'}), 404
        
        return jsonify({
            'customer_name': customer_info.get('customer_name', '고객'),
            'move_in_date': customer_info.get('move_in_date', ''),
            'management_site_id': management_site_id
        })
    
    elif request.method == 'POST':
        # 고객 정보 업데이트 (필요한 경우)
        if not management_site_id:
            return jsonify({'error': 'management_site_id가 필요합니다.'}), 400
        
        data = request.json
        customer_name = data.get('customer_name')
        move_in_date = data.get('move_in_date')
        
        try:
            conn, _ = db_utils.get_db_connection()
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            if customer_name is not None:
                update_fields.append('customer_name = %s')
                params.append(customer_name)
            
            if move_in_date is not None:
                update_fields.append('move_in_date = %s')
                params.append(move_in_date)
            
            if update_fields:
                params.append(management_site_id)
                query = f"UPDATE employee_customers SET {', '.join(update_fields)} WHERE management_site_id = %s"
                cursor.execute(query, params)
                conn.commit()
            
            conn.close()
            return jsonify({'success': True})
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)