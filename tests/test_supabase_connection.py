#!/usr/bin/env python3
"""
Supabase 연결 테스트 스크립트
"""

import os
import sys
sys.path.append('.')
import supabase_utils

def test_supabase_connection():
    """Supabase 연결을 테스트합니다."""
    print("🔍 Supabase 연결 테스트 시작...")
    
    # 환경변수 확인
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    print(f"📋 SUPABASE_URL: {supabase_url}")
    print(f"📋 SUPABASE_KEY: {'설정됨' if supabase_key else '설정되지 않음'}")
    
    # Supabase 클라이언트 초기화 테스트
    success = supabase_utils.init_supabase()
    if success:
        print("✅ Supabase 클라이언트 초기화 성공")
    else:
        print("❌ Supabase 클라이언트 초기화 실패")
        return False
    
    # 테이블 존재 확인
    try:
        supabase = supabase_utils.get_supabase()
        if supabase:
            # employees 테이블 테스트
            print("\n📊 테이블 연결 테스트:")
            
            # employees 테이블 조회
            try:
                response = supabase.table('employees').select('*').limit(1).execute()
                print(f"✅ employees 테이블: 연결 성공 (레코드 수: {len(response.data)})")
            except Exception as e:
                print(f"❌ employees 테이블: {e}")
            
            # maeiple_properties 테이블 조회
            try:
                response = supabase.table('maeiple_properties').select('*').limit(1).execute()
                print(f"✅ maeiple_properties 테이블: 연결 성공 (레코드 수: {len(response.data)})")
            except Exception as e:
                print(f"❌ maeiple_properties 테이블: {e}")
                
            # customers 테이블 조회
            try:
                response = supabase.table('customers').select('*').limit(1).execute()
                print(f"✅ customers 테이블: 연결 성공 (레코드 수: {len(response.data)})")
            except Exception as e:
                print(f"❌ customers 테이블: {e}")
                
        else:
            print("❌ Supabase 클라이언트를 가져올 수 없습니다")
            return False
            
    except Exception as e:
        print(f"❌ 테이블 테스트 중 오류: {e}")
        return False
    
    print("\n🎉 Supabase 연결 테스트 완료!")
    return True

if __name__ == "__main__":
    # 환경변수 설정 (하드코딩된 값 사용)
    # 환경변수는 .env 파일에서 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        print("⚠️ .env 파일에서 환경변수를 설정하세요")
        return
    
    test_supabase_connection()
