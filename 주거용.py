from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
from datetime import datetime
import os
import json
from db_utils import get_db_connection, init_database, execute_query, get_customer_info

# 데이터베이스 초기화 (integrated.db만)
def init_db():
    print("=== 주거용 DB 초기화 시작 ===")
    try:
        # 공통 DB 유틸리티 사용
        init_success = init_database()
        if init_success:
            print("=== 주거용 DB 초기화 완료 ===")
        else:
            print("=== 주거용 DB 초기화 실패 ===")
            raise Exception("DB 초기화 실패")
        
    except Exception as e:
        print(f"=== 주거용 DB 초기화 오류: {e} ===")
        # 실패해도 앱은 계속 실행
        pass

app = Flask(__name__)

# Railway에서 gunicorn 실행 시에도 DB 초기화가 되도록 앱 생성 직후 호출
try:
    init_db()
    print("✅ 주거용 DB 초기화 성공")
except Exception as e:
    print(f"❌ 주거용 DB 초기화 실패: {e}")
    # 실패해도 앱은 계속 실행

@app.route('/')
def index():
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        # 고객 정보 가져오기
        try:
            cursor.execute('SELECT customer_name, move_in_date FROM customer_info WHERE id = 1')
            customer_info_raw = cursor.fetchone()
            
            if customer_info_raw:
                customer_name = customer_info_raw[0] if customer_info_raw[0] else '제일좋은집 찾아드릴분'
                move_in_date = customer_info_raw[1] if customer_info_raw[1] else ''
            else:
                customer_name = '제일좋은집 찾아드릴분'
                move_in_date = ''
        except Exception as e:
            print(f"[주거용] customer_info 조회 오류: {e}")
            customer_name = '제일좋은집 찾아드릴분'
            move_in_date = ''
        
        conn.close()
        # 로그인된 직원의 employee_id를 템플릿 변수로 전달
        employee_id = session.get('employee_id', '')
        return render_template('index.html', customer_name=customer_name, move_in_date=move_in_date, employee_id=employee_id)
        
    except Exception as e:
        print(f"[주거용] 메인 페이지 오류: {e}")
        return f"""
        <html><head><title>주거용 오류</title></head><body>
        <h1>❌ 주거용 사이트 오류</h1>
        <p><strong>오류 내용:</strong> {e}</p>
        <p><strong>현재 디렉토리:</strong> {os.getcwd()}</p>
        <p><strong>/data 존재:</strong> {os.path.exists('/data')}</p>
        <hr>
        <p><a href="/force-init-residence-db">🔧 DB 강제 초기화</a></p>
        </body></html>
        """, 500

@app.route('/customer/<management_site_id>')
def customer_site(management_site_id):
    print(f"[주거ROUTE] 고객 사이트 접근 - management_site_id: {management_site_id}")
    print(f"[주거ROUTE] 현재 작업 디렉토리: {os.getcwd()}")
    print(f"[주거ROUTE] /data 디렉토리 존재: {os.path.exists('/data')}")
    
    # 디렉토리 내용 확인
    try:
        if os.path.exists('/data'):
            files = os.listdir('/data')
            print(f"[주거ROUTE] /data 디렉토리 파일들: {files}")
        else:
            print(f"[주거ROUTE] /data 디렉토리가 존재하지 않음")
    except Exception as e:
        print(f"[주거ROUTE] /data 디렉토리 읽기 오류: {e}")
    
    # 공통 get_customer_info 함수 사용
    customer_info = get_customer_info(management_site_id)
    if not customer_info:
        print(f"[주거ROUTE] 고객 정보를 찾을 수 없음: {management_site_id}")
        
        # DB 상태 상세 확인
        debug_db_info = ""
        try:
            conn, db_type = get_db_connection()
            cursor = conn.cursor()
            debug_db_info += f"<strong>DB 타입:</strong> {db_type}<br><br>"
            
            # 테이블 목록 확인
            if db_type == 'postgresql':
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
                tables = cursor.fetchall()
                debug_db_info += f"<strong>PostgreSQL 테이블 목록:</strong><br>"
                debug_db_info += "<br>".join([f"- {t[0]}" for t in tables]) + "<br><br>"
                
                # employee_customers 테이블 스키마 확인
                try:
                    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'employee_customers' ORDER BY ordinal_position;")
                    columns = cursor.fetchall()
                    if columns:
                        debug_db_info += f"<strong>employee_customers 테이블 컬럼:</strong><br>"
                        debug_db_info += "<br>".join([f"- {col[0]} ({col[1]})" for col in columns]) + "<br><br>"
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
            else:
                # SQLite 처리
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                debug_db_info += f"<strong>SQLite 테이블 목록:</strong><br>"
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
        <html><head><title>주거용 디버깅 정보</title></head><body>
        <h1>🏠 주거용 디버깅 정보</h1>
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
    
    customer_name = customer_info.get('customer_name', '고객')
    print(f"[주거ROUTE] 고객 정보 조회 성공 - 이름: {customer_name}")
    
    # 미확인 좋아요 is_checked=0 → 1로 일괄 갱신
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    if db_type == 'postgresql':
        cursor.execute('UPDATE links SET is_checked = TRUE WHERE management_site_id = %s AND liked = TRUE AND is_checked = FALSE', (management_site_id,))
    else:
        cursor.execute('UPDATE links SET is_checked = 1 WHERE management_site_id = ? AND liked = 1 AND is_checked = 0', (management_site_id,))
    conn.commit()
    conn.close()
    return render_template('index.html', 
                         customer_name=customer_name, 
                         move_in_date=customer_info.get('residence_extra', ''),
                         management_site_id=management_site_id)

