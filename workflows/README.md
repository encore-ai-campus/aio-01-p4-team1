# workflows · n8n 워크플로우 5종

`oke-support.json`(문의 본체), `oke-index.json`(색인), `oke-search.json`(권한별 검색), `oke-handoff.json`(이관), `oke-errors.json`(오류 안전망)을 포함한다.

게시할 때 [deploy/prepare_n8n_workflows.py](../deploy/prepare_n8n_workflows.py)로 실행 환경의 Credential ID를 연결한다. 비밀값은 n8n Credential과 환경 설정에만 둔다. 로컬 초기화는 [배포 안내](../deploy/LOCAL-MAC.md), 실제 노드·계약은 [워크플로우 설계](../docs/WORKFLOW-DESIGN.md)·[API 계약](../docs/API-CONTRACT.md), 검증 근거는 [실행 결과](../docs/EXECUTION-RESULT.md)를 따른다. JSON 존재만으로 게시·실행 완료를 주장하지 않는다.
