#!/usr/bin/env python3
"""
테스트용 직원 데이터 추가 스크립트
"""
from db_utils import get_db_connection
from datetime import datetime

def add_test_employees():
    """다양한 테스트용 직원 추가"""
    try:
        print("=== 👥 테스트 직원 추가 시작 ===")
        
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        test_employees = [
            ('admin', 'admin'),
            ('관리자', 'admin'), 
            ('직원1', 'employee'),
            ('직원2', 'employee'),
            ('테스트직원', 'employee'),
            ('김철수', 'employee'),
            ('이영희', 'employee'),
            ('박민수', 'employee')
        ]
        
        current_time = datetime.now()
        added_count = 0
        
        for name, role in test_employees:
            try:
                # 중복 확인
                if db_type == 'postgresql':
                    cursor.execute("SELECT id FROM employees WHERE name = %s", (name,))
                else:
                    cursor.execute("SELECT id FROM employees WHERE name = ?", (name,))
                
                if cursor.fetchone():
                    print(f"  ⚠️ '{name}' 이미 존재함 - 건너뜀")
                    continue
                
                # 새 직원 추가
                if db_type == 'postgresql':
                    cursor.execute('''
                        INSERT INTO employees (name, email, department, position, created_at, role)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (name, '', '', '', current_time, role))
                else:
                    cursor.execute('''
                        INSERT INTO employees (name, email, department, position, created_at, role)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (name, '', '', '', current_time.strftime('%Y-%m-%d %H:%M:%S'), role))
                
                print(f"  ✅ '{name}' 추가 완료 ({role})")
                added_count += 1
                
            except Exception as e:
                print(f"  ❌ '{name}' 추가 실패: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n=== ✅ 테스트 직원 {added_count}명 추가 완료 ===")
        
        # 최종 확인
        print("\n현재 전체 직원 목록:")
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, role FROM employees ORDER BY id")
        employees = cursor.fetchall()
        
        for emp in employees:
            print(f"  ID:{emp[0]} | 이름:'{emp[1]}' | 역할:{emp[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_test_employees() 