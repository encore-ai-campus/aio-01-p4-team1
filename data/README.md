# data · 가상 초기 데이터·스키마

제공 JSON 8개(`employees`, `faq`, `tickets`, `ops-seed`, `releases`, `prices`, `budget`, `run-logs`)와 `schemas/`를 포함한다. 직원 6명·FAQ 6종·기존 티켓 4건 등의 원본 의미를 유지하며 합성 연락처를 포함한다. 실제 계정·세션·업무 DB 덤프가 아니다.

[제공 API](../data-api/server.py)는 이 폴더를 읽고 규정은 [knowledge/](../knowledge/README.md), 프롬프트는 [prompts/](../prompts/README.md)를 사용한다. 통합 Compose도 동일한 루트 경로를 읽기 전용으로 마운트한다. 애플리케이션 DB 초기화는 [배포 안내](../deploy/LOCAL-MAC.md)의 별도 단계다.