@app.route('/api/customer_info', methods=['GET', 'POST'])
def customer_info():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    management_site_id = request.args.get('management_site_id')
    if management_site_id:
        customer_info = get_customer_info(management_site_id)
        if not customer_info:
            conn.close()
            return jsonify({'success': False, 'error': '고객 정보를 찾을 수 없습니다. 삭제되었거나 존재하지 않는 고객입니다.'}), 404
    if request.method == 'POST':
        data = request.json
        customer_name = data.get('customer_name', '제일좋은집 찾아드릴분')
        move_in_date = data.get('move_in_date', '')
        if not move_in_date:
            move_in_date = datetime.now().strftime('%Y-%m-%d')
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
        try:
            cursor.execute('SELECT customer_name, move_in_date FROM customer_info WHERE id = 1')
            info = cursor.fetchone()
            conn.close()
            
            # PostgreSQL RealDictCursor와 SQLite 호환성 처리
            if info:
                if db_type == 'postgresql':
                    # PostgreSQL은 딕셔너리 형태로 반환
                    customer_name = info.get('customer_name', '제일좋은집 찾아드릴분')
                    move_in_date = info.get('move_in_date', '')
                else:
                    # SQLite는 튜플 형태로 반환
                    customer_name = info[0] if info[0] else '제일좋은집 찾아드릴분'
                    move_in_date = info[1] if info[1] else ''
            else:
                customer_name = '제일좋은집 찾아드릴분'
                move_in_date = ''
            
            return jsonify({
                'customer_name': customer_name,
                'move_in_date': move_in_date
            })
        except Exception as e:
            print(f"[주거용] customer_info 조회 오류: {e}")
            conn.close()
            return jsonify({
                'customer_name': '제일좋은집 찾아드릴분',
                'move_in_date': ''
            })

