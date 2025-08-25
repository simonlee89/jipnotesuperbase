import supabase_utils
import sys
import io

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_employee_operations():
    """직원 관련 작업 테스트"""
    supabase = supabase_utils.get_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return
    
    # 직원 목록 조회
    print("\n🔍 직원 목록 조회 중...")
    try:
        response = supabase.table('employees').select('*').limit(5).execute()
        if response.data:
            print(f"✅ 직원 {len(response.data)}명 조회됨")
            for emp in response.data:
                print(f"  - ID: {emp.get('id')}, 이름: {emp.get('name')}, 팀: {emp.get('team')}, 상태: {emp.get('status')}")
            
            # 첫 번째 직원으로 테스트
            if response.data:
                test_emp_id = response.data[0]['id']
                print(f"\n🧪 직원 ID {test_emp_id}로 테스트 진행")
                
                # 비밀번호 업데이트 테스트
                print(f"\n📝 비밀번호 업데이트 테스트...")
                pwd_response = supabase.table('employees').update({
                    'password': 'test1234'
                }).eq('id', test_emp_id).execute()
                
                if pwd_response.data:
                    print(f"✅ 비밀번호 업데이트 성공: {pwd_response.data}")
                else:
                    print(f"❌ 비밀번호 업데이트 실패: response.data가 None")
                    print(f"   전체 응답: {pwd_response}")
                
                # 상태 업데이트 테스트
                print(f"\n📝 상태 업데이트 테스트...")
                current_status = response.data[0].get('status', 'active')
                new_status = 'inactive' if current_status == 'active' else 'active'
                
                status_response = supabase.table('employees').update({
                    'status': new_status
                }).eq('id', test_emp_id).execute()
                
                if status_response.data:
                    print(f"✅ 상태 업데이트 성공: {current_status} → {new_status}")
                else:
                    print(f"❌ 상태 업데이트 실패: response.data가 None")
                    print(f"   전체 응답: {status_response}")
                
                # 원래 상태로 복구
                supabase.table('employees').update({
                    'status': current_status
                }).eq('id', test_emp_id).execute()
                print(f"↩️ 원래 상태로 복구: {current_status}")
                
        else:
            print("⚠️ 직원 데이터가 없습니다.")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_employee_operations()