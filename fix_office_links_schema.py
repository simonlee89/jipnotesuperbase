#!/usr/bin/env python3
"""
office_links 테이블에 is_checked 컬럼을 추가하는 스크립트
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def fix_office_links_schema():
    """office_links 테이블에 is_checked 컬럼 추가"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다")
        return False
    
    try:
        print("🔄 PostgreSQL 연결 중...")
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # office_links 테이블에 is_checked 컬럼이 있는지 확인
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'office_links' 
            AND column_name = 'is_checked'
        """)
        
        if cursor.fetchone():
            print("✅ office_links 테이블에 is_checked 컬럼이 이미 존재합니다")
        else:
            print("🔧 office_links 테이블에 is_checked 컬럼 추가 중...")
            cursor.execute('ALTER TABLE office_links ADD COLUMN is_checked BOOLEAN DEFAULT FALSE')
            conn.commit()
            print("✅ is_checked 컬럼 추가 완료")
        
        # 기존 좋아요 데이터의 is_checked 값 업데이트
        print("🔄 기존 좋아요 데이터 업데이트 중...")
        cursor.execute('UPDATE office_links SET is_checked = TRUE WHERE liked = TRUE AND is_checked IS NULL')
        updated_rows = cursor.rowcount
        conn.commit()
        print(f"✅ {updated_rows}개 행 업데이트 완료")
        
        # 확인
        cursor.execute('SELECT COUNT(*) FROM office_links WHERE is_checked IS NOT NULL')
        total_rows = cursor.fetchone()[0]
        print(f"📊 office_links 테이블 총 {total_rows}개 행에 is_checked 값 설정됨")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("=== office_links 테이블 스키마 수정 ===")
    success = fix_office_links_schema()
    if success:
        print("🎉 스키마 수정 완료!")
    else:
        print("💥 스키마 수정 실패!") 