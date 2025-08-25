#!/usr/bin/env python3
"""
팀장 대시보드 테스트 스크립트
"""

import requests
import json

# 테스트 서버 URL
BASE_URL = 'http://localhost:5000'

def test_login_as_team_leader():
    """팀장으로 로그인"""
    print("팀장으로 로그인 시도...")
    
    session = requests.Session()
    
    # 로그인 요청
    login_data = {
        'username': 'test_leader',
        'password': 'test_password'  # 테스트용 데이터
    }
    
    response = session.post(f'{BASE_URL}/login', 
                           json=login_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        print("로그인 성공!")
        return session
    else:
        print(f"로그인 실패: {response.status_code}")
        return None

def test_team_leader_dashboard(session):
    """팀장 대시보드 접근 테스트"""
    print("\n팀장 대시보드 접근 테스트...")
    
    response = session.get(f'{BASE_URL}/team-leader')
    
    if response.status_code == 200:
        print("팀장 대시보드 접근 성공!")
        
        # HTML 내용 확인
        content = response.text
        
        # 주요 섹션 존재 확인
        sections = {
            '대시보드': 'default-content' in content,
            '매물관리': 'maeiple-section' in content,
            '고객목록': 'customers-section' in content,
            '직원관리': 'employees-section' in content
        }
        
        print("\n섹션 존재 확인:")
        for section_name, exists in sections.items():
            status = "OK" if exists else "FAIL"
            print(f"  [{status}] {section_name}")
        
        # JavaScript 함수 존재 확인
        functions = {
            'showTab': 'function showTab' in content,
            'activateMaeipeTab': 'function activateMaeipeTab' in content,
            'loadCustomers': 'function loadCustomers' in content,
            'loadEmployees': 'function loadEmployees' in content,
            'loadMaeipeProperties': 'function loadMaeipeProperties' in content
        }
        
        print("\nJavaScript 함수 확인:")
        for func_name, exists in functions.items():
            status = "OK" if exists else "FAIL"
            print(f"  [{status}] {func_name}()")
            
    else:
        print(f"팀장 대시보드 접근 실패: {response.status_code}")

def test_api_endpoints(session):
    """API 엔드포인트 테스트"""
    print("\nAPI 엔드포인트 테스트...")
    
    endpoints = [
        ('/api/customers?all_employees=true', '고객 목록'),
        ('/api/employees?page=1&per_page=20', '직원 목록'),
        ('/api/maeiple?page=1&per_page=20', '매물 목록')
    ]
    
    for endpoint, name in endpoints:
        response = session.get(f'{BASE_URL}{endpoint}')
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'success' in data or isinstance(data, list) or 'customers' in data or 'employees' in data or 'properties' in data:
                    print(f"  [OK] {name} API: 성공")
                else:
                    print(f"  [?] {name} API: 응답 형식 확인 필요")
            except json.JSONDecodeError:
                print(f"  [FAIL] {name} API: JSON 파싱 실패")
        else:
            print(f"  [FAIL] {name} API: HTTP {response.status_code}")

def main():
    print("=" * 50)
    print("팀장 대시보드 테스트 시작")
    print("=" * 50)
    
    # 팀장으로 로그인
    session = test_login_as_team_leader()
    
    if session:
        # 대시보드 테스트
        test_team_leader_dashboard(session)
        
        # API 테스트
        test_api_endpoints(session)
    
    print("\n" + "=" * 50)
    print("테스트 완료")
    print("=" * 50)

if __name__ == '__main__':
    main()