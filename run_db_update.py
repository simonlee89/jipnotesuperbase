#!/usr/bin/env python3
"""
Railway에서 실행할 데이터베이스 업데이트 스크립트
"""

import os
import sys
from db_utils import get_db_connection

def main():
    print("🚀 PostgreSQL 데이터베이스 스키마 업데이트 시작...")
    
    try:
        # 데이터베이스 연결
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        print("✅ 데이터베이스 연결 성공")
        
        # SQL 명령어들
        sql_commands = [
            "ALTER TABLE employees RENAME COLUMN department TO team;",
            "ALTER TABLE employees ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';",
            "DROP TABLE IF EXISTS customer_info CASCADE;",
            "ALTER TABLE links DROP COLUMN IF EXISTS residence_extra;",
            "UPDATE links SET guarantee_insurance = FALSE WHERE guarantee_insurance = TRUE AND date_added < CURRENT_DATE - INTERVAL '30 days';",
            "CREATE INDEX IF NOT EXISTS idx_links_guarantee_date ON links(guarantee_insurance, date_added);",
            "CREATE INDEX IF NOT EXISTS idx_employee_customers_management_site ON employee_customers(management_site_id);",
            "CREATE INDEX IF NOT EXISTS idx_employees_status ON employees(status);"
        ]
        
        # 각 SQL 명령어 실행
        for i, sql in enumerate(sql_commands, 1):
            try:
                print(f"📝 {i}/8: {sql[:50]}...")
                cursor.execute(sql)
                conn.commit()
                print(f"✅ 완료")
            except Exception as e:
                print(f"⚠️ 오류 (무시됨): {e}")
                conn.rollback()
        
        print("🎉 데이터베이스 업데이트 완료!")
        
        # 결과 확인
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'employees';")
        columns = cursor.fetchall()
        print(f"📊 employees 테이블 컬럼: {[col[0] for col in columns]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 