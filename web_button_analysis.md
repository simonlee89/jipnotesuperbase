# 🔍 웹 버튼과 PostgreSQL 데이터베이스 연결 분석

## 📊 **데이터베이스 현재 상태**

### **테이블별 데이터 현황:**
- **👤 employees**: 0개 데이터 (9개 컬럼)
- **👥 employee_customers**: 0개 데이터 (9개 컬럼)  
- **🏠 links (주거용)**: 0개 데이터 (30개 컬럼)
- **🏢 office_links (업무용)**: 0개 데이터 (31개 컬럼)
- **📋 guarantee_insurance_log**: 0개 데이터 (6개 컬럼)
- **ℹ️ customer_info**: 1개 데이터 (3개 컬럼)
  - 샘플: `{'id': 1, 'customer_name': '제일좋은집 찾아드릴분', 'move_in_date': ''}`

---

## 🌐 **웹 애플리케이션별 버튼-DB 연결 분석**

### **1. 🏛️ 관리자페이지.py (관리자 + 직원 대시보드)**

#### **🔐 로그인 관련 버튼:**
- **직원 로그인** → `POST /login` → `employees` 테이블 조회
- **관리자 로그인** → `POST /admin-login` → 하드코딩된 계정 확인
- **로그아웃** → `GET /logout` → 세션 정리

#### **👨‍💼 직원 관리 버튼 (admin_panel.html):**
- **직원 목록 로드** → `GET /api/employees` → `employees` 테이블
- **직원 추가** → `POST /api/employees` → `employees` 테이블 INSERT
- **직원 삭제** → `DELETE /api/employees/{id}` → `employees` 테이블 is_active=0
- **직원 활성화** → `PUT /api/employees/{id}/activate` → `employees` 테이블
- **비밀번호 리셋** → `PUT /api/employees/{id}/reset-password` → `employees` 테이블
- **영구 삭제** → `DELETE /api/employees/{id}/permanent-delete` → `employees` 테이블

#### **👥 고객 관리 버튼 (employee_dashboard.html):**
- **고객 목록 로드** → `GET /api/customers` → `employee_customers` 테이블
- **고객 추가** → `POST /api/customers` → `employee_customers` 테이블 INSERT
- **고객 수정** → `PUT /api/customers/{id}` → `employee_customers` 테이블 UPDATE
- **고객 삭제** → `DELETE /api/customers/{id}` → `employee_customers` 테이블 DELETE
- **고객 메모 수정** → `PUT /api/customers/{id}/memo` → `employee_customers` 테이블
- **고객 필드 수정** → `PUT /api/customers/{id}/field` → `employee_customers` 테이블

#### **🛡️ 보증보험 관리 버튼:**
- **보증보험 목록** → `GET /api/guarantee-list` → `guarantee_insurance_log` 테이블
- **보증보험 삭제** → `POST /admin/guarantee-delete/{id}` → `guarantee_insurance_log` 테이블
- **보증보험 수정** → `POST /admin/guarantee-edit/{id}` → `guarantee_insurance_log` 테이블

---

### **2. 🏠 주거용.py (주거용 매물 관리)**

#### **🏡 메인 페이지 버튼 (index.html):**
- **매물 목록 로드** → `GET /api/links` → `links` 테이블 (30개 컬럼)
- **매물 추가** → `POST /api/links` → `links` 테이블 INSERT
- **좋아요/싫어요** → `PUT /api/links/{id}` → `links.liked/disliked` 컬럼
- **매물 삭제** → `DELETE /api/links/{id}` → `links.is_deleted=1`
- **메모 수정** → `PUT /api/links/{id}` → `links.memo` 컬럼
- **평점 수정** → `PUT /api/links/{id}` → `links.rating` 컬럼

