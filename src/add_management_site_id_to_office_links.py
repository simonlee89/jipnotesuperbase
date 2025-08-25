from supabase_utils import get_supabase

def add_management_site_id_to_office_links():
    supabase = get_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return
    
    try:
        print("🔍 office_links 테이블 구조 확인 중...")
        
        # 1. 현재 테이블 구조 확인
        office_links = supabase.table('office_links').select('*').limit(1).execute()
        
        if office_links.data:
            print("✅ office_links 테이블 존재")
            first_link = office_links.data[0]
            print("📋 현재 컬럼:")
            for key, value in first_link.items():
                print(f"  - {key}: {type(value).__name__} = {value}")
            
            # management_site_id 필드가 이미 있는지 확인
            if 'management_site_id' in first_link:
                print("✅ management_site_id 필드가 이미 존재합니다.")
                return
            else:
                print("❌ management_site_id 필드가 없습니다. 추가가 필요합니다.")
        else:
            print("✅ office_links 테이블 존재 (데이터 없음)")
        
        print("\n🔧 management_site_id 필드 추가 시도...")
        
        # 2. 기존 데이터에 management_site_id 필드 추가 (null 값으로)
        try:
            # 먼저 기존 데이터를 모두 가져와서 management_site_id 필드를 추가
            all_links = supabase.table('office_links').select('*').execute()
            
            if all_links.data:
                print(f"📊 총 {len(all_links.data)}개의 링크 데이터 처리 중...")
                
                for link in all_links.data:
                    # management_site_id 필드가 없는 경우에만 추가
                    if 'management_site_id' not in link:
                        update_result = supabase.table('office_links').update({
                            'management_site_id': None
                        }).eq('id', link['id']).execute()
                        
                        if update_result.data:
                            print(f"  ✅ ID {link['id']} 업데이트 성공")
                        else:
                            print(f"  ❌ ID {link['id']} 업데이트 실패")
                
                print("🎉 모든 기존 데이터에 management_site_id 필드 추가 완료!")
            else:
                print("📊 기존 데이터가 없습니다.")
                
        except Exception as e:
            print(f"❌ 기존 데이터 업데이트 실패: {e}")
            print("💡 이는 정상적인 상황일 수 있습니다. 테이블 구조만 확인해보겠습니다.")
        
        # 3. 새로운 데이터로 테이블 구조 확인
        print("\n🔍 업데이트된 테이블 구조 확인...")
        try:
            updated_links = supabase.table('office_links').select('*').limit(1).execute()
            if updated_links.data:
                first_link = updated_links.data[0]
                print("📋 업데이트된 컬럼:")
                for key, value in first_link.items():
                    print(f"  - {key}: {type(value).__name__} = {value}")
                
                if 'management_site_id' in first_link:
                    print("✅ management_site_id 필드 추가 성공!")
                else:
                    print("❌ management_site_id 필드 추가 실패")
            else:
                print("📊 테이블에 데이터가 없어 구조 확인이 어렵습니다.")
                
        except Exception as e:
            print(f"❌ 업데이트된 테이블 구조 확인 실패: {e}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    add_management_site_id_to_office_links()
