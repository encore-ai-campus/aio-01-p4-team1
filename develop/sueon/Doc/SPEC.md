# 직원·관리자 화면 · SPEC

[README](../README.md) → [TODO](TODO.md) → **SPEC** → [IMP-PLAN](IMP-PLAN.md). 아래 통과 기준은 구현 후 확인할 기대이며 현재 시험 결과가 아니다.

## 적용할 공통 기준

| 항목 | 적용할 기준 |
| --- | --- |
| 계정 | 관리자가 제공 직원 계정 발급. 공개 가입 없음. 임시 비밀번호 첫 로그인 변경. IT팀만 admin |
| 인증 | 로그인 user 요약 id/name/dept/role/must_change_password와 HttpOnly 쿠키, 로그아웃 ok=true. GET /api/auth/me는 id/name/dept/role/must_change_password |
| 호출 | 같은 출처 /api→프론트 프록시→FastAPI. 브라우저의 DB·n8n·data-api 직접 호출 금지. 서버가 user/dept/role 결정 |
| 질문 | question 1~500자, attempt 기본 1. 동일 요청 재시도는 같은 request_id, 새 보완 차례는 새 ID와 증가한 attempt/context. attempt>=3이면 본체가 이관 |
| 결과 | request_id/route/answer/sources/ticket/agents/security 보존, route 5종 그대로 사용. UI에서 점수로 재판정하지 않음 |
| 목록·오류 | 목록 {"items":[]}, 생성·변경은 해당 객체. 웹 오류 {"error":{"code":"forbidden","message":"접근 권한이 없습니다."}}. 공통 웹훅 HTTP400 codes는 변환하지 않음 |
| 관리자 | 직원·계정 목록(`GET /api/admin/employees`, `GET /api/admin/users`), 계정 생성·비활성화·초기화, 티켓 목록·변경, 알림 목록 API 확정 |
| 티켓 | 웹 status=open/in_progress/resolved→접수/처리 중/완료, priority=normal/high→보통/긴급. assignee는 IT팀 `app.employees.id` 정수 또는 `null`. 기존 티켓은 원본 상태 유지. 신규 T-2001부터, 같은 키 한 건 |
| 권한·보안 | 직원 본인 기록만, 관리자 기능은 IT팀 관리자만. 비밀번호·토큰·실제 연락처는 기록·캡처·브라우저 저장소에 남기지 않음 |

출처: [TOPIC](../../../docs/TOPIC.md) · [API-CONTRACT C01/C07/오류](../../../docs/API-CONTRACT.md) · [DATA-AND-DB](../../../docs/DATA-AND-DB.md). 상세 필드·정책 누락은 [HANDOFF H01~H04](HANDOFF.md)의 제안으로 분리한다. 아래 화면 모델은 Mock 내부 표현이며 미확정 서버 JSON을 확정하지 않는다.

## 화면 경로 · 입력·버튼·상태·API

아래 파일은 모두 `develop/sueon/` 아래 구현 예정이다. `(protected)`는 URL에 포함되지 않는 App Router 그룹이다. UI 경로는 담당 범위 안의 구현 선택이다.

