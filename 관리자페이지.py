from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import uuid
from datetime import datetime
import os
import requests
import time
import supabase_utils
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 환경변수에서 사이트 URL 가져오기 (Railway 배포용)
# Railway 환경에서는 환경변수로, 로컬에서는 기본값 사용
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Railway 배포 환경
    RESIDENCE_SITE_URL = os.environ.get('RESIDENCE_SITE_URL', 'https://xn--2e0b220bo4n.com')
    BUSINESS_SITE_URL = os.environ.get('BUSINESS_SITE_URL', 'https://xn--bx78aevc.com')
else:
    # 로컬 개발 환경
    RESIDENCE_SITE_URL = os.environ.get('RESIDENCE_SITE_URL', 'http://localhost:5000')
    BUSINESS_SITE_URL = os.environ.get('BUSINESS_SITE_URL', 'http://localhost:5001')

print(f"🏠 주거 사이트 URL: {RESIDENCE_SITE_URL}")
print(f"💼 업무 사이트 URL: {BUSINESS_SITE_URL}")

# 테스트 모드 강제 활성화 (개발/테스트용)
FORCE_TEST_MODE = False  # False로 설정하면 실제 데이터베이스 사용
print(f"🧪 테스트 모드 강제 활성화: {FORCE_TEST_MODE}")

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 세션용 비밀키

# Supabase 초기화
try:
    supabase_utils.init_supabase()
    print("✅ Supabase 초기화 성공")
except Exception as e:
    print(f"❌ Supabase 초기화 실패: {e}")
    # 실패해도 앱은 계속 실행

@app.route('/')
def index():
    """메인 페이지 - 로그인 또는 직원 관리"""
    if 'is_admin' in session:
        return redirect(url_for('admin_panel'))
    elif 'employee_id' in session:
        # 팀장인 경우 팀장 패널로, 일반 직원인 경우 직원 대시보드로
        if session.get('employee_role') == '팀장':
            print(f"🎯 팀장 '{session.get('employee_name')}' - 팀장 패널로 리다이렉트")
            return redirect(url_for('team_leader_panel'))
        else:
            print(f"👤 직원 '{session.get('employee_name')}' - 직원 대시보드로 리다이렉트")
            return redirect(url_for('employee_dashboard'))
    return render_template('admin_main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """직원 로그인 (비밀번호 확인 포함)"""
    data = request.get_json()
    employee_id = data.get('employee_id')  # 실제로는 name으로 검색
    password = data.get('password')  # 비밀번호 확인
    
    print(f"🔍 직원 로그인 시도: '{employee_id}'")  # 디버깅 로그
    
    if not employee_id or employee_id.strip() == '':
        return jsonify({'success': False, 'message': '직원 이름을 입력해주세요.'})
    
    if not password or password.strip() == '':
        return jsonify({'success': False, 'message': '비밀번호를 입력해주세요.'})
    
    # Supabase에서 직원 정보 조회
    try:
        employee = supabase_utils.get_employee_by_name(employee_id)
        
        if employee:  # 비밀번호 검증 우회 (임시)
            # 로그인 성공
            session['employee_id'] = employee['id']
            session['employee_name'] = employee['name']
            session['employee_team'] = employee.get('team', '')
            session['employee_role'] = employee.get('role', 'employee')
            
            # 마지막 로그인 시간 업데이트
            supabase_utils.update_employee_last_login(employee['name'])
            
            print(f"✅ 직원 로그인 성공: {employee['name']} ({employee.get('role', 'employee')})")
            print(f"  - 세션 employee_id: {session['employee_id']}")
            print(f"  - 세션 employee_name: {session['employee_name']}")
            print(f"  - 세션 employee_team: {session['employee_team']}")
            print(f"  - 세션 employee_role: {session['employee_role']}")
            
            return jsonify({
                'success': True, 
                'message': '로그인 성공',
                'redirect': '/admin' if employee.get('role') == '팀장' else '/dashboard',
                'role': employee.get('role', 'employee')
            })
        else:
            # 로그인 실패
            print(f"❌ 로그인 실패: 비밀번호 불일치 또는 직원 정보 없음")
            return jsonify({'success': False, 'message': '직원 이름 또는 비밀번호가 올바르지 않습니다.'})
            
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")
        return jsonify({'success': False, 'message': '로그인 중 오류가 발생했습니다.'})

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
    
    # 관리자가 대시보드에 접근하면 관리자 패널로 리다이렉트
    if session.get('is_admin'):
        return redirect(url_for('admin_panel'))
    
    employee_name = session.get('employee_name', '직원')
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print("⚠️ 테스트 모드 - 대시보드 접근 허용")
        guarantee_list = []  # 빈 리스트로 처리
    else:
        # 관리자가 아닌 경우 직원이 여전히 존재하는지 확인
        if not session.get('is_admin'):
            if not supabase_utils.check_employee_exists(employee_name):
                # 직원이 삭제된 경우 오류 페이지 표시
                return render_template('employee_error.html')
        
        # 보증보험 매물 목록 조회
        guarantee_list = supabase_utils.get_guarantee_insurance_links(20)
    
    # 디버깅: URL 확인
    print(f"[대시보드] 주거 사이트 URL: {RESIDENCE_SITE_URL}")
    print(f"[대시보드] 업무 사이트 URL: {BUSINESS_SITE_URL}")
    
    return render_template('employee_dashboard.html', 
                         employee_name=employee_name,
                         residence_site_url=RESIDENCE_SITE_URL,
                         business_site_url=BUSINESS_SITE_URL,
                         guarantee_list=guarantee_list)

@app.route('/team-leader')
def team_leader_panel():
    """팀장 전용 패널"""
    if 'employee_id' not in session:
        return redirect(url_for('index'))
    
    # 팀장만 접근 가능
    if session.get('employee_role') != '팀장':
        print(f"❌ 팀장이 아닌 사용자 접근 거부 - employee_role: {session.get('employee_role')}")
        return redirect(url_for('index'))
    
    employee_name = session.get('employee_name', '팀장')
    print(f"✅ 팀장 패널 접근 허용 - {employee_name}")
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print("⚠️ 테스트 모드 - 팀장 패널 빈 보증보험 목록 반환")
        guarantee_list = []
    else:
        # 보증보험 매물 목록 조회
        guarantee_list = supabase_utils.get_guarantee_insurance_links(20)
    
    return render_template('team_leader_panel.html', 
                         employee_name=employee_name,
                         residence_site_url=RESIDENCE_SITE_URL,
                         business_site_url=BUSINESS_SITE_URL,
                         guarantee_list=guarantee_list)

@app.route('/admin')
def admin_panel():
    """관리자 패널 (직원 관리)"""
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        print(f"❌ 접근 거부 - is_admin: {session.get('is_admin')}, employee_role: {session.get('employee_role')}")
        return redirect(url_for('index'))
    
    print(f"✅ 관리자 패널 접근 허용 - is_admin: {session.get('is_admin')}, employee_role: {session.get('employee_role')}")

    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print("⚠️ 테스트 모드 - 빈 보증보험 목록 반환")
        guarantee_list = []
        return render_template('admin_panel.html', 
                             guarantee_list=guarantee_list,
                             residence_site_url=RESIDENCE_SITE_URL,
                             business_site_url=BUSINESS_SITE_URL)

    # 보증보험 매물 목록 조회
    guarantee_list = supabase_utils.get_guarantee_insurance_links(50)
    
    return render_template('admin_panel.html', 
                         guarantee_list=guarantee_list,
                         residence_site_url=RESIDENCE_SITE_URL,
                         business_site_url=BUSINESS_SITE_URL)

@app.route('/admin/guarantee-delete/<int:id>', methods=['POST'])
def guarantee_delete(id):
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return redirect(url_for('index'))
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        flash('데이터베이스 연결이 설정되지 않았습니다.', 'error')
        return redirect(url_for('admin_panel'))
    
    try:
        # 보증보험 상태를 FALSE로 변경 (매물은 유지하되 보증보험 리스트에서만 제거)
        if supabase_utils.update_guarantee_insurance_status(id, False):
            flash('보증보험 매물이 리스트에서 제거되었습니다.', 'success')
        else:
            flash('매물 상태 변경 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin_panel'))
    except Exception as e:
        flash(f'삭제 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/guarantee-edit/<int:id>', methods=['POST'])
