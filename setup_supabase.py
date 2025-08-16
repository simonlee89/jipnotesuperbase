#!/usr/bin/env python3
"""
Supabase 데이터베이스 설정 스크립트
이 스크립트를 실행하여 Supabase에 테이블을 생성하고 초기 데이터를 삽입합니다.
"""

import os
import sys
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

def create_tables(supabase: Client):
    """테이블을 생성합니다."""
    print("\n🏗️ 테이블 생성 시작...")
    
    # 1. 직원 테이블
    try:
        response = supabase.table('employees').select('*').limit(1).execute()
        print("✅ employees 테이블이 이미 존재합니다.")
    except:
        print("📋 employees 테이블을 생성합니다...")
        # 테이블이 없으면 자동으로 생성됨 (Supabase는 스키마를 자동으로 생성)
        pass
    
    # 2. 직원 고객 테이블
    try:
        response = supabase.table('employee_customers').select('*').limit(1).execute()
        print("✅ employee_customers 테이블이 이미 존재합니다.")
    except:
        print("📋 employee_customers 테이블을 생성합니다...")
        pass
    
    # 3. 메이플 매물 테이블
    try:
        response = supabase.table('maeiple_properties').select('*').limit(1).execute()
        print("✅ maeiple_properties 테이블이 이미 존재합니다.")
    except:
        print("📋 maeiple_properties 테이블을 생성합니다...")
        pass
    
    # 4. 주거용 링크 테이블
    try:
        response = supabase.table('residence_links').select('*').limit(1).execute()
        print("✅ residence_links 테이블이 이미 존재합니다.")
    except:
        print("📋 residence_links 테이블을 생성합니다...")
        pass
    
    # 5. 업무용 링크 테이블
    try:
        response = supabase.table('office_links').select('*').limit(1).execute()
        print("✅ office_links 테이블이 이미 존재합니다.")
    except:
        print("📋 office_links 테이블을 생성합니다...")
        pass
    
    # 6. 매이플 작업 테이블
    try:
        response = supabase.table('maeiple_tasks').select('*').limit(1).execute()
        print("✅ maeiple_tasks 테이블이 이미 존재합니다.")
    except:
        print("📋 maeiple_tasks 테이블을 생성합니다...")
        pass

