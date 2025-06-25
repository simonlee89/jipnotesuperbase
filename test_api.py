#!/usr/bin/env python3
"""
관리자페이지 API 테스트 스크립트
"""
import requests
import json

def test_employees_api():
    """직원 목록 API 테스트"""
    try:
        print("=== 🧪 직원 목록 API 테스트 ===")
        
        # 직원 목록 조회
        response = requests.get('http://localhost:8080/api/employees')
        
        print(f"응답 코드: {response.status_code}")
        print(f"응답 헤더: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 성공! 직원 수: {len(data)}명")
            
            for emp in data:
                print(f"  - ID:{emp.get('id')} | 이름:'{emp.get('employee_name')}' | 역할:{emp.get('role')}")
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"응답 내용: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 관리자페이지.py가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def test_login_api():
    """직원 로그인 API 테스트"""
    try:
        print("\n=== 🔐 직원 로그인 API 테스트 ===")
        
        test_names = ['admin', '관리자', '직원1', '테스트직원', '없는직원']
        
        for name in test_names:
            print(f"\n🔍 '{name}' 로그인 테스트:")
            
            response = requests.post('http://localhost:8080/login', 
                                   json={'employee_id': name, 'password': 'dummy'})
            
            print(f"응답 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ 로그인 성공!")
                else:
                    print(f"❌ 로그인 실패: {data.get('message')}")
            else:
                print(f"❌ 서버 오류: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_employees_api()
    test_login_api() 