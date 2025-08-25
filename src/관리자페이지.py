from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import uuid
from datetime import datetime
import os
import sys
import requests
import time

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import supabase_utils
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 환경변수 검증
if not os.environ.get('SUPABASE_URL'):
    raise ValueError("SUPABASE_URL 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

if not os.environ.get('SUPABASE_KEY'):
    raise ValueError("SUPABASE_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

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

print(f"주거 사이트 URL: {RESIDENCE_SITE_URL}")
print(f"업무 사이트 URL: {BUSINESS_SITE_URL}")

# 테스트 모드 강제 활성화 (개발/테스트용)
FORCE_TEST_MODE = False  # False로 설정하여 실제 Supabase DB 사용
print(f"테스트 모드 강제 활성화: {FORCE_TEST_MODE}")

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')  # 세션용 비밀키

# 개발 환경에서 캐싱 방지 및 자동 리로드 설정
if app.debug:
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.jinja_env.auto_reload = True
    app.jinja_env.cache = None

# Supabase 초기화
try:
    supabase_utils.init_supabase()
    print("Supabase 초기화 성공")
except Exception as e:
    print(f"Supabase 초기화 실패: {e}")
    # 실패해도 앱은 계속 실행

@app.route('/health')
def health_check():
    """Railway health check endpoint"""
    return jsonify({'status': 'healthy', 'service': '관리자페이지'}), 200

@app.route('/')
def index():
    """메인 페이지 - 로그인 또는 직원 관리"""
    try:
        if 'is_admin' in session:
            return redirect(url_for('admin_panel'))
        elif 'employee_id' in session:
            # 팀장인 경우 팀장 대시보드로, 일반 직원인 경우 직원 대시보드로
            if session.get('employee_role') == '팀장':
                print(f" 팀장 '{session.get('employee_name')}' - 팀장 대시보드로 리다이렉트")
                return redirect(url_for('team_leader_dashboard'))  # 함수명 변경
            else:
                print(f" 직원 '{session.get('employee_name')}' - 직원 대시보드로 리다이렉트")
                return redirect(url_for('employee_dashboard'))
        return render_template('admin_main.html')
    except Exception as e:
        print(f"루트 경로 오류: {e}")
        import traceback
        traceback.print_exc()
        # 기본 응답 반환
        return jsonify({
            'status': 'ok',
            'message': 'Server is running',
            'error': str(e) if app.debug else 'Internal server error'
        }), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    """직원 로그인 (비밀번호 확인 포함)"""
    data = request.get_json()
    employee_id = data.get('employee_id')  # 실제로는 name으로 검색
    password = data.get('password')  # 비밀번호 확인
    
    print(f"[LOGIN DEBUG] 로그인 요청 데이터: {data}")
    print(f"[LOGIN DEBUG] 직원 로그인 시도: '{employee_id}', 비밀번호: '{password}'")  # 디버깅 로그
    
    if not employee_id or employee_id.strip() == '':
        return jsonify({'success': False, 'message': '직원 이름을 입력해주세요.'})
    
    if not password or password.strip() == '':
        return jsonify({'success': False, 'message': '비밀번호를 입력해주세요.'})
    
    # Supabase에서 직원 정보 조회
    try:
        employee = supabase_utils.get_employee_by_name(employee_id)
        
        if employee:
            # 블랙리스트 체크 (비활성화/삭제된 직원)
            if employee.get('status') == 'inactive':
                return jsonify({'success': False, 'message': '비활성화된 직원입니다. 관리자에게 문의하세요.'})
            
            # 비밀번호 검증
            stored_password = employee.get('password')
            if not stored_password:
                # 비밀번호가 설정되지 않은 경우 기본값 '1234' 사용
                stored_password = '1234'
            
            if password != stored_password:
                print(f" 비밀번호 불일치: 입력='{password}', 저장됨='{stored_password}'")
                return jsonify({'success': False, 'message': '직원 이름 또는 비밀번호가 올바르지 않습니다.'})
            
            # 비밀번호 검증 성공 - 로그인 처리
            session['employee_id'] = employee['id']
            session['employee_name'] = employee['name']
            session['employee_team'] = employee.get('team', '')
            session['employee_role'] = employee.get('role', 'employee')
            
            # 마지막 로그인 시간 업데이트
            supabase_utils.update_employee_last_login(employee['name'])
            
            print(f" 직원 로그인 성공: {employee['name']} ({employee.get('role', 'employee')})")
            print(f"  - 세션 employee_id: {session['employee_id']}")
            print(f"  - 세션 employee_name: {session['employee_name']}")
            print(f"  - 세션 employee_team: {session['employee_team']}")
            print(f"  - 세션 employee_role: {session['employee_role']}")
            
            return jsonify({
                'success': True, 
                'message': '로그인 성공',
                'redirect': '/team-leader' if employee.get('role') == '팀장' else '/dashboard',
                'role': employee.get('role', 'employee')
            })
        else:
            # 로그인 실패
            print(f" 로그인 실패: 비밀번호 불일치 또는 직원 정보 없음")
            return jsonify({'success': False, 'message': '직원 이름 또는 비밀번호가 올바르지 않습니다.'})
            
    except Exception as e:
        print(f" 데이터베이스 오류: {e}")
        return jsonify({'success': False, 'message': '로그인 중 오류가 발생했습니다.'})

@app.route('/admin-login', methods=['POST'])
def admin_login():
    """관리자 로그인"""
    data = request.get_json()
    admin_id = data.get('admin_id')
    admin_password = data.get('admin_password')
    
    ADMIN_ID = os.environ.get('ADMIN_ID', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'change-this-password')
    
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
    
    # 블랙리스트 체크 (비활성화/삭제된 직원)
    if 'employee_id' in session:
        employee_name = session.get('employee_name', '')
        if 'blacklisted_sessions' in session and employee_name in session['blacklisted_sessions']:
            session.clear()
            return redirect(url_for('index'))
    
    # 관리자가 대시보드에 접근하면 관리자 패널로 리다이렉트
    if session.get('is_admin'):
        return redirect(url_for('admin_panel'))
    
    employee_name = session.get('employee_name', '직원')
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print(" 테스트 모드 - 대시보드 접근 허용")
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
def team_leader_dashboard():  # 함수명 변경
    """팀장 전용 대시보드 (직원페이지 기반)"""
    if 'employee_id' not in session:
        return redirect(url_for('index'))
    
    # 블랙리스트 체크 (비활성화/삭제된 직원)
    employee_name = session.get('employee_name', '')
    if 'blacklisted_sessions' in session and employee_name in session['blacklisted_sessions']:
        session.clear()
        return redirect(url_for('index'))
    
    # 팀장만 접근 가능
    if session.get('employee_role') != '팀장':
        print(f" 팀장이 아닌 사용자 접근 거부 - employee_role: {session.get('employee_role')}")
        return redirect(url_for('index'))
    
    employee_name = session.get('employee_name', '팀장')
    employee_team = session.get('employee_team', '')
    print(f" 팀장 대시보드 접근 허용 - {employee_name} ({employee_team})")
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print(" 테스트 모드 - 팀장 대시보드")
        guarantee_list = []
    else:
        # 보증보험 매물 목록 조회
        guarantee_list = supabase_utils.get_guarantee_insurance_links(20)
    
    return render_template('team_leader_dashboard.html',  # 새 템플릿
                         employee_name=employee_name,
                         employee_team=employee_team,
                         residence_site_url=RESIDENCE_SITE_URL,
                         business_site_url=BUSINESS_SITE_URL,
                         guarantee_list=guarantee_list)

@app.route('/admin')
def admin_panel():
    """관리자 패널 (직원 관리)"""
    # 블랙리스트 체크 (비활성화/삭제된 직원)
    if 'employee_id' in session:
        employee_name = session.get('employee_name', '')
        if 'blacklisted_sessions' in session and employee_name in session['blacklisted_sessions']:
            session.clear()
            return redirect(url_for('index'))
    
    # 관리자만 접근 가능 (팀장은 별도 페이지 사용)
    if not session.get('is_admin'):
        print(f" 접근 거부 - is_admin: {session.get('is_admin')}, employee_role: {session.get('employee_role')}")
        return redirect(url_for('index'))
    
    print(f" 관리자 패널 접근 허용 - is_admin: {session.get('is_admin')}, employee_role: {session.get('employee_role')}")

    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print(" 테스트 모드 - 빈 보증보험 목록 반환")
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
    if not session.get('is_admin'):
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
    if not session.get('is_admin'):
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
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return jsonify({'error': 'Unauthorized'}), 401
    
    # 페이지네이션 파라미터 (GET 요청일 때만)
    if request.method == 'GET':
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
    
    # Supabase 연결 확인
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print(" Supabase 환경변수가 설정되지 않음 - 테스트 모드로 동작")
        if request.method == 'GET':
            return jsonify({
                'success': True,
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
                
                # 팀장인 경우 자신의 팀 멤버들만 필터링
                if session.get('employee_role') == '팀장' and not session.get('is_admin'):
                    current_team = session.get('employee_team')
                    print(f"[팀장 권한] 팀 필터링 적용: {current_team}")
                    employees = [emp for emp in employees if emp.get('team') == current_team and emp.get('role') in ['팀장', '직원']]
                    total_count = len(employees)
                    total_pages = 1  # 필터링된 결과는 단일 페이지로 처리
                    print(f"[팀장 권한] 필터링된 직원 수: {len(employees)}")
                
                # 필드명 통일을 위해 매핑
                for emp in employees:
                    emp['employee_id'] = emp.get('name')
                    emp['employee_name'] = emp.get('name')
                    emp['created_date'] = emp.get('created_at')
                    emp['is_active'] = emp.get('status', 'active') == 'active'
                
                print(f"[직원 목록] 최종 응답: {employees}")
                return jsonify({
                    'success': True,
                    'employees': employees,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages
                })
            else:
                print(" 직원 목록 조회 실패")
                return jsonify({
                    'success': False,
                    'employees': [],
                    'total_count': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0,
                    'error': '직원 목록 조회 실패'
                })

        if request.method == 'POST':
            print(" 직원 추가 요청 받음")
            data = request.get_json()
            print(f" 요청 데이터: {data}")
            
            employee_id = data.get('employee_id')
            employee_name = data.get('employee_name')
            team = data.get('team', '')
            email = data.get('email', '')
            position = data.get('position', '')
            role = data.get('role', '직원')
            status = data.get('status', 'active')
            password = data.get('password', '1234')  # 기본 비밀번호 1234
            
            # 팀장이 직원을 추가하는 경우, 자신의 팀으로만 추가 가능
            if session.get('employee_role') == '팀장' and not session.get('is_admin'):
                current_team = session.get('employee_team')
                if team != current_team:
                    print(f" 팀장이 다른 팀에 직원 추가 시도: 현재 팀={current_team}, 요청 팀={team}")
                    return jsonify({'success': False, 'message': f'팀장은 자신의 팀({current_team})에만 직원을 추가할 수 있습니다.'}), 403
                # 팀장은 자신의 팀으로 강제 설정
                team = current_team
            
            # employee_id와 employee_name 중 하나라도 있으면 name으로 사용
            name = employee_name if employee_name else employee_id
            
            print(f" 추출된 데이터 - 이름: '{name}', 팀: '{team}', 이메일: '{email}', 직책: '{position}'")
            
            if not name or name.strip() == '':
                print(f" 이름이 비어있음")
                return jsonify({'success': False, 'message': '이름을 입력해야 합니다.'}), 400
            
            # Supabase에 직원 추가
            new_employee = supabase_utils.add_employee(name, email, team, position, role, status, password)
            
            if new_employee:
                # 필드명 통일을 위해 매핑
                new_employee['employee_id'] = new_employee.get('name')
                new_employee['employee_name'] = new_employee.get('name')
                new_employee['created_date'] = new_employee.get('created_at')
                new_employee['is_active'] = new_employee.get('status') == 'active'
                
                print(f" 직원 추가 성공: {new_employee}")
                return jsonify({'success': True, 'employee': new_employee})
            else:
                print(" 직원 추가 실패")
                return jsonify({'success': False, 'message': '직원 추가 중 오류가 발생했습니다.'})
            
    except Exception as e:
        print(f" 직원 API 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'서버 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/employees/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    """직원 비활성화 (소프트 삭제) 및 강제 로그아웃"""
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 직원 정보 조회 (강제 로그아웃을 위해)
        employee_response = supabase.table('employees').select('name, status, team').eq('id', emp_id).execute()
        if not employee_response.data:
            return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'}), 404
        
        employee_name = employee_response.data[0].get('name')
        employee_team = employee_response.data[0].get('team')
        
        # 팀장인 경우 자신의 팀 직원만 삭제 가능
        if session.get('employee_role') == '팀장' and not session.get('is_admin'):
            current_team = session.get('employee_team')
            if employee_team != current_team:
                return jsonify({'success': False, 'message': '다른 팀 직원은 삭제할 수 없습니다.'}), 403
        
        # 직원 상태를 inactive로 변경
        response = supabase.table('employees').update({'status': 'inactive'}).eq('id', emp_id).execute()
        
        if response.data:
            print(f" 직원 비활성화 성공: ID {emp_id}, 이름: {employee_name}")
            
            # 강제 로그아웃을 위한 세션 무효화 (Redis나 세션 저장소 사용 시)
            # 현재는 세션 ID를 블랙리스트에 추가하는 방식으로 구현
            if 'blacklisted_sessions' not in session:
                session['blacklisted_sessions'] = []
            
            # 해당 직원의 모든 세션을 블랙리스트에 추가
            session['blacklisted_sessions'].append(employee_name)
            
            return jsonify({
                'success': True, 
                'message': f'직원 {employee_name}이(가) 비활성화되었습니다. 강제 로그아웃이 적용됩니다.',
                'employee_name': employee_name
            })
        else:
            print(f" 직원 삭제 실패: ID {emp_id}, response.data가 None")
            return jsonify({'success': False, 'message': '직원 상태 업데이트에 실패했습니다.'}), 500
            
    except Exception as e:
        print(f" 직원 삭제 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'직원 삭제 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/employees/<int:emp_id>/deactivate', methods=['PUT'])
def deactivate_employee(emp_id):
    """직원 비활성화 (팀장용 API)"""
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 먼저 직원 정보 조회
        employee_response = supabase.table('employees').select('name, team').eq('id', emp_id).execute()
        if not employee_response.data:
            return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'}), 404
            
        employee_name = employee_response.data[0]['name']
        employee_team = employee_response.data[0].get('team')
        
        # 팀장인 경우 자신의 팀 직원만 비활성화 가능
        if session.get('employee_role') == '팀장' and not session.get('is_admin'):
            current_team = session.get('employee_team')
            if employee_team != current_team:
                return jsonify({'success': False, 'message': '다른 팀 직원은 수정할 수 없습니다.'}), 403
        
        # 직원 상태를 inactive로 변경
        response = supabase.table('employees').update({
            'status': 'inactive'
        }).eq('id', emp_id).execute()
        
        if response.data:
            print(f" 직원 비활성화 성공: ID {emp_id}, 이름: {employee_name}")
            
            # 강제 로그아웃을 위한 세션 무효화
            if 'blacklisted_sessions' not in session:
                session['blacklisted_sessions'] = []
            
            session['blacklisted_sessions'].append(employee_name)
            
            return jsonify({
                'success': True, 
                'message': f'직원 {employee_name}이(가) 비활성화되었습니다.',
                'employee_name': employee_name
            })
        else:
            print(f" 직원 비활성화 실패: ID {emp_id}")
            return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'}), 404
            
    except Exception as e:
        print(f" 직원 비활성화 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<int:emp_id>/activate', methods=['PUT'])
def activate_employee(emp_id):
    """직원 활성화"""
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 팀장인 경우 권한 체크
        if session.get('employee_role') == '팀장' and not session.get('is_admin'):
            emp_response = supabase.table('employees').select('team').eq('id', emp_id).execute()
            if not emp_response.data:
                return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'}), 404
            
            emp_team = emp_response.data[0].get('team')
            current_team = session.get('employee_team')
            
            if emp_team != current_team:
                return jsonify({'success': False, 'message': '다른 팀 직원은 수정할 수 없습니다.'}), 403
        
        # 직원 상태를 active로 변경
        response = supabase.table('employees').update({'status': 'active'}).eq('id', emp_id).execute()
        
        if response.data:
            print(f" 직원 활성화 성공: ID {emp_id}")
            return jsonify({'success': True, 'message': '직원이 활성화되었습니다.'})
        else:
            print(f" 직원 활성화 실패: ID {emp_id}")
            return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'}), 404
            
    except Exception as e:
        print(f" 직원 활성화 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<int:emp_id>/reset-password', methods=['PUT'])
def reset_employee_password(emp_id):
    """직원 비밀번호 재설정"""
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        new_password = data.get('new_password', '1234')  # 기본값 1234
        
        # Supabase 연결
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 팀장인 경우 권한 체크
        if session.get('employee_role') == '팀장' and not session.get('is_admin'):
            emp_response = supabase.table('employees').select('team').eq('id', emp_id).execute()
            if not emp_response.data:
                return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'}), 404
            
            emp_team = emp_response.data[0].get('team')
            current_team = session.get('employee_team')
            
            if emp_team != current_team:
                return jsonify({'success': False, 'message': '다른 팀 직원은 수정할 수 없습니다.'}), 403
        
        # 비밀번호 업데이트
        print(f" 비밀번호 업데이트 시도: ID={emp_id}, 새 비밀번호={new_password}")
        response = supabase.table('employees').update({
            'password': new_password
        }).eq('id', emp_id).execute()
        
        print(f" Supabase 응답: {response}")
        
        if response.data:
            print(f" 직원 ID {emp_id} 비밀번호 재설정 완료")
            return jsonify({'success': True, 'message': f'비밀번호가 "{new_password}"로 재설정되었습니다.'})
        else:
            print(f" 비밀번호 업데이트 실패: response.data가 None")
            return jsonify({'success': False, 'message': '비밀번호 업데이트에 실패했습니다.'}), 500
            
    except Exception as e:
        print(f" 비밀번호 재설정 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'비밀번호 재설정 중 오류가 발생했습니다: {str(e)}'}), 500

# 팀 관리 API
@app.route('/api/teams', methods=['GET', 'POST'])
def manage_teams():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if request.method == 'GET':
            # DB에서 실제 팀 목록 가져오기
            try:
                supabase = supabase_utils.get_supabase()
                if supabase:
                    # 활성 상태인 팀만 조회 (is_active = true 또는 null)
                    response = supabase.table('teams').select('*').or_('is_active.is.null,is_active.eq.true').execute()
                    teams = response.data
                    print(f" DB에서 활성 팀 목록 조회 성공: {len(teams)}개 팀")
                    return jsonify({'teams': teams})
                else:
                    print(" Supabase 연결 실패, 기본 팀 목록 반환")
                    raise Exception("Supabase 연결 실패")
            except Exception as e:
                print(f" 팀 목록 조회 실패: {e}, 기본 팀 목록 반환")
                # 오류 시 기본 팀 목록 반환
                teams = [
                    {'name': '빈시트', 'description': '빈시트 팀'},
                    {'name': '위플러스', 'description': '위플러스 팀'},
                    {'name': '반클리셰', 'description': '반클리셰 팀'},
                    {'name': '대표', 'description': '대표 팀'},
                    {'name': '관리자', 'description': '관리자 팀'},
                    {'name': '미지정', 'description': '팀 미지정 상태'}
                ]
                return jsonify({'teams': teams})
            
        elif request.method == 'POST':
            data = request.get_json()
            team_name = data.get('name', '').strip()
            team_description = data.get('description', '').strip()
            
            if not team_name:
                return jsonify({'success': False, 'message': '팀 이름을 입력해야 합니다.'}), 400
            
            # DB에 새 팀 추가
            supabase = supabase_utils.get_supabase()
            if not supabase:
                return jsonify({'success': False, 'message': '데이터베이스 연결에 실패했습니다.'}), 500
            
            try:
                # 중복 팀 이름 체크 (DB에서)
                existing_response = supabase.table('teams').select('name').eq('name', team_name).execute()
                if existing_response.data:
                    return jsonify({'success': False, 'message': '이미 존재하는 팀 이름입니다.'}), 400
                
                # 새 팀 추가
                new_team_data = {
                    'name': team_name,
                    'description': team_description,
                    'is_active': True
                }
                
                response = supabase.table('teams').insert(new_team_data).execute()
                
                if response.data:
                    print(f" 새 팀 추가 성공: {team_name} - {team_description}")
                    return jsonify({
                        'success': True, 
                        'message': f'팀 "{team_name}"이(가) 추가되었습니다.',
                        'team': response.data[0]
                    })
                else:
                    return jsonify({'success': False, 'message': '팀 추가에 실패했습니다.'}), 500
                    
            except Exception as e:
                print(f" 팀 추가 오류: {e}")
                return jsonify({'success': False, 'message': f'팀 추가 중 오류가 발생했습니다: {str(e)}'}), 500
            
    except Exception as e:
        print(f" 팀 관리 오류: {e}")
        return jsonify({'error': str(e)}), 500

# 팀 삭제 API
@app.route('/api/teams/<team_name>', methods=['DELETE'])
def delete_team(team_name):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json() or {}
        delete_reason = data.get('reason', '').strip()
        
        # DB에서 팀 삭제
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False, 'message': '데이터베이스 연결에 실패했습니다.'}), 500
        
        try:
            # 기본 팀은 삭제 불가 (DB에서 확인)
            protected_response = supabase.table('teams').select('name').in_('name', ['빈시트', '위플러스', '반클리셰', '대표']).execute()
            protected_teams = [team['name'] for team in protected_response.data] if protected_response.data else []
            
            if team_name in protected_teams:
                return jsonify({'success': False, 'message': '기본 팀은 삭제할 수 없습니다.'}), 400
            
            # 해당 팀에 속한 직원들의 팀을 "미지정"으로 변경
            try:
                # 먼저 "미지정" 팀이 있는지 확인하고, 없으면 생성
                미지정_response = supabase.table('teams').select('name').eq('name', '미지정').execute()
                if not 미지정_response.data:
                    supabase.table('teams').insert({
                        'name': '미지정',
                        'description': '팀 미지정 상태',
                        'is_active': True
                    }).execute()
                
                # 해당 팀에 속한 직원들의 팀을 "미지정"으로 설정
                response = supabase.table('employees').update({'team': '미지정'}).eq('team', team_name).execute()
                print(f" 팀 '{team_name}' 소속 직원들의 팀 정보 업데이트: {response.data}")
            except Exception as e:
                print(f" 직원 팀 정보 업데이트 실패: {e}")
            
            # 팀 삭제 (실제 삭제)
            delete_response = supabase.table('teams').delete().eq('name', team_name).execute()
            
            if delete_response.data:
                print(f" 팀 삭제 성공: {team_name} - 사유: {delete_reason}")
                return jsonify({
                    'success': True,
                    'message': f'팀 "{team_name}"이(가) 삭제되었습니다.',
                    'deleted_team': team_name,
                    'reason': delete_reason
                })
            else:
                return jsonify({'success': False, 'message': '팀 삭제에 실패했습니다.'}), 500
                
        except Exception as e:
            print(f" 팀 삭제 오류: {e}")
            return jsonify({'success': False, 'message': f'팀 삭제 중 오류가 발생했습니다: {str(e)}'}), 500
        
    except Exception as e:
        print(f" 팀 삭제 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<int:emp_id>/update', methods=['PUT'])
def update_employee(emp_id):
    """직원 정보 수정"""
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '수정할 데이터가 없습니다.'}), 400
        
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 팀장인 경우 자신의 팀 직원만 수정 가능
        if session.get('employee_role') == '팀장' and not session.get('is_admin'):
            # 직원 정보 먼저 조회
            emp_response = supabase.table('employees').select('team').eq('id', emp_id).execute()
            if not emp_response.data:
                return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'}), 404
            
            emp_team = emp_response.data[0].get('team')
            current_team = session.get('employee_team')
            
            if emp_team != current_team:
                return jsonify({'success': False, 'message': f'다른 팀 직원은 수정할 수 없습니다.'}), 403
        
        # 업데이트할 데이터 준비
        update_data = {}
        allowed_fields = ['employee_name', 'employee_role', 'employee_status', 'team', 'role', 'status', 'password']
        
        for field in allowed_fields:
            if field in data:
                if field == 'employee_name':
                    update_data['name'] = data[field]  # DB 필드명 매핑
                elif field == 'employee_role':
                    update_data['role'] = data[field]  # DB 필드명 매핑
                elif field == 'employee_status':
                    update_data['status'] = data[field]  # DB 필드명 매핑
                else:
                    update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'success': False, 'message': '수정할 데이터가 없습니다.'}), 400
        
        # 직원 정보 업데이트
        response = supabase.table('employees').update(update_data).eq('id', emp_id).execute()
        
        if response.data:
            print(f" 직원 정보 수정 성공: ID {emp_id}")
            return jsonify({'success': True, 'message': '직원 정보가 수정되었습니다.'})
        else:
            print(f" 직원 정보 수정 실패: ID {emp_id}")
            return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'}), 404
            
    except Exception as e:
        print(f" 직원 정보 수정 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<int:emp_id>/permanent-delete', methods=['DELETE'])
def permanent_delete_employee(emp_id):
    """직원 완전 삭제 (비활성 상태인 경우만)"""
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 직원 정보 조회 (이름, 상태, 팀)
        employee_response = supabase.table('employees').select('name, status, team').eq('id', emp_id).execute()
        
        if not employee_response.data:
            return jsonify({'success': False, 'message': '직원을 찾을 수 없습니다.'}), 404
        
        employee_data = employee_response.data[0]
        employee_name = employee_data.get('name', 'Unknown')
        employee_status = employee_data.get('status')
        employee_team = employee_data.get('team')
        
        # 팀장인 경우 자신의 팀 직원만 삭제 가능
        if session.get('employee_role') == '팀장' and not session.get('is_admin'):
            current_team = session.get('employee_team')
            if employee_team != current_team:
                return jsonify({'success': False, 'message': '다른 팀 직원은 삭제할 수 없습니다.'}), 403
        
        if employee_status == 'active':
            return jsonify({'success': False, 'message': '활성 상태의 직원은 삭제할 수 없습니다.'}), 400
        
        # 직원 완전 삭제
        delete_response = supabase.table('employees').delete().eq('id', emp_id).execute()
        
        if delete_response.data is not None:
            print(f" 직원 완전 삭제 성공: ID {emp_id}, 이름: {employee_name}")
            
            # 강제 로그아웃을 위한 세션 무효화
            if 'blacklisted_sessions' not in session:
                session['blacklisted_sessions'] = []
            
            # 해당 직원의 모든 세션을 블랙리스트에 추가
            session['blacklisted_sessions'].append(employee_name)
            
            return jsonify({
                'success': True, 
                'message': f'직원 {employee_name}이(가) 완전히 삭제되었습니다. 강제 로그아웃이 적용됩니다.',
                'employee_name': employee_name
            })
        else:
            print(f" 직원 완전 삭제 실패: ID {emp_id}")
            return jsonify({'success': False, 'message': '삭제에 실패했습니다.'}), 500
            
    except Exception as e:
        print(f" 직원 완전 삭제 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers', methods=['GET', 'POST'])
def manage_customers():
    print(f"[DEBUG] /api/customers 접근 시도")
    print(f"[DEBUG] 현재 세션: {dict(session)}")
    print(f"[DEBUG] employee_id in session: {'employee_id' in session}")
    print(f"[DEBUG] is_admin: {session.get('is_admin')}")
    
    # 관리자 또는 직원만 접근 가능
    if 'employee_id' not in session and not session.get('is_admin'):
        print(f"[ERROR] 권한 없음 - 세션에 employee_id나 is_admin이 없음")
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
        
        # Supabase 연결
        supabase = supabase_utils.get_supabase()
        if not supabase:
            print(" Supabase 연결 실패 - 빈 데이터 반환")
            return jsonify({
                'customers': [],
                'total_count': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            })
        
        try:
            # all_employees=true 요청 시 권한 검증
            if all_employees:
                # 팀장 또는 관리자만 모든 고객 조회 가능
                is_team_leader = session.get('employee_role') == '팀장'
                is_admin = session.get('is_admin')
                
                if not is_team_leader and not is_admin:
                    print(f" 권한 없음 - 역할: {session.get('employee_role')}, 직원ID: {employee_id}")
                    return jsonify({'error': '팀장 또는 관리자 권한이 필요합니다.'}), 403
            
            # **관리자는 모든 고객 데이터 조회**
            if session.get('is_admin'):
                print(f" 관리자 권한 - 모든 고객 데이터 조회")
                
                # 전체 카운트 조회
                count_response = supabase.table('employee_customers').select('id', count='exact').execute()
                total_count = count_response.count if count_response.count else 0
                
                # 모든 고객 데이터 조회 (페이지네이션 적용)
                query = supabase.table('employee_customers').select('*')
                query = query.order('created_date', desc=True)
                query = query.range(offset, offset + per_page - 1)
                
                response = query.execute()
                
                if hasattr(response, 'data') and response.data:
                    customers = response.data
                    total_pages = (total_count + per_page - 1) // per_page
                    
                    print(f" 관리자 고객 조회 성공: {len(customers)}개 (전체: {total_count}개)")
                    
                    return jsonify({
                        'customers': customers,
                        'total_count': total_count,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': total_pages
                    })
                else:
                    print(" 관리자 권한 - 고객 데이터 없음")
                    return jsonify({
                        'customers': [],
                        'total_count': 0,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': 0
                    })
            
            # **팀장은 자신의 팀 직원들의 고객만 조회**
            elif all_employees and session.get('employee_role') == '팀장':
                current_team = session.get('employee_team')
                print(f" 팀장 권한 - {current_team} 팀 고객 조회")
                
                if not current_team:
                    print(" 팀 정보 없음")
                    return jsonify({'error': '팀 정보를 찾을 수 없습니다.'}), 400
                
                # 팀 기반 고객 카운트 조회
                count_response = supabase.table('employee_customers').select('id', count='exact').eq('employee_team', current_team).execute()
                total_count = count_response.count if count_response.count else 0
                
                # 팀 기반 고객 데이터 조회
                query = supabase.table('employee_customers').select('*')
                query = query.eq('employee_team', current_team)
                query = query.order('created_date', desc=True)
                query = query.range(offset, offset + per_page - 1)
                
                response = query.execute()
                
                if hasattr(response, 'data') and response.data:
                    customers = response.data
                    total_pages = (total_count + per_page - 1) // per_page
                    
                    print(f" 팀장 고객 조회 성공: {len(customers)}개 (팀: {current_team}, 전체: {total_count}개)")
                    
                    return jsonify({
                        'customers': customers,
                        'total_count': total_count,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': total_pages
                    })
                else:
                    print(f" {current_team} 팀 고객 데이터 없음")
                    return jsonify({
                        'customers': [],
                        'total_count': 0,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': 0
                    })
            
            else:
                # 일반 직원은 본인 고객만 조회
                print(f" 직원용 고객관리 - {employee_id} 고객 조회")
                
                count_response = supabase.table('employee_customers').select('id', count='exact').eq('employee_id', employee_id).execute()
                total_count = count_response.count if count_response.count else 0
                
                query = supabase.table('employee_customers').select('*').eq('employee_id', employee_id)
                query = query.order('created_date', desc=True)
                query = query.range(offset, offset + per_page - 1)
                
                response = query.execute()
                
                if hasattr(response, 'data') and response.data:
                    customers = response.data
                    total_pages = (total_count + per_page - 1) // per_page
                    
                    print(f" 직원용 고객관리 조회 성공: {len(customers)}개 고객 (전체: {total_count}개)")
                    
                    return jsonify({
                        'customers': customers,
                        'total_count': total_count,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': total_pages
                    })
                else:
                    return jsonify({
                        'customers': [],
                        'total_count': 0,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': 0
                    })
                
        except Exception as e:
            print(f" 고객관리 조회 오류: {e}")
            return jsonify({
                'error': f'고객 조회 중 오류가 발생했습니다: {str(e)}'
            }), 500
        
        # 아래는 기존 테스트 데이터 (삭제 예정)
        if False:  # 테스트 모드 비활성화
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
                
                # employee_name 필드 추가 및 미확인 좋아요 수 계산
                for customer in customers_list:
                    customer['employee_name'] = customer.get('employee_id', '')
                    
                    # 미확인 좋아요 수 계산 (주거용)
                    management_site_id = customer.get('management_site_id')
                    if management_site_id:
                        try:
                            # Supabase 클라이언트 가져오기
                            supabase_client = supabase_utils.get_supabase()
                            if supabase_client:
                                # 주거용 미확인 좋아요 수
                                residence_likes = supabase_client.table('residence_links').select('id').eq('management_site_id', management_site_id).eq('liked', True).eq('is_checked', False).execute()
                                print(f"  [DEBUG] residence_links 쿼리 결과: {residence_likes.data}")
                                customer['unchecked_likes_residence'] = len(residence_likes.data) if residence_likes.data else 0
                                
                                # 업무용 미확인 좋아요 수
                                office_likes = supabase_client.table('office_links').select('id').eq('management_site_id', management_site_id).eq('liked', True).eq('is_checked', False).execute()
                                print(f"  [DEBUG] office_links 쿼리 결과: {office_likes.data}")
                                customer['unchecked_likes_business'] = len(office_likes.data) if office_likes.data else 0
                                
                                # 디버깅 로그 추가
                                print(f"[고객 {customer.get('customer_name')}] management_site_id: {management_site_id}")
                                print(f"  주거용 미확인 좋아요: {customer['unchecked_likes_residence']}건")
                                print(f"  업무용 미확인 좋아요: {customer['unchecked_likes_business']}건")
                            else:
                                print(f" Supabase 클라이언트를 가져올 수 없음")
                                customer['unchecked_likes_residence'] = 0
                                customer['unchecked_likes_business'] = 0
                            
                        except Exception as e:
                            print(f"미확인 좋아요 수 계산 오류: {e}")
                            customer['unchecked_likes_residence'] = 0
                            customer['unchecked_likes_business'] = 0
                    else:
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
                print(" 고객 목록 조회 실패")
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
            print(f"[DEBUG] 고객 추가 요청 받음")
            print(f"[DEBUG] 요청 데이터: {data}")
            print(f"[DEBUG] 현재 세션: {dict(session)}")
            
            # 관리자인 경우 특별한 employee_id 사용
            if session.get('is_admin'):
                current_employee_id = 999999  # 관리자용 특별 ID
                current_employee_name = '관리자'
                current_employee_team = '관리자'
                print(f"[DEBUG] 관리자 접근")
            else:
                current_employee_id = session.get('employee_id')
                current_employee_name = session.get('employee_name')
                current_employee_team = session.get('employee_team')
                print(f"[DEBUG] 직원 정보: id={current_employee_id}, name={current_employee_name}, team={current_employee_team}")
                
                # 직원 정보가 없으면 오류 반환
                if not current_employee_id:
                    print(f"[ERROR] 직원 ID가 세션에 없음")
                    return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
                
                # employee_id를 정수로 변환
                try:
                    current_employee_id = int(current_employee_id)
                except (ValueError, TypeError):
                    print(f"[ERROR] employee_id를 정수로 변환할 수 없음: {current_employee_id}")
                    return jsonify({'success': False, 'message': '직원 ID가 유효하지 않습니다.'}), 400
            
            is_team_leader = session.get('employee_role') == '팀장'
            
            print(f" 요청자: employee_id={current_employee_id}, name={current_employee_name}, team={current_employee_team}")

            # 데이터 타입 변환 및 검증
            def clean_value(value, field_type='text'):
                if value is None or value == '' or value == '-':
                    if field_type == 'int':
                        return None
                    elif field_type == 'bool':
                        return False
                    else:
                        return ''
                return value
            
            def clean_boolean_field(value):
                """Boolean 필드를 안전하게 처리"""
                if value is None or value == '' or value == '-' or value == 'undefined' or value == 'null':
                    return False
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    # 빈 문자열 처리
                    if not value.strip():
                        return False
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            
            customer_data = {
                'inquiry_date': clean_value(data.get('inquiry_date')),
                'customer_name': clean_value(data.get('customer_name')),
                'customer_phone': clean_value(data.get('customer_phone')),
                'budget': clean_value(data.get('budget'), 'int'),
                'rooms': clean_value(data.get('rooms')),
                'location': clean_value(data.get('location')),
                'loan_needed': clean_value(data.get('loan_needed')),  # 텍스트로 처리
                'parking_needed': clean_value(data.get('parking_needed')),  # 텍스트로 처리
                'pets': clean_value(data.get('pets')),
                'memo': clean_value(data.get('memo')),
                'status': clean_value(data.get('status', '진행중')),
                'employee_id': current_employee_id,
                'employee_name': current_employee_name,
                'employee_team': current_employee_team,
                'created_date': datetime.now().isoformat(),
                'unchecked_likes_residence': 0,  # integer 타입 (미확인 좋아요 개수)
                'unchecked_likes_business': 0   # integer 타입 (미확인 좋아요 개수)
            }
            
            # 팀장의 경우 팀 정보가 제대로 설정되었는지 확인
            if is_team_leader and not customer_data['employee_team']:
                print(f" 팀장 '{current_employee_name}'의 팀 정보가 설정되지 않음")
                return jsonify({'success': False, 'message': '팀 정보가 설정되지 않았습니다. 관리자에게 문의하세요.'}), 400
            
            # 필수 필드 검증
            if not customer_data.get('customer_name'):
                print(f" 필수 필드 누락: customer_name")
                return jsonify({'success': False, 'message': '고객명은 필수 입력 항목입니다.'}), 400
            
            # move_in_date가 제공된 경우에만 추가 (선택적 필드)
            if data.get('move_in_date'):
                customer_data['move_in_date'] = data.get('move_in_date')

            # management_site_id 생성 및 포함
            management_site_id = str(uuid.uuid4().hex)[:8]
            customer_data['management_site_id'] = management_site_id

            print(f" 고객 추가 시도: {customer_data.get('customer_name', 'Unknown')}")
            print(f" 전송할 고객 데이터: {customer_data}")
            
            new_customer = supabase_utils.add_customer(customer_data)
            print(f" add_customer 결과: {new_customer}")
            
            if not new_customer:
                print(f" 고객 추가 실패: add_customer가 None 반환")
                error_msg = '고객 추가 중 오류가 발생했습니다.'
                if not customer_data.get('customer_name'):
                    error_msg = '고객명은 필수 입력 항목입니다.'
                elif not customer_data.get('employee_id'):
                    error_msg = '직원 정보가 설정되지 않았습니다. 다시 로그인해주세요.'
                return jsonify({'success': False, 'message': error_msg}), 500

            # 고객 추가 성공 후 주거사이트와 업무사이트 자동 생성
            try:
                management_site_id = customer_data['management_site_id']
                
                # 주거사이트 생성
                residence_site_data = {
                    'management_site_id': management_site_id,
                    'customer_name': customer_data['customer_name'],
                    'customer_phone': customer_data['customer_phone'],
                    'budget': customer_data['budget'],
                    'rooms': customer_data['rooms'],
                    'location': customer_data['location'],
                    'loan_needed': customer_data['loan_needed'],  # text로 처리
                    'parking_needed': customer_data['parking_needed'],  # text로 처리
                    'pets': customer_data['pets'],
                    'memo': customer_data['memo'],
                    'status': customer_data['status'],
                    'employee_id': current_employee_id,
                    'employee_name': current_employee_name,
                    'employee_team': current_employee_team,
                    'created_date': datetime.now().isoformat()
                }
                
                # 업무사이트 생성
                business_site_data = {
                    'management_site_id': management_site_id,
                    'customer_name': customer_data['customer_name'],
                    'customer_phone': customer_data['customer_phone'],
                    'budget': customer_data['budget'],
                    'rooms': customer_data['rooms'],
                    'location': customer_data['location'],
                    'loan_needed': customer_data['loan_needed'],  # text로 처리
                    'parking_needed': customer_data['parking_needed'],  # text로 처리
                    'pets': customer_data['pets'],
                    'memo': customer_data['memo'],
                    'status': customer_data['status'],
                    'employee_id': current_employee_id,
                    'employee_name': current_employee_name,
                    'employee_team': current_employee_team,
                    'created_date': datetime.now().isoformat()
                }
                
                # Supabase에 사이트 데이터 저장
                supabase = supabase_utils.get_supabase()
                if supabase:
                    # 주거사이트 저장
                    residence_response = supabase.table('residence_links').insert(residence_site_data).execute()
                    print(f" 주거사이트 생성 성공: {management_site_id}")
                    
                    # 업무사이트 저장
                    business_response = supabase.table('office_links').insert(business_site_data).execute()
                    print(f" 업무사이트 생성 성공: {management_site_id}")
                
            except Exception as e:
                print(f" 사이트 생성 중 오류 발생: {e}")
                # 사이트 생성 실패해도 고객 추가는 성공으로 처리

            return jsonify({
                'success': True, 
                'message': '고객이 추가되었습니다. 주거사이트와 업무사이트가 자동으로 생성되었습니다.', 
                'customer': new_customer,
                'management_site_id': customer_data['management_site_id']
            })

        except Exception as e:
            print(f" 고객 추가 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False, 
                'message': f'고객 추가 중 오류 발생: {str(e)}',
                'error_type': type(e).__name__
            }), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT', 'DELETE'])
def update_delete_customer(customer_id):
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    employee_id = session.get('employee_id')
    is_admin = bool(session.get('is_admin'))
    is_team_leader = session.get('employee_role') == '팀장'

    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False, 'message': '데이터베이스 연결 실패'}), 500

        # 권한 확인: 관리자, 팀장, 또는 본인 소유만 허용
        if not is_admin and not is_team_leader:
            owns = supabase.table('employee_customers').select('id').eq('id', customer_id).eq('employee_id', employee_id).execute()
            if not owns.data:
                return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
        elif is_team_leader and not is_admin:
            # 팀장의 경우 같은 팀 고객만 접근 가능하도록 추가 검증
            employee_team = session.get('employee_team')
            customer = supabase.table('employee_customers').select('*, employees!inner(team)').eq('id', customer_id).execute()
            if not customer.data or customer.data[0]['employees']['team'] != employee_team:
                return jsonify({'success': False, 'message': '같은 팀 고객만 수정할 수 있습니다.'}), 403

        if request.method == 'PUT':
            data = request.get_json() or {}
            
            # 업데이트할 데이터 준비
            update_data = {}
            allowed_fields = [
                'inquiry_date', 'move_in_date', 'customer_name', 'customer_phone', 
                'amount', 'room_count', 'location', 'progress_status', 'memo',
                'loan_info', 'parking', 'pets'
            ]
            
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]
            
            # 업데이트 시간 추가
            from datetime import datetime
            update_data['updated_date'] = datetime.now().isoformat()
            
            if update_data:
                response = supabase.table('employee_customers').update(update_data).eq('id', customer_id).execute()
                if response.data:
                    return jsonify({'success': True, 'message': '고객 정보가 수정되었습니다.'})
                else:
                    return jsonify({'success': False, 'message': '수정 실패'}), 500
            else:
                return jsonify({'success': False, 'message': '수정할 데이터가 없습니다.'}), 400

        if request.method == 'DELETE':
            response = supabase.table('employee_customers').delete().eq('id', customer_id).execute()
            if response.data is None:
                return jsonify({'success': False, 'message': '삭제 실패'}), 500
            return jsonify({'success': True, 'message': '고객이 삭제되었습니다.'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'작업 중 오류 발생: {e}'}), 500

@app.route('/api/customers/<int:customer_id>/memo', methods=['PUT'])
def update_customer_memo(customer_id):
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    employee_id = session.get('employee_id')
    is_admin = bool(session.get('is_admin'))
    is_team_leader = session.get('employee_role') == '팀장'
    
    data = request.get_json()
    memo = data.get('memo')
    
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False, 'message': '데이터베이스 연결 실패'}), 500
        
        # 권한 확인: 관리자, 팀장, 또는 본인 소유만 허용
        if not is_admin and not is_team_leader:
            owns = supabase.table('employee_customers').select('id').eq('id', customer_id).eq('employee_id', employee_id).execute()
            if not owns.data:
                return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
        elif is_team_leader and not is_admin:
            # 팀장의 경우 같은 팀 고객만 접근 가능하도록 추가 검증
            employee_team = session.get('employee_team')
            customer = supabase.table('employee_customers').select('*, employees!inner(team)').eq('id', customer_id).execute()
            if not customer.data or customer.data[0]['employees']['team'] != employee_team:
                return jsonify({'success': False, 'message': '같은 팀 고객만 수정할 수 있습니다.'}), 403
        try:
            # updated_date 필드도 함께 업데이트
            from datetime import datetime
            current_time = datetime.now().isoformat()
            update_data = {
                'memo': memo,
                'updated_date': current_time
            }
            res = supabase.table('employee_customers').update(update_data).eq('id', customer_id).execute()
        except Exception as e:
            print(f" 메모 업데이트 실패, 오류: {e}")
            raise e
        
        if res.data is None:
            return jsonify({'success': False, 'message': '메모 업데이트 실패'}), 500
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': '메모 업데이트 실패'}), 500

@app.route('/api/customers/<int:customer_id>/field', methods=['PUT'])
def update_customer_field(customer_id):
    print(f" 고객 필드 업데이트 요청: customer_id={customer_id}")
    
    if 'employee_id' not in session and not session.get('is_admin'):
        print(f" 인증 실패: 세션에 employee_id 없음")
        return jsonify({'error': 'Unauthorized'}), 401
    
    employee_id = session.get('employee_id')
    is_admin = bool(session.get('is_admin'))
    is_team_leader = session.get('employee_role') == '팀장'
    
    print(f" 요청자: employee_id={employee_id}, is_admin={is_admin}, is_team_leader={is_team_leader}")
    
    data = request.get_json()
    print(f" 받은 데이터: {data}")
    
    if not data:
        return jsonify({'success': False, 'error': '데이터가 없습니다'}), 400
    
    field, value = list(data.items())[0]
    print(f" 업데이트할 필드: {field} = {value}")

    # 허용된 필드 목록 (프론트엔드 필드명과 일치)
    allowed_fields = [
        "inquiry_date", "move_in_date", "customer_name", "customer_phone", 
        "budget", "rooms", "location", "loan_needed", 
        "parking_needed", "pets", "status", "memo"
    ]
    if field not in allowed_fields:
        return jsonify({'success': False, 'error': f'허용되지 않은 필드: {field}'}), 400

    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False, 'error': 'DB 연결 실패'}), 500
        
        # 권한 확인: 관리자, 팀장, 또는 본인 소유만 허용
        if not is_admin and not is_team_leader:
            owns = supabase.table('employee_customers').select('id').eq('id', customer_id).eq('employee_id', employee_id).execute()
            if not owns.data:
                return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
        elif is_team_leader and not is_admin:
            # 팀장의 경우 같은 팀 고객만 접근 가능하도록 추가 검증
            employee_team = session.get('employee_team')
            try:
                # employee_team 필드로 직접 확인
                customer = supabase.table('employee_customers').select('*').eq('id', customer_id).execute()
                if not customer.data:
                    return jsonify({'success': False, 'message': '고객을 찾을 수 없습니다.'}), 404
                if customer.data[0].get('employee_team') != employee_team:
                    return jsonify({'success': False, 'message': '같은 팀 고객만 수정할 수 있습니다.'}), 403
            except Exception as e:
                print(f"팀장 권한 확인 중 오류: {e}")
                return jsonify({'success': False, 'message': '권한 확인 중 오류가 발생했습니다.'}), 500
        
        # 데이터 타입 변환 및 검증 (실제 테이블 구조 기반)
        def clean_update_value(val, field_name):
            if val is None or val == '' or val == '-':
                if field_name == 'budget':
                    return None
                else:
                    return ''
            
            # 실제 테이블 필드 타입에 맞춘 변환
            if field_name == 'budget':
                try:
                    # 숫자가 아닌 문자 제거 후 정수 변환
                    cleaned = str(val).replace(',', '').replace('만원', '').replace('원', '').strip()
                    if cleaned and cleaned.replace('-', '').isdigit():
                        return int(cleaned)
                    else:
                        return None
                except (ValueError, TypeError):
                    return None
            elif field_name in ['loan_needed', 'parking_needed', 'rooms', 'location', 'pets', 'memo', 'status', 'inquiry_date', 'move_in_date', 'customer_name', 'customer_phone']:
                # 문자열 타입 (테이블에서 str 타입)
                return str(val)
            else:
                return str(val)
        
        cleaned_value = clean_update_value(value, field)
        update_data = {field: cleaned_value}
        
        print(f"필드 업데이트 시도: {field} = {cleaned_value} (원본: {value})")
        
        # updated_date 필드 업데이트 (실제 테이블에 존재하는 필드명)
        from datetime import datetime
        current_time = datetime.now().isoformat()
        
        # updated_date 필드도 함께 업데이트
        update_data['updated_date'] = current_time
        
        try:
            res = supabase.table('employee_customers').update(update_data).eq('id', customer_id).execute()
            print(f" 업데이트 성공: {res.data}")
        except Exception as e:
            print(f" Supabase 업데이트 오류: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False, 
                'error': f'데이터베이스 업데이트 실패: {str(e)}'
            }), 500
        
        if res.data is None or len(res.data) == 0:
            print(f" 업데이트 결과가 없음")
            return jsonify({'success': False, 'error': '업데이트 실패 - 데이터가 없습니다'}), 500
        
        print(f" 필드 업데이트 성공: {field} = {cleaned_value}")
        return jsonify({'success': True, 'message': f'{field} 필드가 업데이트되었습니다.'})
    except Exception as e:
        print(f" 고객 필드 업데이트 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': f'서버 오류가 발생했습니다: {str(e)}'
        }), 500

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
        print(" 테스트 모드 - 팀장 본인 고객 샘플 데이터 반환")
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
    """팀장 팀 전체 매물 조회 (팀장 + 팀원 모든 매물)"""
    if session.get('employee_role') != '팀장' and not session.get('is_admin'):
        return jsonify({'error': '팀장만 접근 가능합니다.'}), 403
    
    team_name = session.get('employee_team')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # 정렬 파라미터 가져오기
    sort_by = request.args.get('sort_by', 'check_date')
    sort_order = request.args.get('sort_order', 'desc')
    
    print(f" 팀장 팀 전체 매물 조회 - 팀: {team_name}, 페이지: {page}, 정렬: {sort_by} {sort_order}")
    
    # Supabase 연결
    supabase = supabase_utils.get_supabase()
    if not supabase:
        print(" Supabase 연결 실패 - 빈 데이터 반환")
        return jsonify({
            'success': True,
            'properties': [],
            'total_count': 0,
            'page': page,
            'per_page': per_page,
            'total_pages': 0
        })
    
    try:
        # **팀장은 자신의 팀 전체 매물 조회**
        print(f" 팀장용 메이플관리 - 팀 '{team_name}' 전체 매물 조회 시작")
        
        # 전체 카운트 조회 (팀 필터링)
        count_response = supabase.table('maeiple_properties').select('id', count='exact').eq('employee_team', team_name).execute()
        total_count = count_response.count if count_response.count else 0
        
        # 정렬 컬럼 유효성 검사
        valid_sort_columns = ['id', 'check_date', 'building_number', 'room_number', 'status', 'jeonse_price', 'monthly_rent', 'sale_price', 'created_at', 'updated_at']
        if sort_by not in valid_sort_columns:
            sort_by = 'check_date'
        
        # 정렬 방향 유효성 검사
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        
        # 팀 전체 매물 데이터 조회 (페이지네이션 적용)
        query = supabase.table('maeiple_properties').select('*').eq('employee_team', team_name)
        
        # 정렬 적용
        query = query.order(sort_by, desc=(sort_order == 'desc'))
        
        # 페이지네이션 적용
        query = query.range(offset, offset + per_page - 1)
        
        response = query.execute()
        
        if hasattr(response, 'data') and response.data:
            properties = response.data
            total_pages = (total_count + per_page - 1) // per_page
            
            print(f" 팀장용 메이플관리 조회 성공: 팀 '{team_name}' - {len(properties)}개 매물 (전체: {total_count}개, 페이지: {page}/{total_pages})")
            
            return jsonify({
                'success': True,
                'properties': properties,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
            })
        else:
            print(f" 팀 '{team_name}' 매물 데이터 없음")
            return jsonify({
                'success': True,
                'properties': [],
                'total_count': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            })
            
    except Exception as e:
        print(f" 팀장용 메이플관리 조회 오류: {e}")
        return jsonify({
            'success': False,
            'error': f'팀 매물 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

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
        print(" 테스트 모드 - 팀 전체 고객 샘플 데이터 반환")
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
        print(" 테스트 모드 - 팀 전체 매물 샘플 데이터 반환")
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
    try:
        # 고객 정보 Supabase에서 조회
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return "데이터베이스 연결이 설정되지 않았습니다.", 500

        res = supabase.table('employee_customers').select('*').eq('management_site_id', management_site_id).limit(1).execute()
        if not res.data:
            print(f"[주거ROUTE] 고객 정보를 찾을 수 없음: {management_site_id}")
            return f"""
            <h1>고객 정보를 찾을 수 없습니다</h1>
            <p>요청한 management_site_id: <strong>{management_site_id}</strong></p>
            <p>데이터베이스에서 해당 고객을 찾을 수 없습니다.</p>
            <p><a href="/dashboard">대시보드로 돌아가기</a></p>
            """, 404

        customer_info = res.data[0]
        customer_name = customer_info.get('customer_name', '고객')
        print(f"[주거ROUTE] 고객 정보 조회 성공 - 이름: {customer_name}")

        # 미확인 좋아요 처리 (주거용)
        try:
            supabase.table('residence_links').update({'is_checked': True}).eq('management_site_id', management_site_id).eq('liked', True).eq('is_checked', False).execute()
        except Exception as e:
            print(f"미확인 좋아요 처리 오류: {e}")
    except Exception as e:
        print(f"[주거ROUTE] 처리 중 오류: {e}")
        return f"주거용 사이트 오류: {e}", 500
    
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
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return "데이터베이스 연결이 설정되지 않았습니다.", 500

        res = supabase.table('employee_customers').select('*').eq('management_site_id', management_site_id).limit(1).execute()
        if not res.data:
            print(f"[업무ROUTE] 고객 정보를 찾을 수 없음: {management_site_id}")
            return f"""
            <h1>고객 정보를 찾을 수 없습니다</h1>
            <p>요청한 management_site_id: <strong>{management_site_id}</strong></p>
            <p>데이터베이스에서 해당 고객을 찾을 수 없습니다.</p>
            <p><a href="/dashboard">대시보드로 돌아가기</a></p>
            """, 404

        customer_info = res.data[0]
        customer_name = customer_info.get('customer_name', '고객')
        print(f"[업무ROUTE] 고객 정보 조회 성공 - 이름: {customer_name}")

        # 미확인 좋아요 처리 (업무용)
        try:
            supabase.table('office_links').update({'is_checked': True}).eq('management_site_id', management_site_id).eq('liked', True).eq('is_checked', False).execute()
        except Exception as e:
            print(f"미확인 좋아요 처리 오류: {e}")
    except Exception as e:
        print(f"[업무ROUTE] 처리 중 오류: {e}")
        return f"업무용 사이트 오류: {e}", 500
    
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
            # title이 없으면 URL에서 도메인 추출해서 제목 생성
            import re
            from urllib.parse import urlparse
            
            title = data.get('title', '')
            if not title:
                try:
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc or parsed_url.path
                    title = f"{platform} - {domain}" if domain else f"{platform} 링크"
                except:
                    title = f"{platform} 링크"
            
            payload = {
                'title': title,
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
        # title이 없으면 URL에서 도메인 추출해서 제목 생성
        from urllib.parse import urlparse
        
        title = data.get('title', '')
        if not title:
            try:
                parsed_url = urlparse(url)
                domain = parsed_url.netloc or parsed_url.path
                title = f"{platform} - {domain}" if domain else f"{platform} 링크"
            except:
                title = f"{platform} 링크"
        
        payload = {
            'title': title,
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
        # management_site_id가 없는 경우는 전체 조회로 처리
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
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
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
        try:
            supabase = supabase_utils.get_supabase()
            if not supabase:
                return jsonify({'error': '데이터베이스 연결 실패'}), 500
            res = supabase.table('employee_customers').select('*').eq('management_site_id', management_site_id).limit(1).execute()
            if not res.data:
                return jsonify({'error': '고객 정보를 찾을 수 없습니다.'}), 404
            customer_info = res.data[0]
            return jsonify({
                'customer_name': customer_info.get('customer_name', '고객'),
                'move_in_date': customer_info.get('move_in_date', ''),
                'management_site_id': management_site_id
            })
        except Exception as e:
            return jsonify({'error': f'고객 정보 조회 실패: {e}'}), 500
    
    elif request.method == 'POST':
        # 고객 정보 업데이트 (필요한 경우)
        if not management_site_id:
            return jsonify({'error': 'management_site_id가 필요합니다.'}), 400
        try:
            supabase = supabase_utils.get_supabase()
            if not supabase:
                return jsonify({'error': '데이터베이스 연결 실패'}), 500
            data = request.json or {}
            update_data = {}
            if 'customer_name' in data and data.get('customer_name') is not None:
                update_data['customer_name'] = data.get('customer_name')
            # move_in_date 컬럼이 현재 스키마에 없으므로 무시
            if not update_data:
                return jsonify({'success': True})
            res = supabase.table('employee_customers').update(update_data).eq('management_site_id', management_site_id).execute()
            if res.data is None:
                return jsonify({'error': '업데이트 실패'}), 500
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# ==================== 좋아요 알림 확인 처리 API ====================
@app.route('/api/mark-residence-likes-checked', methods=['POST'])
def mark_residence_likes_checked():
    """주거사이트 좋아요 알림을 확인 처리"""
    try:
        data = request.get_json()
        management_site_id = data.get('management_site_id')
        
        if not management_site_id:
            return jsonify({'success': False, 'error': 'management_site_id가 필요합니다.'}), 400
        
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False, 'error': 'DB 연결 실패'}), 500
        
        # 해당 고객의 주거용 좋아요를 모두 확인 처리
        res = supabase.table('residence_links').update({'is_checked': True}).eq('management_site_id', management_site_id).eq('liked', True).eq('is_checked', False).execute()
        
        print(f"주거사이트 좋아요 알림 확인 처리: {management_site_id}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"주거사이트 알림 확인 처리 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mark-business-likes-checked', methods=['POST'])
def mark_business_likes_checked():
    """업무사이트 좋아요 알림을 확인 처리"""
    try:
        data = request.get_json()
        management_site_id = data.get('management_site_id')
        
        if not management_site_id:
            return jsonify({'success': False, 'error': 'management_site_id가 필요합니다.'}), 400
        
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'success': False, 'error': 'DB 연결 실패'}), 500
        
        # 해당 고객의 업무용 좋아요를 모두 확인 처리
        res = supabase.table('office_links').update({'is_checked': True}).eq('management_site_id', management_site_id).eq('liked', True).eq('is_checked', False).execute()
        
        print(f"업무사이트 좋아요 알림 확인 처리: {management_site_id}")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"업무사이트 알림 확인 처리 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 매이플관리 API 라우트 ====================
@app.route('/maeiple')
def maeiple_management():
    """매이플관리 메인 페이지"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return redirect(url_for('index'))
    
    employee_name = session.get('employee_name', '관리자' if session.get('is_admin') else '직원')
    return render_template('maeiple_management.html', 
                         employee_name=employee_name)

@app.route('/api/employee/maeiple', methods=['GET', 'POST'])
def employee_maeiple_api():
    """직원용 메이플관리 API - 개인 매물만 조회 및 생성"""
    if 'employee_id' not in session:
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    if request.method == 'GET':
        # 정렬 파라미터 가져오기
        sort_by = request.args.get('sort_by', 'check_date')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 페이지네이션 파라미터
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Supabase 연결 확인
        if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
            print(" 테스트 모드 - 직원 개인용 샘플 매물 데이터 반환")
            
            # 현재 사용자 정보 가져오기
            current_user = session.get('employee_id', '')
            current_name = session.get('employee_name', '직원')
            current_team = session.get('employee_team', '')
            print(f" 직원 개인 메이플관리 - 사용자: {current_user}, 팀: {current_team}")
            
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
                    'employee_id': current_user,  # 실제 세션 값 사용
                    'employee_name': current_name,  # 실제 세션 값 사용
                    'employee_team': current_team   # 실제 세션 값 사용
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
                    'employee_id': current_user,  # 실제 세션 값 사용
                    'employee_name': current_name,  # 실제 세션 값 사용
                    'employee_team': current_team   # 실제 세션 값 사용
                }
            ]
            
            # 현재 직원의 개인 매물만 필터링
            personal_properties = [p for p in all_sample_properties if p['employee_id'] == current_user]
            print(f" 직원 개인 매물 필터링: {current_user}의 매물 {len(personal_properties)}개")
            
            # 테스트 모드에서 생성된 매물도 포함
            if 'test_maeiple_properties' in session:
                test_properties = session['test_maeiple_properties']
                # 현재 직원의 테스트 매물만 필터링
                user_test_properties = [p for p in test_properties if p['employee_id'] == current_user]
                print(f" 테스트 모드 매물 포함: {len(user_test_properties)}개")
                personal_properties.extend(user_test_properties)
            else:
                print(" 테스트 모드 매물 없음")
            
            print(f" 총 매물 수: {len(personal_properties)}개")
            
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
            # Supabase에서 개인 매물 목록 조회
            current_user = session.get('employee_id', '')
            
            properties_data = supabase_utils.get_maeiple_properties_with_pagination(
                page, per_page, current_user, sort_by, sort_order
            )
            
            if properties_data:
                properties = properties_data.get('properties', [])
                total_count = properties_data.get('total_count', 0)
                total_pages = properties_data.get('total_pages', 0)
                
                print(f"[직원 매물 목록] 조회된 매물 수: {len(properties)} (페이지 {page}/{total_pages})")
                
                return jsonify({
                    'success': True, 
                    'properties': properties,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages
                })
            else:
                print(" 직원 매물 목록 조회 실패")
                return jsonify({
                    'success': False,
                    'properties': [],
                    'total_count': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                })
                
        except Exception as e:
            print(f" 직원 매물 목록 조회 중 오류: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            print("=== 직원 매물 생성 API 호출 ===")
            data = request.json
            print(f" 직원 매물 생성 요청: {data}")
            
            if not data:
                print(" 요청 데이터가 없습니다.")
                return jsonify({'success': False, 'error': '요청 데이터가 없습니다.'}), 400
            
            # 현재 로그인한 사용자 정보 가져오기
            employee_id = session.get('employee_id', 'system')
            employee_name = session.get('employee_name', '시스템')
            employee_team = session.get('employee_team', '관리자')
            
            print(f" 현재 사용자: {employee_id} ({employee_name}) - 팀: {employee_team}")
            print(f" 세션 정보: {dict(session)}")

            # 필수 필드 검증 - 임시로 비활성화하여 테스트
            building_number = data.get('building_number', '')
            room_number = data.get('room_number', '')
            
            print(f" 받은 동 번호: '{building_number}' (타입: {type(building_number)})")
            print(f" 받은 호수: '{room_number}' (타입: {type(room_number)})")
            
            # 임시로 필수 검증 제거 - 테스트 목적
            print(" 필수 필드 검증 임시 비활성화 - 테스트 모드")

            property_data = {
                'check_date': data.get('check_date'),
                'building_number': str(building_number).strip() if building_number else '미입력',
                'room_number': str(room_number).strip() if room_number else '미입력',
                'status': data.get('status', '거래가능'),
                'jeonse_price': data.get('jeonse_price'),
                'monthly_deposit': data.get('monthly_deposit'),  # 월세보증금 필드 추가
                'monthly_rent': data.get('monthly_rent'),
                'sale_price': data.get('sale_price'),
                'is_occupied': data.get('is_occupied', False),
                'phone': data.get('phone'),
                'memo': data.get('memo', ''),
                'likes': data.get('likes', 0),
                'dislikes': data.get('dislikes', 0),
                'employee_id': employee_id,  # 세션의 employee_id 사용
                'employee_name': employee_name,
                'employee_team': employee_team
            }
            
            print(f" 생성할 매물 데이터: {property_data}")

            # Supabase 연결 확인
            if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
                print(" 테스트 모드 - 매물 생성 시뮬레이션")
                
                # 테스트 모드에서는 가상 ID 생성
                import random
                new_id = random.randint(1000, 9999)
                
                # 생성된 매물을 세션에 저장 (실제로는 메모리에만 저장)
                if 'test_maeiple_properties' not in session:
                    session['test_maeiple_properties'] = []
                
                new_property = {
                    'id': new_id,
                    **property_data,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                session['test_maeiple_properties'].append(new_property)
                print(f" 테스트 모드 매물 생성 완료: ID {new_id}")
                print(f" 현재 테스트 매물 수: {len(session['test_maeiple_properties'])}")
                print(f" 생성된 매물 상세: {new_property}")
                
                response_data = {
                    'success': True, 
                    'id': new_id,
                    'message': '테스트 모드 - 매물이 성공적으로 생성되었습니다.',
                    'created_property': new_property
                }
                
                print(f" 응답 데이터: {response_data}")
                return jsonify(response_data)

            # 실제 Supabase 연결이 있는 경우
            print(" Supabase 연결 시도...")
            try:
                new_prop = supabase_utils.create_maeiple_property(property_data)
                if not new_prop:
                    print(" Supabase 매물 생성 실패 - create_maeiple_property returned None")
                    return jsonify({'success': False, 'error': '매물 생성 실패: 데이터베이스 저장 오류'}), 500

                print(f" Supabase 매물 생성 완료: {new_prop}")
                return jsonify({'success': True, 'id': new_prop.get('id')})
            except Exception as supabase_error:
                print(f" Supabase 매물 생성 중 예외 발생: {supabase_error}")
                import traceback
                traceback.print_exc()
                return jsonify({'success': False, 'error': f'데이터베이스 오류: {str(supabase_error)}'}), 500

        except Exception as e:
            print(f" 매물 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'매물 생성 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/employee/maeiple/update', methods=['POST'])
def employee_maeiple_update():
    """직원용 메이플관리 매물 업데이트 API"""
    if 'employee_id' not in session:
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        data = request.json
        property_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([property_id, field]):
            return jsonify({'error': '필수 파라미터가 누락되었습니다.'}), 400
        
        # Supabase 연결
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Supabase 연결 실패'}), 500
        
        print(f" 매물 업데이트 요청: ID={property_id}, field={field}, value={value}")
        
        # 업데이트할 데이터 준비
        update_data = {field: value}
        
        # Supabase에서 데이터 업데이트
        response = supabase.table('maeiple_properties').update(update_data).eq('id', property_id).execute()
        
        if hasattr(response, 'data') and response.data:
            print(f" 업데이트 성공: {field} = {value}")
            return jsonify({
                'success': True, 
                'message': f'{field} 필드가 성공적으로 업데이트되었습니다.',
                'updated_data': response.data[0] if response.data else None
            })
        else:
            print(f" 업데이트 실패: {response}")
            return jsonify({'error': '데이터 업데이트에 실패했습니다.'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employee/maeiple/memo', methods=['POST'])
def employee_maeiple_memo():
    """직원용 메이플관리 메모 저장 API"""
    if 'employee_id' not in session:
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        data = request.json
        property_id = data.get('id')
        memo = data.get('memo', '')
        
        if not property_id:
            return jsonify({'error': '매물 ID가 필요합니다.'}), 400
        
        # DATABASE_URL이 없으면 테스트 모드로 처리
        # Supabase 연결
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 메모 업데이트
        response = supabase.table('maeiple_properties').update({'memo': memo}).eq('id', property_id).execute()
        
        if response.data:
            print(f" 메모 저장 성공: ID {property_id}")
            return jsonify({'success': True, 'message': '메모가 저장되었습니다.'})
        else:
            print(f" 메모 저장 실패: ID {property_id}")
            return jsonify({'success': False, 'message': '매물을 찾을 수 없습니다.'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employee/maeiple/<int:property_id>', methods=['DELETE'])
def employee_maeiple_delete(property_id):
    """직원용 메이플관리 매물 삭제 API"""
    if 'employee_id' not in session:
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        # Supabase 연결
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 매물 삭제
        response = supabase.table('maeiple_properties').delete().eq('id', property_id).execute()
        
        if response.data is not None:
            print(f" 매물 삭제 성공: ID {property_id}")
            return jsonify({'success': True, 'message': '매물이 삭제되었습니다.'})
        else:
            print(f" 매물 삭제 실패: ID {property_id}")
            return jsonify({'success': False, 'message': '매물을 찾을 수 없습니다.'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employee/unchecked-likes', methods=['GET'])
def employee_unchecked_likes():
    """직원용 미확인 좋아요 수 조회 API"""
    if 'employee_id' not in session:
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        management_site_id = request.args.get('management_site_id')
        link_type = request.args.get('type', 'residence')  # residence 또는 business
        
        if not management_site_id:
            return jsonify({'error': 'management_site_id가 필요합니다.'}), 400
        
        # Supabase 연결 확인
        supabase = supabase_utils.get_supabase()
        if not supabase:
            print(f" Supabase 연결 실패 - 0 반환")
            return jsonify({'success': True, 'count': 0})
        
        # 실제 데이터베이스에서 미확인 좋아요 수 조회
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': '데이터베이스 연결 실패'}), 500
        
        if link_type == 'residence':
            # 주거사이트 링크에서 미확인 좋아요 수 조회
            response = supabase.table('residence_links').select('id').eq('management_site_id', management_site_id).eq('liked', True).eq('is_checked', False).execute()
        elif link_type == 'business':
            # 업무사이트 링크에서 미확인 좋아요 수 조회
            response = supabase.table('office_links').select('id').eq('management_site_id', management_site_id).eq('liked', True).eq('is_checked', False).execute()
        else:
            # 알 수 없는 타입은 0 반환
            return jsonify({'success': True, 'count': 0})
        
        unchecked_count = len(response.data) if response.data else 0
        
        print(f" 미확인 좋아요 수 조회 성공: {management_site_id} - {unchecked_count}개")
        return jsonify({'success': True, 'count': unchecked_count})
        
    except Exception as e:
        print(f" 미확인 좋아요 수 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/maeiple', methods=['GET', 'POST'])
def maeiple_api():
    """매이플관리 API - 매물 조회 및 생성 (관리자 및 팀장)"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    # POST 요청(매물 생성)의 경우 관리자 또는 팀장만 접근 가능
    if request.method == 'POST':
        if not session.get('is_admin') and session.get('employee_role') != '팀장':
            return jsonify({'error': '관리자 또는 팀장 권한이 필요합니다.'}), 403
    
    if request.method == 'GET':
        # 정렬 파라미터 가져오기 (ID 기준으로 고정하여 순위 유지)
        sort_by = request.args.get('sort_by', 'id')  # 기본: ID (순위 고정)
        sort_order = request.args.get('sort_order', 'asc')  # 기본: 오름차순
        
        # 페이지네이션 파라미터
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Supabase 연결
        supabase = supabase_utils.get_supabase()
        if not supabase:
            print(" Supabase 연결 실패 - 테스트 모드로 동작")
            
            # 테스트 모드에서는 세션에 저장된 매물 데이터 반환
            if 'test_maeiple_properties' in session:
                test_properties = session['test_maeiple_properties']
                print(f" 테스트 모드 - 세션에 저장된 매물 {len(test_properties)}개 반환")
                
                # 정렬 적용
                if sort_by == 'id':
                    test_properties.sort(key=lambda x: x.get('id', 0), reverse=(sort_order == 'desc'))
                elif sort_by == 'check_date':
                    test_properties.sort(key=lambda x: x.get('check_date', ''), reverse=(sort_order == 'desc'))
                
                # 페이지네이션 적용
                total_count = len(test_properties)
                paginated_properties = test_properties[offset:offset + per_page]
                total_pages = (total_count + per_page - 1) // per_page
                
                return jsonify({
                    'success': True,
                    'properties': paginated_properties,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages
                })
            else:
                print(" 테스트 모드 - 세션에 저장된 매물 없음")
                return jsonify({
                    'success': True,
                    'properties': [],
                    'total_count': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                })
        
        try:
            # **관리자는 모든 매물 데이터 조회** (삭제되지 않은 모든 데이터)
            print(f" 관리자용 메이플관리 - 모든 DB 데이터 조회 시작")
            
            # 전체 카운트 조회
            count_response = supabase.table('maeiple_properties').select('id', count='exact').execute()
            total_count = count_response.count if count_response.count else 0
            
            # 정렬 컬럼 유효성 검사
            valid_sort_columns = ['id', 'check_date', 'building_number', 'room_number', 'status', 'jeonse_price', 'monthly_rent', 'sale_price', 'created_at', 'updated_at']
            if sort_by not in valid_sort_columns:
                sort_by = 'id'  # 기본값을 ID로 변경
            
            # 정렬 방향 유효성 검사
            if sort_order not in ['asc', 'desc']:
                sort_order = 'asc'  # 기본값을 오름차순으로 변경
            
            # 모든 매물 데이터 조회 (페이지네이션 적용)
            query = supabase.table('maeiple_properties').select('*')
            
            # 정렬 적용
            query = query.order(sort_by, desc=(sort_order == 'desc'))
            
            # 페이지네이션 적용
            query = query.range(offset, offset + per_page - 1)
            
            response = query.execute()
            
            if hasattr(response, 'data') and response.data:
                properties = response.data
                total_pages = (total_count + per_page - 1) // per_page
                
                print(f" 관리자용 메이플관리 조회 성공: {len(properties)}개 매물 (전체: {total_count}개, 페이지: {page}/{total_pages})")
                
                return jsonify({
                    'success': True,
                    'properties': properties,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages
                })
            else:
                print(" 매물 데이터 없음")
                return jsonify({
                    'success': True,
                    'properties': [],
                    'total_count': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                })
                
        except Exception as e:
            print(f" 관리자용 메이플관리 조회 오류: {e}")
            return jsonify({
                'success': False,
                'error': f'매물 조회 중 오류가 발생했습니다: {str(e)}'
            }), 500
        
        # 아래는 기존 테스트 데이터 (삭제 예정)
        if False:  # 테스트 모드 비활성화
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
                    'employee_id': current_user,  # 실제 세션 값 사용
                    'employee_name': current_name,  # 실제 세션 값 사용
                    'employee_team': current_team   # 실제 세션 값 사용
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
                    'employee_id': current_user,  # 실제 세션 값 사용
                    'employee_name': current_name,  # 실제 세션 값 사용
                    'employee_team': current_team   # 실제 세션 값 사용
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
            
            # 테스트 모드 완전 제거 - 실제 DB 데이터만 사용
        
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
                print(" 매물 목록 조회 실패")
                return jsonify({
                    'success': False,
                    'properties': [],
                    'total_count': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                })
            
        except Exception as e:
            print(f" 매물 목록 조회 중 오류: {e}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            print("=== 관리자 메이플관리 매물 생성 API 호출 ===")
            data = request.json
            print(f" 받은 데이터: {data}")
            
            # 현재 로그인한 사용자 정보 가져오기
            if session.get('is_admin'):
                employee_id = 'admin'
                employee_name = '관리자'
                employee_team = '관리자'
            else:
                employee_id = session.get('employee_id', 'system')
                employee_name = session.get('employee_name', '시스템')
                employee_team = session.get('employee_team', '관리자')

            print(f" 사용자 정보: {employee_id} ({employee_name}) - 팀: {employee_team}")

            # 모든 필드는 선택사항 (필수 검증 제거)
            building_number = data.get('building_number')
            room_number = data.get('room_number')
            
            print(f" 받은 동/호수: 동={building_number}, 호={room_number}")

            # 데이터 정리 및 변환
            def clean_value(value, field_type='text'):
                if value is None or value == '' or value == '-':
                    if field_type == 'int':
                        return None
                    elif field_type == 'bool':
                        return False
                    else:
                        return ''
                return value

            property_data = {
                'check_date': clean_value(data.get('check_date')) or datetime.now().strftime('%Y-%m-%d'),
                'building_number': str(building_number).strip(),
                'room_number': str(room_number).strip(),
                'status': clean_value(data.get('status')) or '거래가능',
                'jeonse_price': clean_value(data.get('jeonse_price'), 'int'),
                'monthly_deposit': clean_value(data.get('monthly_deposit'), 'int'),
                'monthly_rent': clean_value(data.get('monthly_rent'), 'int'),
                'sale_price': clean_value(data.get('sale_price'), 'int'),
                'is_occupied': clean_value(data.get('is_occupied'), 'bool'),
                'phone': clean_value(data.get('phone')),
                'memo': clean_value(data.get('memo')),
                'likes': 0,
                'dislikes': 0,
                'employee_id': employee_id,
                'employee_name': employee_name,
                'employee_team': employee_team,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            print(f" 생성할 매물 데이터: {property_data}")

            # Supabase 연결 확인
            if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
                print(" 테스트 모드 - 매물 생성 시뮬레이션")
                
                # 테스트 모드에서는 가상 ID 생성
                import random
                new_id = random.randint(1000, 9999)
                
                # 생성된 매물을 세션에 저장 (실제로는 메모리에만 저장)
                if 'test_maeiple_properties' not in session:
                    session['test_maeiple_properties'] = []
                
                new_property = {
                    'id': new_id,
                    **property_data
                }
                
                session['test_maeiple_properties'].append(new_property)
                print(f" 테스트 모드 매물 생성 완료: ID {new_id}")
                print(f" 현재 테스트 매물 수: {len(session['test_maeiple_properties'])}")
                
                return jsonify({
                    'success': True, 
                    'id': new_id,
                    'message': '테스트 모드 - 매물이 성공적으로 생성되었습니다.',
                    'created_property': new_property
                })

            # 실제 Supabase 연결이 있는 경우
            print(" Supabase 연결 시도...")
            try:
                new_prop = supabase_utils.create_maeiple_property(property_data)
                if not new_prop:
                    print(" Supabase 매물 생성 실패 - create_maeiple_property returned None")
                    return jsonify({'success': False, 'error': '매물 생성 실패: 데이터베이스 저장 오류'}), 500

                print(f" Supabase 매물 생성 완료: {new_prop}")
                return jsonify({
                    'success': True, 
                    'id': new_prop.get('id'),
                    'message': '매물이 성공적으로 생성되었습니다.',
                    'created_property': new_prop
                })
            except Exception as supabase_error:
                print(f" Supabase 매물 생성 중 예외 발생: {supabase_error}")
                import traceback
                traceback.print_exc()
                return jsonify({'success': False, 'error': f'데이터베이스 오류: {str(supabase_error)}'}), 500

        except Exception as e:
            print(f" 매물 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'매물 생성 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/team-leader/team-maeiple', methods=['GET'])
def team_leader_team_maeiple():
    """팀장 전용 팀 통합 메이플관리 API - 팀 전체의 매물 조회 (팀 통합용)"""
    print(f" 팀장 팀 통합용 API 호출 - 세션 정보:")
    print(f"  - employee_id: {session.get('employee_id')}")
    print(f"  - employee_role: {session.get('employee_role')}")
    print(f"  - employee_team: {session.get('employee_team')}")
    print(f"  - is_admin: {session.get('is_admin')}")
    
    if 'employee_id' not in session and not session.get('is_admin'):
        print(" 로그인이 필요합니다.")
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    # 팀장이 아니면 접근 거부
    if session.get('employee_role') != '팀장' and not session.get('is_admin'):
        print(f" 팀장만 접근 가능합니다. 현재 역할: {session.get('employee_role')}")
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
        print(" 테스트 모드 - 팀장 팀 통합용 샘플 매물 데이터 반환")
        
        # 현재 사용자의 팀 정보 가져오기
        current_team = session.get('employee_team', '')
        print(f" 팀장 팀 통합용 메이플관리 - 팀: {current_team}")
        
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
        print(f" 팀별 필터링: {current_team}팀 매물 {len(team_properties)}개")
        
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
    print(f" /api/user-info 호출 - 세션 정보:")
    print(f"  - is_admin: {session.get('is_admin')}")
    print(f"  - employee_id: {session.get('employee_id')}")
    print(f"  - employee_name: {session.get('employee_name')}")
    print(f"  - employee_team: {session.get('employee_team')}")
    print(f"  - employee_role: {session.get('employee_role')}")
    
    if not session.get('is_admin') and 'employee_id' not in session:
        print(" 로그인이 필요합니다.")
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    user_info = {
        'is_admin': session.get('is_admin', False),
        'employee_id': session.get('employee_id', ''),
        'employee_name': session.get('employee_name', ''),
        'name': session.get('employee_name', ''),  # JavaScript에서 참조하는 name 필드 추가
        'employee_team': session.get('employee_team', ''),
        'role': session.get('employee_role', '직원'),
        'employee_role': session.get('employee_role', '직원')  # 중복 필드로 호환성 확보
    }
    
    print(f" 반환할 user_info: {user_info}")
    return jsonify(user_info)

@app.route('/api/maeiple/update', methods=['POST'])
def maeiple_update():
    """매이플관리 매물 업데이트 API (개별 필드)"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return jsonify({'error': '관리자 또는 팀장 권한이 필요합니다.'}), 403
    
    try:
        data = request.json
        property_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([property_id, field]):
            return jsonify({'error': '필수 파라미터가 누락되었습니다.'}), 400
        
        # Supabase 연결
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 업데이트 가능한 필드 검증
        allowed_fields = ['status', 'jeonse_price', 'monthly_rent', 'monthly_deposit', 'sale_price', 
                         'is_occupied', 'phone', 'memo', 'likes', 'dislikes', 'check_date',
                         'building_number', 'room_number', 'employee_id', 'employee_name', 'employee_team', 'deposit']
        
        if field not in allowed_fields:
            return jsonify({'error': '업데이트할 수 없는 필드입니다.'}), 400
        
        # 업데이트 데이터 준비
        update_data = {field: value}
        
        # 업데이트 실행
        response = supabase.table('maeiple_properties').update(update_data).eq('id', property_id).execute()
        
        if hasattr(response, 'data') and response.data:
            print(f" 메이플 매물 업데이트 성공: ID={property_id}, {field}={value}")
            return jsonify({'success': True, 'message': f'{field} 업데이트 완료'})
        else:
            return jsonify({'error': '매물을 찾을 수 없거나 업데이트에 실패했습니다.'}), 404
        
        return jsonify({'success': True, 'message': '업데이트 완료'})
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/maeiple/<int:property_id>', methods=['GET'])
def get_maeiple_property(property_id):
    """개별 매물 조회 API"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 매물 조회
        response = supabase.table('maeiple_properties').select('*').eq('id', property_id).execute()
        
        if response.data and len(response.data) > 0:
            property_data = response.data[0]
            return jsonify(property_data)
        else:
            return jsonify({'error': '매물을 찾을 수 없습니다.'}), 404
            
    except Exception as e:
        print(f" 매물 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/maeiple/<int:property_id>/update', methods=['PUT'])
def maeiple_bulk_update(property_id):
    """매이플관리 매물 업데이트 API (전체 필드)"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    try:
        data = request.json
        if not data:
            return jsonify({'error': '업데이트할 데이터가 없습니다.'}), 400
        
        # Supabase 연결
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # 업데이트 가능한 필드 검증
        allowed_fields = ['status', 'jeonse_price', 'monthly_rent', 'monthly_deposit', 'sale_price', 
                         'is_occupied', 'phone', 'memo', 'likes', 'dislikes', 'check_date',
                         'building_number', 'room_number', 'employee_id', 'employee_name', 'employee_team', 'deposit']
        
        # 허용된 필드만 필터링
        update_data = {}
        for field, value in data.items():
            if field in allowed_fields:
                update_data[field] = value
        
        if not update_data:
            return jsonify({'error': '업데이트할 수 있는 필드가 없습니다.'}), 400
        
        print(f" 매물 {property_id} 업데이트 데이터: {update_data}")
        
        # 업데이트 실행
        response = supabase.table('maeiple_properties').update(update_data).eq('id', property_id).execute()
        
        if hasattr(response, 'data') and response.data:
            print(f" 메이플 매물 전체 업데이트 성공: ID={property_id}")
            return jsonify({'success': True, 'message': '매물 정보가 업데이트되었습니다.'})
        else:
            return jsonify({'error': '매물을 찾을 수 없거나 업데이트에 실패했습니다.'}), 404
        
    except Exception as e:
        print(f" 매물 업데이트 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/maeiple/memo', methods=['POST'])
def maeiple_memo():
    """매이플관리 메모 저장 API"""
    if 'employee_id' not in session and not session.get('is_admin'):
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return jsonify({'error': '관리자 또는 팀장 권한이 필요합니다.'}), 403
    
    try:
        data = request.json
        property_id = data.get('id')
        memo = data.get('memo', '')
        
        if not property_id:
            return jsonify({'error': '매물 ID가 필요합니다.'}), 400
        
        # DATABASE_URL이 없으면 테스트 모드로 처리
        if not os.environ.get('DATABASE_URL'):
            print(f" 테스트 모드 - 메모 저장 시뮬레이션: ID {property_id}, 메모: {memo}")
            return jsonify({'success': True, 'message': '테스트 모드 - 메모 저장 시뮬레이션 완료'})
        
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
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
            print(f" 테스트 모드 - 매물 삭제 시뮬레이션: ID {property_id}")
            return jsonify({'success': True, 'message': '테스트 모드 - 매물 삭제 시뮬레이션 완료'})
        
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
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

# ==================== 메이플관리 일괄 처리 API ====================

@app.route('/api/maeiple/bulk-assign', methods=['POST'])
def maeiple_bulk_assign():
    """메이플관리 매물 일괄 담당자 변경 API (관리자 및 팀장)"""
    # 관리자 또는 팀장만 접근 가능
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return jsonify({'error': '관리자 또는 팀장 권한이 필요합니다.'}), 403
    
    try:
        data = request.json
        property_ids = data.get('property_ids', [])
        employee_id = data.get('employee_id')
        employee_name = data.get('employee_name')
        
        if not property_ids:
            return jsonify({'error': '선택된 매물이 없습니다.'}), 400
        
        if not employee_id or not employee_name:
            return jsonify({'error': '담당자 정보가 없습니다.'}), 400
        
        # 팀장의 경우 권한 확인
        if session.get('employee_role') == '팀장':
            team_name = session.get('employee_team')
            print(f" 팀장 권한 확인 - 팀: {team_name}")
            
            # 팀장은 자신의 팀 매물만 변경 가능
            if not team_name:
                return jsonify({'error': '팀 정보가 없습니다.'}), 400
        
        # Supabase 연결 시도
        supabase = supabase_utils.get_supabase()
        if supabase:
            # Supabase를 사용하여 실제 DB 업데이트
            print(f" Supabase를 사용하여 일괄 담당자 변경: {len(property_ids)}개 매물  {employee_name}")
            success_count = 0
            
            for property_id in property_ids:
                try:
                    # 팀장의 경우 매물 소유권 확인
                    if session.get('employee_role') == '팀장':
                        # 해당 매물이 자신의 팀 매물인지 확인
                        property_check = supabase.table('maeiple_properties').select('employee_team').eq('id', property_id).execute()
                        if property_check.data:
                            property_team = property_check.data[0].get('employee_team')
                            if property_team != team_name:
                                print(f" 권한 없음: 매물 {property_id}는 {property_team} 소속 (현재 팀장: {team_name})")
                                continue
                        else:
                            print(f" 매물 {property_id} 정보를 찾을 수 없음")
                            continue
                    
                    response = supabase.table('maeiple_properties').update({
                        'employee_id': employee_id,
                        'employee_name': employee_name
                    }).eq('id', property_id).execute()
                    
                    if response.data:
                        success_count += 1
                        print(f" 매물 {property_id} 담당자 변경 성공")
                    else:
                        print(f" 매물 {property_id} 담당자 변경 실패: 응답 데이터 없음")
                except Exception as e:
                    print(f" 매물 {property_id} 담당자 변경 오류: {e}")
            
            print(f" 일괄 담당자 변경 결과: {success_count}/{len(property_ids)}개 성공")
        else:
            # Supabase 연결 실패 시 테스트 모드
            print(f" Supabase 연결 실패 - 테스트 모드로 일괄 담당자 변경 시뮬레이션: {len(property_ids)}개 매물  {employee_name}")
            return jsonify({'success': True, 'message': f'테스트 모드 - {len(property_ids)}개 매물 담당자 변경 시뮬레이션 완료'})
        
        return jsonify({
            'success': True, 
            'message': f'{len(property_ids)}개 매물의 담당자가 {employee_name}으로 변경되었습니다.'
        })
        
    except Exception as e:
        print(f" 일괄 담당자 변경 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/maeiple/bulk-assign-team', methods=['POST'])
def maeiple_bulk_assign_team():
    """메이플관리 매물 일괄 팀 변경 API"""
    if not session.get('is_admin'):
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
    
    try:
        data = request.json
        property_ids = data.get('property_ids', [])
        team_name = data.get('team_name')
        
        if not property_ids:
            return jsonify({'error': '선택된 매물이 없습니다.'}), 400
        
        if not team_name:
            return jsonify({'error': '팀 정보가 없습니다.'}), 400
        
        # Supabase 연결 시도
        supabase = supabase_utils.get_supabase()
        if supabase:
            # Supabase를 사용하여 실제 DB 업데이트
            print(f" Supabase를 사용하여 일괄 팀 변경: {len(property_ids)}개 매물  {team_name}")
            success_count = 0
            
            for property_id in property_ids:
                try:
                    response = supabase.table('maeiple_properties').update({
                        'employee_team': team_name
                    }).eq('id', property_id).execute()
                    
                    if response.data:
                        success_count += 1
                        print(f" 매물 {property_id} 팀 변경 성공")
                    else:
                        print(f" 매물 {property_id} 팀 변경 실패: 응답 데이터 없음")
                except Exception as e:
                    print(f" 매물 {property_id} 팀 변경 오류: {e}")
            
            print(f" 일괄 팀 변경 결과: {success_count}/{len(property_ids)}개 성공")
        else:
            # Supabase 연결 실패 시 테스트 모드
            print(f" Supabase 연결 실패 - 테스트 모드로 일괄 팀 변경 시뮬레이션: {len(property_ids)}개 매물  {team_name}")
            return jsonify({'success': True, 'message': f'테스트 모드 - {len(property_ids)}개 매물 팀 변경 시뮬레이션 완료'})
        
        return jsonify({
            'success': True, 
            'message': f'{len(property_ids)}개 매물의 팀이 {team_name}으로 변경되었습니다.'
        })
        
    except Exception as e:
        print(f" 일괄 팀 변경 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/maeiple/bulk-delete', methods=['POST'])
def maeiple_bulk_delete():
    """메이플관리 매물 일괄 삭제 API"""
    if not session.get('is_admin'):
        return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
    
    try:
        data = request.json
        property_ids = data.get('property_ids', [])
        
        if not property_ids:
            return jsonify({'error': '선택된 매물이 없습니다.'}), 400
        
        # Supabase 연결 시도
        supabase = supabase_utils.get_supabase()
        if supabase:
            # Supabase를 사용하여 실제 DB 삭제
            print(f" Supabase를 사용하여 일괄 삭제: {len(property_ids)}개 매물")
            success_count = 0
            
            for property_id in property_ids:
                try:
                    response = supabase.table('maeiple_properties').delete().eq('id', property_id).execute()
                    
                    if response.data:
                        success_count += 1
                        print(f" 매물 {property_id} 삭제 성공")
                    else:
                        print(f" 매물 {property_id} 삭제 실패: 응답 데이터 없음")
                except Exception as e:
                    print(f" 매물 {property_id} 삭제 오류: {e}")
            
            print(f" 일괄 삭제 결과: {success_count}/{len(property_ids)}개 성공")
        else:
            # Supabase 연결 실패 시 테스트 모드
            print(f" Supabase 연결 실패 - 테스트 모드로 일괄 삭제 시뮬레이션: {len(property_ids)}개 매물")
            return jsonify({'success': True, 'message': f'테스트 모드 - {len(property_ids)}개 매물 삭제 시뮬레이션 완료'})
        
        return jsonify({
            'success': True, 
            'message': f'{len(property_ids)}개 매물이 삭제되었습니다.'
        })
        
    except Exception as e:
        print(f" 일괄 삭제 오류: {e}")
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
        print(" 테스트 모드 - 팀장 팀 통합용 샘플 고객 데이터 반환")
        
        # 현재 팀 정보
        current_team = session.get('employee_team', '')
        print(f" 팀장 팀 통합용 고객관리 - 팀: {current_team}")
        
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
        supabase = supabase_utils.get_supabase()
        if not supabase:
            return jsonify({'error': 'Database connection failed'}), 500
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

@app.route('/api/db-status', methods=['GET'])
def check_db_status():
    """데이터베이스 연결 상태 확인 API"""
    print("=== DB 연결 상태 확인 ===")
    
    status_info = {
        'timestamp': datetime.now().isoformat(),
        'force_test_mode': FORCE_TEST_MODE,
        'environment': 'local' if not os.environ.get('RAILWAY_ENVIRONMENT') else 'railway'
    }
    
    # 환경 변수 확인
    env_vars = {
        'SUPABASE_URL': os.environ.get('SUPABASE_URL'),
        'SUPABASE_KEY': os.environ.get('SUPABASE_KEY'),
        'DATABASE_URL': os.environ.get('DATABASE_URL'),
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT')
    }
    
    status_info['environment_variables'] = env_vars
    
    # Supabase 연결 상태 확인
    try:
        supabase_client = supabase_utils.get_supabase()
        if supabase_client:
            status_info['supabase_status'] = 'connected'
            status_info['supabase_url'] = str(supabase_client.supabase_url)
            print(" Supabase 연결됨")
        else:
            status_info['supabase_status'] = 'not_initialized'
            print(" Supabase 초기화되지 않음")
    except Exception as e:
        status_info['supabase_status'] = 'error'
        status_info['supabase_error'] = str(e)
        print(f" Supabase 상태 확인 오류: {e}")
    
    # 테스트 모드 여부 확인
    if FORCE_TEST_MODE:
        status_info['current_mode'] = 'test_mode_forced'
        print(" 테스트 모드 강제 활성화")
    elif not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        status_info['current_mode'] = 'test_mode_no_credentials'
        print(" 테스트 모드 - Supabase 인증 정보 없음")
    else:
        status_info['current_mode'] = 'production_mode'
        print(" 프로덕션 모드 - Supabase 연결됨")
    
    # 세션 정보 확인
    if 'test_maeiple_properties' in session:
        status_info['test_data_count'] = len(session['test_maeiple_properties'])
        print(f" 테스트 데이터 수: {status_info['test_data_count']}개")
    else:
        status_info['test_data_count'] = 0
        print(" 테스트 데이터 없음")
    
    print(f" DB 상태 정보: {status_info}")
    return jsonify(status_info)

@app.route('/api/employee/session-info', methods=['GET'])
def get_employee_session_info():
    """직원의 현재 세션 정보를 반환합니다."""
    try:
        session_info = {
            'employee_id': session.get('employee_id'),
            'employee_name': session.get('employee_name'),
            'employee_role': session.get('employee_role'),
            'employee_team': session.get('employee_team'),
            'is_admin': session.get('is_admin', False),
            'is_team_leader': session.get('employee_role') == '팀장',
            'logged_in': 'employee_id' in session or 'is_admin' in session
        }
        
        print(f" 세션 정보 조회: {session_info}")
        return jsonify(session_info)
        
    except Exception as e:
        print(f" 세션 정보 조회 오류: {e}")
        return jsonify({'error': f'세션 정보 조회 실패: {e}'}), 500

if __name__ == '__main__':
    # PORT 환경변수 처리 개선
    port = int(os.environ.get('PORT', 8080))
    print(f" 서버 시작 - 포트: {port}")
    print(f" 환경변수 PORT: {os.environ.get('PORT', '설정되지 않음')}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        print(f" 서버 시작 실패: {e}")
        # 포트가 사용 중인 경우 다른 포트 시도
        if "Address already in use" in str(e):
            fallback_port = 8081
            print(f" 포트 {port}가 사용 중입니다. 포트 {fallback_port}로 시도합니다.")
            app.run(host='0.0.0.0', port=fallback_port, debug=True)