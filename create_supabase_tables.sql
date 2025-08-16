-- Supabase 테이블 생성 스크립트
-- 이 스크립트를 Supabase SQL 편집기에서 실행하세요

-- 1. 직원 테이블
CREATE TABLE IF NOT EXISTS employees (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    email VARCHAR(200) NOT NULL DEFAULT '',
    password VARCHAR(255) NOT NULL DEFAULT '1',
    team VARCHAR(100) NOT NULL DEFAULT '',
    position VARCHAR(100) NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    role VARCHAR(50) NOT NULL DEFAULT 'employee',
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

-- 2. 직원 고객 테이블 (상세 구조)
CREATE TABLE IF NOT EXISTS employee_customers (
    id BIGSERIAL PRIMARY KEY,
    inquiry_date DATE NOT NULL DEFAULT CURRENT_DATE,
    customer_name VARCHAR(200) NOT NULL,
    customer_phone VARCHAR(50),
    budget INTEGER, -- 예산 (만원 단위)
    rooms VARCHAR(50), -- 방 개수 (1룸, 2룸, 3룸)
    location VARCHAR(100), -- 희망 지역 (강남구, 서초구 등)
    loan_needed BOOLEAN DEFAULT FALSE, -- 대출 필요 여부
    parking_needed BOOLEAN DEFAULT FALSE, -- 주차 필요 여부
    pets VARCHAR(20) DEFAULT '불가', -- 펫 가능 여부 (가능, 불가)
    memo TEXT, -- 메모/특이사항
    status VARCHAR(50) DEFAULT '상담중', -- 진행상태 (상담중, 계약완료, 보류)
    employee_id BIGINT REFERENCES employees(id) ON DELETE CASCADE,
    employee_name VARCHAR(200),
    employee_team VARCHAR(100),
    management_site_id VARCHAR(100) UNIQUE, -- 고객별 사이트 ID
    unchecked_likes_residence INTEGER DEFAULT 0, -- 주거용 미확인 좋아요
    unchecked_likes_business INTEGER DEFAULT 0, -- 업무용 미확인 좋아요
    created_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 메이플 아파트 매물 테이블 (핵심!)
CREATE TABLE IF NOT EXISTS maeiple_properties (
    id BIGSERIAL PRIMARY KEY,
    check_date DATE NOT NULL DEFAULT CURRENT_DATE,
    building_number VARCHAR(50) NOT NULL, -- 동
    room_number VARCHAR(50) NOT NULL, -- 호수
    status VARCHAR(50) DEFAULT '거래중', -- 현황 (거래중, 거래완료)
    jeonse_price INTEGER, -- 전세가 (만원 단위)
    monthly_rent INTEGER, -- 월세 (만원 단위)
    sale_price INTEGER, -- 매매가 (만원 단위)
    is_occupied BOOLEAN DEFAULT FALSE, -- 실거주 여부
    phone VARCHAR(50), -- 전화번호
    memo TEXT, -- 특이사항
    likes INTEGER DEFAULT 0 CHECK (likes >= 0 AND likes <= 5), -- 좋아요 (0-5)
    dislikes INTEGER DEFAULT 0 CHECK (dislikes >= 0 AND dislikes <= 5), -- 싫어요 (0-5)
    employee_id BIGINT REFERENCES employees(id) ON DELETE CASCADE,
    employee_name VARCHAR(200),
    employee_team VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 주거용 링크 테이블
CREATE TABLE IF NOT EXISTS residence_links (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 업무용 링크 테이블
CREATE TABLE IF NOT EXISTS office_links (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    is_checked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. 매이플 작업 테이블
CREATE TABLE IF NOT EXISTS maeiple_tasks (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    assigned_to VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_employee_customers_employee_id ON employee_customers(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_customers_team ON employee_customers(employee_team);
CREATE INDEX IF NOT EXISTS idx_employee_customers_inquiry_date ON employee_customers(inquiry_date);
CREATE INDEX IF NOT EXISTS idx_maeiple_properties_employee_id ON maeiple_properties(employee_id);
CREATE INDEX IF NOT EXISTS idx_maeiple_properties_team ON maeiple_properties(employee_team);
CREATE INDEX IF NOT EXISTS idx_maeiple_properties_check_date ON maeiple_properties(check_date);
CREATE INDEX IF NOT EXISTS idx_maeiple_properties_building_room ON maeiple_properties(building_number, room_number);

-- 기본 데이터 삽입
INSERT INTO employees (name, email, password, team, position, role) VALUES
('원형', 'wonhyeong@example.com', '1', '관리자', '관리자', 'employee'),
('테스트', 'test@example.com', '1', '관리자', '테스터', 'employee'),
('admin', 'admin@example.com', '1', '관리자', '시스템관리자', 'employee'),
('관리자', 'manager@example.com', '1', '관리자', '매니저', 'employee'),
('수정', 'sujung@example.com', '1', '위플러스', '팀장', '팀장')
ON CONFLICT (name) DO NOTHING;

-- 샘플 고객 데이터
INSERT INTO employee_customers (customer_name, customer_phone, budget, rooms, location, loan_needed, parking_needed, pets, memo, status, employee_id, employee_name, employee_team, management_site_id) VALUES
('김철수', '010-1234-5678', 5000, '2룸', '강남구', TRUE, TRUE, '불가', '급하게 구하고 있음', '상담중', 1, '원형', '관리자', 'kim-chulsoo-001'),
('이영희', '010-9876-5432', 3000, '1룸', '서초구', FALSE, FALSE, '가능', '펫 가능한 곳 선호', '계약완료', 1, '원형', '관리자', 'lee-younghee-002')
ON CONFLICT DO NOTHING;

-- 샘플 메이플 매물 데이터
INSERT INTO maeiple_properties (check_date, building_number, room_number, status, jeonse_price, monthly_rent, sale_price, is_occupied, phone, memo, employee_id, employee_name, employee_team) VALUES
('2024-08-15', '101', '101', '거래중', 5000, NULL, NULL, FALSE, '010-1111-1111', '강남역 근처, 교통편리', 1, '원형', '관리자'),
('2024-08-14', '101', '102', '거래완료', NULL, 50, NULL, TRUE, '010-2222-2222', '월세 거래 완료', 1, '원형', '관리자'),
('2024-08-13', '102', '201', '거래중', NULL, NULL, 80000, FALSE, '010-3333-3333', '매매 희망', 1, '원형', '관리자')
ON CONFLICT DO NOTHING;

-- 샘플 링크 데이터
INSERT INTO residence_links (title, url, description) VALUES
('네이버', 'https://www.naver.com', '주요 검색 엔진'),
('구글', 'https://www.google.com', '글로벌 검색 엔진')
ON CONFLICT DO NOTHING;

INSERT INTO office_links (title, url, description) VALUES
('회사 홈페이지', 'https://company.com', '회사 공식 웹사이트'),
('업무 시스템', 'https://work.company.com', '업무용 시스템')
ON CONFLICT DO NOTHING;

-- 샘플 매이플 작업 데이터
INSERT INTO maeiple_tasks (title, description, assigned_to, priority, status) VALUES
('강남구 매물 현장 확인', '강남역 근처 신축 아파트 현장 확인 필요', '원형', 'high', 'pending'),
('서초구 계약 진행', '서초구 월세 계약 진행 상황 점검', '수정', 'medium', 'in_progress')
ON CONFLICT DO NOTHING;

-- RLS (Row Level Security) 설정
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE maeiple_properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE residence_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE office_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE maeiple_tasks ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기 가능하도록 정책 설정
CREATE POLICY "Allow public read access" ON employees FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON employee_customers FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON maeiple_properties FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON residence_links FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON office_links FOR SELECT USING (true);
CREATE POLICY "Allow public read access" ON maeiple_tasks FOR SELECT USING (true);

-- 인증된 사용자가 쓰기 가능하도록 정책 설정
CREATE POLICY "Allow authenticated insert" ON employees FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow authenticated insert" ON employee_customers FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow authenticated insert" ON maeiple_properties FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow authenticated insert" ON residence_links FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow authenticated insert" ON office_links FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow authenticated insert" ON maeiple_tasks FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow authenticated update" ON employees FOR UPDATE USING (true);
CREATE POLICY "Allow authenticated update" ON employee_customers FOR UPDATE USING (true);
CREATE POLICY "Allow authenticated update" ON maeiple_properties FOR UPDATE USING (true);
CREATE POLICY "Allow authenticated update" ON residence_links FOR UPDATE USING (true);
CREATE POLICY "Allow authenticated update" ON office_links FOR UPDATE USING (true);
CREATE POLICY "Allow authenticated update" ON maeiple_tasks FOR UPDATE USING (true);

CREATE POLICY "Allow authenticated delete" ON employees FOR DELETE USING (true);
CREATE POLICY "Allow authenticated delete" ON employee_customers FOR DELETE USING (true);
CREATE POLICY "Allow authenticated delete" ON maeiple_properties FOR DELETE USING (true);
CREATE POLICY "Allow authenticated delete" ON residence_links FOR DELETE USING (true);
CREATE POLICY "Allow authenticated delete" ON office_links FOR DELETE USING (true);
CREATE POLICY "Allow authenticated delete" ON maeiple_tasks FOR DELETE USING (true);

-- 뷰 생성 (자주 사용되는 조인 쿼리를 위한 뷰)
CREATE OR REPLACE VIEW employee_customers_with_employee AS
SELECT 
    ec.*,
    e.name as employee_full_name,
    e.team as employee_team_name,
    e.role as employee_role
FROM employee_customers ec
LEFT JOIN employees e ON ec.employee_id = e.id;

CREATE OR REPLACE VIEW maeiple_properties_with_employee AS
SELECT 
    mp.*,
    e.name as employee_full_name,
    e.team as employee_team_name,
    e.role as employee_role
FROM maeiple_properties mp
LEFT JOIN employees e ON mp.employee_id = e.id;

-- 함수 생성 (자동 업데이트 시간 설정)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성 (updated_at 자동 업데이트)
CREATE TRIGGER update_employee_customers_updated_at BEFORE UPDATE ON employee_customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_maeiple_properties_updated_at BEFORE UPDATE ON maeiple_properties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_residence_links_updated_at BEFORE UPDATE ON residence_links
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_office_links_updated_at BEFORE UPDATE ON office_links
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_maeiple_tasks_updated_at BEFORE UPDATE ON maeiple_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 완료 메시지
SELECT '✅ 모든 테이블과 데이터가 성공적으로 생성되었습니다!' as message;