| URL / 예정 페이지 파일 | 입력·표시 | 버튼·이동 | 상태 | 사용 API / 요구 |
| --- | --- | --- | --- | --- |
| `/` · `src/app/page.tsx` | 세션 확인 | 직원 /ask, 관리자 /admin/tickets, 미인증 /login | 확인 중/오류/이동 | GET /api/auth/me / FE-01 |
| `/login` · `src/app/login/page.tsx` | 로그인 ID·가린 비밀번호 | 로그인 | 초기/제출 중/401/장애 | POST /api/auth/login / FE-01 |
| `/change-password` · `src/app/(protected)/change-password/page.tsx` | 현재·새 비밀번호·새 비밀번호 확인(가림) | 변경, 로그아웃 | 불일치/제출 중/400/401/성공 | POST /api/auth/change-password, POST /api/auth/logout / FE-01 |
| `/ask` · `src/app/(protected)/ask/page.tsx` | 질문 textarea·글자수, route·답·근거·티켓, 보완 답 | 보내기, 보완 보내기, 동일 요청 재시도, 새 문의, 내 문의 | 검증/대기/route 5종/연결 불명 | POST /api/ask / FE-02,05 |
| `/my-requests` · `src/app/(protected)/my-requests/page.tsx` | 본인 질문·답·시각·티켓 상태 | 새로고침, 행 펼치기, 질문하기 | 로딩/빈 목록/목록/오류 | GET /api/my-requests / FE-03 |
| `/admin/tickets` · `src/app/(protected)/admin/tickets/page.tsx` | ID·제목·긴급도·담당자·상태·답변 | 행 선택, 저장, 새로고침 | 빈 목록/편집/저장 중/400/403/404/장애 | GET /api/admin/tickets, PATCH /api/admin/tickets/{id} / FE-04T |
| `/admin/users` · `src/app/(protected)/admin/users/page.tsx` | 제공 직원 식별값·로그인 ID·임시 비밀번호, 대상 계정·활성 상태 | 발급, 비활성화/활성화, 초기화 | 입력/생성 중/오류/요약/대상 없음 | GET /api/admin/employees, GET /api/admin/users, POST /api/admin/users, PATCH /api/admin/users/{id}, POST /api/admin/users/{id}/reset-password / FE-04U |
| `/admin/alerts` · `src/app/(protected)/admin/alerts/page.tsx` | 심각도·시각·안내·선택 ticket_id | 새로고침, 로드된 티켓 보기 | 빈 목록/목록/오류/티켓 없음 | GET /api/admin/alerts / FE-04A |

공통 헤더에는 이름·부서·역할, 질문·내 문의·비밀번호 변경·로그아웃을 둔다. 관리자만 티켓·계정·알림 메뉴를 추가한다. 직접 URL도 세션·역할 확인 뒤 렌더링하되 실제 보안 판정은 FastAPI가 한다. 폼 label·오류 설명·키보드 포커스를 제공하고 색상만으로 상태를 표현하지 않는다. 좁은 화면에서 표는 스크롤 가능하게 하고 입력·버튼은 가리지 않는다.

## FE-01 · 로그인·비밀번호·세션

- 입력: login_id/password, 변경 시 현재·새 비밀번호와 확인. 확인 칸은 UI에서만 비교하고 전송하지 않는다. 변경 요청의 실제 키·응답은 H02 제안 상태다.
- 정상 흐름: /login 제출→성공 user→must_change_password=true이면 /change-password→변경 확인 후 직원 /ask·관리자 /admin/tickets. 로그인한 사용자의 /login 접근도 같은 이동 규칙을 적용한다.
- 새로고침 후 최초 변경 강제 여부는 `GET /api/auth/me`의 `must_change_password`로 판단한다(공통 `API-CONTRACT.md` 반영 완료). Mock에서 먼저 확인하고 실제 백엔드 연결 때 검증한다.
- 오류: 빈 입력 전송 차단. 로그인 401은 같은 폼에서 실패 안내. 보호 API 401은 민감 상태를 지우고 /login으로 이동하며 자동 재호출하지 않는다. 403은 권한 안내와 돌아갈 메뉴. 비밀번호 정책 오류는 서버의 안전한 메시지를 사용하고 임의 길이·잠금 정책을 만들지 않는다.
- 변경·로그아웃은 성공 응답 확인 뒤 완료로 표시한다. 로그아웃 실패는 완료 안내를 하지 않는다. 비밀번호·토큰은 localStorage/sessionStorage·로그·캡처에 보관하지 않는다.
- 통과: S01 직원/관리자/최초 변경 Mock의 이동, S02 새 비밀번호 확인 불일치 시 전송 0회, S03 로그아웃 후 보호 접근 401·내용 없음. 실제 연결 때 같은 흐름과 쿠키 HttpOnly를 확인한다.

## FE-02 · 질문과 결과

입력은 question, request_id, attempt, 필요 시 context다. 최초 attempt=1, 화면이 첫 전송 전 1~64자의 request_id를 생성해 유지할 수 있다(계약상 선택 필드). 직원 name/dept/role은 보내지 않는다. 공백뿐인 질문·501자는 전송 차단, 1자·500자 경계를 확인하며 서버 검증도 유지한다. 보완 답변도 공백만 있으면 보내지 않고 입력 안내를 표시한다.

작성→전송 중 버튼 비활성·대기 안내→공통 응답을 렌더링한다. 각 route는 아래대로 표시한다.

