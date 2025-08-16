import os
import logging
from datetime import datetime
from supabase import create_client, Client

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase 클라이언트
supabase: Client = None

def init_supabase():
    """Supabase 클라이언트를 초기화합니다."""
    global supabase
    
    # Supabase 설정
    SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://gkoohafmugtqwtustbrp.supabase.co')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdrb29oYWZtdWd0cXd0dXN0YnJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzMzUwNTMsImV4cCI6MjA3MDkxMTA1M30.nREE7LgpxGUUA__GuzryUx2t_F4mwVtto0bPTFOqEFk')
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase 클라이언트 초기화 성공")
        return True
    except Exception as e:
        logger.error(f"❌ Supabase 클라이언트 초기화 실패: {e}")
        return False

def get_supabase():
    """Supabase 클라이언트를 반환합니다."""
    global supabase
    if supabase is None:
        init_supabase()
    return supabase

def init_database():
    """데이터베이스 테이블을 초기화합니다."""
    try:
        # Supabase에서 테이블이 자동으로 생성되므로 별도 작업 불필요
        logger.info("✅ Supabase 데이터베이스 초기화 완료")
        return True
    except Exception as e:
        logger.error(f"❌ Supabase 데이터베이스 초기화 실패: {e}")
        return False

# 직원 관련 함수들
def get_employee_by_name(name):
    """이름으로 직원을 조회합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('employees').select('*').eq('name', name).execute()
        
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"직원 조회 실패: {e}")
        return None

def create_employee(name, email, team, position, role='employee'):
    """새 직원을 생성합니다."""
    try:
        supabase_client = get_supabase()
        data = {
            'name': name,
            'email': email,
            'team': team,
            'position': position,
            'role': role,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        response = supabase_client.table('employees').insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"직원 생성 실패: {e}")
        return None

def update_employee_last_login(employee_id):
    """직원의 마지막 로그인 시간을 업데이트합니다."""
    try:
        supabase_client = get_supabase()
        data = {'last_login': datetime.now().isoformat()}
        response = supabase_client.table('employees').update(data).eq('id', employee_id).execute()
        return True
    except Exception as e:
        logger.error(f"로그인 시간 업데이트 실패: {e}")
        return False

def get_all_employees():
    """모든 직원을 조회합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('employees').select('*').execute()
        return response.data
    except Exception as e:
        logger.error(f"직원 목록 조회 실패: {e}")
        return []

# 고객 관련 함수들 (상세 구조)
def get_employee_customers(employee_id):
    """직원의 고객 목록을 조회합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('employee_customers').select('*').eq('employee_id', employee_id).execute()
        return response.data
    except Exception as e:
        logger.error(f"고객 목록 조회 실패: {e}")
        return []

def get_all_customers():
    """모든 고객을 조회합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('employee_customers').select('*').execute()
        return response.data
    except Exception as e:
        logger.error(f"전체 고객 목록 조회 실패: {e}")
        return []

def create_customer(customer_data):
    """새 고객을 생성합니다."""
    try:
        supabase_client = get_supabase()
        data = {
            'inquiry_date': customer_data.get('inquiry_date', datetime.now().date().isoformat()),
            'customer_name': customer_data.get('customer_name'),
            'customer_phone': customer_data.get('customer_phone'),
            'budget': customer_data.get('budget'),
            'rooms': customer_data.get('rooms'),
            'location': customer_data.get('location'),
            'loan_needed': customer_data.get('loan_needed', False),
            'parking_needed': customer_data.get('parking_needed', False),
            'pets': customer_data.get('pets', '불가'),
            'memo': customer_data.get('memo'),
            'status': customer_data.get('status', '상담중'),
            'employee_id': customer_data.get('employee_id'),
            'employee_name': customer_data.get('employee_name'),
            'employee_team': customer_data.get('employee_team'),
            'management_site_id': customer_data.get('management_site_id'),
            'created_date': datetime.now().isoformat()
        }
        
        response = supabase_client.table('employee_customers').insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"고객 생성 실패: {e}")
        return None

