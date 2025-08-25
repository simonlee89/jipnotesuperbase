#!/usr/bin/env python3
"""
로컬 개발 서버 실행 스크립트
환경변수는 .env 파일에서 자동으로 로드됩니다.
"""

import os
import sys
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경변수 검증
required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'ADMIN_ID', 'ADMIN_PASSWORD']
missing_vars = [var for var in required_vars if not os.environ.get(var)]

if missing_vars:
    print("❌ 오류: 필수 환경변수가 설정되지 않았습니다:")
    for var in missing_vars:
        print(f"  - {var}")
    print("\n.env 파일을 확인하거나 .env.example을 참고하여 생성하세요.")
    sys.exit(1)

# 플라스크 환경 설정
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = 'True'

# src 디렉토리를 Python 경로에 추가
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print("🚀 로컬 개발 서버를 시작합니다...")
print(f"📁 작업 디렉토리: {os.getcwd()}")
print(f"🔑 환경변수 로드 완료")

# 관리자페이지 모듈 임포트 및 실행
try:
    from 관리자페이지 import app
    app.run(debug=True, host='0.0.0.0', port=5000)
except ImportError as e:
    print(f"❌ 모듈 임포트 오류: {e}")
    print("src/관리자페이지.py 파일이 존재하는지 확인하세요.")
    sys.exit(1)