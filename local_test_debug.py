#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로컬 서버에서 링크 추가 후 목록 표시 문제 디버깅
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_utils import get_db_connection
from datetime import datetime
import json

def test_direct_db_operations():
    """DB에 직접 접근하여 링크 추가/조회 테스트"""
    print("=== 직접 DB 테스트 ===\n")
    
    try:
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        print(f"✅ DB 연결 성공! 타입: {db_type}")
        
        # 테스트 데이터
        test_url = f"https://debug-test-{datetime.now().strftime('%H%M%S')}.com"
        test_data = {
            'url': test_url,
            'platform': 'zigbang',
            'added_by': '디버그테스트',
            'date_added': datetime.now().strftime('%Y-%m-%d'),
            'memo': '디버깅용 테스트 링크',
            'management_site_id': None,
            'guarantee_insurance': 1,
            'residence_extra': ''
        }
        
        print(f"테스트 데이터: {test_data}")
        
        # 1. 링크 추가
        print("\n[1단계] 링크 직접 추가...")
        if db_type == 'postgresql':
            cursor.execute('''
                INSERT INTO links (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance, residence_extra)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (test_data['url'], test_data['platform'], test_data['added_by'], 
                  test_data['date_added'], test_data['memo'], test_data['management_site_id'], 
                  test_data['guarantee_insurance'], test_data['residence_extra']))
            result = cursor.fetchone()
            link_id = result['id'] if isinstance(result, dict) else result[0]
        else:
            cursor.execute('''
                INSERT INTO links (url, platform, added_by, date_added, memo, management_site_id, guarantee_insurance, residence_extra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (test_data['url'], test_data['platform'], test_data['added_by'], 
                  test_data['date_added'], test_data['memo'], test_data['management_site_id'], 
                  test_data['guarantee_insurance'], test_data['residence_extra']))
            link_id = cursor.lastrowid
            
        conn.commit()
        print(f"✅ 링크 추가 성공! ID: {link_id}")
        
        # 2. 링크 조회 (전체)
        print("\n[2단계] 전체 링크 조회...")
        cursor.execute('SELECT * FROM links WHERE management_site_id IS NULL ORDER BY id DESC LIMIT 5')
        all_links = cursor.fetchall()
        print(f"전체 링크 수: {len(all_links)}")
        
        # 방금 추가한 링크 찾기
        found = False
        for link in all_links:
            if db_type == 'postgresql':
                if link.get('url') == test_url:
                    found = True
                    print(f"✅ 추가한 링크 발견!")
                    print(f"   - ID: {link.get('id')}")
                    print(f"   - URL: {link.get('url')}")
                    print(f"   - 플랫폼: {link.get('platform')}")
                    print(f"   - 추가자: {link.get('added_by')}")
                    break
            else:
                if link[1] == test_url:  # url은 두 번째 컬럼
                    found = True
                    print(f"✅ 추가한 링크 발견!")
                    print(f"   - ID: {link[0]}")
                    print(f"   - URL: {link[1]}")
                    print(f"   - 플랫폼: {link[2]}")
                    print(f"   - 추가자: {link[3]}")
                    break
        
        if not found:
            print("❌ 추가한 링크가 조회되지 않음!")
            print("최근 링크 목록:")
            for i, link in enumerate(all_links):
                if db_type == 'postgresql':
                    print(f"   {i+1}. {link.get('url')} ({link.get('added_by')})")
                else:
                    print(f"   {i+1}. {link[1]} ({link[3]})")
        
        # 3. 필터링 테스트
        print("\n[3단계] 필터링 테스트...")
        
        # 플랫폼 필터
        if db_type == 'postgresql':
            cursor.execute("SELECT * FROM links WHERE platform = %s AND management_site_id IS NULL", ('zigbang',))
        else:
            cursor.execute("SELECT * FROM links WHERE platform = ? AND management_site_id IS NULL", ('zigbang',))
        zigbang_links = cursor.fetchall()
        print(f"직방 링크: {len(zigbang_links)}개")
        
        # 보증보험 필터
        if db_type == 'postgresql':
            cursor.execute("SELECT * FROM links WHERE guarantee_insurance = %s AND management_site_id IS NULL", (1,))
        else:
            cursor.execute("SELECT * FROM links WHERE guarantee_insurance = ? AND management_site_id IS NULL", (1,))
        guarantee_links = cursor.fetchall()
        print(f"보증보험 가능 링크: {len(guarantee_links)}개")
        
        conn.close()
        print("\n✅ 직접 DB 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ DB 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_simulation():
    """API 시뮬레이션 테스트"""
    print("\n=== API 시뮬레이션 테스트 ===")
    
    # 주거용.py의 링크 추가 로직 시뮬레이션
    try:
        from 주거용 import app
        
        with app.test_client() as client:
            # 링크 추가 테스트
            test_data = {
                'url': f'https://api-test-{datetime.now().strftime("%H%M%S")}.com',
                'platform': 'zigbang',
                'memo': 'API 테스트 메모',
                'guarantee_insurance': True,
                'residence_extra': ''
            }
            
            print("API 링크 추가 테스트...")
            response = client.post('/api/links', 
                                 json=test_data,
                                 content_type='application/json')
            
            print(f"응답 상태: {response.status_code}")
            print(f"응답 내용: {response.get_json()}")
            
            if response.status_code == 200:
                result = response.get_json()
                if result.get('success'):
                    print("✅ API 링크 추가 성공!")
                    
                    # 링크 조회 테스트
                    print("API 링크 조회 테스트...")
                    response = client.get('/api/links')
                    
                    if response.status_code == 200:
                        links = response.get_json()
                        print(f"✅ API 조회 성공! 링크 수: {len(links)}")
                        
                        # 방금 추가한 링크 찾기
                        found = any(link.get('url') == test_data['url'] for link in links)
                        if found:
                            print("✅ 추가한 링크가 API 조회에서 발견됨!")
                        else:
                            print("❌ 추가한 링크가 API 조회에서 발견되지 않음!")
                    else:
                        print(f"❌ API 조회 실패: {response.status_code}")
                else:
                    print(f"❌ API 링크 추가 실패: {result.get('error')}")
            else:
                print(f"❌ API 요청 실패: {response.status_code}")
                
    except Exception as e:
        print(f"❌ API 시뮬레이션 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("로컬 링크 추가/조회 디버깅 시작...\n")
    
    # 1. 직접 DB 테스트
    db_success = test_direct_db_operations()
    
    # 2. API 시뮬레이션 테스트
    if db_success:
        test_api_simulation()
    
    print("\n디버깅 테스트 완료!") 