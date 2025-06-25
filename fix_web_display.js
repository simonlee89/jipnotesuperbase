// 웹 링크 추가 후 목록 표시 문제 해결 패치
// 이 코드를 브라우저 개발자 도구 콘솔에서 실행하세요

console.log("🔧 링크 표시 문제 해결 패치 시작...");

// 1. 캐시 방지 링크 로드 함수
function loadLinksWithoutCache() {
    const params = new URLSearchParams();
    if (managementSiteId) params.append('management_site_id', managementSiteId);
    
    // 캐시 방지를 위한 타임스탬프 추가
    params.append('_t', Date.now());
    
    // 모든 필터 초기화
    params.append('platform', 'all');
    params.append('user', 'all');
    params.append('like', 'all');
    params.append('guarantee', 'all');
    
    console.log("📡 캐시 없이 링크 조회 중...");
    
    fetch(`/api/links?${params.toString()}`, {
        cache: 'no-cache',
        headers: {
            'Cache-Control': 'no-cache'
        }
    })
    .then(response => {
        console.log("✅ 응답 받음:", response.status);
        return response.json();
    })
    .then(data => {
        console.log("📊 조회된 링크 수:", data.length);
        if (data && data.length > 0) {
            console.log("🔗 최근 링크:", data[0]);
        }
        displayLinks(data);
    })
    .catch(error => {
        console.error('❌ 링크 로드 오류:', error);
    });
}

// 2. 강제 새로고침 함수
function forceRefreshLinks() {
    console.log("🔄 강제 새로고침 시작...");
    
    // 필터 초기화
    document.getElementById('platformFilter').value = 'all';
    document.getElementById('userFilter').value = 'all';
    document.getElementById('likeFilter').value = 'all';
    document.getElementById('guaranteeFilter').value = 'all';
    document.getElementById('dateFilter').value = '';
    
    // 현재 필터 상태 초기화
    currentFilters = {
        platform: 'all',
        user: 'all',
        like: 'all',
        guarantee: 'all'
    };
    
    // 캐시 없이 로드
    loadLinksWithoutCache();
}

// 3. 개선된 링크 추가 함수
function addLinkImproved() {
    const url = document.getElementById('linkUrl').value;
    const memo = document.getElementById('linkMemo').value;
    const guaranteeInsurance = document.getElementById('guaranteeInsurance').checked;
    
    if (!url) {
        alert('링크 URL을 입력해주세요.');
        return;
    }
    
    console.log("➕ 링크 추가 시작:", {url, memo, guaranteeInsurance});
    
    const data = {
        url: url,
        platform: currentPlatform || 'zigbang',
        added_by: currentUser || '중개사',
        memo: memo,
        guarantee_insurance: guaranteeInsurance,
        residence_extra: ''
    };
    
    const apiUrl = managementSiteId ? `/api/links?management_site_id=${managementSiteId}` : '/api/links';
    
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        console.log("✅ 추가 응답:", response.status);
        return response.json();
    })
    .then(result => {
        console.log("📝 추가 결과:", result);
        if (result.success) {
            // 폼 초기화
            document.getElementById('linkUrl').value = '';
            document.getElementById('linkMemo').value = '';
            document.getElementById('guaranteeInsurance').checked = false;
            
            console.log("🎉 링크 추가 성공! 목록 새로고침...");
            
            // 1초 후 강제 새로고침 (DB 동기화 대기)
            setTimeout(() => {
                forceRefreshLinks();
            }, 1000);
            
        } else {
            alert(result.error || '링크 추가에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('❌ 링크 추가 오류:', error);
        alert('링크 추가 중 오류가 발생했습니다.');
    });
}

// 4. 디버깅 정보 출력
function debugLinkStatus() {
    console.log("🔍 현재 상태 디버깅:");
    console.log("- managementSiteId:", managementSiteId);
    console.log("- currentPlatform:", currentPlatform);
    console.log("- currentUser:", currentUser);
    console.log("- currentFilters:", currentFilters);
    
    // 현재 링크 수 확인
    const linksList = document.getElementById('linksList');
    const linkItems = linksList.querySelectorAll('.link-item');
    console.log("- 화면에 표시된 링크 수:", linkItems.length);
    
    // API 직접 호출로 실제 데이터 확인
    fetch('/api/links?_debug=1')
    .then(response => response.json())
    .then(data => {
        console.log("- 실제 API 응답 링크 수:", data.length);
        if (data.length > 0) {
            console.log("- 최근 링크 3개:", data.slice(0, 3));
        }
    });
}

// 5. 자동 수정 실행
console.log("🚀 자동 수정 시작...");

// 기존 addLink 함수를 개선된 버전으로 교체
if (typeof addLink === 'function') {
    window.addLink = addLinkImproved;
    console.log("✅ addLink 함수 교체 완료");
}

// 디버깅 정보 출력
debugLinkStatus();

// 강제 새로고침 실행
forceRefreshLinks();

console.log("✨ 패치 완료! 이제 링크를 추가해보세요.");
console.log("💡 문제가 계속되면 forceRefreshLinks() 함수를 수동으로 호출하세요."); 