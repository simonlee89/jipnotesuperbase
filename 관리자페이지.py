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
        
        if employee and employee.get('password') == password:
            # 로그인 성공
            session['employee_id'] = employee['id']
            session['employee_name'] = employee['name']
            session['employee_team'] = employee.get('team', '')
            session['employee_role'] = employee.get('role', 'employee')
            
            # 마지막 로그인 시간 업데이트
            supabase_utils.update_employee_last_login(employee['id'])
            
            print(f"✅ 직원 로그인 성공: {employee['name']} ({employee.get('role', 'employee')})")
            return jsonify({'success': True, 'message': '로그인 성공'})
        else:
            # 로그인 실패
            return jsonify({'success': False, 'message': '직원 이름 또는 비밀번호가 올바르지 않습니다.'})
            
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")
        # 오류 발생 시 테스트 모드로 폴백
        if FORCE_TEST_MODE:
            print("⚠️ 테스트 모드 - 임시 로그인 허용")
            if employee_id in ['원형', '테스트', 'admin', '관리자', '수정'] and password == '1':
                session['employee_id'] = employee_id
                session['employee_name'] = employee_id
                if employee_id == '수정':
                    session['employee_team'] = '위플러스'
                    session['employee_role'] = '팀장'
                    print(f"🎯 '수정' 사용자 감지 - 팀장으로 설정")
                else:
                    session['employee_team'] = '관리자'
                    session['employee_role'] = '직원'
                return jsonify({'success': True, 'message': '테스트 모드 로그인 성공'})
        
        return jsonify({'success': False, 'message': '로그인 중 오류가 발생했습니다.'})
    
    # 테스트 모드 로그인 처리
    if employee_id in ['원형', '테스트', 'admin', '관리자', '수정'] and password == '1':
        session['employee_id'] = employee_id
        session['employee_name'] = employee_id
        if employee_id == '수정':
            session['employee_team'] = '위플러스'
            session['employee_role'] = '팀장'
        else:
            session['employee_team'] = '관리자'
            session['employee_role'] = '직원'
            print(f"👤 '{employee_id}' 사용자 감지 - 직원으로 설정")
        
        print(f"✅ 테스트 로그인 성공: {employee_id}")
        print(f"  - 세션 employee_id: {session['employee_id']}")
        print(f"  - 세션 employee_name: {session['employee_name']}")
        print(f"  - 세션 employee_team: {session['employee_team']}")
        print(f"  - 세션 employee_role: {session['employee_role']}")
        
        # 역할에 따른 리다이렉트 정보 포함
        if employee_id == '수정':
            return jsonify({
                'success': True, 
                'message': '테스트 로그인 성공',
                'redirect': '/team-leader',
                'role': '팀장'
            })
        else:
            return jsonify({
                'success': True, 
                'message': '테스트 로그인 성공',
                'redirect': '/dashboard',
                'role': '직원'
            })
    else:
        print(f"❌ 허용되지 않은 사용자 또는 잘못된 비밀번호")
        return jsonify({'success': False, 'message': '테스트 모드에서는 지정된 이름과 비밀번호를 사용해주세요.'})
    
    # Supabase를 사용한 로그인 처리
    try:
        from supabase_utils import get_employee_by_name, update_employee_last_login
        
        # 직원 정보 조회
        employee = get_employee_by_name(employee_id)
        
        if employee:
            # 비밀번호 확인
            if employee.get('password') != password:
                print(f"❌ 비밀번호 불일치: '{employee_id}'")
                return jsonify({'success': False, 'message': '비밀번호가 일치하지 않습니다.'})
            
            # 세션 설정
            session['employee_id'] = employee['name']
            session['employee_name'] = employee['name']
            session['employee_role'] = employee.get('role', 'employee')
            session['employee_team'] = employee.get('team', '미지정')
            
            # 마지막 로그인 시간 업데이트
            update_employee_last_login(employee['name'])
            
            print(f"✅ Supabase 로그인 성공: {employee['name']} (팀:{session['employee_team']}, 역할:{session['employee_role']})")
            
            # 역할에 따른 리다이렉트 정보 포함
            if employee['name'] == '수정':
                return jsonify({
                    'success': True, 
                    'message': '로그인 성공',
                    'redirect': '/team-leader',
                    'role': '팀장'
                })
            else:
                return jsonify({
                    'success': True, 
                    'message': '로그인 성공',
                    'redirect': '/dashboard',
                    'role': 'employee'
                })
        else:
            print(f"❌ 로그인 실패: '{employee_id}' 직원을 찾을 수 없음")
            return jsonify({'success': False, 'message': '존재하지 않는 직원입니다.'})
            
    except Exception as e:
        print(f"❌ Supabase 로그인 처리 중 오류: {e}")
        return jsonify({'success': False, 'message': '로그인 처리 중 오류가 발생했습니다.'})

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
    
    # DATABASE_URL이 없으면 테스트 모드로 처리
    if not os.environ.get('DATABASE_URL'):
        print("⚠️ 테스트 모드 - 대시보드 접근 허용")
        guarantee_list = []  # 빈 리스트로 처리
    else:
        # 관리자가 아닌 경우 직원이 여전히 존재하는지 확인
        if not session.get('is_admin'):
            conn = None
            try:
                conn, _ = db_utils.get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT id, name FROM employees WHERE name = %s', (employee_name,))
                employee = cursor.fetchone()
                
                if not employee:
                    # 직원이 삭제된 경우 오류 페이지 표시
                    return render_template('employee_error.html')
            except Exception as e:
                print(f"직원 존재 확인 오류: {e}")
                return render_template('employee_error.html')
            finally:
                if conn:
                    conn.close()
        
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
    
    # DATABASE_URL이 없으면 테스트용 빈 목록 반환
    if not os.environ.get('DATABASE_URL'):
        print("⚠️ 테스트 모드 - 팀장 패널 빈 보증보험 목록 반환")
        guarantee_list = []
    else:
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
            print(f"팀장 패널 보증보험 목록 조회 오류: {e}")
        finally:
            if conn:
                conn.close()
    
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

    # DATABASE_URL이 없으면 테스트용 빈 목록 반환
    if not os.environ.get('DATABASE_URL'):
        print("⚠️ 테스트 모드 - 빈 보증보험 목록 반환")
        guarantee_list = []
        return render_template('admin_panel.html', 
                             guarantee_list=guarantee_list,
                             residence_site_url=RESIDENCE_SITE_URL,
                             business_site_url=BUSINESS_SITE_URL)

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
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
        return redirect(url_for('index'))
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 보증보험 상태를 FALSE로 변경 (매물은 유지하되 보증보험 리스트에서만 제거)
        cursor.execute('UPDATE links SET guarantee_insurance = FALSE WHERE id = %s', (id,))
        
        # 선택적: 완전 삭제를 원하면 아래 주석을 해제
        # cursor.execute('DELETE FROM links WHERE id = %s', (id,))
        
        conn.commit()
        flash('보증보험 매물이 리스트에서 제거되었습니다.', 'success')
        return redirect(url_for('admin_panel'))
    except Exception as e:
        if conn: conn.rollback()
        flash(f'삭제 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('admin_panel'))
    finally:
        if conn: conn.close()

@app.route('/admin/guarantee-edit/<int:id>', methods=['POST'])
def guarantee_edit(id):
    if not session.get('is_admin') and session.get('employee_role') != '팀장':
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
    
    # 페이지네이션 파라미터 (GET 요청일 때만)
    if request.method == 'GET':
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
    
    # DATABASE_URL이 없으면 테스트용 빈 목록 반환
    if not os.environ.get('DATABASE_URL'):
        print("⚠️ 테스트 모드 - 빈 직원 목록 반환")
        if request.method == 'GET':
            return jsonify({
                'employees': [],
                'total_count': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            })
        elif request.method == 'POST':
            return jsonify({'success': False, 'message': '테스트 모드에서는 직원 추가가 지원되지 않습니다.'})
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            # 전체 개수 조회
            cursor.execute('SELECT COUNT(*) FROM employees')
            total_count = cursor.fetchone()[0]
            
            # 페이지네이션 적용한 데이터 조회
            cursor.execute('SELECT id, name, email, team, position, created_at, role, status FROM employees ORDER BY created_at DESC LIMIT %s OFFSET %s', (per_page, offset))
            employees_raw = cursor.fetchall()
            print(f"[직원 목록] 조회된 직원 수: {len(employees_raw)} (페이지 {page}/{(total_count + per_page - 1) // per_page})")
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
            return jsonify({
                'employees': employees,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            })

        if request.method == 'POST':
            print("🔄 직원 추가 요청 받음")
            data = request.get_json()
            print(f"📥 요청 데이터: {data}")
            
            employee_id = data.get('employee_id')  # 실제로는 name으로 사용
            employee_name = data.get('employee_name')
            team = data.get('team', '')
            email = data.get('email', '')
            position = data.get('position', '')
            role = data.get('role', '직원')  # 새로 추가된 역할 필드
            
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
                VALUES (%s, %s, %s, %s, %s, %s, 'active') RETURNING *
            """, (name, email, team, position, datetime.now(), role))
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
        # all_employees 파라미터로 모든 직원의 고객 조회 여부 결정
        all_employees = request.args.get('all_employees') == 'true'
        
        # 페이지네이션 파라미터
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # DATABASE_URL이 없으면 테스트용 샘플 고객 목록 반환
        if not os.environ.get('DATABASE_URL'):
            print("⚠️ 테스트 모드 - 샘플 고객 목록 반환")
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
            
        conn = None
        try:
            conn, _ = db_utils.get_db_connection()
            cursor = conn.cursor()
            
            # 전체 개수 조회
            if session.get('is_admin') and all_employees:
                count_query = "SELECT COUNT(*) FROM employee_customers"
                cursor.execute(count_query)
                total_count = cursor.fetchone()[0]
                
                query = "SELECT * FROM employee_customers ORDER BY inquiry_date DESC, id DESC LIMIT %s OFFSET %s"
                cursor.execute(query, (per_page, offset))
            elif employee_id == 'admin':
                count_query = "SELECT COUNT(*) FROM employee_customers"
                cursor.execute(count_query)
                total_count = cursor.fetchone()[0]
                
                query = "SELECT * FROM employee_customers ORDER BY inquiry_date DESC, id DESC LIMIT %s OFFSET %s"
                cursor.execute(query, (per_page, offset))
            else:
                count_query = "SELECT COUNT(*) FROM employee_customers WHERE employee_id = %s"
                cursor.execute(count_query, (employee_id,))
                total_count = cursor.fetchone()[0]
                
                query = "SELECT * FROM employee_customers WHERE employee_id = %s ORDER BY inquiry_date DESC, id DESC LIMIT %s OFFSET %s"
                cursor.execute(query, (employee_id, per_page, offset))
            
            customers_raw = cursor.fetchall()
            customers_list = [db_utils.dict_from_row(row) for row in customers_raw]
            
            # employee_name 필드 추가 (employee_id와 동일하게 설정)
            for customer in customers_list:
                customer['employee_name'] = customer.get('employee_id', '')
            
            # LEFT JOIN을 사용한 효율적인 미확인 좋아요 수 계산
            try:
                # 모든 고객의 미확인 좋아요 수를 한 번에 가져오기
                query = """
                    SELECT 
                        ec.id,
                        COALESCE(residence_likes.count, 0) as unchecked_likes_residence,
                        COALESCE(business_likes.count, 0) as unchecked_likes_business
                    FROM employee_customers ec
                    LEFT JOIN (
                        SELECT management_site_id, COUNT(*) as count 
                        FROM links 
                        WHERE liked = TRUE AND COALESCE(is_checked, FALSE) = FALSE 
                        GROUP BY management_site_id
                    ) residence_likes ON ec.management_site_id = residence_likes.management_site_id
                    LEFT JOIN (
                        SELECT management_site_id, COUNT(*) as count 
                        FROM office_links 
                        WHERE liked = TRUE AND COALESCE(is_checked, FALSE) = FALSE 
                        GROUP BY management_site_id
                    ) business_likes ON ec.management_site_id = business_likes.management_site_id
                """
                
                if employee_id != 'admin':
                    query += " WHERE ec.employee_id = %s"
                    cursor.execute(query, (employee_id,))
                else:
                    cursor.execute(query)
                
                likes_data = cursor.fetchall()
                likes_dict = {row['id']: row for row in likes_data}
                
                # 고객 목록에 미확인 좋아요 수 추가
                for customer in customers_list:
                    customer_id = customer.get('id')
                    if customer_id in likes_dict:
                        customer['unchecked_likes_residence'] = likes_dict[customer_id]['unchecked_likes_residence']
                        customer['unchecked_likes_business'] = likes_dict[customer_id]['unchecked_likes_business']
                    else:
                        customer['unchecked_likes_residence'] = 0
                        customer['unchecked_likes_business'] = 0
                    
                    # 디버깅 로그
                    if customer['unchecked_likes_residence'] > 0 or customer['unchecked_likes_business'] > 0:
                        print(f"[미확인 좋아요] {customer.get('customer_name')}: 주거용 {customer['unchecked_likes_residence']}개, 업무용 {customer['unchecked_likes_business']}개")
                        
            except Exception as e:
                print(f"[미확인 좋아요 계산 오류] {e}")
                # 오류가 발생해도 고객 목록은 정상적으로 반환
                for customer in customers_list:
                    customer['unchecked_likes_residence'] = 0
                    customer['unchecked_likes_business'] = 0
            
            return jsonify({
                'customers': customers_list,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            })

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
    
    # DATABASE_URL이 없으면 테스트용 샘플 데이터 반환
    if not os.environ.get('DATABASE_URL'):
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
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 팀장 본인의 고객만 조회
        count_query = "SELECT COUNT(*) FROM employee_customers WHERE employee_id = %s"
        cursor.execute(count_query, (team_leader_id,))
        total_count = cursor.fetchone()[0]
        
        query = "SELECT * FROM employee_customers WHERE employee_id = %s ORDER BY inquiry_date DESC, id DESC LIMIT %s OFFSET %s"
        cursor.execute(query, (team_leader_id, per_page, offset))
        
        customers_raw = cursor.fetchall()
        customers_list = [db_utils.dict_from_row(row) for row in customers_raw]
        
        # employee_name 필드 추가
        for customer in customers_list:
            customer['employee_name'] = customer.get('employee_id', '')
        
        return jsonify({
            'customers': customers_list,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"팀장 본인 고객 조회 오류: {e}")
        return jsonify({'error': f'팀장 본인 고객 조회 실패: {e}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/team-leader/maeiple', methods=['GET'])
def team_leader_maeiple():
    """팀장 본인의 매물만 조회"""
    if session.get('employee_role') != '팀장':
        return jsonify({'error': '팀장만 접근 가능합니다.'}), 403
    
    team_leader_id = session.get('employee_id')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # DATABASE_URL이 없으면 테스트용 샘플 데이터 반환
    if not os.environ.get('DATABASE_URL'):
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
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 팀장 본인의 매물만 조회
        count_query = "SELECT COUNT(*) FROM maeiple_properties WHERE employee_id = %s"
        cursor.execute(count_query, (team_leader_id,))
        total_count = cursor.fetchone()[0]
        
        query = '''
            SELECT id, check_date, building_number, room_number, status,
                   jeonse_price, monthly_rent, sale_price, is_occupied,
                   phone, memo, likes, dislikes, employee_id, employee_name, employee_team,
                   created_at, updated_at
            FROM maeiple_properties
            WHERE employee_id = %s
            ORDER BY check_date DESC, building_number, room_number
            LIMIT %s OFFSET %s
        '''
        
        cursor.execute(query, (team_leader_id, per_page, offset))
        properties = []
        for row in cursor.fetchall():
            properties.append({
                'id': row['id'],
                'check_date': row['check_date'].strftime('%Y-%m-%d') if row['check_date'] else '',
                'building_number': row['building_number'],
                'room_number': row['room_number'],
                'status': row['status'],
                'jeonse_price': row['jeonse_price'],
                'monthly_rent': row['monthly_rent'],
                'sale_price': row['sale_price'],
                'is_occupied': row['is_occupied'],
                'phone': row['phone'] or '',
                'memo': row['memo'] or '',
                'likes': row['likes'],
                'dislikes': row['dislikes'],
                'employee_id': row['employee_id'] or '',
                'employee_name': row['employee_name'] or '',
                'employee_team': row['employee_team'] or ''
            })
        
        conn.close()
        return jsonify({
            'success': True,
            'properties': properties,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
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
    
    # DATABASE_URL이 없으면 테스트용 샘플 데이터 반환
    if not os.environ.get('DATABASE_URL'):
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
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 팀 전체 고객 조회 (팀장 + 팀원)
        count_query = """
            SELECT COUNT(*) FROM employee_customers ec
            JOIN employees e ON ec.employee_id = e.name
            WHERE e.team = %s
        """
        cursor.execute(count_query, (team_name,))
        total_count = cursor.fetchone()[0]
        
        query = """
            SELECT ec.*, e.team FROM employee_customers ec
            JOIN employees e ON ec.employee_id = e.name
            WHERE e.team = %s
            ORDER BY ec.inquiry_date DESC, ec.id DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (team_name, per_page, offset))
        
        customers_raw = cursor.fetchall()
        customers_list = [db_utils.dict_from_row(row) for row in customers_raw]
        
        # employee_name 필드 추가
        for customer in customers_list:
            customer['employee_name'] = customer.get('employee_id', '')
        
        return jsonify({
            'customers': customers_list,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"팀 전체 고객 조회 오류: {e}")
        return jsonify({'error': f'팀 전체 고객 조회 실패: {e}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/team/maeiple', methods=['GET'])
def team_maeiple():
    """팀 전체 매물 조회 (팀장 + 팀원)"""
    if session.get('employee_role') != '팀장':
        return jsonify({'error': '팀장만 접근 가능합니다.'}), 403
    
    team_name = session.get('employee_team')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    # DATABASE_URL이 없으면 테스트용 샘플 데이터 반환
    if not os.environ.get('DATABASE_URL'):
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
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 팀 전체 매물 조회 (팀장 + 팀원)
        count_query = "SELECT COUNT(*) FROM maeiple_properties WHERE employee_team = %s"
        cursor.execute(count_query, (team_name,))
        total_count = cursor.fetchone()[0]
        
        query = '''
            SELECT id, check_date, building_number, room_number, status,
                   jeonse_price, monthly_rent, sale_price, is_occupied,
                   phone, memo, likes, dislikes, employee_id, employee_name, employee_team,
                   created_at, updated_at
            FROM maeiple_properties
            WHERE employee_team = %s
            ORDER BY check_date DESC, building_number, room_number
            LIMIT %s OFFSET %s
        '''
        
        cursor.execute(query, (team_name, per_page, offset))
        properties = []
        for row in cursor.fetchall():
            properties.append({
                'id': row['id'],
                'check_date': row['check_date'].strftime('%Y-%m-%d') if row['check_date'] else '',
                'building_number': row['building_number'],
                'room_number': row['room_number'],
                'status': row['status'],
                'jeonse_price': row['jeonse_price'],
                'monthly_rent': row['monthly_rent'],
                'sale_price': row['sale_price'],
                'is_occupied': row['is_occupied'],
                'phone': row['phone'] or '',
                'memo': row['memo'] or '',
                'likes': row['likes'],
                'dislikes': row['dislikes'],
                'employee_id': row['employee_id'] or '',
                'employee_name': row['employee_name'] or '',
                'employee_team': row['employee_team'] or ''
            })
        
        conn.close()
        return jsonify({
            'success': True,
            'properties': properties,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
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
        
        # DATABASE_URL이 없으면 테스트용 샘플 데이터 반환
        if not os.environ.get('DATABASE_URL'):
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
            conn, _ = db_utils.get_db_connection()
            cursor = conn.cursor()
            
            # 정렬 조건 설정
            valid_sort_fields = ['check_date', 'building_number', 'room_number', 'status', 'jeonse_price', 'monthly_rent', 'sale_price']
            if sort_by not in valid_sort_fields:
                sort_by = 'check_date'
            
            sort_direction = 'DESC' if sort_order == 'desc' else 'ASC'
            
            # 현재 사용자의 매물만 조회 (개인 메이플관리)
            current_user = session.get('employee_id', '')
            current_team = session.get('employee_team', '')
            
            # 관리자인 경우 모든 매물, 일반 직원인 경우 개인 매물만
            if session.get('is_admin'):
                # 전체 개수 조회 (모든 매물)
                count_query = "SELECT COUNT(*) FROM maeiple_properties"
                cursor.execute(count_query)
                total_count = cursor.fetchone()[0]
                
                # 매물 목록 조회 (모든 매물, 정렬 및 페이지네이션 적용)
                query = f'''
                    SELECT id, check_date, building_number, room_number, status,
                           jeonse_price, monthly_rent, sale_price, is_occupied,
                           phone, memo, likes, dislikes, employee_id, employee_name, employee_team,
                           created_at, updated_at
                    FROM maeiple_properties
                    ORDER BY {sort_by} {sort_direction}, building_number, room_number
                    LIMIT %s OFFSET %s
                '''
                
                cursor.execute(query, (per_page, offset))
            else:
                # 전체 개수 조회 (개인 매물만)
                count_query = "SELECT COUNT(*) FROM maeiple_properties WHERE employee_id = %s"
                cursor.execute(count_query, (current_user,))
                total_count = cursor.fetchone()[0]
                
                # 매물 목록 조회 (개인 매물만, 정렬 및 페이지네이션 적용)
                query = f'''
                    SELECT id, check_date, building_number, room_number, status,
                           jeonse_price, monthly_rent, sale_price, is_occupied,
                           phone, memo, likes, dislikes, employee_id, employee_name, employee_team,
                           created_at, updated_at
                    FROM maeiple_properties
                    WHERE employee_id = %s
                    ORDER BY {sort_by} {sort_direction}, building_number, room_number
                    LIMIT %s OFFSET %s
                '''
                
                cursor.execute(query, (current_user, per_page, offset))
            
            properties = []
            for row in cursor.fetchall():
                properties.append({
                    'id': row['id'],
                    'check_date': row['check_date'].strftime('%Y-%m-%d') if row['check_date'] else '',
                    'building_number': row['building_number'],
                    'room_number': row['room_number'],
                    'status': row['status'],
                    'jeonse_price': row['jeonse_price'],
                    'monthly_rent': row['monthly_rent'],
                    'sale_price': row['sale_price'],
                    'is_occupied': row['is_occupied'],
                    'phone': row['phone'] or '',
                    'memo': row['memo'] or '',
                    'likes': row['likes'],
                    'dislikes': row['dislikes'],
                    'employee_id': row['employee_id'] or '',
                    'employee_name': row['employee_name'] or '',
                    'employee_team': row['employee_team'] or ''
                })
            
            conn.close()
            return jsonify({
                'success': True, 
                'properties': properties,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            })
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            conn, _ = db_utils.get_db_connection()
            cursor = conn.cursor()
            
            # 현재 로그인한 사용자 정보 가져오기
            employee_id = session.get('employee_id', 'system')
            employee_name = session.get('employee_name', '시스템')
            employee_team = session.get('employee_team', '관리자')
            
            # 새 매물 생성
            cursor.execute('''
                INSERT INTO maeiple_properties 
                (check_date, building_number, room_number, status, jeonse_price, 
                 monthly_rent, sale_price, is_occupied, phone, memo, employee_id, employee_name, employee_team)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                data.get('check_date'),
                data.get('building_number'),
                data.get('room_number'),
                data.get('status', '거래중'),
                data.get('jeonse_price'),
                data.get('monthly_rent'),
                data.get('sale_price'),
                data.get('is_occupied', False),
                data.get('phone'),
                data.get('memo', ''),
                employee_id,
                employee_name,
                employee_team
            ))
            
            new_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'id': new_id})
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
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
    
    # DATABASE_URL이 없으면 테스트용 샘플 데이터 반환
    if not os.environ.get('DATABASE_URL'):
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
    
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # 현재 사용자의 팀 정보 가져오기
        current_team = session.get('employee_team', '')
        
        # 전체 개수 조회
        count_query = "SELECT COUNT(*) FROM maeiple_properties WHERE employee_team = %s"
        cursor.execute(count_query, (current_team,))
        total_count = cursor.fetchone()[0]
        
        # 해당 팀의 매물 조회 (페이지네이션 적용)
        order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
        query = f'''
            SELECT id, check_date, building_number, room_number, status, 
                   jeonse_price, monthly_rent, sale_price, is_occupied, 
                   phone, memo, likes, dislikes, employee_id, employee_name, employee_team
            FROM maeiple_properties 
            WHERE employee_team = %s
            {order_clause}
            LIMIT %s OFFSET %s
        '''
        
        cursor.execute(query, (current_team, per_page, offset))
        rows = cursor.fetchall()
        
        properties = []
        for row in rows:
            if isinstance(row, dict):
                properties.append(row)
            else:
                properties.append({
                    'id': row[0],
                    'check_date': str(row[1]) if row[1] else '',
                    'building_number': row[2],
                    'room_number': row[3],
                    'status': row[4] or '',
                    'jeonse_price': row[5] or 0,
                    'monthly_rent': row[6] or 0,
                    'sale_price': row[7] or 0,
                    'is_occupied': bool(row[8]),
                    'phone': row[9] or '',
                    'memo': row[10] or '',
                    'likes': row[11] or 0,
                    'dislikes': row[12] or 0,
                    'employee_id': row[13] or '',
                    'employee_name': row[14] or '',
                    'employee_team': row[15] or ''
                })
        
        conn.close()
        return jsonify({
            'success': True, 
            'properties': properties,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'type': 'team'  # 팀 통합용임을 명시
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
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
    
    # DATABASE_URL이 없으면 테스트용 샘플 데이터 반환
    if not os.environ.get('DATABASE_URL'):
        print("⚠️ 테스트 모드 - 보증보험 샘플 데이터 반환")
        return jsonify([
            {
                'id': 1,
                'url': 'https://example.com/property1',
                'platform': '직방',
                'added_by': '팀장',
                'date_added': '2024-08-15',
                'memo': '보증보험 가능한 매물'
            },
            {
                'id': 2,
                'url': 'https://example.com/property2',
                'platform': '네이버',
                'added_by': '직원',
                'date_added': '2024-08-14',
                'memo': '보증보험 가능한 매물'
            }
        ])
    
    conn = None
    try:
        conn, _ = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.id, l.url, l.platform, l.added_by, l.date_added, l.memo
            FROM links l
            WHERE l.guarantee_insurance = TRUE 
            ORDER BY l.id DESC
            LIMIT 50
        ''')
        
        guarantee_list = [db_utils.dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(guarantee_list)
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        print(f"보증보험 목록 조회 오류: {e}")
        return jsonify({'error': f'보증보험 목록 조회 실패: {e}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)