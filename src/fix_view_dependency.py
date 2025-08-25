"""
View 의존성 문제 해결하여 컬럼 타입 변경
"""

def generate_fix_sql():
    """View 의존성 해결을 위한 SQL 생성"""
    
    print("=== View 의존성 해결을 위한 SQL ===")
    print()
    print("다음 SQL을 Supabase Dashboard의 SQL Editor에서 순서대로 실행하세요:")
    print()
    print("="*70)
    
    # 1단계: 기존 view 백업 및 삭제
    print("-- 1단계: 의존하는 view 삭제 (백업용으로 먼저 조회)")
    print("""
-- view 정의 확인 (백업용)
SELECT definition 
FROM pg_views 
WHERE viewname = 'employee_customers_with_employee';

-- view 삭제
DROP VIEW IF EXISTS employee_customers_with_employee CASCADE;
""")
    
    # 2단계: 컬럼 타입 변경
    print("\n-- 2단계: 컬럼 타입 변경")
    print("""
-- 컬럼 타입을 boolean에서 varchar로 변경
ALTER TABLE employee_customers 
ALTER COLUMN loan_needed TYPE VARCHAR(255),
ALTER COLUMN parking_needed TYPE VARCHAR(255);
""")
    
    # 3단계: 기존 데이터 변환
    print("\n-- 3단계: 기존 boolean 데이터를 텍스트로 변환")
    print("""
-- boolean 값을 의미있는 텍스트로 변환
UPDATE employee_customers 
SET 
    loan_needed = CASE 
        WHEN loan_needed = 'true' THEN '필요'
        WHEN loan_needed = 'false' THEN '불필요'
        WHEN loan_needed = 't' THEN '필요'
        WHEN loan_needed = 'f' THEN '불필요'
        ELSE COALESCE(loan_needed, '미정')
    END,
    parking_needed = CASE 
        WHEN parking_needed = 'true' THEN '필요'
        WHEN parking_needed = 'false' THEN '불필요'
        WHEN parking_needed = 't' THEN '필요' 
        WHEN parking_needed = 'f' THEN '불필요'
        ELSE COALESCE(parking_needed, '미정')
    END;
""")
    
    # 4단계: View 재생성
    print("\n-- 4단계: View 재생성 (기존 정의 기반으로)")
    print("""
-- employee_customers_with_employee view 재생성
-- 주의: 기존 view 정의를 1단계에서 확인한 내용으로 대체하세요
-- 아래는 예상되는 view 정의입니다:

CREATE VIEW employee_customers_with_employee AS
SELECT 
    ec.*,
    e.name as employee_full_name,
    e.team as employee_team_info,
    e.role as employee_role_info
FROM employee_customers ec
LEFT JOIN employees e ON ec.employee_id = e.employee_id;

-- 또는 더 간단한 버전:
CREATE VIEW employee_customers_with_employee AS
SELECT * FROM employee_customers;
""")
    
    # 5단계: 변경 확인
    print("\n-- 5단계: 변경 확인")
    print("""
-- 컬럼 타입 확인
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'employee_customers' 
    AND column_name IN ('loan_needed', 'parking_needed');

-- 데이터 확인
SELECT id, customer_name, loan_needed, parking_needed 
FROM employee_customers 
LIMIT 5;

-- View 작동 확인
SELECT id, customer_name, loan_needed, parking_needed
FROM employee_customers_with_employee
LIMIT 3;
""")
    
    print("="*70)
    print()
    print("⚠️  주의사항:")
    print("1. 1단계에서 view 정의를 꼭 백업하세요")
    print("2. 4단계에서 실제 view 정의로 교체하세요")
    print("3. 각 단계를 순서대로 실행하세요")
    print("4. 오류 발생 시 즉시 중단하고 문의하세요")

def generate_safe_alternative():
    """더 안전한 대안 방법"""
    
    print("\n" + "="*70)
    print("🛡️  더 안전한 대안 방법 (새 테이블 생성)")
    print("="*70)
    
    print("""
-- 대안: 새 테이블 생성 후 데이터 이전

-- 1. 새 테이블 생성 (loan_needed, parking_needed가 VARCHAR)
CREATE TABLE employee_customers_new AS 
SELECT 
    id,
    inquiry_date,
    move_in_date,
    customer_name,
    customer_phone,
    budget,
    rooms,
    location,
    CASE 
        WHEN loan_needed = true THEN '필요'
        WHEN loan_needed = false THEN '불필요'
        ELSE '미정'
    END as loan_needed,
    CASE 
        WHEN parking_needed = true THEN '필요'
        WHEN parking_needed = false THEN '불필요'
        ELSE '미정'
    END as parking_needed,
    pets,
    memo,
    status,
    employee_id,
    employee_name,
    employee_team,
    created_date,
    unchecked_likes_residence,
    unchecked_likes_business
FROM employee_customers;

-- 2. 기존 테이블 백업
ALTER TABLE employee_customers RENAME TO employee_customers_backup;

-- 3. 새 테이블을 원래 이름으로 변경
ALTER TABLE employee_customers_new RENAME TO employee_customers;

-- 4. 인덱스 및 제약조건 재생성 (필요한 경우)
-- CREATE INDEX ... (기존 인덱스 정보에 따라)

-- 5. View 재생성
CREATE VIEW employee_customers_with_employee AS
SELECT * FROM employee_customers;

-- 6. 확인 후 백업 테이블 삭제 (신중하게!)
-- DROP TABLE employee_customers_backup;
""")

if __name__ == '__main__':
    generate_fix_sql()
    generate_safe_alternative()
    
    print("\n🎯 권장사항:")
    print("1. 먼저 '더 안전한 대안 방법'을 시도해보세요")
    print("2. 데이터가 중요한 경우 백업을 먼저 생성하세요") 
    print("3. 테스트 환경에서 먼저 실행해보세요")