@app.route('/api/links', methods=['GET', 'POST'])
def links():
    management_site_id = request.args.get('management_site_id')
    
    if request.method == 'POST':
        try:
            conn, db_type = get_db_connection()
            cursor = conn.cursor()
            
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'JSON 데이터가 필요합니다.'}), 400
            
            url = data.get('url')
            platform = data.get('platform')
            added_by = session.get('employee_id', '중개사')  # 세션에서 가져오되 기본값 설정
            memo = data.get('memo', '')
            guarantee_insurance = data.get('guarantee_insurance', False)
            # PostgreSQL과 SQLite 모두 INTEGER 사용 (타입 통일)
            guarantee_int = 1 if guarantee_insurance else 0
            residence_extra = data.get('residence_extra', '')
            
            # 필수 필드 검증 (added_by는 기본값이 있으므로 제외)
            if not url or not platform:
                conn.close()
                return jsonify({'success': False, 'error': 'URL과 플랫폼은 필수 입력 항목입니다.'}), 400
            
            date_added = datetime.now().strftime('%Y-%m-%d')
            
            # 고객 정보 검증 (management_site_id가 있는 경우)
            if management_site_id:
                customer_info = get_customer_info(management_site_id)
                if not customer_info:
                    conn.close()
                    return jsonify({'success': False, 'error': '존재하지 않는 고객입니다.'}), 404
            
            # DB에 링크 추가
            if db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO links (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance, residence_extra)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                ''', (url, platform, added_by, date_added, memo, management_site_id, guarantee_int, residence_extra))
                # PostgreSQL RealDictCursor 호환성 처리
                result = cursor.fetchone()
                link_id = result['id'] if isinstance(result, dict) else result[0]
            else:
                cursor.execute('''
                    INSERT INTO links (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance, residence_extra)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (url, platform, added_by, date_added, memo, management_site_id, guarantee_int, residence_extra))
                link_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            print(f"✅ 새 링크 추가 성공 - ID: {link_id}, URL: {url[:50]}..., 고객: {management_site_id or '기본'}, 추가자: {added_by}")
            return jsonify({'success': True, 'id': link_id, 'message': '링크가 성공적으로 추가되었습니다.'})
            
        except Exception as e:
            # 에러 발생 시 DB 연결 안전하게 종료
            try:
                if 'conn' in locals():
                    conn.close()
            except:
                pass
            print(f"❌ 링크 추가 실패: {e}")
            return jsonify({'success': False, 'error': f'링크 추가 중 오류가 발생했습니다: {str(e)}'}), 500
    
    else:  # GET 요청
        try:
            conn, db_type = get_db_connection()
            cursor = conn.cursor()
            
            platform_filter = request.args.get('platform', 'all')
            user_filter = request.args.get('user', 'all')
            like_filter = request.args.get('like', 'all')
            date_filter = request.args.get('date', '')
            guarantee_filter = request.args.get('guarantee', 'all')
            query = 'SELECT * FROM links WHERE 1=1'
            params = []
            
            if management_site_id:
                print(f"고객별 링크 조회 - management_site_id: {management_site_id}")
                if db_type == 'postgresql':
                    query += ' AND management_site_id = %s'
                else:
                    query += ' AND management_site_id = ?'
                params.append(management_site_id)
            else:
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
                # PostgreSQL과 SQLite 모두 INTEGER 사용 (타입 통일)
                query += ' AND liked = 1'
            elif like_filter == 'disliked':
                # PostgreSQL과 SQLite 모두 INTEGER 사용 (타입 통일)
                query += ' AND disliked = 1'
            
            if date_filter:
                if db_type == 'postgresql':
                    query += ' AND date_added = %s'
                else:
                    query += ' AND date_added = ?'
                params.append(date_filter)
            
            if guarantee_filter == 'available':
                # PostgreSQL과 SQLite 모두 INTEGER 사용 (타입 통일)
                query += ' AND guarantee_insurance = 1'
            elif guarantee_filter == 'unavailable':
                # PostgreSQL과 SQLite 모두 INTEGER 사용 (타입 통일)
                query += ' AND guarantee_insurance = 0'
            
            query += ' ORDER BY id DESC'
            cursor.execute(query, params)
            links_data = cursor.fetchall()
            total_count = len(links_data)
            conn.close()
            
            links_list = []
            for index, link in enumerate(links_data):
                link_number = total_count - index
                
                # PostgreSQL RealDictCursor와 SQLite 호환성 처리
                if db_type == 'postgresql':
                    # PostgreSQL은 딕셔너리 형태로 반환
                    link_dict = {
                        'id': link.get('id'),
                        'number': link_number,
                        'url': link.get('url'),
                        'platform': link.get('platform'),
                        'added_by': link.get('added_by'),
                        'date_added': link.get('date_added'),
                        'rating': link.get('rating', 0),
                        'liked': bool(link.get('liked', 0)),
                        'disliked': bool(link.get('disliked', 0)),
                        'memo': link.get('memo', ''),
                        'guarantee_insurance': bool(link.get('guarantee_insurance', 0))
                    }
                else:
                    # SQLite는 튜플 형태로 반환
                    link_dict = {
                        'id': link[0],
                        'number': link_number,
                        'url': link[1],
                        'platform': link[2],
                        'added_by': link[3],
                        'date_added': link[4],
                        'rating': link[5],
                        'liked': bool(link[6]),
                        'disliked': bool(link[7]),
                        'memo': link[8] if len(link) > 8 else '',
                        'guarantee_insurance': bool(link[12]) if len(link) > 12 else False
                    }
                
                links_list.append(link_dict)
            print(f"링크 조회 완료 - 총 {len(links_list)}개, 고객: {management_site_id or '기본'}")
            return jsonify(links_list)
            
        except Exception as e:
            # 에러 발생 시 DB 연결 안전하게 종료
            try:
                if 'conn' in locals():
                    conn.close()
            except:
                pass
            print(f"❌ 링크 조회 실패: {e}")
            return jsonify({'success': False, 'error': f'링크 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/links/<int:link_id>', methods=['PUT', 'DELETE'])
def update_link(link_id):
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgresql':
        cursor.execute('SELECT management_site_id FROM links WHERE id = %s', (link_id,))
    else:
        cursor.execute('SELECT management_site_id FROM links WHERE id = ?', (link_id,))
    
    link_result = cursor.fetchone()
    if link_result:
        # PostgreSQL RealDictCursor와 SQLite 호환성 처리
        if db_type == 'postgresql':
            management_site_id = link_result.get('management_site_id')
        else:
            management_site_id = link_result[0]
        
        if management_site_id:
            customer_info = get_customer_info(management_site_id)
            if not customer_info:
                conn.close()
                return jsonify({'success': False, 'error': '삭제된 고객의 링크입니다. 작업을 수행할 수 없습니다.'}), 404
    
    if request.method == 'PUT':
        data = request.json
        action = data.get('action')
        
        if action == 'rating':
            rating = data.get('rating', 5)
            if db_type == 'postgresql':
                cursor.execute('UPDATE links SET rating = %s WHERE id = %s', (rating, link_id))
            else:
                cursor.execute('UPDATE links SET rating = ? WHERE id = ?', (rating, link_id))
        
        elif action == 'like':
            liked = data.get('liked', False)
            # PostgreSQL과 SQLite 모두 INTEGER 사용 (타입 통일)
            liked_int = 1 if liked else 0
            if db_type == 'postgresql':
                cursor.execute('UPDATE links SET liked = %s, disliked = 0, is_checked = 0 WHERE id = %s', (liked_int, link_id))
            else:
                cursor.execute('UPDATE links SET liked = ?, disliked = 0, is_checked = 0 WHERE id = ?', (liked_int, link_id))
        
        elif action == 'dislike':
            disliked = data.get('disliked', False)
            # PostgreSQL과 SQLite 모두 INTEGER 사용 (타입 통일)
            disliked_int = 1 if disliked else 0
            if db_type == 'postgresql':
                cursor.execute('UPDATE links SET disliked = %s, liked = 0 WHERE id = %s', (disliked_int, link_id))
            else:
                cursor.execute('UPDATE links SET disliked = ?, liked = 0 WHERE id = ?', (disliked_int, link_id))
        
        elif action == 'memo':
            memo = data.get('memo', '')
            if db_type == 'postgresql':
                cursor.execute('UPDATE links SET memo = %s WHERE id = %s', (memo, link_id))
            else:
                cursor.execute('UPDATE links SET memo = ? WHERE id = ?', (memo, link_id))
        
        elif action == 'guarantee':
            guarantee_insurance = data.get('guarantee_insurance', False)
            # PostgreSQL과 SQLite 모두 INTEGER 사용 (타입 통일)
            guarantee_int = 1 if guarantee_insurance else 0
            if db_type == 'postgresql':
                cursor.execute('UPDATE links SET guarantee_insurance = %s WHERE id = %s', (guarantee_int, link_id))
            else:
                cursor.execute('UPDATE links SET guarantee_insurance = ? WHERE id = ?', (guarantee_int, link_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        if db_type == 'postgresql':
            cursor.execute('DELETE FROM links WHERE id = %s', (link_id,))
        else:
            cursor.execute('DELETE FROM links WHERE id = ?', (link_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/backup', methods=['GET'])
def backup_data():
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'links': [],
            'customer_info': None
        }
        
        cursor.execute('SELECT * FROM links')
        links = cursor.fetchall()
        
        # 컬럼 이름 가져오기
        if db_type == 'postgresql':
            columns = ['id', 'url', 'platform', 'added_by', 'date_added', 'rating', 'liked', 'disliked', 'memo', 'customer_name', 'move_in_date', 'management_site_id', 'guarantee_insurance', 'is_checked', 'is_deleted', 'residence_extra']
        else:
            cursor.execute("PRAGMA table_info(links)")
            columns = [row[1] for row in cursor.fetchall()]
        
        for link in links:
            link_dict = dict(zip(columns, link))
            backup_data['links'].append(link_dict)
        
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
    try:
        backup_data = request.json
        if not backup_data or 'links' not in backup_data:
            return jsonify({'success': False, 'error': '잘못된 백업 데이터입니다.'})
        
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM links')
        cursor.execute('DELETE FROM customer_info')
        
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
            if db_type == 'postgresql':
                cursor.execute('INSERT INTO customer_info (id, customer_name, move_in_date) VALUES (1, %s, %s)', ('제일좋은집 찾아드릴분', ''))
            else:
                cursor.execute('INSERT INTO customer_info (id, customer_name, move_in_date) VALUES (1, "제일좋은집 찾아드릴분", "")')
        
        for link_data in backup_data['links']:
            if db_type == 'postgresql':
                cursor.execute('''
                    INSERT INTO links (url, platform, added_by, date_added, rating, liked, disliked, memo)
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
                    INSERT INTO links (url, platform, added_by, date_added, rating, liked, disliked, memo)
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
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        if db_type == 'postgresql':
            cursor.execute('DELETE FROM links WHERE management_site_id = %s', (management_site_id,))
        else:
            cursor.execute('DELETE FROM links WHERE management_site_id = ?', (management_site_id,))
            
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"관리자페이지 요청으로 management_site_id {management_site_id} 관련 링크 {deleted_count}개 삭제됨")
        return jsonify({'success': True, 'deleted_count': deleted_count})
    except Exception as e:
        print(f"링크 정리 실패: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/guarantee-log', methods=['POST'])
def guarantee_log():
    data = request.get_json()
    link_id = data.get('link_id')
    if not link_id:
        return jsonify({'success': False, 'message': 'link_id가 필요합니다.'})
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE links SET guarantee_insurance = 1 WHERE id = ?', (link_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/force-init-residence-db')
def force_init_residence_db():
    """주거용 사이트에서 DB 강제 초기화 및 테이블 생성"""
    try:
        # 공통 DB 초기화 함수 사용
        success = init_database()
        
        if success:
            # 테이블 목록 확인
            conn, db_type = get_db_connection()
            cursor = conn.cursor()
            
            if db_type == 'postgresql':
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            
            tables = cursor.fetchall()
            conn.close()
            
            return f"""
            <html><head><title>주거용 DB 초기화</title></head><body>
            <h2>🏠 주거용 DB 초기화 성공! (DB 타입: {db_type})</h2>
            <h3>현재 테이블 목록:</h3>
            <ul>
            {''.join([f'<li>{table[0]}</li>' for table in tables])}
            </ul>
            <hr>
            <p><strong>✅ 모든 필요한 테이블이 생성되었습니다!</strong></p>
            <p><a href="/">주거용 사이트로 돌아가기</a></p>
            </body></html>
            """
        else:
            return f"""
            <html><head><title>주거용 DB 초기화 실패</title></head><body>
            <h2>❌ DB 초기화 실패</h2>
            <p>DB 초기화 중 오류가 발생했습니다.</p>
            <p><a href="/">돌아가기</a></p>
            </body></html>
            """
    except Exception as e:
        return f"""
        <html><head><title>주거용 DB 초기화 실패</title></head><body>
        <h2>❌ DB 초기화 실패</h2>
        <p>오류: {e}</p>
        <p><a href="/">돌아가기</a></p>
        </body></html>
        """

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
        return jsonify({'success': False, 'message': str(e)}), 500

def auto_expire_guarantee_insurance():
    """보증보험이 1이고 date_added가 30일 이상 지난 링크는 guarantee_insurance를 0으로 자동 변경"""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgresql':
        # PostgreSQL에서 날짜 차이 계산
        cursor.execute('''
            UPDATE links
            SET guarantee_insurance = FALSE
            WHERE guarantee_insurance = TRUE
            AND date_added IS NOT NULL
            AND (CURRENT_DATE - date_added::date) >= 30
        ''')
    else:
        # SQLite에서 날짜 차이 계산: julianday('now') - julianday(date_added)
        cursor.execute('''
            UPDATE links
            SET guarantee_insurance = 0
            WHERE guarantee_insurance = 1
            AND date(date_added) IS NOT NULL
            AND (julianday('now') - julianday(date_added)) >= 30
        ''')
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    if affected:
        print(f"만료된 보증보험 {affected}건 자동 해제 완료")

@app.route('/api/test-link-add', methods=['POST'])
def test_link_add():
    """링크 추가 기능 테스트 및 디버깅용 엔드포인트"""
    try:
        print("=== 링크 추가 테스트 시작 ===")
        
        # 요청 데이터 확인
        data = request.json
        print(f"받은 데이터: {data}")
        
        # DB 연결 테스트
        conn, db_type = get_db_connection()
        print(f"DB 연결 성공 - 타입: {db_type}")
        
        # 테이블 존재 확인
        cursor = conn.cursor()
        if db_type == 'postgresql':
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'links';")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='links';")
        
        table_exists = cursor.fetchone()
        print(f"links 테이블 존재: {bool(table_exists)}")
        
        if not table_exists:
            conn.close()
            return jsonify({
                'success': False, 
                'error': 'links 테이블이 존재하지 않습니다.',
                'debug': {
                    'db_type': db_type,
                    'table_exists': False
                }
            })
        
        # 테이블 스키마 확인
        if db_type == 'postgresql':
            cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'links' ORDER BY ordinal_position;")
        else:
            cursor.execute("PRAGMA table_info(links);")
        
        schema = cursor.fetchall()
        print(f"links 테이블 스키마: {schema}")
        
        # 세션 정보 확인
        employee_id = session.get('employee_id', '중개사')
        print(f"세션에서 가져온 employee_id: {employee_id}")
        
        # 간단한 테스트 데이터로 INSERT 시도
        test_url = "https://test.example.com"
        test_platform = "test"
        test_added_by = "테스트용"
        test_date = datetime.now().strftime('%Y-%m-%d')
        
        if db_type == 'postgresql':
            cursor.execute('''
                INSERT INTO links (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance, residence_extra)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (test_url, test_platform, test_added_by, test_date, '테스트 메모', None, 0, ''))
            result = cursor.fetchone()
            link_id = result['id'] if isinstance(result, dict) else result[0]
        else:
            cursor.execute('''
                INSERT INTO links (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance, residence_extra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (test_url, test_platform, test_added_by, test_date, '테스트 메모', None, 0, ''))
            link_id = cursor.lastrowid
        
        conn.commit()
        print(f"테스트 링크 추가 성공 - ID: {link_id}")
        
        # 추가된 데이터 확인
        if db_type == 'postgresql':
            cursor.execute('SELECT * FROM links WHERE id = %s', (link_id,))
        else:
            cursor.execute('SELECT * FROM links WHERE id = ?', (link_id,))
        
        inserted_data = cursor.fetchone()
        print(f"추가된 데이터: {inserted_data}")
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '테스트 링크 추가 성공',
            'debug': {
                'db_type': db_type,
                'table_exists': True,
                'schema': schema,
                'employee_id': employee_id,
                'link_id': link_id,
                'inserted_data': str(inserted_data)
            }
        })
        
    except Exception as e:
        print(f"❌ 테스트 링크 추가 실패: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            if 'conn' in locals():
                conn.close()
        except:
            pass
            
        return jsonify({
            'success': False,
            'error': str(e),
            'debug': {
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
        }), 500

if __name__ == '__main__':
    auto_expire_guarantee_insurance()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port) 