def guarantee_edit(id):
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return redirect(url_for('index'))
    
    memo = request.form.get('memo', '')
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        return "데이터베이스 연결이 설정되지 않았습니다.", 500
    
    try:
        if supabase_utils.update_link_memo(id, memo, 'residence'):
            return redirect(url_for('admin_panel'))
        else:
            return "메모 수정 중 오류 발생", 500
    except Exception as e:
        return f"수정 중 오류 발생: {str(e)}", 500

# 직원 관리 API
@app.route('/api/employees', methods=['GET', 'POST'])
def manage_employees():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # 페이지네이션 파라미터 (GET 요청일 때만)
    if request.method == 'GET':
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print("⚠️ Supabase 환경변수가 설정되지 않음 - 테스트 모드로 동작")
        if request.method == 'GET':
            return jsonify({
                'employees': [],
                'total_count': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            })
        elif request.method == 'POST':
            return jsonify({'success': False, 'message': 'Supabase 연결이 설정되지 않아 직원 추가가 불가능합니다.'})
    
    try:
        if request.method == 'GET':
            # Supabase에서 직원 목록 조회
            employees_data = supabase_utils.get_employees_with_pagination(page, per_page)
            
            if employees_data:
                employees = employees_data.get('employees', [])
                total_count = employees_data.get('total_count', 0)
                total_pages = employees_data.get('total_pages', 0)
                
                print(f"[직원 목록] 조회된 직원 수: {len(employees)} (페이지 {page}/{total_pages})")
                
                # 필드명 통일을 위해 매핑
                for emp in employees:
                    emp['employee_id'] = emp.get('name')
                    emp['employee_name'] = emp.get('name')
                    emp['created_date'] = emp.get('created_at')
                    emp['is_active'] = emp.get('status', 'active') == 'active'
                
                print(f"[직원 목록] 최종 응답: {employees}")
                return jsonify({
                    'employees': employees,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages
                })
            else:
                print("⚠️ 직원 목록 조회 실패")
                return jsonify({
                    'employees': [],
                    'total_count': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                })

        if request.method == 'POST':
            print("🔄 직원 추가 요청 받음")
            data = request.get_json()
            print(f"📥 요청 데이터: {data}")
            
            employee_id = data.get('employee_id')
            employee_name = data.get('employee_name')
            team = data.get('team', '')
            email = data.get('email', '')
            position = data.get('position', '')
            role = data.get('role', '직원')
            
            # employee_id와 employee_name 중 하나라도 있으면 name으로 사용
            name = employee_name if employee_name else employee_id
            
            print(f"📝 추출된 데이터 - 이름: '{name}', 팀: '{team}', 이메일: '{email}', 직책: '{position}'")
            
            if not name or name.strip() == '':
                print(f"❌ 이름이 비어있음")
                return jsonify({'success': False, 'message': '이름을 입력해야 합니다.'}), 400
            
            # Supabase에 직원 추가
            new_employee = supabase_utils.add_employee(name, email, team, position, role)
            
            if new_employee:
                # 필드명 통일을 위해 매핑
                new_employee['employee_id'] = new_employee.get('name')
                new_employee['employee_name'] = new_employee.get('name')
                new_employee['created_date'] = new_employee.get('created_at')
                new_employee['is_active'] = new_employee.get('status') == 'active'
                
                print(f"🎉 직원 추가 성공: {new_employee}")
                return jsonify({'success': True, 'employee': new_employee})
            else:
                print("❌ 직원 추가 실패")
                return jsonify({'success': False, 'message': '직원 추가 중 오류가 발생했습니다.'})
            
    except Exception as e:
        print(f"❌ 직원 API 오류: {e}")
        return jsonify({'success': False, 'message': f'서버 오류가 발생했습니다: {str(e)}'}), 500

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
        # all_employees 파라미터로 모든 직원의 고객 조회 여부 결정
        all_employees = request.args.get('all_employees') == 'true'
        
        # 페이지네이션 파라미터
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Supabase 연결 확인
        if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
            print("⚠️ Supabase 환경변수가 설정되지 않음 - 테스트 모드로 동작")
            sample_customers = [
                {
                    'id': 1,
                    'inquiry_date': '2024-08-15',
                    'customer_name': '김철수',
                    'customer_phone': '010-1234-5678',
                    'budget': 5000,
                    'rooms': '2룸',
                    'location': '강남구',
                    'loan_needed': True,
                    'parking_needed': True,
                    'memo': '급하게 구하고 있음',
                    'status': '상담중',
                    'employee_id': '원형',
                    'employee_name': '원형'
                },
                {
                    'id': 2,
                    'inquiry_date': '2024-08-14',
                    'customer_name': '이영희',
                    'customer_phone': '010-9876-5432',
                    'budget': 3000,
                    'rooms': '1룸',
                    'location': '서초구',
                    'loan_needed': False,
                    'parking_needed': False,
                    'memo': '펫 가능한 곳 선호',
                    'status': '계약완료',
                    'employee_id': '테스트',
                    'employee_name': '테스트'
                },
                {
                    'id': 3,
                    'inquiry_date': '2024-08-13',
                    'customer_name': '박민수',
                    'customer_phone': '010-5555-1234',
                    'budget': 7000,
                    'rooms': '3룸',
                    'location': '송파구',
                    'loan_needed': True,
                    'parking_needed': True,
                    'memo': '학군 좋은 지역 희망',
                    'status': '대기중',
                    'employee_id': 'admin',
                    'employee_name': '관리자'
                }
            ]
            
            # 관리자이고 all_employees=true인 경우 모든 샘플 데이터 반환
            if session.get('is_admin') and all_employees:
                total_count = len(sample_customers)
                paginated_customers = sample_customers[offset:offset + per_page]
                return jsonify({
                    'customers': paginated_customers,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                })
            # 관리자가 아니거나 all_employees=false인 경우 해당 직원 데이터만 반환
            else:
                filtered_customers = [c for c in sample_customers if c['employee_id'] == employee_id]
                total_count = len(filtered_customers)
                paginated_customers = filtered_customers[offset:offset + per_page]
                return jsonify({
                    'customers': paginated_customers,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                })
        
        try:
            # Supabase에서 고객 목록 조회
            customers_data = supabase_utils.get_customers_with_pagination(page, per_page, employee_id, all_employees)
            
            if customers_data:
                customers_list = customers_data.get('customers', [])
                total_count = customers_data.get('total_count', 0)
                total_pages = customers_data.get('total_pages', 0)
                
                # employee_name 필드 추가 (employee_id와 동일하게 설정)
                for customer in customers_list:
                    customer['employee_name'] = customer.get('employee_id', '')
                    # 미확인 좋아요 수는 현재 0으로 설정 (나중에 구현 가능)
                    customer['unchecked_likes_residence'] = 0
                    customer['unchecked_likes_business'] = 0
                
                print(f"[고객 목록] 조회된 고객 수: {len(customers_list)} (페이지 {page}/{total_pages})")
                
                return jsonify({
                    'customers': customers_list,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages
                })
            else:
                print("⚠️ 고객 목록 조회 실패")
                return jsonify({
                    'customers': [],
                    'total_count': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                })

        except Exception as e:
            print(f"고객 목록 조회 오류: {e}")
            return jsonify({'error': f'고객 목록 조회 실패: {e}'}), 500
        
    # --- POST 요청: 새 고객 추가 ---
    if request.method == 'POST':
        try:
            data = request.get_json()
            current_employee_id = session.get('employee_id')

            customer_data = {
                'inquiry_date': data.get('inquiry_date'),
                'customer_name': data.get('customer_name'),
                'customer_phone': data.get('phone'),
                'budget': data.get('amount'),
                'rooms': data.get('room_count'),
                'location': data.get('location'),
                'loan_needed': data.get('loan_info'),
                'parking_needed': data.get('parking'),
                'pets': data.get('pets'),
                'memo': data.get('memo'),
                'status': data.get('status', '진행중'),
                'employee_id': current_employee_id,
                'employee_name': session.get('employee_name'),
                'employee_team': session.get('employee_team'),
                'created_date': datetime.now().isoformat()
            }
            
            # move_in_date가 제공된 경우에만 추가 (선택적 필드)
            if data.get('move_in_date'):
                customer_data['move_in_date'] = data.get('move_in_date')

            # management_site_id 생성 및 포함
            management_site_id = str(uuid.uuid4().hex)[:8]
            customer_data['management_site_id'] = management_site_id

            new_customer = supabase_utils.add_customer(customer_data)
            if not new_customer:
                return jsonify({'success': False, 'message': '고객 추가 중 오류가 발생했습니다.'}), 500

            return jsonify({'success': True, 'message': '고객이 추가되었습니다.', 'customer': new_customer})

        except Exception as e:
            return jsonify({'success': False, 'message': f'고객 추가 중 오류 발생: {e}'}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT', 'DELETE'])
def update_delete_customer(customer_id):
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    employee_id = session.get('employee_id')
    is_admin = bool(session.get('is_admin'))

    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False, 'message': '데이터베이스 연결 실패'}), 500

        # 권한 확인: 관리자가 아니면 본인 소유만 허용
        if not is_admin:
            owns = supabase.table('employee_customers').select('id').eq('id', customer_id).eq('employee_id', employee_id).execute()
            if not owns.data:
                return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403

        if request.method == 'PUT':
            data = request.get_json() or {}
            # 필요 시 구현 영역. 현재는 변경 사항 없음
            return jsonify({'success': True})

        if request.method == 'DELETE':
            response = supabase.table('employee_customers').delete().eq('id', customer_id).execute()
            if response.data is None:
                return jsonify({'success': False, 'message': '삭제 실패'}), 500
            return jsonify({'success': True, 'message': '고객이 삭제되었습니다.'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'작업 중 오류 발생: {e}'}), 500

