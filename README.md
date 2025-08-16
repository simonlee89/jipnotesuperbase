# 🏠 집노트 - Supabase 기반 부동산 관리 시스템

## 📋 프로젝트 개요

집노트는 부동산 중개업체를 위한 종합 관리 시스템입니다. 직원 관리, 고객 관리, 매물 관리, 작업 관리 등의 기능을 제공합니다.

## 🚀 주요 기능

### 👥 직원 관리
- 직원 등록/수정/삭제
- 팀별 직원 관리
- 역할 기반 권한 관리
- 로그인 기록 관리

### 🏘️ 고객 관리
- 고객 정보 등록/수정/삭제
- 고객별 매물 선호도 관리
- 상담 기록 관리
- 계약 상태 추적

### 🏢 매물 관리 (메이플)
- 매물 정보 등록/수정/삭제
- 건물별/호수별 매물 관리
- 거래 상태 관리 (전세/월세/매매)
- 좋아요/싫어요 기능

### 📋 작업 관리
- 작업 할당 및 진행 상황 추적
- 우선순위 및 상태 관리
- 담당자별 작업 분배

### 🔗 링크 관리
- 주거용 링크 관리
- 업무용 링크 관리
- 카테고리별 링크 정리

## 🛠️ 기술 스택

- **Backend**: Python Flask
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Railway
- **Authentication**: Supabase Auth

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/simonlee89/jipnotesuperbase.git
cd jipnotesuperbase
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정
`.env` 파일 생성 또는 환경변수 설정:
```bash
SUPABASE_URL=https://gkoohafmugtqwtustbrp.supabase.co
SUPABASE_KEY=your_supabase_key_here
```

### 4. 애플리케이션 실행
```bash
python 관리자페이지.py
```

## 🌐 접속 정보

- **메인 페이지**: http://localhost:8080
- **관리자 패널**: http://localhost:8080/admin
- **직원 대시보드**: http://localhost:8080/dashboard
- **팀장 패널**: http://localhost:8080/team-leader

## 🔐 기본 계정

### 관리자 계정
- **ID**: `admin`
- **비밀번호**: `ejxkqdnjs1emd`

### 테스트 직원 계정
- **원형** / `1` (관리자)
- **테스트** / `1` (관리자)
- **수정** / `1` (팀장)

## 🚂 Railway 배포

### 1. Railway 프로젝트 생성
1. [Railway.app](https://railway.app) 접속
2. GitHub 계정으로 로그인
3. "New Project" → "Deploy from GitHub repo" 선택

### 2. 환경변수 설정
```bash
SUPABASE_URL=https://gkoohafmugtqwtustbrp.supabase.co
SUPABASE_KEY=your_supabase_key_here
FLASK_ENV=production
```

### 3. 배포 설정
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn 관리자페이지:app --bind 0.0.0.0:$PORT`

## 📊 데이터베이스 구조

### 주요 테이블
- `employees`: 직원 정보
- `employee_customers`: 고객 정보
- `maeiple_properties`: 매물 정보
- `maeiple_tasks`: 작업 정보
- `residence_links`: 주거용 링크
- `office_links`: 업무용 링크

## 🔧 개발 환경

- **Python**: 3.11.0
- **Flask**: 2.3.3
- **Supabase**: 2.0.2
- **Gunicorn**: 21.2.0

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 GitHub Issues를 통해 연락해주세요.
