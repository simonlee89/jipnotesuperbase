#!/usr/bin/env python3
"""
새 고객 추가 테스트
"""

import uuid
from datetime import datetime
from supabase_utils import init_supabase, add_customer

def test_new_customer():
    """새 고객 추가 테스트"""
    print("🧪 새 고객 추가 테스트")
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
    
    # 고객 추가
    print("\n🔄 고객 추가 중...")
    new_customer = add_customer(test_customer_data)
    
    if new_customer:
        print("✅ 고객 추가 성공!")
        print(f"  - 고객 ID: {new_customer.get('id')}")
        print("\n✅ 테스트 완료! 고객이 성공적으로 추가되었습니다.")
        
    else:
        print("❌ 고객 추가 실패")

if __name__ == "__main__":
    test_new_customer()
