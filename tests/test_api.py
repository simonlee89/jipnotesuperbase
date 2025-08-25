import requests
import json

def test_customers_api():
    """고객 목록 API를 직접 호출하여 미확인 좋아요 수 확인"""
    
    # 대시보드 고객 목록 API 호출
    url = "http://127.0.0.1:8080/api/customers"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            customers = data.get('customers', [])
            
            print(f"✅ API 호출 성공 - 고객 수: {len(customers)}")
            
            # 고객_250818_134801 고객 찾기
            target_customer = None
            for customer in customers:
                if customer.get('customer_name') == '고객_250818_134801':
                    target_customer = customer
                    break
            
            if target_customer:
                print(f"\n🎯 대상 고객 발견:")
                print(f"  이름: {target_customer.get('customer_name')}")
                print(f"  ID: {target_customer.get('id')}")
                print(f"  management_site_id: {target_customer.get('management_site_id')}")
                print(f"  unchecked_likes_residence: {target_customer.get('unchecked_likes_residence')}")
                print(f"  unchecked_likes_business: {target_customer.get('unchecked_likes_business')}")
                
                # 알림 표시 여부 확인
                residence_alarm = target_customer.get('unchecked_likes_residence', 0) > 0
                business_alarm = target_customer.get('unchecked_likes_business', 0) > 0
                
                print(f"\n🔔 알림 상태:")
                print(f"  주거사이트 알림: {'표시됨' if residence_alarm else '표시안됨'}")
                print(f"  업무사이트 알림: {'표시됨' if business_alarm else '표시안됨'}")
                
            else:
                print("❌ '고객_250818_134801' 고객을 찾을 수 없습니다.")
                
        else:
            print(f"❌ API 호출 실패 - 상태 코드: {response.status_code}")
            print(f"응답 내용: {response.text}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_customers_api()
