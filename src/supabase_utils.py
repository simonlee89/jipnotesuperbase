#!/usr/bin/env python3
"""
Supabase 데이터베이스 유틸리티
"""

import os
import logging
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase 클라이언트
_supabase_client = None

def init_supabase():
    """Supabase 클라이언트를 초기화합니다."""
    global _supabase_client
    
    try:
        SUPABASE_URL = os.environ.get('SUPABASE_URL')
        SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("환경변수 SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다.")
        
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase 클라이언트 초기화 성공")
        return True
    except Exception as e:
        logger.error(f"❌ Supabase 클라이언트 초기화 실패: {e}")
        return False

def get_supabase() -> Optional[Client]:
    """Supabase 클라이언트를 반환합니다."""
    if _supabase_client is None:
        init_supabase()
    return _supabase_client

# 직원 관련 함수들
def get_employee_by_name(name: str) -> Optional[Dict[str, Any]]:
    """이름으로 직원을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return None
            
        response = supabase.table('employees').select('*').eq('name', name).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"직원 조회 실패: {e}")
        return None

def update_employee_last_login(name: str) -> bool:
    """직원의 마지막 로그인 시간을 업데이트합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        from datetime import datetime
        current_time = datetime.utcnow().isoformat()
        
        supabase.table('employees').update({'last_login': current_time}).eq('name', name).execute()
        return True
    except Exception as e:
        logger.error(f"마지막 로그인 업데이트 실패: {e}")
        return False

def get_all_employees() -> List[Dict[str, Any]]:
    """모든 직원을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('employees').select('*').order('name').execute()
        return response.data
    except Exception as e:
        logger.error(f"직원 목록 조회 실패: {e}")
        return []

# 고객 관련 함수들
def get_all_customers() -> List[Dict[str, Any]]:
    """모든 고객을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('employee_customers').select('*').order('created_date', desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"고객 목록 조회 실패: {e}")
        return []

def create_customer(customer_data: Dict[str, Any]) -> bool:
    """새 고객을 생성합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('employee_customers').insert(customer_data).execute()
        return True
    except Exception as e:
        logger.error(f"고객 생성 실패: {e}")
        return False

def get_employees_with_pagination(page: int, per_page: int) -> Optional[Dict[str, Any]]:
    """페이지네이션을 적용하여 직원 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return None
            
        # 전체 개수 조회
        count_response = supabase.table('employees').select('id', count='exact').execute()
        total_count = count_response.count if count_response.count is not None else 0
        
        # 페이지네이션 적용한 데이터 조회
        offset = (page - 1) * per_page
        response = supabase.table('employees').select('*').order('created_at', desc=True).range(offset, offset + per_page - 1).execute()
        
        if response.data is not None:
            total_pages = (total_count + per_page - 1) // per_page
            return {
                'employees': response.data,
                'total_count': total_count,
                'total_pages': total_pages
            }
        return None
    except Exception as e:
        logger.error(f"직원 목록 페이지네이션 조회 실패: {e}")
        return None

def add_employee(name: str, email: str, team: str, position: str, role: str, status: str = 'active', password: str = '1234') -> Optional[Dict[str, Any]]:
    """새 직원을 추가합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return None
            
        # 중복 이름 체크
        existing = supabase.table('employees').select('id').eq('name', name).execute()
        if existing.data:
            logger.warning(f"이미 존재하는 직원 이름: {name}")
            return None
            
        # 새 직원 데이터 (created_at은 Supabase에서 자동 설정)
        employee_data = {
            'name': name,
            'email': email,
            'team': team,
            'position': position,
            'role': role,
            'status': status,
            'password': password
        }
        
        # 직원 추가
        response = supabase.table('employees').insert(employee_data).execute()
        
        if response.data:
            logger.info(f"직원 추가 성공: {name}")
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"직원 추가 실패: {e}")
        return None

def update_customer(customer_id: int, customer_data: Dict[str, Any]) -> bool:
    """고객 정보를 업데이트합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('employee_customers').update(customer_data).eq('id', customer_id).execute()
        return True
    except Exception as e:
        logger.error(f"고객 업데이트 실패: {e}")
        return False