def update_customer(customer_id, customer_data):
    """고객 정보를 업데이트합니다."""
    try:
        supabase_client = get_supabase()
        data = {
            'inquiry_date': customer_data.get('inquiry_date'),
            'customer_name': customer_data.get('customer_name'),
            'customer_phone': customer_data.get('customer_phone'),
            'budget': customer_data.get('budget'),
            'rooms': customer_data.get('rooms'),
            'location': customer_data.get('location'),
            'loan_needed': customer_data.get('loan_needed'),
            'parking_needed': customer_data.get('parking_needed'),
            'pets': customer_data.get('pets'),
            'memo': customer_data.get('memo'),
            'status': customer_data.get('status'),
            'updated_date': datetime.now().isoformat()
        }
        
        response = supabase_client.table('employee_customers').update(data).eq('id', customer_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"고객 업데이트 실패: {e}")
        return None

def delete_customer(customer_id):
    """고객을 삭제합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('employee_customers').delete().eq('id', customer_id).execute()
        return True
    except Exception as e:
        logger.error(f"고객 삭제 실패: {e}")
        return False

# 메이플 매물 관련 함수들 (핵심!)
def get_maeiple_properties(employee_id=None, team=None):
    """메이플 매물 목록을 조회합니다."""
    try:
        supabase_client = get_supabase()
        query = supabase_client.table('maeiple_properties').select('*')
        
        if employee_id:
            query = query.eq('employee_id', employee_id)
        if team:
            query = query.eq('employee_team', team)
            
        response = query.order('check_date', desc=True).execute()
        return response.data
    except Exception as e:
        logger.error(f"메이플 매물 조회 실패: {e}")
        return []

def get_maeiple_property(property_id):
    """특정 메이플 매물을 조회합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('maeiple_properties').select('*').eq('id', property_id).execute()
        
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"메이플 매물 조회 실패: {e}")
        return None

def create_maeiple_property(property_data):
    """새 메이플 매물을 생성합니다."""
    try:
        supabase_client = get_supabase()
        data = {
            'check_date': property_data.get('check_date', datetime.now().date().isoformat()),
            'building_number': property_data.get('building_number'),
            'room_number': property_data.get('room_number'),
            'status': property_data.get('status', '거래중'),
            'jeonse_price': property_data.get('jeonse_price'),
            'monthly_rent': property_data.get('monthly_rent'),
            'sale_price': property_data.get('sale_price'),
            'is_occupied': property_data.get('is_occupied', False),
            'phone': property_data.get('phone'),
            'memo': property_data.get('memo'),
            'likes': property_data.get('likes', 0),
            'dislikes': property_data.get('dislikes', 0),
            'employee_id': property_data.get('employee_id'),
            'employee_name': property_data.get('employee_name'),
            'employee_team': property_data.get('employee_team'),
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase_client.table('maeiple_properties').insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"메이플 매물 생성 실패: {e}")
        return None

def update_maeiple_property(property_id, property_data):
    """메이플 매물을 업데이트합니다."""
    try:
        supabase_client = get_supabase()
        data = {
            'check_date': property_data.get('check_date'),
            'building_number': property_data.get('building_number'),
            'room_number': property_data.get('room_number'),
            'status': property_data.get('status'),
            'jeonse_price': property_data.get('jeonse_price'),
            'monthly_rent': property_data.get('monthly_rent'),
            'sale_price': property_data.get('sale_price'),
            'is_occupied': property_data.get('is_occupied'),
            'phone': property_data.get('phone'),
            'memo': property_data.get('memo'),
            'likes': property_data.get('likes'),
            'dislikes': property_data.get('dislikes'),
            'updated_at': datetime.now().isoformat()
        }
        
        response = supabase_client.table('maeiple_properties').update(data).eq('id', property_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"메이플 매물 업데이트 실패: {e}")
        return None

def delete_maeiple_property(property_id):
    """메이플 매물을 삭제합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('maeiple_properties').delete().eq('id', property_id).execute()
        return True
    except Exception as e:
        logger.error(f"메이플 매물 삭제 실패: {e}")
        return False

def update_maeiple_likes(property_id, likes, dislikes):
    """메이플 매물의 좋아요/싫어요를 업데이트합니다."""
    try:
        supabase_client = get_supabase()
        data = {
            'likes': likes,
            'dislikes': dislikes,
            'updated_at': datetime.now().isoformat()
        }
        
        response = supabase_client.table('maeiple_properties').update(data).eq('id', property_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"좋아요/싫어요 업데이트 실패: {e}")
        return None

# 링크 관련 함수들
def get_residence_links():
    """주거용 링크 목록을 조회합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('residence_links').select('*').execute()
        return response.data
    except Exception as e:
        logger.error(f"주거용 링크 조회 실패: {e}")
        return []

