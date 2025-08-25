from supabase_utils import get_supabase

def update_unchecked_likes():
    supabase = get_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return
    
    try:
        print("🔄 미확인 좋아요 수 업데이트 중...")
        
        # 1. 고객 목록 조회
        customers = supabase.table('employee_customers').select('*').execute()
        
        if not customers.data:
            print("❌ 고객 데이터가 없습니다.")
            return
            
        print(f"📊 총 고객 수: {len(customers.data)}명")
        
        updated_count = 0
        
        # 2. 각 고객별로 미확인 좋아요 수 계산 및 업데이트
        for customer in customers.data:
            if not customer.get('management_site_id'):
                continue
                
            management_site_id = customer['management_site_id']
            customer_name = customer['customer_name']
            customer_id = customer['id']
            
            print(f"\n👤 {customer_name} (ID: {customer_id})")
            print(f"   관리사이트ID: {management_site_id}")
            
            # 주거사이트 미확인 좋아요 수 계산
            residence_likes = supabase.table('residence_links').select('*').eq('management_site_id', management_site_id).eq('liked', True).eq('is_checked', False).execute()
            unchecked_residence_count = len(residence_likes.data) if residence_likes.data else 0
            
            # 업무사이트 미확인 좋아요 수 계산 (business_links 테이블이 없으므로 0으로 설정)
            unchecked_business_count = 0
            
            print(f"   🏠 주거사이트 미확인 좋아요: {unchecked_residence_count}개")
            print(f"   💼 업무사이트 미확인 좋아요: {unchecked_business_count}개")
            
            # 데이터베이스에 저장된 값과 비교
            db_residence = customer.get('unchecked_likes_residence', 0)
            db_business = customer.get('unchecked_likes_business', 0)
            
            print(f"   📊 DB 저장값 - 주거: {db_residence}, 업무: {db_business}")
            
            # 값이 다른 경우 업데이트
            if unchecked_residence_count != db_residence or unchecked_business_count != db_business:
                print(f"   🔄 업데이트 필요! 계산값과 DB값이 다릅니다.")
                
                try:
                    # 고객 정보 업데이트 (필드 목록 명시)
                    update_data = {
                        'unchecked_likes_residence': unchecked_residence_count,
                        'unchecked_likes_business': unchecked_business_count
                    }
                    
                    update_result = supabase.table('employee_customers').update(update_data).eq('id', customer_id).execute()
                    
                    if update_result.data:
                        print(f"   ✅ 업데이트 성공!")
                        updated_count += 1
                    else:
                        print(f"   ❌ 업데이트 실패")
                        
                except Exception as e:
                    print(f"   ❌ 업데이트 오류: {e}")
                    
                    # 오류가 발생한 경우 SQL 쿼리로 직접 업데이트 시도
                    try:
                        print(f"   🔄 SQL 쿼리로 재시도...")
                        sql_query = f"""
                        UPDATE employee_customers 
                        SET unchecked_likes_residence = {unchecked_residence_count}, 
                            unchecked_likes_business = {unchecked_business_count}
                        WHERE id = {customer_id}
                        """
                        
                        sql_result = supabase.rpc('exec_sql', {'sql': sql_query}).execute()
                        print(f"   ✅ SQL 업데이트 성공!")
                        updated_count += 1
                        
                    except Exception as sql_error:
                        print(f"   ❌ SQL 업데이트도 실패: {sql_error}")
            else:
                print(f"   ✅ 이미 최신 상태입니다.")
                
        print(f"\n🎉 업데이트 완료! 총 {updated_count}명의 고객 정보가 업데이트되었습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    update_unchecked_likes()
