# 🔒 보안 가이드

## 중요 보안 공지

이 프로젝트는 민감한 정보를 환경 변수로 관리합니다. **절대로** 실제 비밀번호나 API 키를 코드에 하드코딩하지 마세요.

## 환경 변수 설정

### 1. .env 파일 생성
```bash
cp .env.example .env
```

### 2. 필수 환경 변수
- `SUPABASE_URL`: Supabase 프로젝트 URL
- `SUPABASE_KEY`: Supabase Anon Key
- `ADMIN_ID`: 관리자 ID
- `ADMIN_PASSWORD`: 관리자 비밀번호
- `FLASK_SECRET_KEY`: Flask 세션 암호화 키

### 3. 보안 체크리스트

#### ✅ 해야 할 일
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] 강력한 비밀번호 사용 (최소 12자, 특수문자 포함)
- [ ] 정기적으로 API 키 재발급
- [ ] 프로덕션 환경에서는 환경 변수를 안전하게 관리

#### ❌ 하지 말아야 할 일
- [ ] 비밀번호를 코드에 하드코딩
- [ ] `.env` 파일을 Git에 커밋
- [ ] 공개 저장소에 실제 API 키 노출
- [ ] 테스트 파일에 실제 인증 정보 포함

## Supabase 키 재발급 방법

1. [Supabase Dashboard](https://app.supabase.com) 접속
2. 프로젝트 선택
3. Settings > API 메뉴 이동
4. "Regenerate anon key" 클릭
5. 새 키를 `.env` 파일에 업데이트

## Git 히스토리에서 민감한 정보 제거

만약 실수로 민감한 정보를 커밋했다면:

```bash
# BFG Repo-Cleaner 사용
java -jar bfg.jar --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 또는 git filter-branch 사용
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
```

## 보안 문제 신고

보안 취약점을 발견하면 공개 이슈로 등록하지 말고 비공개로 연락 주세요.

## 추가 보안 권장사항

1. **2단계 인증(2FA)** 활성화
2. **환경별 다른 키 사용** (개발/스테이징/프로덕션)
3. **정기 보안 감사** 실시
4. **의존성 정기 업데이트** (`pip list --outdated`)

---

⚠️ **경고**: 이 저장소가 공개되기 전에 반드시 모든 민감한 정보가 제거되었는지 확인하세요!