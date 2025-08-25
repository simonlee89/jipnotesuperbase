#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

def test_employee_customer_api():
    base_url = 'http://localhost:5000'
    session = requests.Session()
    
    print('1. 직원 로그인 시도...')
    login_data = {'employee_id': '강태석', 'password': '1'}
    headers = {'Content-Type': 'application/json'}
    login_response = session.post(f'{base_url}/login', headers=headers, json=login_data)
    print(f'로그인 응답: {login_response.status_code}')
    
    if login_response.status_code == 200:
        try:
            login_result = login_response.json()
            print(f'로그인 결과: {login_result}')
            
            if login_result.get('success'):
                print('로그인 성공!')
                session_response = session.get(f'{base_url}/api/employee/session-info')
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    print(f'세션 정보: {session_data}')
                    
                    test_customer = {
                        'inquiry_date': '2025-08-23',
                        'customer_name': '테스트고객',
                        'customer_phone': '010-1234-5678',
                        'budget': 50000000,
                        'rooms': '원룸',
                        'location': '서울시 강남구',
                        'loan_needed': '필요없음',
                        'parking_needed': '필요없음',
                        'pets': '없음',
                        'memo': '직원 페이지 테스트용 고객',
                        'status': '진행중'
                    }
                    
                    customer_response = session.post(f'{base_url}/api/customers', headers=headers, json=test_customer)
                    print(f'고객 추가 응답 상태: {customer_response.status_code}')
                    try:
                        customer_result = customer_response.json()
                        print(f'고객 추가 응답: {customer_result}')
                    except:
                        print(f'응답 텍스트: {customer_response.text}')
        except Exception as e:
            print(f'오류: {e}')

if __name__ == '__main__':
    test_employee_customer_api()

