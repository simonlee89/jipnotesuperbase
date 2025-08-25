import requests
import json

def test_office_links_api():
    base_url = "http://localhost:5000"
    
    print("🧪 업무용 링크 API 테스트 시작...")
    
    # 1. GET 요청으로 기존 링크 조회
    print("\n📋 1. 기존 링크 조회 테스트:")
    try:
        response = requests.get(f"{base_url}/api/office-links")
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   응답 데이터: {len(data)}개 링크")
            for i, link in enumerate(data[:3]):  # 처음 3개만 표시
                print(f"     {i+1}. {link.get('title', '제목없음')} - {link.get('url', 'URL없음')}")
        else:
            print(f"   오류 응답: {response.text}")
    except Exception as e:
        print(f"   ❌ GET 요청 실패: {e}")
    
    # 2. POST 요청으로 새 링크 추가 테스트
    print("\n📝 2. 새 링크 추가 테스트:")
    test_data = {
        "url": "https://test-office.example.com",
        "platform": "테스트플랫폼",
        "added_by": "테스트사용자",
        "memo": "테스트 메모입니다.",
        "management_site_id": "test-customer-001"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/office-links?management_site_id=test-customer-001",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답 헤더: {dict(response.headers)}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"   ✅ 성공 응답: {data}")
        else:
            print(f"   ❌ 오류 응답: {response.text}")
            try:
                error_data = response.json()
                print(f"   오류 상세: {error_data}")
            except:
                print(f"   오류 텍스트: {response.text}")
                
    except Exception as e:
        print(f"   ❌ POST 요청 실패: {e}")
    
    # 3. 특정 고객의 링크 조회 테스트
    print("\n🔍 3. 특정 고객 링크 조회 테스트:")
    try:
        response = requests.get(f"{base_url}/api/office-links?management_site_id=test-customer-001")
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   응답 데이터: {len(data)}개 링크")
            for i, link in enumerate(data):
                print(f"     {i+1}. {link.get('title', '제목없음')} - {link.get('url', 'URL없음')}")
        else:
            print(f"   오류 응답: {response.text}")
    except Exception as e:
        print(f"   ❌ GET 요청 실패: {e}")
    
    print("\n🎯 테스트 완료!")

if __name__ == "__main__":
    test_office_links_api()
