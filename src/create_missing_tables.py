#!/usr/bin/env python3
"""
누락된 테이블들을 생성하는 스크립트
"""

import os
import sys
from supabase_utils import get_supabase

def create_guarantee_list_table():
    """보증보험 목록 테이블 생성"""
    print("🔄 guarantee_list 테이블 생성 중...")
    
    supabase = get_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return False
    
    try:
        # guarantee_list 테이블이 이미 존재하는지 확인
        try:
            response = supabase.table('guarantee_list').select('*').limit(1).execute()
            print("✅ guarantee_list 테이블이 이미 존재합니다.")
            return True
        except Exception:
            print("📝 guarantee_list 테이블을 생성해야 합니다.")
            print("⚠️  Supabase 대시보드에서 수동으로 테이블을 생성해주세요.")
            print("   테이블 구조:")
            print("   - id: bigint (Primary Key, auto increment)")
            print("   - title: text")
            print("   - url: text")
            print("   - description: text")
            print("   - platform: text")
            print("   - added_by: text")
            print("   - date_added: date")
            print("   - memo: text")
            print("   - guarantee_insurance: boolean (default: true)")
            print("   - liked: boolean (default: false)")
            print("   - disliked: boolean (default: false)")
            print("   - is_checked: boolean (default: false)")
            print("   - management_site_id: text")
            print("   - created_at: timestamptz (default: now())")
            print("   - updated_at: timestamptz (default: now())")
            return False
    except Exception as e:
        print(f"❌ guarantee_list 테이블 생성 확인 실패: {e}")
        return False

def create_links_table():
    """주거용 통합 링크 테이블 생성"""
    print("🔄 links 테이블 생성 중...")
    
    supabase = get_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return False
    
    try:
        # links 테이블이 이미 존재하는지 확인
        try:
            response = supabase.table('links').select('*').limit(1).execute()
            print("✅ links 테이블이 이미 존재합니다.")
            return True
        except Exception:
            print("📝 links 테이블을 생성해야 합니다.")
            print("⚠️  Supabase 대시보드에서 수동으로 테이블을 생성해주세요.")
            print("   테이블 구조 (residence_links 확장 버전):")
            print("   - id: bigint (Primary Key, auto increment)")
            print("   - title: text")
            print("   - url: text")
            print("   - description: text")
            print("   - platform: text")
            print("   - added_by: text")
            print("   - date_added: date")
            print("   - memo: text")
            print("   - guarantee_insurance: boolean (default: false)")
            print("   - liked: boolean (default: false)")
            print("   - disliked: boolean (default: false)")
            print("   - is_checked: boolean (default: false)")
            print("   - rating: integer (default: 5)")
            print("   - management_site_id: text")
            print("   - created_at: timestamptz (default: now())")
            print("   - updated_at: timestamptz (default: now())")
            return False
    except Exception as e:
        print(f"❌ links 테이블 생성 확인 실패: {e}")
        return False

def enhance_residence_links_table():
    """residence_links 테이블에 부족한 컬럼들 추가"""
    print("🔄 residence_links 테이블 확장 중...")
    
    supabase = get_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return False
    
    print("⚠️  residence_links 테이블에 다음 컬럼들을 추가해주세요:")
    print("   - platform: text")
    print("   - added_by: text") 
    print("   - date_added: date")
    print("   - memo: text")
    print("   - guarantee_insurance: boolean (default: false)")
    print("   - liked: boolean (default: false)")
    print("   - disliked: boolean (default: false)")
    print("   - is_checked: boolean (default: false)")
    print("   - rating: integer (default: 5)")
    print("   - management_site_id: text")
    
    return True

def enhance_office_links_table():
    """office_links 테이블에 부족한 컬럼들 추가"""
    print("🔄 office_links 테이블 확장 중...")
    
    supabase = get_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return False
    
    print("⚠️  office_links 테이블에 다음 컬럼들을 추가해주세요:")
    print("   - platform: text")
    print("   - added_by: text")
    print("   - date_added: date") 
    print("   - memo: text")
    print("   - guarantee_insurance: boolean (default: false)")
    print("   - liked: boolean (default: false)")
    print("   - disliked: boolean (default: false)")
    print("   - rating: integer (default: 5)")
    print("   - management_site_id: text")
    
    return True

def main():
    """메인 함수"""
    print("🚀 누락된 테이블 생성 및 기존 테이블 확장")
    print("=" * 60)
    
    # 1. guarantee_list 테이블 생성
    create_guarantee_list_table()
    
    print()
    
    # 2. links 테이블 생성 (주거용 통합)
    create_links_table()
    
    print()
    
    # 3. residence_links 테이블 확장
    enhance_residence_links_table()
    
    print()
    
    # 4. office_links 테이블 확장  
    enhance_office_links_table()
    
    print()
    print("=" * 60)
    print("📝 작업 완료!")
    print("⚠️  Supabase 대시보드에서 수동으로 테이블과 컬럼을 생성해주세요.")
    print("🔗 Supabase 대시보드: https://supabase.com/dashboard")

if __name__ == "__main__":
    main()
