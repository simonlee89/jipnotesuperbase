from supabase_utils import get_supabase

def check_db_structure():
    supabase = get_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return
    
    try:
        # 고객 테이블 구조 확인
        print("🔍 고객 테이블 구조 확인 중...")
        customer_res = supabase.table('employee_customers').select('*').limit(1).execute()
        
        if customer_res.data:
            print("✅ employee_customers 테이블 존재")
            first_customer = customer_res.data[0]
            print("📋 고객 테이블 컬럼:")
            for key, value in first_customer.items():
                print(f"  {key}: {value}")
            
            # 미확인 좋아요 필드 확인
            print("\n🔍 미확인 좋아요 필드 확인:")
            if 'unchecked_likes_residence' in first_customer:
                print(f"  unchecked_likes_residence: {first_customer['unchecked_likes_residence']}")
            else:
                print("  ❌ unchecked_likes_residence 필드가 없습니다!")
                
            if 'unchecked_likes_business' in first_customer:
                print(f"  unchecked_likes_business: {first_customer['unchecked_likes_business']}")
            else:
                print("  ❌ unchecked_likes_business 필드가 없습니다!")
        else:
            print("❌ employee_customers 테이블에 데이터가 없습니다.")
            
        # 전체 고객 수 확인
        all_customers = supabase.table('employee_customers').select('id').execute()
        print(f"\n📊 전체 고객 수: {len(all_customers.data) if all_customers.data else 0}개")
        
        # 미확인 좋아요가 있는 고객들 확인
        if customer_res.data and 'unchecked_likes_residence' in first_customer:
            unchecked_residence = supabase.table('employee_customers').select('*').gt('unchecked_likes_residence', 0).execute()
            print(f"🏠 미확인 주거사이트 좋아요가 있는 고객: {len(unchecked_residence.data) if unchecked_residence.data else 0}명")
            
        if customer_res.data and 'unchecked_likes_business' in first_customer:
            unchecked_business = supabase.table('employee_customers').select('*').gt('unchecked_likes_business', 0).execute()
            print(f"💼 미확인 업무사이트 좋아요가 있는 고객: {len(unchecked_business.data) if unchecked_business.data else 0}명")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_db_structure()
