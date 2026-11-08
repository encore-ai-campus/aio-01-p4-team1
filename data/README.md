# data · 제공 초기 데이터 제출본

`main-backup` 기준 커밋 `b8448d0`의 `data-api/data/*.json` 8개를 원문 그대로 복사했다: `employees.json`, `faq.json`, `tickets.json`, `ops-seed.json`, `releases.json`, `prices.json`, `budget.json`, `run-logs.json`.

제공 가상 직원 6명·FAQ 6종·기존 티켓 4건 등의 원본 의미를 유지한다. 테스트용 가상 연락처도 원문에 포함된다. 실제 업무 DB·계정·세션 덤프가 아니다. VM data-api는 기존 `data-api/data/`를 계속 사용하며 [서버 구현](../data-api/server.py)과 [DB·초기화 안내](../develop/jihye/deploy/README.md)를 따른다. 제공 JSON 복사와 애플리케이션 DB 초기화는 별도 단계다.
