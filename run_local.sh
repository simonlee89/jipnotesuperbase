#!/bin/bash

echo "================================="
echo "   로컬 개발 서버 시작"
echo "================================="
echo ""

# .env 파일 확인
if [ ! -f .env ]; then
    echo "[오류] .env 파일이 없습니다!"
    echo ".env.example을 참고하여 .env 파일을 생성하세요."
    exit 1
fi

echo "[정보] .env 파일에서 환경변수를 로드합니다..."

# Python 실행
python3 run_local.py || python run_local.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[오류] 서버 실행 중 오류가 발생했습니다."
    exit 1
fi