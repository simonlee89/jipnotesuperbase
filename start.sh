#!/bin/bash

# PORT 환경변수 설정 (기본값: 8080)
export PORT=${PORT:-8080}

# PORT 유효성 검사 (숫자만 허용)
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
	echo "❌ Error: '$PORT' is not a valid port number."
	echo "ℹ️  PORT 환경변수를 숫자로 설정하세요. 예: 8080"
	exit 1
fi

echo "🚀 서버 시작 준비 중..."
echo "🌍 환경변수 PORT: $PORT"
echo "📁 현재 디렉토리: $(pwd)"
echo "🐍 Python 버전: $(python --version)"

# 애플리케이션 실행
exec gunicorn \
	--bind 0.0.0.0:$PORT \
	--workers 1 \
	--timeout 120 \
	--keep-alive 2 \
	--max-requests 1000 \
	--max-requests-jitter 100 \
	--access-logfile - \
	--error-logfile - \
	관리자페이지:app
