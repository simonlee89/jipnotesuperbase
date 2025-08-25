@echo off
echo 🚀 집노트 로컬 서버 시작
echo.
echo 📦 의존성 설치 확인 중...
pip install -r requirements.txt
echo.
echo 🌍 환경변수 설정 중...
set SUPABASE_URL=https://gkoohafmugtqwtustbrp.supabase.co
set SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdrb29oYWZtdWd0cXd0dXN0YnJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzMzUwNTMsImV4cCI6MjA3MDkxMTA1M30.nREE7LgpxGUUA__GuzryUx2t_F4mwVtto0bPTFOqEFk
set FLASK_ENV=development
set FLASK_DEBUG=True
echo.
echo 🔑 테스트 계정 정보:
echo    - 관리자: admin / ejxkqdnjs1emd
echo    - 직원: 원형 / 1
echo    - 팀장: 수정 / 1
echo.
echo 📱 접속 주소: http://localhost:5000
echo.
echo ========================================
echo.
python run_local.py
pause