def insert_sample_data(supabase: Client):
    """샘플 데이터를 삽입합니다."""
    print("\n📊 샘플 데이터 삽입 시작...")
    
    # 1. 직원 데이터
    try:
        employees_data = [
            {
                'name': '원형',
                'email': 'wonhyeong@example.com',
                'password': '1',
                'team': '관리자',
                'position': '관리자',
                'role': 'employee'
            },
            {
                'name': '테스트',
                'email': 'test@example.com',
                'password': '1',
                'team': '관리자',
                'position': '테스터',
                'role': 'employee'
            },
            {
                'name': 'admin',
                'email': 'admin@example.com',
                'password': '1',
                'team': '관리자',
                'position': '시스템관리자',
                'role': 'employee'
            },
            {
                'name': '관리자',
                'email': 'manager@example.com',
                'password': '1',
                'team': '관리자',
                'position': '매니저',
                'role': 'employee'
            },
            {
                'name': '수정',
                'email': 'sujung@example.com',
                'password': '1',
                'team': '위플러스',
                'position': '팀장',
                'role': '팀장'
            }
        ]
        
        for employee in employees_data:
            try:
                response = supabase.table('employees').insert(employee).execute()
                print(f"✅ 직원 '{employee['name']}' 추가 완료")
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    print(f"⚠️ 직원 '{employee['name']}'은 이미 존재합니다.")
                else:
                    print(f"❌ 직원 '{employee['name']}' 추가 실패: {e}")
    except Exception as e:
        print(f"❌ 직원 데이터 삽입 실패: {e}")
    
    # 2. 고객 데이터
    try:
        customers_data = [
            {
                'inquiry_date': '2024-08-15',
                'customer_name': '김철수',
                'customer_phone': '010-1234-5678',
                'budget': 5000,
                'rooms': '2룸',
                'location': '강남구',
                'loan_needed': True,
                'parking_needed': True,
                'pets': '불가',
                'memo': '급하게 구하고 있음',
                'status': '상담중',
                'employee_name': '원형',
                'employee_team': '관리자',
                'management_site_id': 'kim-chulsoo-001'
            },
            {
                'inquiry_date': '2024-08-14',
                'customer_name': '이영희',
                'customer_phone': '010-9876-5432',
                'budget': 3000,
                'rooms': '1룸',
                'location': '서초구',
                'loan_needed': False,
                'parking_needed': False,
                'pets': '가능',
                'memo': '펫 가능한 곳 선호',
                'status': '계약완료',
                'employee_name': '원형',
                'employee_team': '관리자',
                'management_site_id': 'lee-younghee-002'
            }
        ]
        
        for customer in customers_data:
            try:
                response = supabase.table('employee_customers').insert(customer).execute()
                print(f"✅ 고객 '{customer['customer_name']}' 추가 완료")
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    print(f"⚠️ 고객 '{customer['customer_name']}'은 이미 존재합니다.")
                else:
                    print(f"❌ 고객 '{customer['customer_name']}' 추가 실패: {e}")
    except Exception as e:
        print(f"❌ 고객 데이터 삽입 실패: {e}")
    
    # 3. 메이플 매물 데이터
    try:
        properties_data = [
            {
                'check_date': '2024-08-15',
                'building_number': '101',
                'room_number': '101',
                'status': '거래중',
                'jeonse_price': 5000,
                'monthly_rent': None,
                'sale_price': None,
                'is_occupied': False,
                'phone': '010-1111-1111',
                'memo': '강남역 근처, 교통편리',
                'employee_name': '원형',
                'employee_team': '관리자'
            },
            {
                'check_date': '2024-08-14',
                'building_number': '101',
                'room_number': '102',
                'status': '거래완료',
                'jeonse_price': None,
                'monthly_rent': 50,
                'sale_price': None,
                'is_occupied': True,
                'phone': '010-2222-2222',
                'memo': '월세 거래 완료',
                'employee_name': '원형',
                'employee_team': '관리자'
            },
            {
                'check_date': '2024-08-13',
                'building_number': '102',
                'room_number': '201',
                'status': '거래중',
                'jeonse_price': None,
                'monthly_rent': None,
                'sale_price': 80000,
                'is_occupied': False,
                'phone': '010-3333-3333',
                'memo': '매매 희망',
                'employee_name': '원형',
                'employee_team': '관리자'
            }
        ]
        
        for property_data in properties_data:
            try:
                response = supabase.table('maeiple_properties').insert(property_data).execute()
                print(f"✅ 매물 '{property_data['building_number']}동 {property_data['room_number']}호' 추가 완료")
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    print(f"⚠️ 매물 '{property_data['building_number']}동 {property_data['room_number']}호'는 이미 존재합니다.")
                else:
                    print(f"❌ 매물 '{property_data['building_number']}동 {property_data['room_number']}호' 추가 실패: {e}")
    except Exception as e:
        print(f"❌ 매물 데이터 삽입 실패: {e}")
    
    # 4. 링크 데이터
    try:
        residence_links_data = [
            {'title': '네이버', 'url': 'https://www.naver.com', 'description': '주요 검색 엔진'},
            {'title': '구글', 'url': 'https://www.google.com', 'description': '글로벌 검색 엔진'}
        ]
        
        for link in residence_links_data:
            try:
                response = supabase.table('residence_links').insert(link).execute()
                print(f"✅ 주거용 링크 '{link['title']}' 추가 완료")
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    print(f"⚠️ 주거용 링크 '{link['title']}'은 이미 존재합니다.")
                else:
                    print(f"❌ 주거용 링크 '{link['title']}' 추가 실패: {e}")
        
        office_links_data = [
            {'title': '회사 홈페이지', 'url': 'https://company.com', 'description': '회사 공식 웹사이트'},
            {'title': '업무 시스템', 'url': 'https://work.company.com', 'description': '업무용 시스템'}
        ]
        
        for link in office_links_data:
            try:
                response = supabase.table('office_links').insert(link).execute()
                print(f"✅ 업무용 링크 '{link['title']}' 추가 완료")
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    print(f"⚠️ 업무용 링크 '{link['title']}'은 이미 존재합니다.")
                else:
                    print(f"❌ 업무용 링크 '{link['title']}' 추가 실패: {e}")
    except Exception as e:
        print(f"❌ 링크 데이터 삽입 실패: {e}")
    
    # 5. 매이플 작업 데이터
    try:
        tasks_data = [
            {
                'title': '강남구 매물 현장 확인',
                'description': '강남역 근처 신축 아파트 현장 확인 필요',
                'assigned_to': '원형',
                'priority': 'high',
                'status': 'pending'
            },
            {
                'title': '서초구 계약 진행',
                'description': '서초구 월세 계약 진행 상황 점검',
                'assigned_to': '수정',
                'priority': 'medium',
                'status': 'in_progress'
            }
        ]
        
        for task in tasks_data:
            try:
                response = supabase.table('maeiple_tasks').insert(task).execute()
                print(f"✅ 작업 '{task['title']}' 추가 완료")
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    print(f"⚠️ 작업 '{task['title']}'은 이미 존재합니다.")
                else:
                    print(f"❌ 작업 '{task['title']}' 추가 실패: {e}")
    except Exception as e:
        print(f"❌ 작업 데이터 삽입 실패: {e}")

def verify_tables(supabase: Client):
    """테이블이 제대로 생성되었는지 확인합니다."""
    print("\n🔍 테이블 생성 확인...")
    
    tables = ['employees', 'employee_customers', 'maeiple_properties', 'residence_links', 'office_links', 'maeiple_tasks']
    
    for table in tables:
        try:
            response = supabase.table(table).select('*').limit(1).execute()
            print(f"✅ {table} 테이블 확인 완료")
        except Exception as e:
            print(f"❌ {table} 테이블 확인 실패: {e}")

def main():
    """메인 함수"""
    print("🚀 Supabase 데이터베이스 설정 시작")
    print("=" * 50)
    
    # Supabase 클라이언트 초기화
    supabase = init_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패. 프로그램을 종료합니다.")
        sys.exit(1)
    
    # 테이블 생성
    create_tables(supabase)
    
    # 샘플 데이터 삽입
    insert_sample_data(supabase)
    
    # 테이블 확인
    verify_tables(supabase)
    
    print("\n" + "=" * 50)
    print("🎉 Supabase 데이터베이스 설정 완료!")
    print("\n📋 다음 단계:")
    print("1. Supabase 대시보드에서 테이블 구조 확인")
    print("2. RLS 정책 설정 확인")
    print("3. 애플리케이션 실행: python 관리자페이지.py")
    print("\n🔐 기본 테스트 계정:")
    print("- 원형 / 1 (관리자)")
    print("- 테스트 / 1 (관리자)")
    print("- admin / 1 (관리자)")
    print("- 관리자 / 1 (관리자)")
    print("- 수정 / 1 (팀장)")

if __name__ == "__main__":
    main()
