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
| `oke-support-08.json` | P1-2 | writer·verifier 분리, 엄격한 JSON·출처 검사, Mock 점수 분기, 최종 출력 가림 |
| `oke-support-09.json` | P1-2 보완 | 티켓 조회 404/장애 시 자동 답변 차단, 일반전화·국제전화 가림 |
| `oke-support-10.json` | P1-3 | 긴급 high 선이관 뒤 보안 근거·본인 상태 Mock 보강, 같은 실행 내 C04 재호출 차단 |
| `oke-support-11.json` | P1-4 | N05 결과 재사용 Mock, 소유권·내용 충돌·처리 중·조회 장애 보수적 종료 |
| `oke-support-12.json` | P1-5 연결 준비 1단계 | 직원·C03·기존 티켓·C04 HTTP 경로와 응답 어댑터 추가. 로컬 실행 전 원본으로 보존 |
| `oke-support-13.json` | P1-5 로컬 실행 수정 | 12의 로컬 n8n 실행에서 찾은 직원 응답 형식·webhookId·triage 프롬프트/파서·보완 문구 수정, 근거 없는 본인 티켓 상태 문의 안내 경로, tickets_down 확인 불가 문구, WF-12 긴급 보안 사고 초동 조치 안내, 근거가 있어도 자동 답변 불가 시 본인 상태 안내 추가 |
| `oke-support-14.json` | 자동 답변 잠금 구조 | 13에 N12 승인 기준값 상수 `APPROVED_MIN_SCORE`(현재 `null`, 잠금 유지)·N15 승인 시 실제 writer·verifier 통과로 자동 답변 허용·N22 `agents` 실제 실행 목록 반영 |
| `oke-support-15.json` | 실제 데이터 품질 수정 | 14에 main의 N03·N10(인증 없음) 반영·보안 사고 키워드(랜섬웨어·감염·유출, 피싱 링크 클릭 등)는 LLM 결과와 무관하게 긴급 high(팀장 승인)·writer/verifier 프롬프트를 근거 문장만 쓰도록 강화·writer `answerable=false`면 자동 답변 대신 이관·비밀번호 분실/계정 잠김 질문은 보완 질문 없이 진행. 현재 최신 개발본 |

모든 JSON의 내부 워크플로우 이름과 웹훅 경로는 `oke-support`다. 버전 기록용으로 보존하며 **여러 버전을 동시에 n8n에 활성화하지 않는다.** 공식 게시·시험 대상은 팀이 선택한 한 버전으로 정한다. 현재 모두 프로젝트 n8n에 게시·시험하지 않았다. `12`~`15`는 `SERVICE_MODE=practice|app`일 때 직원·C03·기존 티켓·C04의 HTTP 분기를 선택한다. 실제 Credential을 연결하고 사람이 n8n에서 시험하기 전에는 실행 성공이 아니다. replay는 여전히 Mock이며 실제 결과 저장·중복 보장은 미검증이다.

`12`~`14`의 HTTP Credential 참조 이름은 `SUPPORT_DATA_API_X_API_KEY`(직원·기존 티켓)와 `SUPPORT_X_TEAM_KEY`(C03·C04)다. `15`는 main과 같이 직원·기존 티켓 조회에 Credential을 쓰지 않고 C03·C04만 `SUPPORT_X_TEAM_KEY`를 쓴다. JSON에는 값이 없으며 프로젝트 n8n에서 실제 Credential로 바인딩해야 한다. `SERVICE_MODE`가 없거나 `practice|app` 외의 값이면 직원 확인을 안전하게 종료하고 합성 티켓을 만들지 않는다. 로컬 Code 시뮬레이션만 가짜 `mock` 모드를 주입한다.

[자기 개발 계획](../Doc/IMP-PLAN.md) → [공통 계약](../../../docs/API-CONTRACT.md) → 단계별 JSON 작성·check → 사람이 선택한 버전만 push·test 순서로 진행한다.
전체 경로·작업 디렉터리를 명령에 명시하고, 키는 Credential에만 둔다. 제출은 [리드의 취합 안내](../../ohyun/SUBMISSION.md)를 따른다.
