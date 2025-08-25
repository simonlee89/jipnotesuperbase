-- residence_links 테이블에 컬럼 추가
ALTER TABLE residence_links 
ADD COLUMN platform text,
ADD COLUMN added_by text,
ADD COLUMN date_added date,
ADD COLUMN memo text,
ADD COLUMN guarantee_insurance boolean DEFAULT false,
ADD COLUMN liked boolean DEFAULT false,
ADD COLUMN disliked boolean DEFAULT false,
ADD COLUMN is_checked boolean DEFAULT false,
ADD COLUMN rating integer DEFAULT 5,
ADD COLUMN management_site_id text;

-- office_links 테이블에 컬럼 추가
ALTER TABLE office_links 
ADD COLUMN platform text,
ADD COLUMN added_by text,
ADD COLUMN date_added date,
ADD COLUMN memo text,
ADD COLUMN guarantee_insurance boolean DEFAULT false,
ADD COLUMN liked boolean DEFAULT false,
ADD COLUMN disliked boolean DEFAULT false,
ADD COLUMN rating integer DEFAULT 5,
ADD COLUMN management_site_id text;

-- guarantee_list 테이블 생성 (선택사항)
CREATE TABLE guarantee_list (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title text,
    url text,
    description text,
    platform text,
    added_by text,
    date_added date,
    memo text,
    guarantee_insurance boolean DEFAULT true,
    liked boolean DEFAULT false,
    disliked boolean DEFAULT false,
    is_checked boolean DEFAULT false,
    management_site_id text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- links 테이블 생성 (주거용 통합 테이블, 선택사항)
CREATE TABLE links (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title text,
    url text,
    description text,
    platform text,
    added_by text,
    date_added date,
    memo text,
    guarantee_insurance boolean DEFAULT false,
    liked boolean DEFAULT false,
    disliked boolean DEFAULT false,
    is_checked boolean DEFAULT false,
    rating integer DEFAULT 5,
    management_site_id text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
