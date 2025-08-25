-- 기존 시도에서 생성된 컬럼들을 정리하고 다시 시작
-- Supabase SQL Editor에서 실행하세요

-- 🔍 1단계: 현재 테이블 구조 확인
SELECT 
    column_name, 
    data_type, 
    character_maximum_length,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'employee_customers' 
AND column_name LIKE '%loan_needed%' OR column_name LIKE '%parking_needed%'
ORDER BY column_name;

-- 🧹 2단계: 기존에 생성된 임시 컬럼들 정리 (존재하는 경우에만)
ALTER TABLE employee_customers DROP COLUMN IF EXISTS loan_needed_new;
ALTER TABLE employee_customers DROP COLUMN IF EXISTS parking_needed_new;

-- 🔍 3단계: 정리 후 상태 확인
SELECT 
    column_name, 
    data_type, 
    character_maximum_length,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'employee_customers' 
AND (column_name LIKE '%loan_needed%' OR column_name LIKE '%parking_needed%')
ORDER BY column_name;
