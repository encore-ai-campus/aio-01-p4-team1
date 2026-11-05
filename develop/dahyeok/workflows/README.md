# 다혁님 n8n 개발 결과물

이 폴더에는 단계별 워크플로우 JSON을 번호로 보존한다.

| 파일 | 단계 | 상태 |
| --- | --- | --- |
| `oke-support.json` | P0-1 | 입력·직원 Mock·주입 차단 골격. 이전 원본으로 보존 |
| `oke-support-02.json` | P0-2 | triage Mock·보완 질문 추가. 이전 버전으로 보존 |
| `oke-support-03.json` | P0-3 | C04 이관 Mock·티켓/알림/전송 실패 매핑. 현재 최신 개발본 |

세 JSON은 내부 워크플로우 이름과 웹훅 경로가 모두 `oke-support`다. 버전 기록용으로 보존하며 **여러 버전을 동시에 n8n에 활성화하지 않는다.** 공식 게시·시험 대상은 팀이 선택한 한 버전으로 정한다. 현재 모두 프로젝트 n8n에 게시·시험하지 않았다. P0-3의 ticket_id는 로컬 Mock 값이며 실제 IT팀 티켓을 만들지 않는다.

[자기 개발 계획](../Doc/IMP-PLAN.md) → [공통 계약](../../../docs/API-CONTRACT.md) → 단계별 JSON 작성·check → 사람이 선택한 버전만 push·test 순서로 진행한다.
전체 경로·작업 디렉터리를 명령에 명시하고, 키는 Credential에만 둔다. 제출은 [리드의 취합 안내](../../ohyun/SUBMISSION.md)를 따른다.
