#!/usr/bin/env python3
"""
기존 고객들에게 전용 주거용/업무용 링크를 생성하는 스크립트
"""

import os
import sys
from supabase_utils import init_supabase, create_links_for_existing_customers

def main():
    """메인 함수"""
    print("🚀 기존 고객들에게 전용 링크 생성")
    print("=" * 50)
    
    # Supabase 초기화
    if not init_supabase():
        print("❌ Supabase 초기화 실패")
        return
    
    # 기존 고객들에게 전용 링크 생성
    print("🔄 기존 고객들에게 전용 링크 생성 중...")
    
    if create_links_for_existing_customers():
        print("✅ 기존 고객 전용 링크 생성 완료!")
    else:
        print("❌ 기존 고객 전용 링크 생성 실패")
    
    print("=" * 50)
    print("📝 작업 완료!")
    print()
    print("🎯 이제 각 고객별로 독립적인 주거용/업무용 링크가 생성됩니다:")
    print("  - 새 고객 추가 시 자동으로 전용 링크 생성")
    print("  - 각 고객은 자신만의 링크 목록을 가짐")
    print("  - management_site_id로 링크 분리 관리")

if __name__ == "__main__":
    main()
