# 다혁님 n8n 개발 결과물

이 폴더에는 단계별 워크플로우 JSON을 번호로 보존한다.

| 파일 | 단계 | 상태 |
| --- | --- | --- |
| `oke-support.json` | P0-1 | 입력·직원 Mock·주입 차단 골격. 이전 원본으로 보존 |
| `oke-support-02.json` | P0-2 | triage Mock·보완 질문 추가. 이전 버전으로 보존 |
| `oke-support-03.json` | P0-3 | C04 이관 Mock·티켓/알림/전송 실패 매핑 |
| `oke-support-04.json` | P1-1 1단계 | 검증된 부서로 C03 요청 생성, 검색 Mock |
| `oke-support-05.json` | P1-1 2단계 | 티켓 ID가 있을 때 본인 조회 요청, 403/404/장애 구분 Mock |
| `oke-support-06.json` | P1-1 3단계 | 검색·티켓 병렬 결과 병합, 근거 없음/검색 장애 구분, 연락처 제거 |
| `oke-support-07.json` | P1-1 4단계 | 원민님 C04 신규·중복·부분 실패 응답 매핑 대조·수정 |
| `oke-support-08.json` | P1-2 | writer·verifier 분리, 엄격한 JSON·출처 검사, Mock 점수 분기, 최종 출력 가림. 현재 최신 개발본 |

모든 JSON의 내부 워크플로우 이름과 웹훅 경로는 `oke-support`다. 버전 기록용으로 보존하며 **여러 버전을 동시에 n8n에 활성화하지 않는다.** 공식 게시·시험 대상은 팀이 선택한 한 버전으로 정한다. 현재 모두 프로젝트 n8n에 게시·시험하지 않았다. P1-2의 C03·티켓 조회·C04·writer·verifier는 로컬 Mock이며 실제 검색·조회·티켓 저장·LLM 검증을 하지 않는다.

[자기 개발 계획](../Doc/IMP-PLAN.md) → [공통 계약](../../../docs/API-CONTRACT.md) → 단계별 JSON 작성·check → 사람이 선택한 버전만 push·test 순서로 진행한다.
전체 경로·작업 디렉터리를 명령에 명시하고, 키는 Credential에만 둔다. 제출은 [리드의 취합 안내](../../ohyun/SUBMISSION.md)를 따른다.
