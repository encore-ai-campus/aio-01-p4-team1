# 오케퐁 API 연결 계약 · 기존 기준과 v0 상세안

> 상태: 개발용 초안. n8n 공통 웹훅의 필드·route는 강사 자료를 따른다. FastAPI·하위 연결 상세 기본안은 BASELINE-v0.md에서 팀장 검토·배포용으로 준비했고 실제 코드·설계서와 일치시킨다.

## 연결 원칙

`Next.js → FastAPI → n8n(oke-support) → FastAPI(/tickets·/alerts) → PostgreSQL`

- 브라우저는 DB와 n8n을 직접 호출하지 않는다.
- 웹 문의의 직원 신원은 FastAPI 로그인 세션에서 얻는다. 질문 본문의 이름이나 권한 주장을 믿지 않는다.
- 수업 공통 시험은 `POST /webhook/oke-support`를 직접 호출한다. 시험용 문의 처리 본체를 복제하지 않는다.
- 비밀값은 환경변수·n8n Credential에 둔다. 요청·응답·로그에 비밀번호와 API 키를 넣지 않는다.

## 1. n8n 공통 웹훅 · 강사 계약

`POST /webhook/oke-support` 요청 필수: `request_id`, `user`, `question`. 선택: `channel`, `attempt`, `context`.

```json
{"request_id":"req-001","user":"박서연","channel":"web","question":"VPN이 계속 끊겨요","attempt":1}
```

응답은 `request_id`, `route`, `answer`, `sources`, `ticket`, `agents`, `security`를 포함한다. `route`는 `자동 답변`·`보완 질문`·`담당자 이관`·`권한 없음`·`차단` 중 하나다. 빈 질문·없는 직원·너무 긴 질문은 공통 계약의 HTTP 400과 `codes`를 따른다. 각 필드의 상세 형식은 강사 `04-REFERENCE-ARCHITECTURE.md` 3절을 기준으로 고정한다.

## 2. 화면이 부르는 FastAPI

| API | 요청 | 응답 | 권한 |
| --- | --- | --- | --- |
| `POST /api/auth/login` | `login_id`, `password` | 계정 요약·첫 비밀번호 변경 필요 여부 + 세션 쿠키 | 공개 |
| `POST /api/auth/logout` | 세션 쿠키 | 로그아웃 확인 | 로그인 |
| `GET /api/auth/me` | 세션 쿠키 | `id`, `name`, `dept`, `role` | 로그인 |
| `POST /api/auth/change-password` | 현재·새 비밀번호 | 변경 확인 | 로그인 |
| `POST /api/ask` | `question`, 선택 `request_id`, `attempt`, `context` | `request_id`, `route`, `answer`, `sources`, `ticket` | 로그인 |
| `GET /api/my-requests` | 세션 쿠키 | 본인의 문의·답변·티켓 상태 목록 | 로그인 |
| `GET /api/admin/tickets` | 세션 쿠키 | 이관 티켓·긴급도·담당자·상태 목록 | IT팀 관리자 |
| `PATCH /api/admin/tickets/{id}` | `status`, 선택 `assignee`, `reply` | 변경된 티켓 | IT팀 관리자 |
| `POST /api/admin/users` | 제공 직원의 식별값, 로그인 ID, 임시 비밀번호 | 생성된 계정 요약 | IT팀 관리자 |

`POST /api/ask`에서 `request_id`가 없으면 FastAPI가 생성하고 로그인한 `user`를 넣어 n8n에 보낸다. 동일 요청 재시도에는 앞서 받은 `request_id`를 다시 보낸다. 첫 관리자 계정은 환경변수로 최초 1회 생성하고, 관리자가 나머지 계정을 발급한다. 공개 회원가입은 없다.

## 3. n8n이 부르는 FastAPI

| API | 요청 핵심 값 | 응답 핵심 값 | 저장 |
| --- | --- | --- | --- |
| `POST /tickets` | `key`(=`request_id`), `title`, `requester`, `category`, `priority` | `ticket_id`, `duplicate` | PostgreSQL 티켓 |
| `POST /alerts` | `workflow`, `node`, `message`, `severity`, 선택 `ticket_id` | `stored`, `count` | PostgreSQL 알림 |