| route | 예상 출력·다음 행동 |
| --- | --- |
| 자동 답변 | answer와 sources의 doc/section. sources에 URL이 없으므로 링크나 직접 문서 조회 API를 창작하지 않음 |
| 보완 질문 | answer 아래 보완 입력. 원 질문 유지, 새 request_id·attempt+1·누적 context로 전송. context는 이전 보완 질문/사용자 답 순서의 문자열. 길이 제한은 H04 제안 |
| 담당자 이관 | ticket 존재 시 ID·보통/긴급·기존 접수 여부. ticket=null은 접수 완료로 쓰지 않고 연결 과정 문제·내 문의 확인 안내와 안전한 사유 표시 |
| 권한 없음 | 안전한 answer와 접근 불가 상태, 숨겨진 근거를 렌더링하지 않음 |
| 차단 | 안전한 answer와 요청 차단 상태, 입력 HTML/지시문 실행 없음 |

세 번째 차례 이관은 본체 응답을 따른다. 자동 답변인데 sources=[] 등 계약 위반은 응답 확인 오류로 처리하며 성공으로 확정하지 않는다. agents/security는 응답 모델에 보존하고 일반 화면에 내부 진단값을 그대로 노출하지 않는다.

대기 중 연타는 1회만 전송한다. 네트워크 단절/timeout/5xx는 결과 미확정 안내 후 사용자가 동일 request_id·동일 본문으로 재시도한다. 변경 질문은 새 문의다. 400/401/403/404 자동 재시도는 없다. 새로고침·세션 만료 후 진행 중 요청 복구는 H04 제안 상태이며 자동 재제출하지 않는다.

통과 S04~S09: route 5종, 출처·티켓 유무, attempt 1→2→3, 재시도 ID 유지/보완 새 ID를 확인한다. 점수 임계값·가짜 소요시간은 만들지 않는다.

## FE-03 · 내 문의

입력은 세션 쿠키만인 GET /api/my-requests다. 타인 데이터까지 받아 화면 필터로 권한을 대신하지 않는다. items=[]는 “아직 문의가 없습니다”와 질문하기 버튼. 행 펼치기로 질문·답·route·근거·티켓 상태를 확인한다. 별도 상세 API가 없으므로 목록 데이터를 쓴다.

화면 모델은 request_id/question/result/created_at/티켓 상태로 잡되 실제 JSON 위치는 H02 후 어댑터에서 맞춘다. 티켓 없음과 실패 이관을 구별하고 새 웹 status만 한글 매핑한다. 기존 티켓 상태는 원본 표시한다.

통과 S10: 빈 목록/복수 행/로드 오류 구별. S11: 두 직원으로 실제 로그인 시 각자 기록만 있고 이전 세션 데이터가 남지 않음. 계약에 없는 상세 URL을 만들어 권한 시험하지 않는다. 타인 request_id 재사용 거절은 지혜님·원민님의 통합 시험 근거에 연결한다.

## FE-04T · 관리자 티켓

GET 목록의 경로용 id(내부 정수 PK)를 선택해 PATCH한다. ticket_id는 표시용(`T-2001` 등)이며 경로 id와 혼동하지 않는다. status는 필수, assignee/reply는 선택이다. status는 open/in_progress/resolved, priority는 표시만 하고 변경 요청에 넣지 않는다. assignee는 IT팀 `app.employees.id` 정수 또는 `null`(해제)이다.

목록→행 편집→저장 중 중복 차단→성공 객체로 행 갱신. 실패는 편집값을 유지하고 저장 완료로 덮지 않는다. 알림에서 티켓을 볼 때 목록의 ticket_id와 맞추고 없으면 찾을 수 없음을 표시한다.

통과 S12: 담당자·답변·접수→처리 중→완료 저장 후 재조회에도 유지. S13: 400 폼 오류/403 접근 제한/404 없는 티켓. 직원의 직접 관리자 API 호출도 403·데이터 없음. 동시 편집 잠금은 공통 확정 정책으로 쓰지 않는다.

## FE-04U · 관리자 계정

