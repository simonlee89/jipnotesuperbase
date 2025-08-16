# 집노트 관리자 시스템

## 🚀 개요

이 프로젝트는 직원 관리, 고객 관리, 링크 관리, 매이플 작업 관리를 위한 통합 관리자 시스템입니다.

## 🗄️ 데이터베이스

**Supabase**를 사용하여 데이터를 관리합니다.

### 주요 테이블
- `employees`: 직원 정보
- `employee_customers`: 직원별 고객 정보
- `residence_links`: 주거용 링크
- `office_links`: 업무용 링크
- `maeiple_tasks`: 매이플 작업 관리

## 🛠️ 기술 스택

- **Backend**: Flask (Python)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Deployment**: Railway

## 📋 기능

### 👥 직원 관리
- 직원 등록/수정/삭제
- 팀별 직원 관리
- 역할 기반 접근 제어 (직원/팀장/관리자)

### 🏠 주거용 서비스
- 주거 관련 링크 관리
- 고객 정보 관리

### 💼 업무용 서비스
- 업무 관련 링크 관리
- 작업 상태 추적

### 📊 매이플 관리
- 작업 할당 및 추적
- 우선순위 및 상태 관리

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
`.env` 파일을 생성하고 Supabase 설정을 추가하세요:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. Supabase 테이블 생성
`create_supabase_tables.sql` 파일을 Supabase SQL 편집기에서 실행하세요.

### 4. 애플리케이션 실행
```bash
python 관리자페이지.py
```

## 🔐 기본 계정

- **원형** / 1 (관리자)
- **테스트** / 1 (관리자)
- **admin** / 1 (관리자)
- **관리자** / 1 (관리자)
- **수정** / 1 (팀장)

## 📁 프로젝트 구조

```
├── 관리자페이지.py          # 메인 Flask 애플리케이션
├── supabase_utils.py        # Supabase 데이터베이스 유틸리티
├── create_supabase_tables.sql # 테이블 생성 스크립트
├── requirements.txt          # Python 의존성
├── templates/                # HTML 템플릿
│   ├── admin_main.html      # 메인 페이지
│   ├── admin_panel.html     # 관리자 패널
│   ├── employee_dashboard.html # 직원 대시보드
│   └── ...
└── docs/                     # 문서
    ├── 매이플관리_작업지시서.md
    └── 팀장페이지_기능정리.md
```

## 🔧 개발 모드

개발 중에는 `FORCE_TEST_MODE = True`로 설정되어 있어 데이터베이스 연결 없이도 테스트할 수 있습니다.

## 📚 추가 문서

- [Supabase 설정 가이드](SUPABASE_SETUP.md)
- [매이플 관리 작업지시서](docs/매이플관리_작업지시서.md)
- [팀장페이지 기능정리](docs/팀장페이지_기능정리.md)

## 🤝 기여

이 프로젝트에 기여하고 싶으시다면:
1. 이슈를 생성하여 개선사항을 제안
2. 풀 리퀘스트를 통해 코드 개선 제안
3. 문서 개선 및 번역 제안

## 📄 라이선스

이 프로젝트는 내부 사용을 위한 프로젝트입니다.
