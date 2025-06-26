-- 1. employees 테이블 수정: department를 team으로 변경하고 status 필드 추가
ALTER TABLE employees RENAME COLUMN department TO team;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';

-- 2. customer_info 테이블 삭제
DROP TABLE IF EXISTS customer_info CASCADE;

-- 3. links 테이블에서 residence_extra 필드 제거
ALTER TABLE links DROP COLUMN IF EXISTS residence_extra;

-- 4. 기존 데이터 정리 (선택사항)
-- 30일 이상된 보증보험 항목을 guarantee_insurance = FALSE로 변경
UPDATE links 
SET guarantee_insurance = FALSE 
WHERE guarantee_insurance = TRUE 
AND date_added < CURRENT_DATE - INTERVAL '30 days';

-- 5. 인덱스 추가 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_links_guarantee_date ON links(guarantee_insurance, date_added);
CREATE INDEX IF NOT EXISTS idx_employee_customers_management_site ON employee_customers(management_site_id);
CREATE INDEX IF NOT EXISTS idx_employees_status ON employees(status);

-- 변경사항 확인
SELECT 
    'employees 테이블 구조:' as info,
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'employees'
ORDER BY ordinal_position;

-- customer_info 테이블 삭제 확인
SELECT 
    'customer_info 테이블 존재 여부:' as info,
    COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_name = 'customer_info';

-- links 테이블의 residence_extra 필드 제거 확인
SELECT 
    'links 테이블에 residence_extra 필드 존재 여부:' as info,
    COUNT(*) as column_count
FROM information_schema.columns 
WHERE table_name = 'links' AND column_name = 'residence_extra';

-- 6. links와 office_links 테이블에 is_checked 필드 추가 (없는 경우)
ALTER TABLE links ADD COLUMN IF NOT EXISTS is_checked BOOLEAN DEFAULT TRUE;
ALTER TABLE office_links ADD COLUMN IF NOT EXISTS is_checked BOOLEAN DEFAULT TRUE;

-- 기존 좋아요 데이터의 is_checked 값 업데이트
-- 이미 좋아요가 눌린 항목들은 확인된 것으로 처리
UPDATE links SET is_checked = TRUE WHERE liked = TRUE AND is_checked IS NULL;
UPDATE office_links SET is_checked = TRUE WHERE liked = TRUE AND is_checked IS NULL;

-- is_checked 필드 확인
SELECT 
    'links 테이블 is_checked 필드:' as info,
    column_name, 
    data_type, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'links' AND column_name = 'is_checked';

SELECT 
    'office_links 테이블 is_checked 필드:' as info,
    column_name, 
    data_type, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'office_links' AND column_name = 'is_checked'; 