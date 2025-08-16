#!/usr/bin/env python3
"""
Supabase 데이터베이스 유틸리티
"""

import os
import logging
from typing import Dict, List, Optional, Any
from supabase import create_client, Client

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase 클라이언트
_supabase_client = None

def init_supabase():
    """Supabase 클라이언트를 초기화합니다."""
    global _supabase_client
    
    try:
        SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://gkoohafmugtqwtustbrp.supabase.co')
        SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdrb29oYWZtdWd0cXd0dXN0YnJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzMzUwNTMsImV4cCI6MjA3MDkxMTA1M30.nREE7LgpxGUUA__GuzryUx2t_F4mwVtto0bPTFOqEFk')
        
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
            
        supabase.table('employees').update({'last_login': 'now()'}).eq('name', name).execute()
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

def create_maeiple_property(property_data: Dict[str, Any]) -> bool:
    """새 매물을 생성합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('maeiple_properties').insert(property_data).execute()
        return True
    except Exception as e:
        logger.error(f"매물 생성 실패: {e}")
        return False

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

# 작업 관련 함수들
def get_maeiple_tasks() -> List[Dict[str, Any]]:
    """모든 작업을 조회합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return []
            
        response = supabase.table('maeiple_tasks').select('*').order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"작업 목록 조회 실패: {e}")
        return []

def delete_maeiple_task(task_id: int) -> bool:
    """작업을 삭제합니다."""
    try:
        supabase = get_supabase()
        if not supabase:
            return False
            
        supabase.table('maeiple_tasks').delete().eq('id', task_id).execute()
        return True
    except Exception as e:
        logger.error(f"작업 삭제 실패: {e}")
        return False

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
        
        # 작업 수
        tasks_response = supabase.table('maeiple_tasks').select('id', count='exact').execute()
        task_count = tasks_response.count if hasattr(tasks_response, 'count') else 0
        
        return {
            'customers': customer_count,
            'properties': property_count,
            'tasks': task_count
        }
    except Exception as e:
        logger.error(f"대시보드 통계 조회 실패: {e}")
        return {}
