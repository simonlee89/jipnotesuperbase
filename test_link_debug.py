#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
링크 추가 후 목록 표시 문제 디버깅 스크립트
"""

import os
import sys
import requests
import json
from datetime import datetime

def test_link_operations():
    """링크 추가 및 조회 테스트"""
    print("=== 링크 추가 및 조회 디버깅 테스트 ===\n")
    
    # Railway 배포된 서버 URL (포트 제거)
    BASE_URL = "https://pages-production-c2eb.up.railway.app"
    
    # 테스트 데이터
    test_data = {
        "url": f"https://test-link-{datetime.now().strftime('%H%M%S')}.com",
        "platform": "zigbang",
        "added_by": "테스트직원",
        "memo": "디버깅 테스트 링크",
        "guarantee_insurance": True,
        "residence_extra": ""
    }
    
    print("1. 주거용 사이트 테스트")
    print(f"테스트 데이터: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    # 1. 링크 추가 테스트
    print("\n[1단계] 링크 추가 테스트...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/links",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        print(f"추가 응답 상태: {response.status_code}")
        print(f"추가 응답 내용: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                link_id = result.get('id')
                print(f"✅ 링크 추가 성공! ID: {link_id}")
            else:
                print(f"❌ 링크 추가 실패: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 링크 추가 예외: {e}")
        return False
    
    # 2. 링크 목록 조회 테스트
    print("\n[2단계] 링크 목록 조회 테스트...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/links",
            timeout=10
        )
        print(f"조회 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            links = response.json()
            print(f"조회된 링크 수: {len(links)}")
            
            # 방금 추가한 링크 찾기
            found_link = None
            for link in links:
                if link.get('url') == test_data['url']:
                    found_link = link
                    break
            
            if found_link:
                print(f"✅ 추가한 링크 발견!")
                print(f"   - ID: {found_link.get('id')}")
                print(f"   - URL: {found_link.get('url')}")
                print(f"   - 플랫폼: {found_link.get('platform')}")
                print(f"   - 추가자: {found_link.get('added_by')}")
                print(f"   - 메모: {found_link.get('memo')}")
                print(f"   - 보증보험: {found_link.get('guarantee_insurance')}")
            else:
                print("❌ 추가한 링크가 목록에서 발견되지 않음!")
                print("전체 링크 목록:")
                for i, link in enumerate(links[:5]):  # 최근 5개만 표시
                    print(f"   {i+1}. {link.get('url')} ({link.get('added_by')})")
                return False
                
        else:
            print(f"❌ 조회 HTTP 오류: {response.status_code}")
            print(f"응답 내용: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 링크 조회 예외: {e}")
        return False
    
    print("\n✅ 모든 테스트 통과!")
    return True

def test_filters():
    """필터링 테스트"""
    print("\n=== 필터링 테스트 ===")
    
    BASE_URL = "https://pages-production-c2eb.up.railway.app"
    
    # 다양한 필터 조건 테스트
    filters = [
        {"platform": "all"},
        {"platform": "zigbang"},
        {"user": "all"},
        {"guarantee": "all"},
        {"guarantee": "available"},
        {"guarantee": "unavailable"}
    ]
    
    for filter_params in filters:
        try:
            response = requests.get(
                f"{BASE_URL}/api/links",
                params=filter_params,
                timeout=10
            )
            
            if response.status_code == 200:
                links = response.json()
                print(f"필터 {filter_params}: {len(links)}개 링크")
            else:
                print(f"필터 {filter_params}: HTTP {response.status_code} 오류")
                
        except Exception as e:
            print(f"필터 {filter_params}: 예외 {e}")

if __name__ == "__main__":
    print("링크 추가/조회 디버깅 테스트 시작...\n")
    
    # 기본 테스트
    success = test_link_operations()
    
    if success:
        # 필터링 테스트
        test_filters()
    
    print("\n테스트 완료!") 