def get_office_links():
    """업무용 링크 목록을 조회합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('office_links').select('*').execute()
        return response.data
    except Exception as e:
        logger.error(f"업무용 링크 조회 실패: {e}")
        return []

def create_link(table_name, link_data):
    """새 링크를 생성합니다."""
    try:
        supabase_client = get_supabase()
        data = {
            'title': link_data.get('title'),
            'url': link_data.get('url'),
            'description': link_data.get('description', ''),
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase_client.table(table_name).insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"링크 생성 실패: {e}")
        return None

def update_link(table_name, link_id, link_data):
    """링크를 업데이트합니다."""
    try:
        supabase_client = get_supabase()
        data = {
            'title': link_data.get('title'),
            'url': link_data.get('url'),
            'description': link_data.get('description', ''),
            'updated_at': datetime.now().isoformat()
        }
        
        response = supabase_client.table(table_name).update(data).eq('id', link_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"링크 업데이트 실패: {e}")
        return None

def delete_link(table_name, link_id):
    """링크를 삭제합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table(table_name).delete().eq('id', link_id).execute()
        return True
    except Exception as e:
        logger.error(f"링크 삭제 실패: {e}")
        return False

# 매이플 작업 관련 함수들
def get_maeiple_tasks():
    """매이플 작업 목록을 조회합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('maeiple_tasks').select('*').execute()
        return response.data
    except Exception as e:
        logger.error(f"매이플 작업 조회 실패: {e}")
        return []

def create_maeiple_task(task_data):
    """새 매이플 작업을 생성합니다."""
    try:
        supabase_client = get_supabase()
        data = {
            'title': task_data.get('title'),
            'description': task_data.get('description'),
            'assigned_to': task_data.get('assigned_to'),
            'priority': task_data.get('priority', 'medium'),
            'status': task_data.get('status', 'pending'),
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase_client.table('maeiple_tasks').insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"매이플 작업 생성 실패: {e}")
        return None

def update_maeiple_task(task_id, task_data):
    """매이플 작업을 업데이트합니다."""
    try:
        supabase_client = get_supabase()
        data = {
            'title': task_data.get('title'),
            'description': task_data.get('description'),
            'assigned_to': task_data.get('assigned_to'),
            'priority': task_data.get('priority'),
            'status': task_data.get('status'),
            'updated_at': datetime.now().isoformat()
        }
        
        response = supabase_client.table('maeiple_tasks').update(data).eq('id', task_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"매이플 작업 업데이트 실패: {e}")
        return None

def delete_maeiple_task(task_id):
    """매이플 작업을 삭제합니다."""
    try:
        supabase_client = get_supabase()
        response = supabase_client.table('maeiple_tasks').delete().eq('id', task_id).execute()
        return True
    except Exception as e:
        logger.error(f"매이플 작업 삭제 실패: {e}")
        return False

# 통계 및 대시보드 함수들
def get_dashboard_stats(employee_id=None, team=None):
    """대시보드 통계를 조회합니다."""
    try:
        stats = {}
        
        # 고객 통계
        customers = get_employee_customers(employee_id) if employee_id else get_all_customers()
        stats['total_customers'] = len(customers)
        stats['active_customers'] = len([c for c in customers if c.get('status') == '상담중'])
        stats['completed_customers'] = len([c for c in customers if c.get('status') == '계약완료'])
        
        # 매물 통계
        properties = get_maeiple_properties(employee_id, team)
        stats['total_properties'] = len(properties)
        stats['available_properties'] = len([p for p in properties if p.get('status') == '거래중'])
        stats['completed_properties'] = len([p for p in properties if p.get('status') == '거래완료'])
        
        # 작업 통계
        tasks = get_maeiple_tasks()
        stats['total_tasks'] = len(tasks)
        stats['pending_tasks'] = len([t for t in tasks if t.get('status') == 'pending'])
        stats['in_progress_tasks'] = len([t for t in tasks if t.get('status') == 'in_progress'])
        stats['completed_tasks'] = len([t for t in tasks if t.get('status') == 'completed'])
        
        return stats
    except Exception as e:
        logger.error(f"대시보드 통계 조회 실패: {e}")
        return {}
