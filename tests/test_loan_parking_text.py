"""
대출여부, 주차 필드 텍스트 저장 테스트
"""

import requests
import json

# 테스트 서버 URL
BASE_URL = 'http://localhost:5000'

def test_customer_field_update():
    print("=== 대출여부, 주차 필드 텍스트 저장 테스트 ===")
    
    # 1. 로그인 (세션 획득)
    login_data = {
        'employee_id': '테스트',  # 실제 직원 ID로 변경
        'password': 'password'   # 실제 비밀번호로 변경
    }
    
    session = requests.Session()
    login_response = session.post(f'{BASE_URL}/login', json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ 로그인 실패: {login_response.status_code}")
        return
    
    print("✅ 로그인 성공")
    
    # 2. 새 고객 생성 (텍스트 값으로)
    customer_data = {
        'customer_name': '텍스트테스트고객',
        'customer_phone': '010-1234-5678',
        'loan_needed': '대출 필요함',  # 텍스트 값
        'parking_needed': '주차 1대 가능',  # 텍스트 값
        'rooms': '2룸',
        'location': '테스트구'
    }
    
    print(f"\n📤 새 고객 생성 요청: {customer_data}")
    create_response = session.post(f'{BASE_URL}/api/customers', json=customer_data)
    
    if create_response.status_code == 200:
        result = create_response.json()
        if result.get('success'):
            customer_id = result.get('customer', {}).get('id')
            print(f"✅ 고객 생성 성공: ID={customer_id}")
            
            # 3. 생성된 고객 정보 확인
            get_response = session.get(f'{BASE_URL}/api/employee/customers')
            if get_response.status_code == 200:
                customers = get_response.json().get('customers', [])
                test_customer = next((c for c in customers if c['id'] == customer_id), None)
                
                if test_customer:
                    print(f"\n📋 저장된 데이터:")
                    print(f"  - loan_needed: '{test_customer.get('loan_needed')}'")
                    print(f"  - parking_needed: '{test_customer.get('parking_needed')}'")
                    
                    # 4. 필드 업데이트 테스트
                    print(f"\n🔄 필드 업데이트 테스트")
                    
                    # 대출여부 업데이트
                    update_data = {'loan_needed': '은행 대출 가능'}
                    update_response = session.put(f'{BASE_URL}/api/customers/{customer_id}/field', json=update_data)
                    
                    if update_response.status_code == 200:
                        result = update_response.json()
                        print(f"✅ 대출여부 업데이트 성공: {result}")
                    else:
                        print(f"❌ 대출여부 업데이트 실패: {update_response.status_code}, {update_response.text}")
                    
                    # 주차 업데이트  
                    update_data = {'parking_needed': '지하 주차 불가능'}
                    update_response = session.put(f'{BASE_URL}/api/customers/{customer_id}/field', json=update_data)
                    
                    if update_response.status_code == 200:
                        result = update_response.json()
                        print(f"✅ 주차 업데이트 성공: {result}")
                    else:
                        print(f"❌ 주차 업데이트 실패: {update_response.status_code}, {update_response.text}")
                    
                    # 5. 최종 확인
                    get_response = session.get(f'{BASE_URL}/api/employee/customers')
                    if get_response.status_code == 200:
                        customers = get_response.json().get('customers', [])
                        final_customer = next((c for c in customers if c['id'] == customer_id), None)
                        
                        if final_customer:
                            print(f"\n📋 최종 저장된 데이터:")
                            print(f"  - loan_needed: '{final_customer.get('loan_needed')}'")
                            print(f"  - parking_needed: '{final_customer.get('parking_needed')}'")
                else:
                    print("❌ 생성된 고객을 찾을 수 없음")
        else:
            print(f"❌ 고객 생성 실패: {result}")
    else:
        print(f"❌ 고객 생성 요청 실패: {create_response.status_code}, {create_response.text}")

if __name__ == '__main__':
    test_customer_field_update()