제공 직원 식별값·login_id·임시 비밀번호로 발급한다. 성공은 계정 요약만 표시하고 비밀번호 입력은 지운다. 반환된 계정 id로 PATCH is_active 또는 reset-password temporary_password를 보낸다. 비활성화/초기화 전 화면에서 대상 이름·ID와 작업을 확인한다. 초기화 결과는 ok·변경 필요 여부만 표시하고 응답에 비밀번호가 있다고 가정하지 않는다.

`GET /api/admin/employees`와 `GET /api/admin/users`로 미발급 직원 및 기존 계정을 조회한다(백엔드 미기동 시에는 계약 Mock 사용). 직원 이름·부서를 임의 생성하거나 브라우저에서 data-api를 직접 조회하지 않는다.

통과 S14: 발급 성공/직원 또는 ID 중복 오류(H02 상태·code 제안)/비활성화/초기화, 직원 403. 초기화된 계정은 다음 로그인 변경 화면 이동을 실제 확인한다. 자기 비활성화·마지막 관리자 보호는 H03 제안 상태다.

## FE-04A · 관리자 알림

GET /api/admin/alerts의 items를 심각도·시각·안내·선택 ticket_id로 표시한다(H02 상세 어댑터). 확인·삭제·외부 전송 API를 새로 만들지 않는다. ticket_id=null인 티켓 생성 실패 알림도 행을 유지한다.

통과 S15: 빈 목록/긴급 알림/티켓 없는 알림/조회 오류 구별, 직원 403, 연락처·키가 든 원문 진단창 노출 없음.

## FE-05 · 공통 상태·연결 실패

| 상황 | 예상 화면·행동 | 통과 기준 |
| --- | --- | --- |
| HTTP400 codes | 코드와 안전한 입력 안내, 입력 유지 | 공통 웹훅 codes를 웹 error로 바꾸지 않음 |
| HTTP400 웹 error | 안전한 메시지, 폼 수정 | 미정 코드도 일반 입력 오류 처리 |
| 로그인 401 / 보호 API 401 | 폼 실패 / 로그인 이동 | 무한 재시도·이전 직원 데이터 없음 |
| HTTP403 / 404 | 권한 없음 / 없는 티켓 | 성공 안내·자동 재시도 없음 |
| 비JSON·스키마 불일치 | 응답 확인 오류 | 원문 노출·화면 충돌·가짜 성공 없음 |
| 네트워크·5xx·timeout | 실패 또는 결과 미확정, 수동 재시도 | 생성 자동 반복 없음, ask ID 유지 |
| 지연 | 로딩과 버튼 비활성 | 연타로 동시 전송 없음 |

S16은 Mock 지연·실패·잘못된 응답을 주입한다. backend·n8n·키 없이 화면을 확인해야 한다(구현 후 프론트 개발 서버는 필요). 클라이언트 제한 시간·backend 상한은 H04 검토 후 설정하며 임의 성공 시간을 약속하지 않는다. 브라우저 업무 호출이 /api뿐인지 확인한다.

## Mock 예시 · 예정 src/mocks/fixtures.ts

문서 안의 예시이며 파일 생성·실제 실행 결과가 아니다. 질문 응답의 필수 필드를 유지한다. score는 표시 시험용이며 임계값·측정값이 아니다. 실제 비밀번호·키·연락처를 넣지 않는다.

M01 정상 · HTTP200 · S04:

```json
{"request_id":"ui-auto-001","route":"자동 답변","answer":"VPN 접속 오류 항목의 점검 순서를 확인해 주세요.","sources":[{"doc":"remote-work-vpn","section":"접속 오류","score":0.82}],"ticket":null,"agents":["triage","retriever","writer","verifier"],"security":{"blocked_by":"","reason":"","masked":0}}
```

M02 보완 · HTTP200 · S05: question=VPN 연결이 안 돼요, attempt=1의 응답. “Windows, 오류 809”를 보완 입력하면 새 ID·attempt=2·누적 context로 전송한다.

```json
{"request_id":"ui-more-001","route":"보완 질문","answer":"운영체제와 표시되는 오류 코드를 알려 주세요.","sources":[],"ticket":null,"agents":["triage"],"security":{"blocked_by":"","reason":"","masked":0}}
```

M03 이관 · HTTP200 · S06: 동일 논리 요청 재시도 Mock은 같은 ticket_id와 duplicate=true로 표시한다. 알림만 실패한 변형은 ticket을 유지하고 reason=alerts_down으로 표시하며 새 티켓을 만들지 않는다.

