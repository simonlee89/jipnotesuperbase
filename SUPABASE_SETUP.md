# Supabase 설정 가이드

## 1. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# Supabase 설정
SUPABASE_URL=https://gkoohafmugtqwtustbrp.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdrb29oYWZtdWd0cXd0dXN0YnJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzMzUwNTMsImV4cCI6MjA3MDkxMTA1M30.nREE7LgpxGUUA__GuzryUx2t_F4mwVtto0bPTFOqEFk

# 사이트 URL 설정
RESIDENCE_SITE_URL=http://localhost:5000
BUSINESS_SITE_URL=http://localhost:5001

# Flask 설정
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

## 2. Supabase 테이블 생성

1. [Supabase 대시보드](https://supabase.com/dashboard)에 로그인
2. 프로젝트 `gkoohafmugtqwtustbrp` 선택
3. SQL 편집기에서 `create_supabase_tables.sql` 파일의 내용을 실행

## 3. 의존성 설치

```bash
pip install -r requirements.txt
```

## 4. 애플리케이션 실행

```bash
python 관리자페이지.py
```

## 5. 테스트 계정

기본 테스트 계정들이 자동으로 생성됩니다:
- **원형** / 1 (관리자)
- **테스트** / 1 (관리자)
- **admin** / 1 (관리자)
- **관리자** / 1 (관리자)
- **수정** / 1 (팀장)

## 6. 주요 변경사항

- ✅ PostgreSQL → Supabase로 변경
- ✅ `db_utils.py` → `supabase_utils.py`로 변경
- ✅ 환경변수 기반 설정
- ✅ 자동 테이블 생성 및 샘플 데이터
- ✅ RLS (Row Level Security) 설정
- ✅ 에러 처리 및 폴백 시스템

## 7. 문제 해결

### 연결 오류가 발생하는 경우:
1. `.env` 파일이 올바르게 설정되었는지 확인
2. Supabase 프로젝트가 활성 상태인지 확인
3. API 키가 올바른지 확인

### 테이블이 보이지 않는 경우:
1. SQL 편집기에서 `create_supabase_tables.sql` 실행
2. RLS 정책이 올바르게 설정되었는지 확인