def delete_customer(customer_id: int) -> bool:
    """고객을 삭제합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('employee_customers').delete().eq('id', customer_id).execute()
        return True
    except Exception as e:
        logger.error(f"고객 삭제 실패: {e}")
        return False

# 매물 관련 함수들
def get_maeiple_properties() -> List[Dict[str, Any]]:
    """모든 매물을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('maeiple_properties').select('*').order('check_date', desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"매물 목록 조회 실패: {e}")
        return []

def get_maeiple_properties_with_pagination(page: int, per_page: int, employee_id: str = None, sort_by: str = 'check_date', sort_order: str = 'desc') -> Optional[Dict[str, Any]]:
    """페이지네이션을 적용하여 매물 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return None
            
        # 정렬 방향 설정
        order_direction = 'desc' if sort_order == 'desc' else 'asc'
        
        # 기본 쿼리 구성
        query = supabase.table('maeiple_properties').select('*')
        
        # 직원 ID가 지정된 경우 필터링
        if employee_id:
            query = query.eq('employee_id', employee_id)
        
        # 정렬 적용
        if sort_by == 'check_date':
            query = query.order('check_date', desc=(order_direction == 'desc'))
        elif sort_by == 'building_number':
            query = query.order('building_number', desc=(order_direction == 'desc'))
        elif sort_by == 'room_number':
            query = query.order('room_number', desc=(order_direction == 'desc'))
        elif sort_by == 'status':
            query = query.order('status', desc=(order_direction == 'desc'))
        elif sort_by == 'jeonse_price':
            query = query.order('jeonse_price', desc=(order_direction == 'desc'))
        elif sort_by == 'monthly_rent':
            query = query.order('monthly_rent', desc=(order_direction == 'desc'))
        elif sort_by == 'sale_price':
            query = query.order('sale_price', desc=(order_direction == 'desc'))
        else:
            # 기본 정렬
            query = query.order('check_date', desc=True)
        
        # 전체 개수 조회
        count_query = supabase.table('maeiple_properties').select('id', count='exact')
        if employee_id:
            count_query = count_query.eq('employee_id', employee_id)
        count_response = count_query.execute()
        total_count = count_response.count if count_response.count is not None else 0
        
        # 페이지네이션 적용
        offset = (page - 1) * per_page
        response = query.range(offset, offset + per_page - 1).execute()
        
        if response.data is not None:
            total_pages = (total_count + per_page - 1) // per_page
            return {
                'properties': response.data,
                'total_count': total_count,
                'total_pages': total_pages
            }
        return None
    except Exception as e:
        logger.error(f"매물 목록 페이지네이션 조회 실패: {e}")
        return None

def get_maeiple_property(property_id: int) -> Optional[Dict[str, Any]]:
    """특정 매물을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return None
            
        response = supabase.table('maeiple_properties').select('*').eq('id', property_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"매물 조회 실패: {e}")
        return None