```json
{"request_id":"ui-handoff-001","route":"담당자 이관","answer":"IT팀에 문의를 접수했습니다.","sources":[],"ticket":{"ticket_id":"T-2001","priority":"high","duplicate":false},"agents":["triage"],"security":{"blocked_by":"","reason":"","masked":0},"reason":"urgent"}
```

M04 이관 중 티켓 장애 · HTTP200 · S07:

```json
{"request_id":"ui-failure-001","route":"담당자 이관","answer":"티켓 접수 상태를 확인할 수 없습니다.","sources":[],"ticket":null,"agents":["triage"],"security":{"blocked_by":"","reason":"","masked":0},"reason":"tickets_down"}
```

M05 권한 없음 / M06 차단 · HTTP200 · S08~09:

```json
{"request_id":"ui-denied-001","route":"권한 없음","answer":"이 자료를 조회할 권한이 없습니다.","sources":[],"ticket":null,"agents":["triage"],"security":{"blocked_by":"","reason":"forbidden","masked":0}}
```

```json
{"request_id":"ui-block-001","route":"차단","answer":"허용되지 않은 요청입니다.","sources":[],"ticket":null,"agents":[],"security":{"blocked_by":"rule","reason":"prompt_injection","masked":0}}
```

M07 오류 · HTTP403 · S13,S16:

```json
{"error":{"code":"forbidden","message":"접근 권한이 없습니다."}}
```

M08 빈 목록 HTTP200은 `{"items":[]}`. HTTP400 공통 웹훅 오류는 codes를 포함한 원본 형식을 유지하고 백엔드가 제공하는 예시를 그대로 사용한다. 로그인 Mock user는 id=1/name=김민지/dept=IT팀/role=admin/must_change_password=true로 두되 최상위 포장은 H02 제안으로 표시한다. 비어 있지 않은 목록 Mock은 H02 화면 모델과 실제 계약 어댑터를 분리한다.

## FE-06 · 실제 연결과 측정

S17은 Mock을 끄고 직원 로그인→질문→보완 또는 답·이관→내 문의, 관리자 로그인→티켓 변경→직원 재조회·알림을 확인한다. 환경·API 주소 종류(로컬/VM, 비밀값 제외)·기준 커밋·실제 응답·request_id·시나리오별 결과를 남긴다. Mock을 통합 결과로 집계하지 않는다.

- 처리시간: 원민님의 공통 시나리오/bench와 질문·환경·SERVICE_MODE를 맞춘다. 브라우저 전송 직전부터 파싱 후 결과 렌더링까지 ms를 측정하고 서버 timings는 별도 열로 기록한다. 최초/재시도/캐시를 구분한다. 동일 조건 5회 이내 원자료·표본 수·중앙값·최댓값을 남긴다. 작은 표본 p95를 일반 성능 보장으로 쓰지 않는다. LLM 반복은 팀 3회 기록을 재사용하고 중복 대량 호출하지 않는다. 공통 max_seconds는 유지, 없는 화면 목표는 실측 후 변경 절차로 반영한다.
- 검색 품질: 유빈님·원민님이 권한별 질문과 기대 doc/section을 먼저 정의한 결과를 제공한다. 수언님은 화면 sources와 응답의 일치, 자동 답변 sources 누락·권한 없는 출처 노출 건수를 확인한다. 기대 근거가 top_k=3에 있는 질문 수/평가 질문 수와 자동 답변 중 근거 누락 수를 원자료에 연결한다. 점수 임계값은 실측·공통 반영 전에 고정하지 않는다.
- 구현 후 증거는 `evidence/S17-*.png`, `Doc/SUBMISSION-NOTES.md`에 기대·실제·측정 원자료 경로·미해결 사항과 함께 기록한다. 비밀번호·쿠키·연락처는 캡처하지 않는다. 현재 측정·증거 파일은 없다.

## 참고

[협업](../../../docs/COORDINATION.md) · [팀 헌장](../../../docs/TEAM-CHARTER.md) · [주제](../../../docs/TOPIC.md) · [아키텍처](../../../docs/ARCHITECTURE.md) · [시나리오·평가 가이드](../../../docs/EVALUATION-GUIDE.md).
