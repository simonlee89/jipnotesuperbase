#!/usr/bin/env python3
"""
Supabase 데이터베이스 연결 테스트 및 테이블 정보 확인
"""

import os
import sys
from supabase_utils import init_supabase, get_supabase

def check_database_connection():
    """데이터베이스 연결을 테스트합니다."""
    print("🔍 Supabase 데이터베이스 연결 테스트 중...")
    
    # Supabase 초기화
    if init_supabase():
        print("✅ Supabase 클라이언트 초기화 성공")
        
        # 클라이언트 가져오기
        supabase = get_supabase()
        if supabase:
            print("✅ Supabase 클라이언트 연결 성공")
            return supabase
        else:
            print("❌ Supabase 클라이언트 연결 실패")
            return None
    else:
        print("❌ Supabase 초기화 실패")
        return None

def get_table_info(supabase):
    """테이블 정보를 조회합니다."""
    print("\n📊 데이터베이스 테이블 정보 조회 중...")
    
    # 주요 테이블들 확인
    tables_to_check = [
        'employees',
        'employee_customers', 
        'maeiple_properties',
        'maeiple_tasks',
        'residence_links',
        'office_links',
        'guarantee_list',
        'links'
    ]
    
    table_info = {}
    
    for table_name in tables_to_check:
        try:
            print(f"\n🔍 테이블 '{table_name}' 확인 중...")
            
            # 테이블 존재 여부 확인 (첫 번째 레코드 조회)
            response = supabase.table(table_name).select('*').limit(1).execute()
            
            if response.data is not None:
                # 컬럼 정보 추출 (첫 번째 레코드의 키들)
                if response.data:
                    columns = list(response.data[0].keys())
                    record_count = len(response.data)
                    
                    # 전체 레코드 수 조회
                    count_response = supabase.table(table_name).select('id', count='exact').execute()
                    total_count = count_response.count if count_response.count is not None else 0
                    
                    table_info[table_name] = {
                        'exists': True,
                        'columns': columns,
                        'sample_record': response.data[0] if response.data else None,
                        'total_count': total_count
                    }
                    
                    print(f"  ✅ 테이블 존재 - 컬럼 수: {len(columns)}, 총 레코드: {total_count}")
                    print(f"  📋 컬럼: {', '.join(columns)}")
                    
                else:
                    table_info[table_name] = {
                        'exists': True,
                        'columns': [],
                        'sample_record': None,
                        'total_count': 0
                    }
                    print(f"  ✅ 테이블 존재 (빈 테이블)")
                    
            else:
                table_info[table_name] = {
                    'exists': False,
                    'columns': [],
                    'sample_record': None,
                    'total_count': 0
                }
                print(f"  ❌ 테이블이 존재하지 않음")
                
        except Exception as e:
            table_info[table_name] = {
                'exists': False,
                'error': str(e),
                'columns': [],
                'sample_record': None,
                'total_count': 0
            }
            print(f"  ❌ 테이블 조회 오류: {e}")
    
    return table_info

def show_sample_data(supabase, table_name, limit=3):
    """테이블의 샘플 데이터를 보여줍니다."""
    try:
        print(f"\n📋 테이블 '{table_name}' 샘플 데이터 (최대 {limit}개):")
        
        response = supabase.table(table_name).select('*').limit(limit).execute()
        
        if response.data:
            for i, record in enumerate(response.data, 1):
                print(f"\n  📝 레코드 {i}:")
                for key, value in record.items():
                    print(f"    {key}: {value}")
        else:
            print("  📭 데이터가 없습니다.")
            
    except Exception as e:
        print(f"  ❌ 샘플 데이터 조회 실패: {e}")

def main():
    """메인 함수"""
    print("🚀 Supabase 데이터베이스 정보 확인 도구")
    print("=" * 50)
    
    # 데이터베이스 연결 테스트
    supabase = check_database_connection()
    
    if not supabase:
        print("\n❌ 데이터베이스 연결에 실패했습니다.")
        return
    
    # 테이블 정보 조회
    table_info = get_table_info(supabase)
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 데이터베이스 요약")
    print("=" * 50)
    
    existing_tables = [name for name, info in table_info.items() if info.get('exists')]
    total_records = sum(info.get('total_count', 0) for info in table_info.values())
    
    print(f"✅ 존재하는 테이블: {len(existing_tables)}개")
    print(f"📊 총 레코드 수: {total_records:,}개")
    
    if existing_tables:
        print(f"\n📋 테이블 목록:")
        for table_name in existing_tables:
            info = table_info[table_name]
            count = info.get('total_count', 0)
            print(f"  • {table_name}: {count:,}개 레코드")
    
    # 사용자 선택으로 샘플 데이터 보기
    print("\n" + "=" * 50)
    print("🔍 샘플 데이터 확인")
    print("=" * 50)
    
    if existing_tables:
        print("샘플 데이터를 확인할 테이블을 선택하세요:")
        for i, table_name in enumerate(existing_tables, 1):
            print(f"  {i}. {table_name}")
        
        try:
            choice = input("\n테이블 번호를 입력하세요 (Enter로 종료): ").strip()
            if choice.isdigit():
                table_index = int(choice) - 1
                if 0 <= table_index < len(existing_tables):
                    selected_table = existing_tables[table_index]
                    show_sample_data(supabase, selected_table)
                else:
                    print("❌ 잘못된 번호입니다.")
            else:
                print("프로그램을 종료합니다.")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()
