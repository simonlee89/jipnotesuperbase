@echo off
echo =================================
echo   로컬 개발 서버 시작
echo =================================
echo.

REM .env 파일 확인
if not exist .env (
    echo [오류] .env 파일이 없습니다!
    echo .env.example을 참고하여 .env 파일을 생성하세요.
    pause
    exit /b 1
)

echo [정보] .env 파일에서 환경변수를 로드합니다...

REM Python 실행
python run_local.py

if errorlevel 1 (
    echo.
    echo [오류] 서버 실행 중 오류가 발생했습니다.
    pause
)