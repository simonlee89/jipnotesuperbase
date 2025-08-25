-- Supabase에서 loan_needed, parking_needed 컬럼을 boolean에서 text로 변경
-- 주의: 기존 데이터가 있다면 백업을 먼저 하세요!

-- 1. employee_customers 테이블에서 컬럼 타입 변경
ALTER TABLE employee_customers 
ALTER COLUMN loan_needed TYPE TEXT,
ALTER COLUMN parking_needed TYPE TEXT;

-- 2. 기존 boolean 데이터를 텍스트로 변환 (선택사항)
-- True -> '필요', False -> '불필요' 또는 NULL로 변환
UPDATE employee_customers 
SET 
    loan_needed = CASE 
        WHEN loan_needed::boolean = true THEN '필요'
        WHEN loan_needed::boolean = false THEN '불필요'
        ELSE NULL
    END,
    parking_needed = CASE 
        WHEN parking_needed::boolean = true THEN '필요'
        WHEN parking_needed::boolean = false THEN '불필요'  
        ELSE NULL
    END
WHERE loan_needed IS NOT NULL OR parking_needed IS NOT NULL;

-- 3. 확인 쿼리
SELECT 
    id, customer_name, loan_needed, parking_needed
FROM employee_customers 
WHERE loan_needed IS NOT NULL OR parking_needed IS NOT NULL
LIMIT 5;