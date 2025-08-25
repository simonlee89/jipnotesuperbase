-- employee_customers 테이블의 loan_needed, parking_needed 컬럼 스키마 조회
-- Supabase SQL Editor에서 실행하세요

-- 1. 컬럼 정보 확인
SELECT 
    column_name AS "컬럼명", 
    data_type AS "데이터타입", 
    character_maximum_length AS "최대길이",
    is_nullable AS "NULL허용",
    column_default AS "기본값"
FROM information_schema.columns 
WHERE table_name = 'employee_customers' 
AND column_name IN ('loan_needed', 'parking_needed')
ORDER BY column_name;

-- 2. 현재 데이터 샘플 확인
SELECT 
    id,
    customer_name,
    loan_needed,
    parking_needed,
    created_date
FROM employee_customers 
ORDER BY id DESC 
LIMIT 10;

-- 3. false 값이 있는 레코드 개수 확인
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN loan_needed = 'false' THEN 1 END) as loan_false_count,
    COUNT(CASE WHEN parking_needed = 'false' THEN 1 END) as parking_false_count,
    COUNT(CASE WHEN loan_needed IS NULL THEN 1 END) as loan_null_count,
    COUNT(CASE WHEN parking_needed IS NULL THEN 1 END) as parking_null_count
FROM employee_customers;

-- 4. 최근 추가된 데이터의 상태 확인 (NULL vs false 비교)
SELECT 
    id,
    customer_name,
    loan_needed,
    parking_needed,
    created_date,
    CASE 
        WHEN loan_needed = 'false' THEN 'OLD_FALSE'
        WHEN loan_needed IS NULL THEN 'NEW_NULL'
        ELSE loan_needed
    END as loan_status,
    CASE 
        WHEN parking_needed = 'false' THEN 'OLD_FALSE'
        WHEN parking_needed IS NULL THEN 'NEW_NULL'
        ELSE parking_needed
    END as parking_status
FROM employee_customers 
ORDER BY id DESC 
LIMIT 20;