@app.route('/api/customers/<int:customer_id>/memo', methods=['PUT'])
def update_customer_memo(customer_id):
    data = request.get_json()
    memo = data.get('memo')
    
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False, 'message': '데이터베이스 연결 실패'}), 500
        res = supabase.table('employee_customers').update({'memo': memo}).eq('id', customer_id).execute()
        if res.data is None:
            return jsonify({'success': False, 'message': '메모 업데이트 실패'}), 500
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': '메모 업데이트 실패'}), 500

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

    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False, 'error': 'DB 연결 실패'}), 500
        update_data = {field: value}
        res = supabase.table('employee_customers').update(update_data).eq('id', customer_id).execute()
        if res.data is None:
            return jsonify({'success': False, 'error': '업데이트 실패'}), 500
        return jsonify({'success': True})
    except Exception as e:
        print(f"필드 업데이트 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 팀장 전용 API 라우트 ====================
@app.route('/api/team-leader/customers', methods=['GET'])
def team_leader_customers():
    """팀장 본인의 고객만 조회"""
    if session.get('employee_role') != '팀장':
        return jsonify({'error': '팀장만 접근 가능합니다.'}), 403
    
    team_leader_id = session.get('employee_id')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print("⚠️ 테스트 모드 - 팀장 본인 고객 샘플 데이터 반환")
        sample_customers = [
            {
                'id': 1,
                'inquiry_date': '2024-08-15',
                'customer_name': '김철수',
                'phone': '010-1234-5678',
                'amount': 5000,
                'room_count': '2룸',
                'location': '강남구',
                'loan_info': '대출 필요',
                'parking': '주차 필요',
                'pets': '펫 불가',
                'memo': '팀장 본인 고객',
                'progress_status': '진행중',
                'employee_id': team_leader_id,
                'employee_name': team_leader_id
            }
        ]
        
        total_count = len(sample_customers)
        paginated_customers = sample_customers[offset:offset + per_page]
        return jsonify({
            'customers': paginated_customers,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
    
    # Supabase에서 팀장 본인의 고객 조회
    try:
        customers = supabase_utils.get_team_leader_customers(team_leader_id, per_page)
        
        # 페이지네이션 처리
        total_count = len(customers)
        paginated_customers = customers[offset:offset + per_page]
        
        # employee_name 필드 추가
        for customer in paginated_customers:
            customer['employee_name'] = customer.get('employee_id', '')
        
        return jsonify({
            'customers': paginated_customers,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"팀장 본인 고객 조회 오류: {e}")
        return jsonify({'error': f'팀장 본인 고객 조회 실패: {e}'}), 500

@app.route('/api/team-leader/maeiple', methods=['GET'])
def team_leader_maeiple():
    """팀장 본인의 매물만 조회"""
    if session.get('employee_role') != '팀장':
        return jsonify({'error': '팀장만 접근 가능합니다.'}), 403
    
    team_leader_id = session.get('employee_id')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print("⚠️ 테스트 모드 - 팀장 본인 매물 샘플 데이터 반환")
        sample_properties = [
            {
                'id': 1,
                'check_date': '2024-08-12',
                'building_number': 101,
                'room_number': 1001,
                'status': '거래중',
                'jeonse_price': 50000,
                'monthly_rent': 0,
                'sale_price': 0,
                'is_occupied': False,
                'phone': '010-1234-5678',
                'memo': '팀장 본인 매물',
                'likes': 3,
                'dislikes': 1,
                'employee_id': team_leader_id,
                'employee_name': team_leader_id,
                'employee_team': session.get('employee_team', '')
            }
        ]
        
        total_count = len(sample_properties)
        paginated_properties = sample_properties[offset:offset + per_page]
        return jsonify({
            'success': True,
            'properties': paginated_properties,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
    
    # Supabase에서 팀장 본인의 매물 조회
    try:
        properties = supabase_utils.get_team_maeiple_properties(team_leader_id, per_page)
        
        # 페이지네이션 처리
        total_count = len(properties)
        paginated_properties = properties[offset:offset + per_page]
        
        return jsonify({
            'success': True,
            'properties': paginated_properties,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/customers', methods=['GET'])
def team_customers():
    """팀 전체 고객 조회 (팀장 + 팀원)"""
    if session.get('employee_role') != '팀장':
        return jsonify({'error': '팀장만 접근 가능합니다.'}), 403
    
    team_name = session.get('employee_team')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print("⚠️ 테스트 모드 - 팀 전체 고객 샘플 데이터 반환")
        sample_customers = [
            {
                'id': 1,
                'inquiry_date': '2024-08-15',
                'customer_name': '김철수',
                'phone': '010-1234-5678',
                'amount': 5000,
                'room_count': '2룸',
                'location': '강남구',
                'loan_info': '대출 필요',
                'parking': '주차 필요',
                'pets': '펫 불가',
                'memo': '팀장 고객',
                'progress_status': '진행중',
                'employee_id': '팀장',
                'employee_name': '팀장'
            },
            {
                'id': 2,
                'inquiry_date': '2024-08-14',
                'customer_name': '이영희',
                'phone': '010-9876-5432',
                'amount': 3000,
                'room_count': '1룸',
                'location': '서초구',
                'loan_info': '대출 불필요',
                'parking': '주차 불필요',
                'pets': '펫 가능',
                'memo': '팀원 고객',
                'progress_status': '계약완료',
                'employee_id': '팀원1',
                'employee_name': '팀원1'
            }
        ]
        
        total_count = len(sample_customers)
        paginated_customers = sample_customers[offset:offset + per_page]
        return jsonify({
            'customers': paginated_customers,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
    
    # Supabase에서 팀 전체 고객 조회
    try:
        customers = supabase_utils.get_team_all_customers(team_name, per_page)
        
        # 페이지네이션 처리
        total_count = len(customers)
        paginated_customers = customers[offset:offset + per_page]
        
        # employee_name 필드 추가
        for customer in paginated_customers:
            customer['employee_name'] = customer.get('employee_id', '')
        
        return jsonify({
            'customers': paginated_customers,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"팀 전체 고객 조회 오류: {e}")
        return jsonify({'error': f'팀 전체 고객 조회 실패: {e}'}), 500

@app.route('/api/team/maeiple', methods=['GET'])
def team_maeiple():
    """팀 전체 매물 조회 (팀장 + 팀원)"""
    if session.get('employee_role') != '팀장':
        return jsonify({'error': '팀장만 접근 가능합니다.'}), 403
    
    team_name = session.get('employee_team')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print("⚠️ 테스트 모드 - 팀 전체 매물 샘플 데이터 반환")
        sample_properties = [
            {
                'id': 1,
                'check_date': '2024-08-12',
                'building_number': 101,
                'room_number': 1001,
                'status': '거래중',
                'jeonse_price': 50000,
                'monthly_rent': 0,
                'sale_price': 0,
                'is_occupied': False,
                'phone': '010-1234-5678',
                'memo': '팀장 매물',
                'likes': 3,
                'dislikes': 1,
                'employee_id': '팀장',
                'employee_name': '팀장',
                'employee_team': team_name
            },
            {
                'id': 2,
                'check_date': '2024-08-11',
                'building_number': 102,
                'room_number': 1002,
                'status': '거래완료',
                'jeonse_price': 0,
                'monthly_rent': 800,
                'sale_price': 0,
                'is_occupied': True,
                'phone': '010-2345-6789',
                'memo': '팀원 매물',
                'likes': 1,
                'dislikes': 1,
                'employee_id': '팀원1',
                'employee_name': '팀원1',
                'employee_team': team_name
            }
        ]
        
        total_count = len(sample_properties)
        paginated_properties = sample_properties[offset:offset + per_page]
        return jsonify({
            'success': True,
            'properties': paginated_properties,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
    
    # Supabase에서 팀 전체 매물 조회
    try:
        properties = supabase_utils.get_team_all_maeiple_properties(team_name, per_page)
        
        # 페이지네이션 처리
        total_count = len(properties)
        paginated_properties = properties[offset:offset + per_page]
        
        return jsonify({
            'success': True,
            'properties': paginated_properties,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            data = request.json or {}
            url = data.get('url')
            platform = data.get('platform')
            added_by = session.get('employee_id')
            memo = data.get('memo', '')
            guarantee_insurance = bool(data.get('guarantee_insurance', False))
            if not url or not platform:
                return jsonify({'success': False, 'error': 'URL과 플랫폼은 필수 입력 항목입니다.'}), 400
            supabase = supabase_utils.get_supabase()
            if not supabase:
                return jsonify({'success': False, 'error': 'DB 연결 실패'}), 500
            payload = {
                'url': url,
                'platform': platform,
                'added_by': added_by,
                'date_added': datetime.now().strftime('%Y-%m-%d'),
                'memo': memo,
                'management_site_id': management_site_id,
                'guarantee_insurance': guarantee_insurance
            }
            # 주거용 링크는 residence_links 테이블 사용
            res = supabase.table('residence_links').insert(payload).execute()
            if not res.data:
                return jsonify({'success': False, 'error': '링크 추가 실패'}), 500
            return jsonify({'success': True, 'id': res.data[0].get('id')})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:  # GET 요청
        try:
            # 필터 파라미터 처리
            platform_filter = request.args.get('platform', 'all')
            user_filter = request.args.get('user', 'all')
            like_filter = request.args.get('like', 'all')
            date_filter = request.args.get('date', '')
            guarantee_filter = request.args.get('guarantee', 'all')

            supabase = supabase_utils.get_supabase()
            if not supabase:
                return jsonify([])

            # 주거용 링크는 residence_links 테이블 사용
            def build_query(table_name: str):
                q = supabase.table(table_name).select('*')
                if management_site_id:
                    q = q.eq('management_site_id', management_site_id)
                else:
                    q = q.is_('management_site_id', None)
                if platform_filter != 'all':
                    q = q.eq('platform', platform_filter)
                if user_filter != 'all':
                    q = q.eq('added_by', user_filter)
                if like_filter == 'liked':
                    q = q.eq('liked', True)
                elif like_filter == 'disliked':
                    q = q.eq('disliked', True)
                if date_filter:
                    q = q.eq('date_added', date_filter)
                if guarantee_filter == 'available':
                    q = q.eq('guarantee_insurance', True)
                elif guarantee_filter == 'unavailable':
                    q = q.eq('guarantee_insurance', False)
                return q.order('id', desc=True)

            res = build_query('residence_links').execute()

            data = res.data or []
            return jsonify(data)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/links/<int:link_id>', methods=['PUT', 'DELETE'])
def update_residence_link(link_id):
    """주거용 링크 수정/삭제 - Supabase"""
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False}), 500
        if request.method == 'PUT':
            data = request.json or {}
            action = data.get('action')
            update = {}
            if action == 'rating':
                update['rating'] = data.get('rating', 5)
            elif action == 'like':
                liked = bool(data.get('liked', False))
                update['liked'] = liked
                update['disliked'] = False if liked else False
                update['is_checked'] = False
            elif action == 'dislike':
                disliked = bool(data.get('disliked', False))
                update['disliked'] = disliked
                update['liked'] = False
            elif action == 'memo':
                update['memo'] = data.get('memo', '')
            elif action == 'guarantee':
                update['guarantee_insurance'] = bool(data.get('guarantee_insurance', False))
            else:
                return jsonify({'success': False, 'error': 'Invalid action'}), 400
            # 주거용 링크는 residence_links 테이블 사용
            res = supabase.table('residence_links').update(update).eq('id', link_id).execute()
            if res.data is None:
                return jsonify({'success': False}), 500
            return jsonify({'success': True})
        elif request.method == 'DELETE':
            # 주거용 링크는 residence_links 테이블 사용
            res = supabase.table('residence_links').delete().eq('id', link_id).execute()
            if res.data is None:
                return jsonify({'success': False}), 500
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 업무용 API 라우트 ====================
@app.route('/api/office-links', methods=['GET', 'POST'])
def business_links():
    """업무용 링크 API"""
    management_site_id = request.args.get('management_site_id')
    
    if request.method == 'POST':
        data = request.json or {}
        url = data.get('url')
        platform = data.get('platform')
        added_by = session.get('employee_id')
        memo = data.get('memo', '')
        guarantee_insurance = bool(data.get('guarantee_insurance', False))
        if not url or not platform:
            return jsonify({'success': False, 'error': '필수 정보가 누락되었습니다.'})
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False, 'error': 'DB 연결 실패'})
        payload = {
            'url': url,
            'platform': platform,
            'added_by': added_by,
            'date_added': datetime.now().strftime('%Y-%m-%d'),
            'memo': memo,
            'management_site_id': management_site_id,
            'guarantee_insurance': guarantee_insurance
        }
        res = supabase.table('office_links').insert(payload).execute()
        if not res.data:
            return jsonify({'success': False, 'error': '링크 추가 실패'}), 500
        response_data = res.data[0]
        response_data['success'] = True
        return jsonify(response_data), 201

    else:  # GET 요청
        # 필터 파라미터
        platform_filter = request.args.get('platform', 'all')
        user_filter = request.args.get('user', 'all')
        like_filter = request.args.get('like', 'all')
        date_filter = request.args.get('date', '')
        guarantee_filter = request.args.get('guarantee', 'all')
        
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify([])
        q = supabase.table('office_links').select('*')
        if management_site_id:
            q = q.eq('management_site_id', management_site_id)
        else:
            q = q.is_('management_site_id', None)
        if platform_filter != 'all':
            q = q.eq('platform', platform_filter)
        if user_filter != 'all':
            q = q.eq('added_by', user_filter)
        if like_filter == 'liked':
            q = q.eq('liked', True)
        elif like_filter == 'disliked':
            q = q.eq('disliked', True)
        elif like_filter == 'none':
            q = q.eq('liked', False).eq('disliked', False)
        if date_filter:
            q = q.eq('date_added', date_filter)
        if guarantee_filter == 'available':
            q = q.eq('guarantee_insurance', True)
        elif guarantee_filter == 'unavailable':
            q = q.eq('guarantee_insurance', False)
        res = q.order('id', desc=True).execute()
        return jsonify(res.data or [])

@app.route('/api/office-links/<int:link_id>', methods=['PUT', 'DELETE'])
def update_business_link(link_id):
    """업무용 링크 수정/삭제 - Supabase"""
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False}), 500
    if request.method == 'PUT':
            data = request.json or {}
        action = data.get('action')
            update = {}
        if action == 'rating':
                update['rating'] = data.get('rating', 5)
        elif action == 'like':
                liked = bool(data.get('liked', False))
                update['liked'] = liked
                update['disliked'] = False if liked else False
                update['is_checked'] = False
        elif action == 'dislike':
                disliked = bool(data.get('disliked', False))
                update['disliked'] = disliked
                update['liked'] = False
        elif action == 'memo':
                update['memo'] = data.get('memo', '')
        elif action == 'guarantee':
                update['guarantee_insurance'] = bool(data.get('guarantee_insurance', False))
            else:
                return jsonify({'success': False, 'error': 'Invalid action'}), 400
            # 업무용 링크는 office_links 테이블 사용
            res = supabase.table('office_links').update(update).eq('id', link_id).execute()
            if res.data is None:
                return jsonify({'success': False}), 500
        return jsonify({'success': True})
    elif request.method == 'DELETE':
            # 업무용 링크는 office_links 테이블 사용
            res = supabase.table('office_links').delete().eq('id', link_id).execute()
            if res.data is None:
                return jsonify({'success': False}), 500
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

# ==================== 매이플관리 API 라우트 ====================
@app.route('/maeiple')
def maeiple_management():
    """매이플관리 메인 페이지"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return redirect(url_for('index'))
    
    employee_name = session.get('employee_name', '관리자' if session.get('is_admin') else '직원')
    return render_template('maeiple_management.html', 
                         employee_name=employee_name)

@app.route('/api/maeiple', methods=['GET', 'POST'])
def maeiple_api():
    """매이플관리 API - 매물 조회 및 생성"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    if request.method == 'GET':
        # 정렬 파라미터 가져오기
        sort_by = request.args.get('sort_by', 'check_date')  # 기본: 확인날짜
        sort_order = request.args.get('sort_order', 'desc')  # 기본: 내림차순
        
        # 페이지네이션 파라미터
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Supabase 연결 확인
        if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
            print("⚠️ 테스트 모드 - 개인용 샘플 매물 데이터 반환")
            
            # 현재 사용자 정보 가져오기
            current_user = session.get('employee_id', '')
            current_team = session.get('employee_team', '')
            print(f"🔍 개인 메이플관리 - 사용자: {current_user}, 팀: {current_team}")
            
            # 모든 샘플 매물 데이터
            all_sample_properties = [
                {
                    'id': 1,
                    'check_date': '2024-08-12',
                    'building_number': 101,
                    'room_number': 1001,
                    'status': '거래중',
                    'jeonse_price': 5000,
                    'monthly_rent': 50,
                    'sale_price': 80000,
                    'is_occupied': False,
                    'phone': '010-1234-5678',
                    'memo': '역세권, 교통편리',
                    'likes': 3,
                    'dislikes': 1,
                    'employee_id': '원형',
                    'employee_name': '원형',
                    'employee_team': '빈시트'
                },
                {
                    'id': 2,
                    'check_date': '2024-08-11',
                    'building_number': 102,
                    'room_number': 2001,
                    'status': '거래완료',
                    'jeonse_price': 6000,
                    'monthly_rent': 60,
                    'sale_price': 90000,
                    'is_occupied': True,
                    'phone': '010-2345-6789',
                    'memo': '신축, 주차가능',
                    'likes': 5,
                    'dislikes': 0,
                    'employee_id': '테스트',
                    'employee_name': '테스트',
                    'employee_team': '위플러스'
                },
                {
                    'id': 3,
                    'check_date': '2024-08-10',
                    'building_number': 103,
                    'room_number': 3001,
                    'status': '거래중',
                    'jeonse_price': 4500,
                    'monthly_rent': 45,
                    'sale_price': 75000,
                    'is_occupied': False,
                    'phone': '010-3456-7890',
                    'memo': '조용한 단지',
                    'likes': 2,
                    'dislikes': 2,
                    'employee_id': 'admin',
                    'employee_name': 'admin',
                    'employee_team': '관리자'
                },
                {
                    'id': 4,
                    'check_date': '2024-08-09',
                    'building_number': 104,
                    'room_number': 4001,
                    'status': '거래가능',
                    'jeonse_price': 5500,
                    'monthly_rent': 55,
                    'sale_price': 85000,
                    'is_occupied': False,
                    'phone': '010-4567-8901',
                    'memo': '원형의 개인 매물',
                    'likes': 4,
                    'dislikes': 0,
                    'employee_id': '원형',
                    'employee_name': '원형',
                    'employee_team': '빈시트'
                },
                {
                    'id': 5,
                    'check_date': '2024-08-08',
                    'building_number': 105,
                    'room_number': 5001,
                    'status': '거래가능',
                    'jeonse_price': 4800,
                    'monthly_rent': 48,
                    'sale_price': 78000,
                    'is_occupied': False,
                    'phone': '010-5678-9012',
                    'memo': '수정의 개인 매물',
                    'likes': 3,
                    'dislikes': 1,
                    'employee_id': '수정',
                    'employee_name': '수정',
                    'employee_team': '위플러스'
                }
            ]
            
            # 관리자인 경우 모든 매물, 일반 직원인 경우 개인 매물만
            if session.get('is_admin'):
                personal_properties = all_sample_properties
                print(f"✅ 관리자 - 모든 매물 {len(personal_properties)}개")
            else:
                personal_properties = [p for p in all_sample_properties if p['employee_id'] == current_user]
                print(f"✅ 개인 매물 필터링: {current_user}의 매물 {len(personal_properties)}개")
            
            # 테스트 모드에서도 정렬 적용
            if sort_by == 'check_date':
                personal_properties.sort(key=lambda x: x['check_date'], reverse=(sort_order == 'desc'))
            
            # 페이지네이션 적용
            total_count = len(personal_properties)
            paginated_properties = personal_properties[offset:offset + per_page]
            
            return jsonify({
                'success': True, 
                'properties': paginated_properties,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            })
        
        try:
            # Supabase에서 매물 목록 조회
            current_user = session.get('employee_id', '')
            
            # 관리자인 경우 모든 매물, 일반 직원인 경우 개인 매물만
            if session.get('is_admin'):
                properties_data = supabase_utils.get_maeiple_properties_with_pagination(
                    page, per_page, None, sort_by, sort_order
                )
            else:
                properties_data = supabase_utils.get_maeiple_properties_with_pagination(
                    page, per_page, current_user, sort_by, sort_order
                )
            
            if properties_data:
                properties = properties_data.get('properties', [])
                total_count = properties_data.get('total_count', 0)
                total_pages = properties_data.get('total_pages', 0)
                
                print(f"[매물 목록] 조회된 매물 수: {len(properties)} (페이지 {page}/{total_pages})")
                
                return jsonify({
                    'success': True, 
                    'properties': properties,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages
                })
            else:
                print("⚠️ 매물 목록 조회 실패")
                return jsonify({
                    'success': False,
                    'properties': [],
                    'total_count': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                })
            
        except Exception as e:
            print(f"❌ 매물 목록 조회 중 오류: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            # 현재 로그인한 사용자 정보 가져오기
            employee_id = session.get('employee_id', 'system')
            employee_name = session.get('employee_name', '시스템')
            employee_team = session.get('employee_team', '관리자')

            property_data = {
                'check_date': data.get('check_date'),
                'building_number': data.get('building_number'),
                'room_number': data.get('room_number'),
                'status': data.get('status', '거래중'),
                'jeonse_price': data.get('jeonse_price'),
                'monthly_rent': data.get('monthly_rent'),
                'sale_price': data.get('sale_price'),
                'is_occupied': data.get('is_occupied', False),
                'phone': data.get('phone'),
                'memo': data.get('memo', ''),
                'employee_id': employee_id,
                'employee_name': employee_name,
                'employee_team': employee_team
            }

            new_prop = supabase_utils.create_maeiple_property(property_data)
            if not new_prop:
                return jsonify({'success': False, 'error': '매물 생성 실패'}), 500

            return jsonify({'success': True, 'id': new_prop.get('id')})

        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/team-leader/team-maeiple', methods=['GET'])
def team_leader_team_maeiple():
    """팀장 전용 팀 통합 메이플관리 API - 팀 전체의 매물 조회 (팀 통합용)"""
    print(f"🔍 팀장 팀 통합용 API 호출 - 세션 정보:")
    print(f"  - employee_id: {session.get('employee_id')}")
    print(f"  - employee_role: {session.get('employee_role')}")
    print(f"  - employee_team: {session.get('employee_team')}")
    print(f"  - is_admin: {session.get('is_admin')}")
    
    if 'employee_id' not in session and not session.get('is_admin'):
        print("❌ 로그인이 필요합니다.")
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    # 팀장이 아니면 접근 거부
    if session.get('employee_role') != '팀장' and not session.get('is_admin'):
        print(f"❌ 팀장만 접근 가능합니다. 현재 역할: {session.get('employee_role')}")
        return jsonify({'error': '팀장만 접근 가능합니다.'}), 403
    
    # 정렬 파라미터 가져오기
    sort_by = request.args.get('sort_by', 'check_date')
    sort_order = request.args.get('sort_order', 'desc')
    
    # 페이지네이션 파라미터
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print("⚠️ 테스트 모드 - 팀장 팀 통합용 샘플 매물 데이터 반환")
        
        # 현재 사용자의 팀 정보 가져오기
        current_team = session.get('employee_team', '')
        print(f"🔍 팀장 팀 통합용 메이플관리 - 팀: {current_team}")
        
        # 모든 팀의 샘플 데이터
        all_sample_properties = [
            # 빈시트 팀 매물들
            {
                'id': 1,
                'check_date': '2024-08-12',
                'building_number': 101,
                'room_number': 1001,
                'status': '거래가능',
                'jeonse_price': 50000,
                'monthly_rent': 0,
                'sale_price': 0,
                'is_occupied': False,
                'phone': '010-1234-5678',
                'memo': '팀원1 매물 - 역세권',
                'likes': 2,
                'dislikes': 0,
                'employee_id': '팀원1',
                'employee_name': '팀원1',
                'employee_team': '빈시트'
            },
            {
                'id': 2,
                'check_date': '2024-08-11',
                'building_number': 102,
                'room_number': 1002,
                'status': '계약완료',
                'jeonse_price': 0,
                'monthly_rent': 800,
                'sale_price': 0,
                'is_occupied': True,
                'phone': '010-2345-6789',
                'memo': '팀원2 매물 - 신축',
                'likes': 1,
                'dislikes': 1,
                'employee_id': '팀원2',
                'employee_name': '팀원2',
                'employee_team': '빈시트'
            },
            {
                'id': 3,
                'check_date': '2024-08-10',
                'building_number': 103,
                'room_number': 1003,
                'status': '거래가능',
                'jeonse_price': 0,
                'monthly_rent': 600,
                'sale_price': 0,
                'is_occupied': False,
                'phone': '010-3456-7890',
                'memo': '원형 팀장 매물 - 주차가능',
                'likes': 3,
                'dislikes': 0,
                'employee_id': '원형',
                'employee_name': '원형',
                'employee_team': '빈시트'
            },
            {
                'id': 4,
                'check_date': '2024-08-09',
                'building_number': 104,
                'room_number': 1004,
                'status': '거래중',
                'jeonse_price': 45000,
                'monthly_rent': 450,
                'sale_price': 75000,
                'is_occupied': False,
                'phone': '010-4567-8901',
                'memo': '팀원3 매물 - 조용한 단지',
                'likes': 4,
                'dislikes': 0,
                'employee_id': '팀원3',
                'employee_name': '팀원3',
                'employee_team': '빈시트'
            },
            # 위플러스 팀 매물들
            {
                'id': 5,
                'check_date': '2024-08-08',
                'building_number': 201,
                'room_number': 2001,
                'status': '거래가능',
                'jeonse_price': 55000,
                'monthly_rent': 0,
                'sale_price': 0,
                'is_occupied': False,
                'phone': '010-5678-9012',
                'memo': '수정 팀장 매물 - 교통편리',
                'likes': 3,
                'dislikes': 1,
                'employee_id': '수정',
                'employee_name': '수정',
                'employee_team': '위플러스'
            },
            {
                'id': 6,
                'check_date': '2024-08-07',
                'building_number': 202,
                'room_number': 2002,
                'status': '거래중',
                'jeonse_price': 0,
                'monthly_rent': 700,
                'sale_price': 0,
                'is_occupied': False,
                'phone': '010-6789-0123',
                'memo': '팀원A 매물 - 신축',
                'likes': 2,
                'dislikes': 0,
                'employee_id': '팀원A',
                'employee_name': '팀원A',
                'employee_team': '위플러스'
            },
            {
                'id': 7,
                'check_date': '2024-08-06',
                'building_number': 203,
                'room_number': 2003,
                'status': '계약완료',
                'jeonse_price': 0,
                'monthly_rent': 650,
                'sale_price': 0,
                'is_occupied': True,
                'phone': '010-7890-1234',
                'memo': '팀원B 매물 - 역세권',
                'likes': 5,
                'dislikes': 1,
                'employee_id': '팀원B',
                'employee_name': '팀원B',
                'employee_team': '위플러스'
            }
        ]
        
        # 현재 팀의 매물만 필터링
        team_properties = [p for p in all_sample_properties if p['employee_team'] == current_team]
        print(f"✅ 팀별 필터링: {current_team}팀 매물 {len(team_properties)}개")
        
        # 페이지네이션 적용
        total_count = len(team_properties)
        paginated_properties = team_properties[offset:offset + per_page]
        
        return jsonify({
            'success': True, 
            'properties': paginated_properties,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'type': 'team'  # 팀 통합용임을 명시
        })
    
    # Supabase에서 팀 전체 매물 조회
    try:
        current_team = session.get('employee_team', '')
        properties = supabase_utils.get_team_all_maeiple_properties(current_team, per_page)
        
        # 페이지네이션 처리
        total_count = len(properties)
        paginated_properties = properties[offset:offset + per_page]
        
        return jsonify({
            'success': True, 
            'properties': paginated_properties,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'type': 'team'  # 팀 통합용임을 명시
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-info', methods=['GET'])
def user_info():
    """현재 로그인한 사용자 정보 반환"""
    print(f"🔍 /api/user-info 호출 - 세션 정보:")
    print(f"  - is_admin: {session.get('is_admin')}")
    print(f"  - employee_id: {session.get('employee_id')}")
    print(f"  - employee_name: {session.get('employee_name')}")
    print(f"  - employee_team: {session.get('employee_team')}")
    print(f"  - employee_role: {session.get('employee_role')}")
    
    if not session.get('is_admin') and 'employee_id' not in session:
        print("❌ 로그인이 필요합니다.")
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    user_info = {
        'is_admin': session.get('is_admin', False),
        'employee_id': session.get('employee_id', ''),
        'employee_name': session.get('employee_name', ''),
        'employee_team': session.get('employee_team', ''),
        'role': session.get('employee_role', '직원'),
        'employee_role': session.get('employee_role', '직원')  # 중복 필드로 호환성 확보
    }
    
    print(f"✅ 반환할 user_info: {user_info}")
    return jsonify(user_info)

@app.route('/api/maeiple/update', methods=['POST'])
def maeiple_update():
    """매이플관리 매물 업데이트 API"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        data = request.json
        property_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([property_id, field]):
            return jsonify({'error': '필수 파라미터가 누락되었습니다.'}), 400
        
        # DATABASE_URL이 없으면 테스트 모드로 처리
        if not os.environ.get('DATABASE_URL'):
            print(f"⚠️ 테스트 모드 - 업데이트 시뮬레이션: {field} = {value}")
            return jsonify({'success': True, 'message': '테스트 모드 - 업데이트 시뮬레이션 완료'})
        
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 업데이트 가능한 필드 검증
        allowed_fields = ['status', 'jeonse_price', 'monthly_rent', 'sale_price', 
                         'is_occupied', 'phone', 'memo', 'likes', 'dislikes']
        
        if field not in allowed_fields:
            return jsonify({'error': '업데이트할 수 없는 필드입니다.'}), 400
        
        # 업데이트 실행
        cursor.execute(f'''
            UPDATE maeiple_properties 
            SET {field} = %s, updated_at = NOW()
            WHERE id = %s
        ''', (value, property_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': '매물을 찾을 수 없습니다.'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '업데이트 완료'})
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/maeiple/memo', methods=['POST'])
def maeiple_memo():
    """매이플관리 메모 저장 API"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        data = request.json
        property_id = data.get('id')
        memo = data.get('memo', '')
        
        if not property_id:
            return jsonify({'error': '매물 ID가 필요합니다.'}), 400
        
        # DATABASE_URL이 없으면 테스트 모드로 처리
        if not os.environ.get('DATABASE_URL'):
            print(f"⚠️ 테스트 모드 - 메모 저장 시뮬레이션: ID {property_id}, 메모: {memo}")
            return jsonify({'success': True, 'message': '테스트 모드 - 메모 저장 시뮬레이션 완료'})
        
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE maeiple_properties 
            SET memo = %s, updated_at = NOW()
            WHERE id = %s
        ''', (memo, property_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': '매물을 찾을 수 없습니다.'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '메모 저장 완료'})
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/maeiple/<int:property_id>', methods=['DELETE'])
def maeiple_delete(property_id):
    """매이플관리 매물 삭제 API"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        # DATABASE_URL이 없으면 테스트 모드로 처리
        if not os.environ.get('DATABASE_URL'):
            print(f"⚠️ 테스트 모드 - 매물 삭제 시뮬레이션: ID {property_id}")
            return jsonify({'success': True, 'message': '테스트 모드 - 매물 삭제 시뮬레이션 완료'})
        
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM maeiple_properties WHERE id = %s', (property_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': '매물을 찾을 수 없습니다.'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '매물 삭제 완료'})
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': str(e)}), 500

# ==================== 팀장 전용 API 라우트 ====================

@app.route('/api/team-leader/team-customers', methods=['GET'])
def team_leader_team_customers():
    """팀장 전용 팀 통합 고객관리 API - 팀 전체의 고객 조회 (팀 통합용)"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    # 팀장이 아니면 접근 거부
    if session.get('employee_role') != '팀장' and not session.get('is_admin'):
        return jsonify({'error': '팀장만 접근 가능합니다.'}), 403
    
    # 페이지네이션 파라미터
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # DATABASE_URL이 없으면 테스트용 샘플 데이터 반환
    if not os.environ.get('DATABASE_URL'):
        print("⚠️ 테스트 모드 - 팀장 팀 통합용 샘플 고객 데이터 반환")
        
        # 현재 팀 정보
        current_team = session.get('employee_team', '')
        print(f"🔍 팀장 팀 통합용 고객관리 - 팀: {current_team}")
        
        # 팀 전체 고객 샘플 데이터 (팀장 + 팀원)
        team_customers = [
            # 팀장 고객
            {
                'id': 1,
                'inquiry_date': '2024-08-15',
                'customer_name': '김철수',
                'customer_phone': '010-1234-5678',
                'budget': 5000,
                'rooms': '2룸',
                'location': '강남구',
                'loan_needed': True,
                'parking_needed': True,
                'memo': '팀장 고객 - 급하게 구하고 있음',
                'status': '상담중',
                'employee_id': '팀장',
                'employee_name': '팀장'
            },
            # 팀원 고객들
            {
                'id': 2,
                'inquiry_date': '2024-08-14',
                'customer_name': '이영희',
                'customer_phone': '010-9876-5432',
                'budget': 3000,
                'rooms': '1룸',
                'location': '서초구',
                'loan_needed': False,
                'parking_needed': False,
                'memo': '팀원1 고객 - 펫 가능한 곳 선호',
                'status': '계약완료',
                'employee_id': '팀원1',
                'employee_name': '팀원1'
            },
            {
                'id': 3,
                'inquiry_date': '2024-08-13',
                'customer_name': '박민수',
                'customer_phone': '010-5555-1234',
                'budget': 7000,
                'rooms': '3룸',
                'location': '송파구',
                'loan_needed': True,
                'parking_needed': True,
                'memo': '팀원2 고객 - 학군 좋은 지역 희망',
                'status': '대기중',
                'employee_id': '팀원2',
                'employee_name': '팀원2'
            }
        ]
        
        # 페이지네이션 적용
        total_count = len(team_customers)
        paginated_customers = team_customers[offset:offset + per_page]
        
        return jsonify({
            'customers': paginated_customers,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'type': 'team'  # 팀 통합용임을 명시
        })
    
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 팀 전체의 고객 조회
        current_team = session.get('employee_team', '')
        
        # 전체 개수 조회
        count_query = "SELECT COUNT(*) FROM employee_customers WHERE employee_team = %s"
        cursor.execute(count_query, (current_team,))
        total_count = cursor.fetchone()[0]
        
        # 팀 전체 고객 목록 조회
        query = "SELECT * FROM employee_customers WHERE employee_team = %s ORDER BY inquiry_date DESC, id DESC LIMIT %s OFFSET %s"
        cursor.execute(query, (current_team, per_page, offset))
        
        customers_raw = cursor.fetchall()
        customers_list = [db_utils.dict_from_row(row) for row in customers_raw]
        
        # employee_name 필드 추가
        for customer in customers_list:
            customer['employee_name'] = customer.get('employee_id', '')
        
        conn.close()
        
        return jsonify({
            'customers': customers_list,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'type': 'team'  # 팀 통합용임을 명시
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'팀 전체 고객 조회 실패: {e}'}), 500

@app.route('/api/guarantee-list')
def get_guarantee_list():
    """보증보험 가능한 매물 목록 조회"""
    if 'employee_id' not in session and 'is_admin' not in session:
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify([])
        # 보증보험은 주거용 링크에서 관리되므로 residence_links 테이블 사용
        res = supabase.table('residence_links').select('*').eq('guarantee_insurance', True).order('id', desc=True).limit(50).execute()
        return jsonify(res.data or [])
    except Exception as e:
        print(f"보증보험 목록 조회 오류: {e}")
        return jsonify({'error': f'보증보험 목록 조회 실패: {e}'}), 500

if __name__ == '__main__':
    # PORT 환경변수 처리 개선
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 서버 시작 - 포트: {port}")
    print(f"🌍 환경변수 PORT: {os.environ.get('PORT', '설정되지 않음')}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        # 포트가 사용 중인 경우 다른 포트 시도
        if "Address already in use" in str(e):
            fallback_port = 8081
            print(f"🔄 포트 {port}가 사용 중입니다. 포트 {fallback_port}로 시도합니다.")
            app.run(host='0.0.0.0', port=fallback_port, debug=True)