# 부동산 관리 시스템 (통합 버전)

## 개요
관리자페이지, 주거용 사이트, 업무용 사이트가 하나의 앱으로 통합된 부동산 관리 시스템입니다.

## 주요 기능

### 1. 관리자/직원 시스템
- 직원 로그인 및 관리
- 고객 정보 관리 (추가/수정/삭제)
- 고객별 사이트 링크 생성

### 2. 주거용 사이트 (`/residence/*`)
- 고객별 주거 매물 관리
- 링크 평가 및 좋아요 기능
- 보증보험 관리

### 3. 업무용 사이트 (`/business/*`)
- 고객별 업무 공간 관리
- 링크 평가 및 좋아요 기능
- 보증보험 관리

## URL 구조

```
/ - 메인 페이지 (로그인)
/dashboard - 직원 대시보드
/admin - 관리자 패널

/residence - 주거용 메인 페이지
/residence/customer/<id> - 고객별 주거 사이트

/business - 업무용 메인 페이지
/business/customer/<id> - 고객별 업무 사이트
```

## API 엔드포인트

### 관리자 API
- `/api/employees` - 직원 관리
- `/api/customers` - 고객 관리

### 주거용 API
- `/api/links` - 주거용 링크 관리
- `/api/links/<id>` - 주거용 링크 수정/삭제

### 업무용 API
- `/api/office-links` - 업무용 링크 관리
- `/api/office-links/<id>` - 업무용 링크 수정/삭제

## 데이터베이스 구조

### 주요 테이블
1. `employees` - 직원 정보
2. `employee_customers` - 고객 정보
3. `links` - 주거용 링크
4. `office_links` - 업무용 링크

## 배포 (Railway)

### 환경변수 설정
```
DATABASE_URL=postgresql://...
PORT=8080
```

### 배포 명령
```bash
git add .
git commit -m "Deploy integrated app"
git push
```

## 로컬 개발

### 설치
```bash
pip install -r requirements.txt
```

### 실행
```bash
python 관리자페이지.py
```

## 주의사항
- 모든 서비스가 하나의 PostgreSQL 데이터베이스를 공유합니다
- Railway 배포 시 하나의 서비스로 운영됩니다
- 기존 주거용.py, 업무용.py 파일은 더 이상 사용하지 않습니다

---

**🎨 에르메스 감성의 프리미엄 업무공간 매물 관리 시스템**