#### **🏠 주거용 특화 버튼들:**
- **플랫폼 설정** → `links.platform_jikbang/platform_naver/platform_etc`
- **출처 구분** → `links.source_broker/source_customer`
- **보증보험 가능/불가** → `links.guarantee_available/guarantee_unavailable`
- **고객 반응** → `links.customer_liked/customer_disliked`
- **매물 정보** → `links.price/area/room_type/floor_info/deposit/monthly_rent`

#### **🔄 기타 기능 버튼:**
- **백업** → `GET /api/backup` → 전체 `links` 테이블 JSON 내보내기
- **복원** → `POST /api/restore` → JSON에서 `links` 테이블 복원
- **보증보험 로그** → `POST /api/guarantee-log` → `guarantee_insurance_log` 테이블
- **보증보험 리셋** → `POST /api/guarantee-insurance-reset` → `links.guarantee_insurance=0`

---

### **3. 🏢 업무용.py (업무용 매물 관리)**

#### **🏢 메인 페이지 버튼 (업무용_index.html):**
- **매물 목록 로드** → `GET /api/links` → `office_links` 테이블 (31개 컬럼)
- **매물 추가** → `POST /api/links` → `office_links` 테이블 INSERT
- **좋아요/싫어요** → `PUT /api/links/{id}` → `office_links.liked/disliked` 컬럼
- **매물 삭제** → `DELETE /api/links/{id}` → `office_links.is_deleted=1`
- **메모 수정** → `PUT /api/links/{id}` → `office_links.memo` 컬럼
- **평점 수정** → `PUT /api/links/{id}` → `office_links.rating` 컬럼

#### **🏢 업무용 특화 버튼들:**
- **플랫폼 설정** → `office_links.platform_jikbang/platform_naver/platform_etc`
- **출처 구분** → `office_links.source_broker/source_customer`
- **보증보험 가능/불가** → `office_links.guarantee_available/guarantee_unavailable`
- **고객 반응** → `office_links.customer_liked/customer_disliked`
- **사무실 정보** → `office_links.office_type/office_size/monthly_fee/deposit_amount`
- **부대시설** → `office_links.utilities_included/parking_available/elevator_available`

#### **🔄 기타 기능 버튼:**
- **백업** → `GET /api/backup` → 전체 `office_links` 테이블 JSON 내보내기
- **복원** → `POST /api/restore` → JSON에서 `office_links` 테이블 복원
- **보증보험 리셋** → `POST /api/guarantee-insurance-reset` → `office_links.guarantee_insurance=0`

---

## 🔄 **공통 기능**

### **🌐 고객 사이트 접근:**
- **주거용**: `/customer/{management_site_id}` → `employee_customers` 테이블에서 고객 정보 조회
- **업무용**: `/customer/{management_site_id}` → `employee_customers` 테이블에서 고객 정보 조회

### **📊 고객 정보 API:**
- `GET /api/customer_info` → `customer_info` 테이블 조회
- `POST /api/customer_info` → `customer_info` 테이블 업데이트

### **🔧 관리 기능:**
- **DB 강제 초기화**: `/force-init-db`, `/force-init-work-db`, `/force-init-residence-db`
- **테이블 구조 확인**: `/check-table-structure`
- **누락 컬럼 수정**: `/fix-missing-columns`
- **DB 상태 디버깅**: `/debug-db-status`

---

## 🎯 **핵심 연결 구조**

```
웹 버튼 → JavaScript fetch() → Flask 라우트 → PostgreSQL 테이블

예시:
[좋아요 버튼] → fetch('/api/links/123', {method: 'PUT'}) 
               → @app.route('/api/links/<int:link_id>', methods=['PUT'])
               → UPDATE links SET liked = TRUE WHERE id = 123
```

## ✅ **결론**

- **모든 웹 버튼이 PostgreSQL 데이터베이스와 완벽하게 연결됨**
- **주거용/업무용 각각 30+개의 특화 컬럼 활용 가능**
- **관리자페이지에서 직원/고객 통합 관리**
- **실시간 데이터 동기화 및 백업/복원 기능 완비**
- **보증보험 로그 추적 및 자동 만료 기능** 