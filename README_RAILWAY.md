# Railway 배포 가이드

## 배포 준비 완료 ✅

이 프로젝트는 Railway 배포를 위해 완전히 구성되어 있습니다.

## 빠른 배포 단계

### 1. Railway 프로젝트 설정
1. [Railway](https://railway.app) 대시보드로 이동
2. GitHub 저장소 연결: `simonlee89/jipnotesuperbase`
3. 자동으로 배포가 시작됩니다

### 2. 환경변수 설정 (필수!)

Railway 대시보드 → Variables 탭에서 다음 환경변수를 추가하세요:

```bash
# 필수 환경변수
SUPABASE_URL=https://gkoohafmugtqwtustbrp.supabase.co
SUPABASE_KEY=your_supabase_key_here
ADMIN_ID=admin
ADMIN_PASSWORD=your_admin_password
FLASK_SECRET_KEY=your-secret-key-change-in-production

# 선택 환경변수
RESIDENCE_SITE_URL=https://xn--2e0b220bo4n.com
BUSINESS_SITE_URL=https://xn--bx78aevc.com
```

### 3. 배포 확인
- Railway가 자동으로 Python 앱을 감지하고 배포합니다
- 배포 로그에서 오류가 없는지 확인하세요
- 제공된 URL로 접속하여 앱이 정상 작동하는지 확인하세요

## 프로젝트 구조

```
├── src/
│   ├── 관리자페이지.py      # 메인 Flask 애플리케이션
│   └── supabase_utils.py    # 데이터베이스 유틸리티
├── templates/               # HTML 템플릿
├── requirements.txt         # Python 패키지 의존성
├── runtime.txt             # Python 버전 (3.11.0)
├── Procfile                # Railway 시작 명령
├── railway.json            # Railway 설정
└── .env.example            # 환경변수 예시
```

## 기술 스택

- **Framework**: Flask 2.3.3
- **Database**: Supabase
- **Server**: Gunicorn
- **Python**: 3.11.0
- **Deployment**: Railway (Nixpacks)

## 주요 기능

- 관리자 대시보드
- 팀장 대시보드
- 직원 대시보드
- 매물 관리 (메이플관리)
- 보증보험 조회
- 고객 정보 관리

## 문제 해결

### 배포 실패 시
1. 환경변수가 모두 설정되었는지 확인
2. Railway 로그에서 상세 오류 메시지 확인
3. Python 버전이 3.11.0인지 확인

### 모듈 임포트 오류
- `PYTHONPATH`가 railway.json에 올바르게 설정되어 있음
- src 디렉토리의 모든 Python 파일이 정상적으로 임포트됨

### 데이터베이스 연결 오류
- `SUPABASE_URL`과 `SUPABASE_KEY`가 올바른지 확인
- Supabase 프로젝트가 활성화되어 있는지 확인

## 로컬 개발

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일 편집하여 실제 값 입력

# 실행
python src/관리자페이지.py
```

## 보안 주의사항

- `.env` 파일은 절대 커밋하지 마세요
- `FLASK_SECRET_KEY`는 프로덕션에서 반드시 변경하세요
- 관리자 비밀번호는 강력한 비밀번호로 설정하세요
- Supabase API 키는 안전하게 관리하세요

## 지원

문제가 있으시면 GitHub Issues에 문의해주세요.