def create_maeiple_property(property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """새 매물을 생성하고 생성된 레코드를 반환합니다."""
    try:
        logger.info(f"매물 생성 시도: {property_data}")
        
        supabase = get_supabase()
        if not supabase:
            logger.error("Supabase 클라이언트를 가져올 수 없습니다")
            return None
            
        logger.info("Supabase 테이블에 데이터 삽입 시도...")
        response = supabase.table('maeiple_properties').insert(property_data).execute()
        
        logger.info(f"Supabase 응답: {response}")
        
        if response.data and len(response.data) > 0:
            logger.info(f"매물 생성 성공: {response.data[0]}")
            return response.data[0]
        else:
            logger.error(f"매물 생성 실패: 응답 데이터가 비어있음. 전체 응답: {response}")
            return None
            
    except Exception as e:
        logger.error(f"매물 생성 실패: {e}")
        logger.error(f"매물 데이터: {property_data}")
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        return None

def update_maeiple_property(property_id: int, property_data: Dict[str, Any]) -> bool:
    """매물 정보를 업데이트합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('maeiple_properties').update(property_data).eq('id', property_id).execute()
        return True
    except Exception as e:
        logger.error(f"매물 업데이트 실패: {e}")
        return False

def delete_maeiple_property(property_id: int) -> bool:
    """매물을 삭제합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('maeiple_properties').delete().eq('id', property_id).execute()
        return True
    except Exception as e:
        logger.error(f"매물 삭제 실패: {e}")
        return False

def update_maeiple_likes(property_id: int, likes: int, dislikes: int) -> bool:
    """매물의 좋아요/싫어요를 업데이트합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('maeiple_properties').update({
            'likes': likes,
            'dislikes': dislikes
        }).eq('id', property_id).execute()
        return True
    except Exception as e:
        logger.error(f"좋아요 업데이트 실패: {e}")
        return False

# 링크 관련 함수들
def get_residence_links() -> List[Dict[str, Any]]:
    """주거용 링크를 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('residence_links').select('*').order('id').execute()
        return response.data
    except Exception as e:
        logger.error(f"주거용 링크 조회 실패: {e}")
        return []

def get_office_links() -> List[Dict[str, Any]]:
    """업무용 링크를 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('office_links').select('*').order('id').execute()
        return response.data
    except Exception as e:
        logger.error(f"업무용 링크 조회 실패: {e}")
        return []

# 작업 관련 함수들 (maeiple_tasks 테이블 제거로 인해 삭제됨)

# 대시보드 통계
def get_dashboard_stats() -> Dict[str, Any]:
    """대시보드 통계를 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return {}
        
        # 고객 수
        customers_response = supabase.table('employee_customers').select('id', count='exact').execute()
        customer_count = customers_response.count if hasattr(customers_response, 'count') else 0
        
        # 매물 수
        properties_response = supabase.table('maeiple_properties').select('id', count='exact').execute()
        property_count = properties_response.count if hasattr(properties_response, 'count') else 0
        
        return {
            'customers': customer_count,
            'properties': property_count
        }
    except Exception as e:
        logger.error(f"대시보드 통계 조회 실패: {e}")
        return {}

def get_customers_with_pagination(page: int, per_page: int, employee_id: str = None, all_employees: bool = False) -> Optional[Dict[str, Any]]:
    """페이지네이션을 적용하여 고객 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return None
            
        # 전체 개수 조회
        if all_employees:
            count_response = supabase.table('employee_customers').select('id', count='exact').execute()
        else:
            count_response = supabase.table('employee_customers').select('id', count='exact').eq('employee_id', employee_id).execute()
        
        total_count = count_response.count if count_response.count is not None else 0
        
        # 페이지네이션 적용한 데이터 조회
        offset = (page - 1) * per_page
        if all_employees:
            response = supabase.table('employee_customers').select('*').order('created_date', desc=True).range(offset, offset + per_page - 1).execute()
        else:
            response = supabase.table('employee_customers').select('*').eq('employee_id', employee_id).order('created_date', desc=True).range(offset, offset + per_page - 1).execute()
        
        if response.data is not None:
            total_pages = (total_count + per_page - 1) // per_page
            return {
                'customers': response.data,
                'total_count': total_count,
                'total_pages': total_pages
            }
        return None
    except Exception as e:
        logger.error(f"고객 목록 페이지네이션 조회 실패: {e}")
        return None

def add_customer(customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """새 고객을 추가합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            logger.error("[ERROR] Supabase 연결 실패")
            return None
            
        # 고객 추가 전 데이터 확인
        logger.info(f"[DEBUG] 고객 추가 시도: {customer_data.get('customer_name', 'Unknown')}")
        logger.info(f"[DEBUG] 전체 고객 데이터: {customer_data}")
        
        # 데이터 필드 상세 확인
        for key, value in customer_data.items():
            logger.info(f"[DEBUG] 필드 {key}: {value} (타입: {type(value)})")
        
        # 필수 필드 확인
        if not customer_data.get('customer_name'):
            logger.error("[ERROR] 고객명이 없습니다")
            return None
        
        # boolean 필드 안전 처리 (loan_needed, parking_needed만)
        # 필드가 존재하는 경우만 처리, 없으면 그대로 두어 NULL로 저장되도록 함
        for bool_field in ['loan_needed', 'parking_needed']:
            if bool_field in customer_data:
                value = customer_data[bool_field]
                if value == '' or value is None or value == 'null' or value == 'undefined':
                    # 빈 값이면 필드 자체를 제거하여 NULL로 저장되도록 함
                    del customer_data[bool_field]
                elif isinstance(value, str):
                    # 문자열인 경우 boolean으로 변환
                    customer_data[bool_field] = value.lower() in ('true', '1', 'yes', 'on', '필요', '있음')
                elif not isinstance(value, bool):
                    customer_data[bool_field] = bool(value)
        
        # integer 필드 안전 처리 (unchecked_likes는 미확인 좋아요 개수)
        for int_field in ['unchecked_likes_residence', 'unchecked_likes_business']:
            if int_field in customer_data:
                value = customer_data[int_field]
                if value == '' or value is None or value == 'null' or value == 'undefined' or value is False:
                    customer_data[int_field] = 0
                elif isinstance(value, bool):
                    customer_data[int_field] = 0  # boolean False를 0으로 변환
                elif isinstance(value, str):
                    try:
                        customer_data[int_field] = int(value)
                    except ValueError:
                        customer_data[int_field] = 0
                elif not isinstance(value, int):
                    customer_data[int_field] = 0
            else:
                customer_data[int_field] = 0
        
        logger.info(f"[DEBUG] Supabase insert 시작")
        response = supabase.table('employee_customers').insert(customer_data).execute()
        
        logger.info(f"[DEBUG] Supabase 응답: {response}")
        logger.info(f"[DEBUG] 응답 데이터: {response.data}")
        
        if response.data and len(response.data) > 0:
            new_customer = response.data[0]
            customer_name = customer_data.get('customer_name', 'Unknown')
            
            logger.info(f"[SUCCESS] 고객 추가 성공: {customer_name}, ID: {new_customer.get('id')}")
            
            return new_customer
        else:
            logger.error(f"[ERROR] 고객 추가 실패: response.data가 비어있음")
            return None
    except Exception as e:
        logger.error(f"[ERROR] 고객 추가 실패: {e}")
        logger.error(f"[ERROR] 고객 데이터 타입별 상세:")
        for key, value in customer_data.items():
            logger.error(f"[ERROR]   {key}: {repr(value)} (type: {type(value)})")
        import traceback
        traceback.print_exc()
        return None





def get_guarantee_insurance_links(limit: int = 20) -> List[Dict[str, Any]]:
    """보증보험 매물 목록을 조회합니다. (주거용 링크에서)"""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
        
        # 보증보험은 주거용 링크에서 관리되므로 residence_links 테이블 우선 사용
        try:
            # residence_links 테이블에서 guarantee_insurance 컬럼이 있는 경우
            response = supabase.table('residence_links').select('*').eq('guarantee_insurance', True).order('id', desc=True).limit(limit).execute()
            return response.data
        except Exception:
            # guarantee_insurance 컬럼이 없는 경우 모든 주거용 링크 반환
            try:
                response = supabase.table('residence_links').select('*').order('id', desc=True).limit(limit).execute()
                return response.data
            except Exception:
                # residence_links도 실패하면 빈 리스트 반환
                logger.warning("보증보험 매물 목록 조회 실패 - 빈 리스트 반환")
                return []
                
    except Exception as e:
        logger.error(f"보증보험 매물 목록 조회 실패: {e}")
        return []

def check_employee_exists(name: str) -> bool:
    """직원이 존재하는지 확인합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        response = supabase.table('employees').select('id, name').eq('name', name).execute()
        return len(response.data) > 0
    except Exception as e:
        logger.error(f"직원 존재 확인 실패: {e}")
        return False

def get_maeiple_properties(limit: int = 50) -> List[Dict[str, Any]]:
    """메이플 아파트 매물 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('maeiple_properties').select('*').order('id', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"메이플 아파트 매물 목록 조회 실패: {e}")
        return []

def get_team_customers(team_leader_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """팀장의 고객 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('employee_customers').select('*').eq('employee_id', team_leader_id).order('created_date', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"팀 고객 목록 조회 실패: {e}")
        return []

def get_team_maeiple_properties(team_leader_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """팀장의 메이플 아파트 매물 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('maeiple_properties').select('*').eq('employee_id', team_leader_id).order('id', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"팀 메이플 아파트 매물 목록 조회 실패: {e}")
        return []

def update_maeiple_property(property_id: int, update_data: Dict[str, Any]) -> bool:
    """메이플 아파트 매물을 업데이트합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('maeiple_properties').update(update_data).eq('id', property_id).execute()
        return True
    except Exception as e:
        logger.error(f"메이플 아파트 매물 업데이트 실패: {e}")
        return False

def add_maeiple_memo(property_id: int, memo: str) -> bool:
    """메이플 아파트 매물에 메모를 추가합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('maeiple_properties').update({'memo': memo}).eq('id', property_id).execute()
        return True
    except Exception as e:
        logger.error(f"메이플 아파트 매물 메모 추가 실패: {e}")
        return False

def delete_maeiple_property(property_id: int) -> bool:
    """메이플 아파트 매물을 삭제합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('maeiple_properties').delete().eq('id', property_id).execute()
        return True
    except Exception as e:
        logger.error(f"메이플 아파트 매물 삭제 실패: {e}")
        return False

def get_guarantee_list(limit: int = 50) -> List[Dict[str, Any]]:
    """보증보험 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('guarantee_list').select('*').order('id', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"보증보험 목록 조회 실패: {e}")
        return []

def update_guarantee_insurance_status(link_id: int, status: bool) -> bool:
    """보증보험 매물 상태를 변경합니다. (주거용 링크에서)"""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        # 보증보험은 주거용 링크에서 관리되므로 'residence_links' 테이블 사용
        supabase.table('residence_links').update({'guarantee_insurance': status}).eq('id', link_id).execute()
        return True
    except Exception as e:
        logger.error(f"보증보험 매물 상태 변경 실패: {e}")
        return False

def update_link_memo(link_id: int, memo: str, table_type: str = 'residence') -> bool:
    """링크 메모를 업데이트합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        # 테이블 타입에 따라 적절한 테이블 선택
        table_name = 'residence_links' if table_type == 'residence' else 'office_links'
        supabase.table(table_name).update({'memo': memo}).eq('id', link_id).execute()
        return True
    except Exception as e:
        logger.error(f"링크 메모 업데이트 실패: {e}")
        return False

def get_team_all_customers(team_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """팀 전체 고객 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        # 팀 전체 고객 조회 (팀장 + 팀원)
        response = supabase.table('employee_customers').select('*, employees!inner(team)').eq('employees.team', team_name).order('inquiry_date', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"팀 전체 고객 목록 조회 실패: {e}")
        return []

def get_team_all_maeiple_properties(team_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """팀 전체 메이플 아파트 매물 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('maeiple_properties').select('*').eq('employee_team', team_name).order('check_date', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"팀 전체 메이플 아파트 매물 목록 조회 실패: {e}")
        return []

def get_personal_maeiple_properties(employee_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """개인용 메이플 아파트 매물 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        if employee_id:
            # 특정 직원의 매물만 조회
            response = supabase.table('maeiple_properties').select('*').eq('employee_id', employee_id).order('check_date', desc=True).limit(limit).execute()
        else:
            # 모든 매물 조회
            response = supabase.table('maeiple_properties').select('*').order('check_date', desc=True).limit(limit).execute()
        
        return response.data
    except Exception as e:
        logger.error(f"개인용 메이플 아파트 매물 목록 조회 실패: {e}")
        return []

def get_team_leader_customers(team_leader_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """팀장 본인의 고객 목록을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('employee_customers').select('*').eq('employee_id', team_leader_id).order('inquiry_date', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"팀장 본인 고객 목록 조회 실패: {e}")
        return []
