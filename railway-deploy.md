# 🚂 Railway 배포 가이드

## 1. Railway 프로젝트 생성
1. [Railway.app](https://railway.app) 접속
2. GitHub 계정으로 로그인
3. "New Project" 클릭
4. "Deploy from GitHub repo" 선택

## 2. 환경변수 설정
Railway 대시보드 → Variables 탭에서 다음 환경변수 추가:

```bash
SUPABASE_URL=https://gkoohafmugtqwtustbrp.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdrb29oYWZtdWd0cXd0dXN0YnJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzMzUwNTMsImV4cCI6MjA3MDkxMTA1M30.nREE7LgpxGUUA__GuzryUx2t_F4mwVtto0bPTFOqEFk
FLASK_ENV=production
```

## 3. 배포 설정
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn 관리자페이지:app --bind 0.0.0.0:$PORT`

## 4. 도메인 설정
- Railway에서 제공하는 기본 도메인 사용
- 또는 커스텀 도메인 연결 가능

## 5. 배포 후 확인
- 로그 확인
- 애플리케이션 접속 테스트
- Supabase 연결 상태 확인
