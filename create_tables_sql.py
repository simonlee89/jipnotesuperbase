#!/usr/bin/env python3
"""
Supabase에 SQL 스크립트를 직접 실행하여 테이블을 생성하는 스크립트
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 환경변수 로드
load_dotenv()

def init_supabase():
    """Supabase 클라이언트를 초기화합니다."""
    SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://gkoohafmugtqwtustbrp.supabase.co')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdrb29oYWZtdWd0cXd0dXN0YnJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzMzUwNTMsImV4cCI6MjA3MDkxMTA1M30.nREE7LgpxGUUA__GuzryUx2t_F4mwVtto0bPTFOqEFk')
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase 클라이언트 초기화 성공")
        return supabase
    except Exception as e:
        print(f"❌ Supabase 클라이언트 초기화 실패: {e}")
        return None

def create_tables_with_sql(supabase: Client):
    """SQL을 사용하여 테이블을 생성합니다."""
    print("\n🏗️ SQL로 테이블 생성 시작...")
    
    # 1. 직원 테이블 생성
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS employees (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(200) UNIQUE NOT NULL,
            email VARCHAR(200) NOT NULL DEFAULT '',
            password VARCHAR(255) NOT NULL DEFAULT '1',
            team VARCHAR(100) NOT NULL DEFAULT '',
            position VARCHAR(100) NOT NULL DEFAULT '',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_login TIMESTAMP WITH TIME ZONE,
            role VARCHAR(50) NOT NULL DEFAULT 'employee',
            status VARCHAR(20) NOT NULL DEFAULT 'active'
        );
        """
        
        # Supabase에서는 직접 SQL 실행이 제한적이므로, 테이블 존재 여부만 확인
        response = supabase.table('employees').select('*').limit(1).execute()
        print("✅ employees 테이블이 이미 존재합니다.")
    except Exception as e:
        if "does not exist" in str(e):
            print("❌ employees 테이블이 존재하지 않습니다.")
            print("💡 Supabase 대시보드에서 SQL 편집기를 사용하여 테이블을 생성해주세요.")
        else:
            print(f"⚠️ employees 테이블 확인 중 오류: {e}")
    
    # 2. 직원 고객 테이블 확인
    try:
        response = supabase.table('employee_customers').select('*').limit(1).execute()
        print("✅ employee_customers 테이블이 이미 존재합니다.")
    except Exception as e:
        if "does not exist" in str(e):
            print("❌ employee_customers 테이블이 존재하지 않습니다.")
        else:
            print(f"⚠️ employee_customers 테이블 확인 중 오류: {e}")
    
    # 3. 메이플 매물 테이블 확인
    try:
        response = supabase.table('maeiple_properties').select('*').limit(1).execute()
        print("✅ maeiple_properties 테이블이 이미 존재합니다.")
    except Exception as e:
        if "does not exist" in str(e):
            print("❌ maeiple_properties 테이블이 존재하지 않습니다.")
        else:
            print(f"⚠️ maeiple_properties 테이블 확인 중 오류: {e}")
    
    # 4. 주거용 링크 테이블 확인
    try:
        response = supabase.table('residence_links').select('*').limit(1).execute()
        print("✅ residence_links 테이블이 이미 존재합니다.")
    except Exception as e:
        if "does not exist" in str(e):
            print("❌ residence_links 테이블이 존재하지 않습니다.")
        else:
            print(f"⚠️ residence_links 테이블 확인 중 오류: {e}")
    
    # 5. 업무용 링크 테이블 확인
    try:
        response = supabase.table('office_links').select('*').limit(1).execute()
        print("✅ office_links 테이블이 이미 존재합니다.")
    except Exception as e:
        if "does not exist" in str(e):
            print("❌ office_links 테이블이 존재하지 않습니다.")
        else:
            print(f"⚠️ office_links 테이블 확인 중 오류: {e}")
    
    # 6. 매이플 작업 테이블 확인
    try:
        response = supabase.table('maeiple_tasks').select('*').limit(1).execute()
        print("✅ maeiple_tasks 테이블이 이미 존재합니다.")
    except Exception as e:
        if "does not exist" in str(e):
            print("❌ maeiple_tasks 테이블이 존재하지 않습니다.")
        else:
            print(f"⚠️ maeiple_tasks 테이블 확인 중 오류: {e}")

def show_manual_instructions():
    """수동으로 테이블을 생성하는 방법을 안내합니다."""
    print("\n" + "=" * 60)
    print("📋 수동으로 테이블을 생성하는 방법")
    print("=" * 60)
    
    print("\n1️⃣ Supabase 대시보드 접속")
    print("   https://supabase.com/dashboard")
    print("   → 프로젝트 'gkoohafmugtqwtustbrp' 선택")
    
    print("\n2️⃣ SQL 편집기 열기")
    print("   → 왼쪽 메뉴에서 'SQL Editor' 클릭")
    print("   → 'New query' 클릭")
    
    print("\n3️⃣ 테이블 생성 SQL 실행")
    print("   → create_supabase_tables.sql 파일의 내용을 복사")
    print("   → SQL 편집기에 붙여넣기")
    print("   → 'Run' 버튼 클릭")
    
    print("\n4️⃣ 테이블 확인")
    print("   → 왼쪽 메뉴에서 'Table Editor' 클릭")
    print("   → 생성된 테이블들 확인")
    
    print("\n5️⃣ RLS 정책 확인")
    print("   → 각 테이블의 'Policies' 탭에서 RLS 정책 확인")
    
    print("\n" + "=" * 60)
    print("💡 자동 테이블 생성을 원한다면:")
    print("   - Supabase 대시보드에서 'Database' → 'Tables'")
    print("   - 'New table' 버튼으로 하나씩 생성")
    print("   - 또는 SQL 편집기에서 스크립트 실행")
    print("=" * 60)

def main():
    """메인 함수"""
    print("🚀 Supabase 테이블 생성 확인")
    print("=" * 50)
    
    # Supabase 클라이언트 초기화
    supabase = init_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패. 프로그램을 종료합니다.")
        return
    
    # 테이블 존재 여부 확인
    create_tables_with_sql(supabase)
    
    # 수동 생성 방법 안내
    show_manual_instructions()
    
    print("\n🎯 다음 단계:")
    print("1. Supabase 대시보드에서 테이블 생성")
    print("2. 테이블 생성 완료 후: python setup_supabase.py")
    print("3. 애플리케이션 실행: python 관리자페이지.py")

if __name__ == "__main__":
    main()
