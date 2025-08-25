import requests
import json
import sys
import io

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Base URL for the application
BASE_URL = "http://127.0.0.1:8080"

def test_two_stage_deletion():
    """Test the two-stage deletion functionality"""
    
    # Start a session to maintain cookies
    session = requests.Session()
    
    # First, login as an admin or team leader
    print("\n1. Logging in as admin...")
    login_data = {
        'employee_id': '수정',  # Use an existing employee ID
        'password': 'test1234'  # Using the password we just set
    }
    
    headers = {'Content-Type': 'application/json'}
    login_response = session.post(f"{BASE_URL}/login", json=login_data, headers=headers)
    
    if login_response.status_code == 200:
        result = login_response.json()
        if result.get('success'):
            print(f"✅ Login successful: {result.get('message')}")
        else:
            print(f"❌ Login failed: {result.get('message')}")
            return
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    # Get the list of employees
    print("\n2. Getting employee list...")
    employees_response = session.get(f"{BASE_URL}/api/employees")
    
    if employees_response.status_code == 200:
        data = employees_response.json()
        employees = data.get('employees', [])
        print(f"✅ Found {len(employees)} employees")
        
        # Find an active employee to test
        active_employee = None
        inactive_employee = None
        
        for emp in employees:
            if emp.get('status') == 'active' or emp.get('employee_status') == 'active':
                if not active_employee:
                    active_employee = emp
            elif emp.get('status') == 'inactive' or emp.get('employee_status') == 'inactive':
                if not inactive_employee:
                    inactive_employee = emp
        
        # Test 1: Try to deactivate an active employee
        if active_employee:
            emp_id = active_employee['id']
            emp_name = active_employee.get('name') or active_employee.get('employee_name')
            print(f"\n3. Testing deactivation of active employee: {emp_name} (ID: {emp_id})")
            
            # Call deactivate endpoint
            deactivate_response = session.put(f"{BASE_URL}/api/employees/{emp_id}/deactivate")
            
            if deactivate_response.status_code == 200:
                result = deactivate_response.json()
                if result.get('success'):
                    print(f"✅ Employee deactivated successfully")
                else:
                    print(f"❌ Deactivation failed: {result.get('message')}")
            else:
                print(f"❌ Deactivation request failed: {deactivate_response.status_code}")
        else:
            print("⚠️ No active employee found to test deactivation")
        
        # Test 2: Try to permanently delete an inactive employee
        if inactive_employee:
            emp_id = inactive_employee['id']
            emp_name = inactive_employee.get('name') or inactive_employee.get('employee_name')
            print(f"\n4. Testing permanent deletion of inactive employee: {emp_name} (ID: {emp_id})")
            
            # Call permanent delete endpoint
            delete_response = session.delete(f"{BASE_URL}/api/employees/{emp_id}/permanent-delete")
            
            if delete_response.status_code == 200:
                result = delete_response.json()
                if result.get('success'):
                    print(f"✅ Employee permanently deleted successfully")
                else:
                    print(f"❌ Permanent deletion failed: {result.get('message')}")
            else:
                print(f"❌ Permanent deletion request failed: {delete_response.status_code}")
        else:
            print("⚠️ No inactive employee found to test permanent deletion")
            
            # If we just deactivated an employee, try to delete them
            if active_employee:
                print(f"\n5. Testing permanent deletion of just-deactivated employee...")
                emp_id = active_employee['id']
                
                delete_response = session.delete(f"{BASE_URL}/api/employees/{emp_id}/permanent-delete")
                
                if delete_response.status_code == 200:
                    result = delete_response.json()
                    if result.get('success'):
                        print(f"✅ Employee permanently deleted successfully")
                    else:
                        print(f"❌ Permanent deletion failed: {result.get('message')}")
                else:
                    print(f"❌ Permanent deletion request failed: {delete_response.status_code}")
        
        # Test 3: Try to permanently delete an active employee (should fail)
        active_for_fail_test = None
        for emp in employees:
            if (emp.get('status') == 'active' or emp.get('employee_status') == 'active') and emp['id'] != active_employee.get('id') if active_employee else True:
                active_for_fail_test = emp
                break
        
        if active_for_fail_test:
            emp_id = active_for_fail_test['id']
            emp_name = active_for_fail_test.get('name') or active_for_fail_test.get('employee_name')
            print(f"\n6. Testing permanent deletion of ACTIVE employee (should fail): {emp_name} (ID: {emp_id})")
            
            delete_response = session.delete(f"{BASE_URL}/api/employees/{emp_id}/permanent-delete")
            
            if delete_response.status_code == 400:
                result = delete_response.json()
                print(f"✅ Correctly prevented deletion of active employee: {result.get('message')}")
            elif delete_response.status_code == 200:
                print(f"❌ ERROR: Active employee was deleted when it shouldn't have been!")
            else:
                print(f"❌ Unexpected response: {delete_response.status_code}")
        
    else:
        print(f"❌ Failed to get employee list: {employees_response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Two-Stage Employee Deletion")
    print("=" * 60)
    test_two_stage_deletion()
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)