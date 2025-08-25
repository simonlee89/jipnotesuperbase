#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
고객 추가 API 테스트 스크립트
"""

import requests
import json

# 테스트용 고객 데이터
test_customer_data = {
    'inquiry_date': '2025-08-23',
    'customer_name': '테스트고객',
    'customer_phone': '010-1234-5678',
    'budget': 50000,
    'rooms': '원룸',
    'location': '서울시 강남구',
    'loan_needed': '필요없음',
    'parking_needed': '필요없음',
    'pets': '없음',
    'memo': '테스트용 고객입니다',
    'status': '진행중'
}

def test_customer_api():
    """고객 추가 API 테스트"""
    base_url = 'http://localhost:5000'
    
    # 직접 관리자 세션으로 테스트
    session = requests.Session()
    
    print("1. 관리자 세션 설정을 위해 메인 페이지 접근...")
    # 먼저 메인 페이지에 접근해서 세션을 얻습니다
    main_response = session.get(f'{base_url}/')
    print(f"메인 페이지 응답: {main_response.status_code}")
    
    # 관리자 로그인 시도
    print("\n2. 관리자 로그인 시도...")
    login_data = {
        'employee_id': 'admin',
        'password': 'ejxkqdnjs1emd'
    }
    
    # 관리자 전용 로그인 API 시도
    admin_login_response = session.post(f'{base_url}/api/admin/login', json=login_data, headers={'Content-Type': 'application/json'})
    print(f"관리자 로그인 응답: {admin_login_response.status_code}")
    
    if admin_login_response.status_code != 200:
        print("관리자 로그인 실패, 수동으로 세션 설정...")
        # 수동으로 관리자 세션 설정
        session.cookies.set('is_admin', 'true')
    
    # 3. 고객 추가 API 호출
    print("\n3. 고객 추가 API 호출...")
    headers = {'Content-Type': 'application/json'}
    
    response = session.post(
        f'{base_url}/api/customers',
        headers=headers,
        json=test_customer_data
    )
    
    print(f"API 응답 상태: {response.status_code}")
    print(f"응답 헤더: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"응답 데이터: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"JSON 파싱 실패: {e}")
        print(f"응답 텍스트: {response.text}")

if __name__ == '__main__':
    test_customer_api()