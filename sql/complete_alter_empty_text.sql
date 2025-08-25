-- employee_customers 테이블의 loan_needed, parking_needed 컬럼을 VARCHAR(255)로 변경
-- 기존 데이터를 비우고 완전히 새로운 텍스트 입력 가능하도록 설정
-- cleanup_and_restart.sql 실행 후 이 스크립트를 실행하세요

-- 🔄 1단계: 의존성이 있는 뷰를 먼저 삭제
DROP VIEW IF EXISTS employee_customers_with_employee;

-- 🧹 2단계: 혹시 남아있을 수 있는 임시 컬럼들 정리
ALTER TABLE employee_customers DROP COLUMN IF EXISTS loan_needed_new;
ALTER TABLE employee_customers DROP COLUMN IF EXISTS parking_needed_new;

-- 🔄 3단계: 새로운 VARCHAR 컬럼 추가 (기본값 없음)
ALTER TABLE employee_customers 
ADD COLUMN loan_needed_new VARCHAR(255);

ALTER TABLE employee_customers 
ADD COLUMN parking_needed_new VARCHAR(255);

-- 🔄 4단계: 새 컬럼은 모두 NULL로 설정 (사용자가 직접 입력할 수 있도록)
-- 별도의 UPDATE 문 불필요 (기본적으로 NULL)

-- 🔄 5단계: 기존 boolean 컬럼 삭제
ALTER TABLE employee_customers 
DROP COLUMN loan_needed;

ALTER TABLE employee_customers 
DROP COLUMN parking_needed;

-- 🔄 6단계: 새 컬럼명을 원래 이름으로 변경
ALTER TABLE employee_customers 
RENAME COLUMN loan_needed_new TO loan_needed;

ALTER TABLE employee_customers 
RENAME COLUMN parking_needed_new TO parking_needed;

-- 🔄 7단계: employee_customers_with_employee 뷰 재생성
CREATE VIEW employee_customers_with_employee AS
SELECT 
    ec.*,
    e.name AS employee_full_name,
    e.team AS employee_team_name,
    e.role AS employee_role
FROM employee_customers ec
LEFT JOIN employees e ON ec.employee_id = e.id;

-- 🔍 8단계: 결과 확인
SELECT 
    id, 
    customer_name, 
    loan_needed, 
    parking_needed,
    employee_full_name,
    employee_team_name
FROM employee_customers_with_employee 
LIMIT 5;

-- 🔍 9단계: 변경된 컬럼 타입 확인
SELECT 
    column_name, 
    data_type, 
    character_maximum_length,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'employee_customers' 
AND column_name IN ('loan_needed', 'parking_needed')
ORDER BY column_name;
