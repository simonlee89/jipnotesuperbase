#!/usr/bin/env python3
"""
로컬 실행용 스크립트
환경변수를 직접 설정하여 Supabase 연결 문제를 해결합니다.
"""

import os
import sys

# 환경변수 설정
os.environ['SUPABASE_URL'] = 'https://gkoohafmugtqwtustbrp.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdrb29oYWZtdWd0cXd0dXN0YnJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUzMzUwNTMsImV4cCI6MjA3MDkxMTA1M30.nREE7LgpxGUUA__GuzryUx2t_F4mwVtto0bPTFOqEFk'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = 'True'

# 관리자페이지 모듈 import
from 관리자페이지 import app

if __name__ == '__main__':
    print("로컬 서버 시작")
    print("접속 주소: http://localhost:5000")
    print("테스트 계정:")
    print("   - 관리자: admin / ejxkqdnjs1emd")
    print("   - 직원: 원형 / 1")
    print("   - 팀장: 수정 / 1")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"서버 시작 실패: {e}")
        # 포트 5000이 사용 중인 경우 다른 포트 시도
        try:
            print("포트 5001로 시도합니다...")
            app.run(host='0.0.0.0', port=5001, debug=True)
        except Exception as e2:
            print(f"포트 5001도 실패: {e2}")
            print("다른 포트를 사용하거나 실행 중인 프로세스를 종료해주세요.")