중복 `key`는 새 티켓을 만들지 않고 기존 티켓을 반환한다. n8n 내부 호출은 별도 인증을 적용한다. 수업 data-api의 직원·기존 티켓·규정 조회는 제공된 계약을 사용한다.

## 4. 공통 오류 원칙

| 상황 | 처리 |
| --- | --- |
| 잘못된 입력 | HTTP 400, 필드별 오류 코드 |
| 로그인하지 않음·로그인 실패 | HTTP 401 |
| 다른 직원의 문의·관리자 API 접근 | HTTP 403, 데이터 노출 없음 |
| 없는 티켓 | HTTP 404 |
| n8n 시간 초과·장애 | 화면에 정해진 안내, 서버에는 개인정보를 가린 오류 기록 |

세션은 브라우저 스크립트가 읽지 못하는 쿠키로 관리한다. 새 정책이 기준에 빠져 있으면 백엔드 담당이 기존 password-policy와 호환되는 안을 오현님에게 제안한다. 전체 구현 시작을 막는 반복 협의로 취급하지 않는다.

## 5. 하위 연결 · 변경 책임

| 연결 | 작성할 필드·상태 | 공동 작성자 | 상태 |
| --- | --- | --- | --- |
| support → search | query·직원 권한 등 검색 입력, evidence의 doc·section·text·score, 빈 목록과 장애 구분 | 문의·RAG | C03 기본안 적용, 변경 시 협의 |
| support → handoff | request_id·requester·title·category·priority, ticket·duplicate·실패 사유 | 문의·안정성 | C04 기본안 적용, 변경 시 협의 |
| handoff → FastAPI | /tickets·/alerts와 내부 인증·중복·오류 상태 | 안정성·백엔드 | C05 수업 호환안 적용 |
| 화면 → 계정·알림 관리 | 비활성화·초기화·관리자 알림 조회 | 화면·백엔드 | C01 추가 경로 기본안 적용 |

각 연결에 정상·빈 결과·권한·시간 초과·서버 오류 예시를 작성하고 합의한 날짜를 남긴다. 본체와 하위 워크플로우 호출에도 Header Auth와 시간 제한을 둔다. 공통 웹훅 필드는 교사 계약을 유지한다.

data-api의 fault/reset/ops가 적용되는 공통 시험 설정과 FastAPI로 티켓·알림을 저장하는 통합 설정을 구별한다. 같은 support를 사용하며, 호출 대상 전환과 관측 위치는 안정성·백엔드 담당이 함께 정한다. 공통 시험의 기대값을 바꿔 맞추지 않는다.

변경 순서: 담당자 제안 → 연결 상대 검토 → 리드 승인 → 이 문서와 관련 역할 SPEC 갱신. 역할별 문서 위치와 공통 연결 단계는 [DEVELOPMENT-FLOW](DEVELOPMENT-FLOW.md)를 따른다.

## 계약 문서의 편집 담당

이 공통 문서는 오현님만 편집한다. C01~C07 담당자는 자기 Doc/HANDOFF.md에서 정상·오류 예시를 제안하고 상대 확인 기록을 전달한다. 오현님이 기준을 반영한 뒤 각자 자기 SPEC·코드만 수정한다. 상세 연결 책임·절차는 [COORDINATION](COORDINATION.md)을 따른다. 아직 JSON 세부안이 미정인 연결은 합의 완료로 취급하지 않는다.

## 팀장 기본안으로 시작하기

초기 JSON·추가 API·서비스 기본값은 [BASELINE-v0](BASELINE-v0.md), 제공 데이터와 업무/벡터 테이블 제안은 [DATA-AND-DB](DATA-AND-DB.md)에 정리했다. 새 값은 팀장 검토·배포용이며 수업에서 이미 제공한 값과 구분한다. 배포 기준 그대로 구현하는 데 사전 재협의는 필요 없다. 변경할 때만 COORDINATION의 상대에게 요청한다.

수업 호환 /tickets 응답은 ticket_id·duplicate이며 priority는 handoff가 입력에서 붙인다. /alerts는 확인한 78일차 서버 기준 HTTP200 stored·count다. 위 요약표의 priority·alert_id는 가정으로 의존하지 않고 실제 호환 계약을 따른다.
