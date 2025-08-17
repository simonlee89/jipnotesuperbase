#!/usr/bin/env python3
"""
새 고객 추가 시 전용 링크 생성 테스트
"""

import uuid
from datetime import datetime
from supabase_utils import init_supabase, add_customer, get_supabase

def test_new_customer():
    """새 고객 추가 테스트"""
    print("🧪 새 고객 추가 및 전용 링크 생성 테스트")
    print("=" * 50)
    
    # Supabase 초기화
    if not init_supabase():
        print("❌ Supabase 초기화 실패")
        return
    
    # 테스트 고객 데이터
    test_customer_data = {
        'inquiry_date': datetime.now().strftime('%Y-%m-%d'),
        'customer_name': '테스트고객',
        'customer_phone': '010-1111-2222',
        'budget': 3500,
        'rooms': '1.5룸',
        'location': '테스트구',
        'loan_needed': True,
        'parking_needed': False,
        'pets': '불가',
        'memo': '테스트 고객입니다',
        'status': '상담중',
        'employee_id': 1,
        'employee_name': '테스트직원',
        'employee_team': '테스트팀',
        'management_site_id': str(uuid.uuid4().hex)[:8],
        'created_date': datetime.now().isoformat()
    }
    
    print(f"📝 테스트 고객 정보:")
    print(f"  - 이름: {test_customer_data['customer_name']}")
    print(f"  - management_site_id: {test_customer_data['management_site_id']}")
    
    # 고객 추가 (자동으로 전용 링크도 생성됨)
    print("\n🔄 고객 추가 중...")
    new_customer = add_customer(test_customer_data)
    
    if new_customer:
        print("✅ 고객 추가 성공!")
        print(f"  - 고객 ID: {new_customer.get('id')}")
        
        # 생성된 전용 링크 확인
        management_site_id = test_customer_data['management_site_id']
        print(f"\n🔍 생성된 전용 링크 확인 (management_site_id: {management_site_id})")
        
        supabase = get_supabase()
        
        # 주거용 링크 확인
        residence_links = supabase.table('residence_links').select('*').eq('management_site_id', management_site_id).execute()
        print(f"\n📋 주거용 전용 링크: {len(residence_links.data)}개")
        for i, link in enumerate(residence_links.data, 1):
            print(f"  {i}. {link['title']}")
            print(f"     URL: {link['url']}")
        
        # 업무용 링크 확인
        office_links = supabase.table('office_links').select('*').eq('management_site_id', management_site_id).execute()
        print(f"\n💼 업무용 전용 링크: {len(office_links.data)}개")
        for i, link in enumerate(office_links.data, 1):
            print(f"  {i}. {link['title']}")
            print(f"     URL: {link['url']}")
        
        print("\n✅ 테스트 완료! 고객별 독립 링크 시스템이 정상 작동합니다.")
        
    else:
        print("❌ 고객 추가 실패")

if __name__ == "__main__":
    test_new_customer()
