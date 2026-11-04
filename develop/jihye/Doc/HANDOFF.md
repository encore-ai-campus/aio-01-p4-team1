# 지혜님 · 변경 제안·전달 기록

[README](../README.md) → [TODO](TODO.md) → [SPEC](SPEC.md) → [IMP-PLAN](IMP-PLAN.md)을 기준으로 바로 개발한다. 이 파일은 **공통 기준의 누락 정책/변경 제안**만 기록한다. 기존 기준을 적용하기 위한 사전 승인 목록이 아니다.

작성일: 2026-11-03. 아래 제안은 문서에 기록한 상태다. 외부 메시지 전송·상대 검토·동의·공통 반영·실연결을 수행하지 않았다. 상대는 자기 HANDOFF에 확인을 남기고 공통 문서는 오현님이 반영한다. 답변 없음은 채택이 아니다. 다른 역할 문서의 미검토400/409·assignee 식별값 등도 채택하지 않는다.

## 연결과 상태

| 연결 | 검토 상대 | 상태 |
| --- | --- | --- |
| C01 | 수언님·오현님 | H01·03·05 핵심(세션 쿠키·관리자 목록·assignee=employees.id·최후 관리자 보호) 공통 반영 완료, H02 세부 제안 유지·실연결 미실행 |
| C02 | 다혁님·오현님 | H04 및 H03 support 세부 형식 제안, 실연결 미실행 |
| C05 | 원민님·오현님 | H06(`POST /dlq`, `alerts.event_key`) 공통 반영 완료, H03 세부 오류 제안·실연결 미실행 |
| C06 | 유빈님 | 기본 app/rag·모델3072·cosine/top_k3 적용, 변경 제안 없음·실연결 미확인 |
| C07 | 오현님·영향받는 담당 | 기본 서비스명/포트/`BACKEND_ORIGIN` 공통 반영 완료, 실제 설치/기동 미실행 |

아래 ‘H01’ 표기는 JH-H01의 축약이다. 제안과 무관한 P0 골격·기본 모델·공통 스키마·Mock 작업은 계속한다. 정책에 의존하는 외부 응답/추가 DB 변경은 공통 반영 전 확정 구현·배포로 취급하지 않는다.

## JH-H01 · 세션·쿠키·첫 변경 제한

- 연결/요구: C01·C07 / BE-01·05. 상태: **제안, 미채택**.
- 기존: API 2·8절은 HttpOnly 세션·첫 암호 변경·로그아웃을 정했지만 쿠키 이름/기간/SameSite/Secure·회수 범위·첫 변경 전 허용 API가 없다.
- 제안: 쿠키 이름 `oke_session`, Path=/api, HttpOnly, SameSite=Lax, 운영 HTTPS에서 Secure=true·로컬 HTTP에서만 false. 절대 만료8시간으로 시작하며 매 요청 활성 계정/만료/폐기를 검사한다. 로그인 때 새 난수 토큰을 발급하고 DB에는 해시만 둔다. 첫 변경 전 me/change-password/logout만 허용하고 다른 보호 API는403 `password_change_required`로 한다. 암호 변경 후 기존 세션을 모두 폐기하고 현재 브라우저에는 새 세션을 발급한다. 초기화·비활성화는 해당 사용자의 모든 세션을 폐기한다. 상태 변경 요청에는 동일 출처 Origin 검증도 적용하는 안이다.
- 입출력: 웹 error.code/message 외형 유지. 로그아웃 ok=true. 쿠키 발급/삭제 헤더와 first-change403은 수언님 화면에 반영 필요. 외부 Origin/프록시 허용 목록의 실제 주소는 비밀 관리/배포 설정으로 주고 문서에 쓰지 않는다.
- 영향: security/deps/auth·users 서비스·세션 시험, 프론트 credentials/첫 변경 화면, VM HTTPS 프록시. expires_at/revoked_at은 기존 스키마로 수용 가능하다.
- 검토 상대/반영 요청: 수언님·오현님이 API 인증 절에 반영. 상대 확인 근거 없음·반영 커밋 없음·실연결 미실행. 값8시간은 사용자 확정 사항이 아니다.

## JH-H02 · 비밀번호 규정의 웹 적용 범위와 저장 구조

- 연결/요구: C01·C07 / BE-01·05. 상태: **제안, 미채택**.
- 기존: 첫 변경/초기화는 공통에 있지만 users에는 password_hash/must_change_password만 있다. 제공 `password-policy`는12자 이상·문자3종·추측하기 쉬운 단어 금지,90일 변경·최근5개 재사용 금지·5회 실패30분 잠금·회사 밖 OTP를 안내한다. 이를 웹 인증에 어떻게 적용할지와 이력/잠금 저장 구조는 공통에 없다.
- 제안: 생성/초기화/변경 모두 최소12자·대소문자/숫자/특수문자 중3종·알고 있는 본인 이름/회사명 포함 금지를 서버에서 검사한다. 최근5개 해시 이력을 검사하고90일 경과 시 변경 제한 흐름을 적용한다. 연속 실패5회면30분 잠금, 성공 시 실패 횟수를 초기화한다. 원본에 없는 생일/연락처를 새 필수 개인정보로 수집하지 않는다.
- DB 제안: users에 password_changed_at(timestamptz), failed_login_attempts(integer, 기본0), locked_until(timestamptz nullable) 추가; app.user_password_history에 id/user_id/password_hash/created_at 추가. H02 채택 후 다음 별도 revision으로 생성하고 현재 기본 revision에 끼워 넣지 않는다. 최근5개의 범위는 현재 암호 포함5개로 제안한다.
- 추가 범위 요청: 외부 접속 OTP의 웹 필수 적용 여부·수단/복구 경로를 오현님이 명시하도록 요청한다. 현재 문서에서 OTP 제외가 승인됐거나 규정 전체 준수가 완료됐다고 쓰지 않는다. OTP 구현 경로를 이번 문서 작업 범위에 새로 확장하지 않는다.
- 영향: 계정/암호/로그인 서비스·DB 변경·만료/잠금 화면·실패 응답. 로그인 실패/잠금은 동일401 안내로 계정 유무 노출을 줄이는 안이다. 입력 검증 실패400 세부 코드는 H03과 함께 검토한다.
- 검토 상대/반영 요청: 오현님(범위·API/DB 공통 반영), 수언님(화면), 원민님(경계 시험). 확인·채택·DB 변경·시험 모두 미실행. 이력·잠금 구현이 없어도 기존 스키마/seed 작업은 진행한다.

## JH-H03 · C01 세부 모델·HTTP 상태·내부 필드

- 연결/요구: C01·C02·C05 / BE-01~04. 상태: **제안, 미채택**.
- 기존: API 경로와 핵심 필드, 목록 items, 단건 객체, 웹 error 외형, 공통400 codes는 확정이다. current/new 암호의 정확한 키·직원 식별값·assignee 의미·목록 단건 필드·생성 성공 상태·중복/일부 오류코드는 미정이다.
- 제안 요청: change-password 키 current_password/new_password, 관리자 발급 employee_id/login_id/temporary_password(임의 role 입력 없음). 경로 users/{id}·tickets/{id}는 내부 bigint PK, assignee는 IT팀 `app.employees.id` 또는 null로 하고 외부 ticket_id(T-번호)와 구별한다(공통 `API-CONTRACT.md`·`DATA-AND-DB.md` 반영 완료). ticket patch는 status 필수, assignee/reply 생략 시 유지·명시 null 시 해제로 제안한다.
- 제안 응답: SPEC 4절의 AccountView/InquiryView/TicketView/AlertView 필드 목록을 사용한다. 로그인은 user 객체, me는 직접 요약 객체. 웹 생성 계정201, 나머지 웹 성공200. 기존 확정 C05 티켓 신규201/중복200·알림200은 변경하지 않는다. 목록 정렬은 created_at 내림차순·동일 시 id 내림차순으로 제안한다.
- 오류 제안: 웹400 `validation_error`와 필드별 codes(비밀번호 값 제외), 없는 계정404 `not_found`, 중복 employee/login_id409 `account_exists`, 없는 assignee/비IT400 `invalid_assignee`, 없는 외부 알림 ticket_id400 `unknown_ticket`. 추가 입력 필드는400으로 거절하고 context는 최대2000자로 제한하는 안이다. 공통 웹훅400 codes는 변환하지 않는다. 아직 이 세부400/409를 확정 계약으로 쓰지 않는다.
- support 세부 제안: security.blocked_by/reason은 문자열 또는 null, masked는 비음수 정수로 모델화한다. 기존 필드/route 및 추가 reason/timings는 그대로 유지한다. severity/category는 공통이 enum을 정하지 않았으므로 비어 있지 않은 문자열로 검증하고 임의 enum을 추가하지 않는다.
- 영향: Pydantic/OpenAPI, 화면의 ID/담당자 선택·목록 렌더링, 내부 알림 T-번호→PK 매핑, 계약 시험 fixture. 숫자형 id7/8 등은 문서 예시이며 실제 직원 매핑이 아니다.
- 검토 상대/반영 요청: 수언님(C01), 다혁님(C02 security), 원민님(C05), 오현님(API 반영). 기존/제안 차이는 SPEC 3~5절에 초안 표시. 상대 확인·반영·연결 모두 없음.

## JH-H04 · support 시간 제한·장애 응답·키 재사용

- 연결/요구: C01·C02 / BE-02·03·07. 상태: **제안, 미채택**.
- 기존: n8n 장애 때 정해진 안내/마스킹 로그, 같은 논리 요청은 같은 request_id, 타인 키403·입력400은 정해져 있다. 정확한 timeout·웹 장애 상태/코드·실행 중 재시도·같은 키의 본문 변경은 없다.
- 제안: 연결3초·요청 전체30초 제한(읽기 timeout만으로 전체 상한이라 주장하지 않고 전체 deadline 적용), FastAPI의 support 자동 재시도0회로 시작한다. n8n 내부 재시도와 중첩되지 않게 한다. 전체 예산은 실제 지연/하위 최악시간 측정 후 다혁님과 재검토한다. 숫자는 응답시간 달성 결과가 아니다.
- 제안 출력: 전체 시간 초과504 `support_timeout`, 연결/서비스 장애503 `support_unavailable`, 형식/ID 불일치502 `invalid_support_response`, 안내는 재시도/문의 확인을 요청한다. 성공200·담당자 이관으로 위장하거나 ticket을 꾸미지 않는다. 오류에도 생성 request_id를 error.request_id로 반환하도록 웹 외형의 선택 필드 추가를 제안한다. 공통 웹훅400 본문은 그대로 유지한다.
- 키 처리 제안: 소유권을 먼저 확인한 뒤 같은 key의 question/attempt/context가 다르면409 `request_conflict`, 이미 처리 중이면409 `request_in_progress`, 완료면 저장된 공통 응답 반환. inquiries.status는 pending/processing/succeeded/failed로 시작하고 원자적 상태 변경으로 단일 호출을 보장한다. 실패 재시도는 동일 소유자/동일 입력만 허용하며 티켓은 C05 UNIQUE로 중복을 방지한다.
- 복구 제안: 프로세스 중단으로 processing이 남으면 실제 n8n 결과·티켓 상태를 운영자가 확인한 뒤 재시도 가능 상태로 전환한다. 임의 시간 경과만으로 진행 중 호출을 다시 생성하지 않는다. 이 복구 동작/운영 인터페이스는 채택 전 확정 구현하지 않는다.
- 영향: HTTPX deadline/취소·문의 상태 거래·웹 재시도/안내·오류 모델/동시성 시험. 기존401/403을 retry하지 않는다. 데이터가 없는 오류를 정상 결과로 저장하지 않는다.
- 검토 상대/반영 요청: 다혁님(하위 timeout/재시도), 수언님(웹 오류/재시도), 원민님(중복/장애 시험), 오현님(공통 API 반영). 모두 미확인. 기본 입력/소유권/공통 응답 Mock 작업은 계속한다.

## JH-H05 · 최초 관리자 재실행·최후 관리자 안전장치

- 연결/요구: C01·C07 / BE-01·05. 상태: **제안, 미채택**.
- 기존: 첫 관리자1회·IT팀만 admin·나머지 관리자 발급은 정해져 있다. 첫 IT팀 인물/로그인 ID를 고정하는 정책, 비활성 관리자를 이용한 bootstrap 재생성/최후 관리자 차단은 없다.
- 제안: bootstrap CLI에서 제공 IT팀 이름과 login_id를 명시하고 특정 인물/ID를 공통 고정값으로 만들지 않는다. 관리자 계정이 있으면 활성 여부와 무관하게 생성하지 않고 기존 hash/role을 유지한다. 계정이 존재하는데 관리자가 전혀 없으면 자동 복구 생성을 거절하고 오현님 관리 절차로 넘긴다.
- 관리자 보호 제안: 마지막 활성 admin 비활성화는409 `last_admin_required`, 자기 계정 비활성화는409 `self_deactivation_forbidden`. 동시 두 관리자 변경도 거래/잠금으로 검사해 활성 관리자0명이 되지 않게 한다. 새로운 관리자 자동 추가로 우회하지 않는다.
- 영향: bootstrap CLI·관리자 활성 변경 거래·화면 오류. 신규 테이블 필요 없음. 기존 데이터/비밀번호를 덮어쓰지 않는 기본 재실행 동작은 그대로 진행한다.
- 검토 상대/반영 요청: 오현님(계정 운영·API), 수언님(버튼/오류), 원민님(동시 변경). 미검토·미반영·시험 미실행. 409 등은 제안 상태다.

## JH-H06 · app 모드 DLQ 쓰기 계약 반영

- 연결/요구: C05·C07 / BE-04·05. 상태: **공통 문서 반영 완료(실연결 미실행)**.
- 반영 내용: `docs/API-CONTRACT.md` 5절과 `docs/DATA-AND-DB.md` 3절에 X-Api-Key 인증 `POST /dlq`(`request_id`, `workflow`, `node`, `reason`, `safe_payload`, `execution_ref`) 및 `POST /alerts` 선택 `event_key`가 반영되었다.
- 영향: backend 라우터/모델·저장 서비스와 원민님 워크플로우 호출부·관측/시험에서 공통 스키마를 사용한다. 동일 실패를 두 저장소에 동시에 쓰지 않는다.
- 검토 상대/반영 요청: 원민님(입력/중복/재처리·실제 관측), 오현님(API C05/모드 반영 완료). 실제 연결은 미실행 상태다.

## 후속 기록과 버그 전달

상대 확인이 오면 요청ID·상대 HANDOFF 링크·검토 내용·오현님 공통 반영 커밋/절·관련 SPEC/계획 변경·실제 연결 입력/출력/증거를 구분해 덧붙인다. 현재 전 항목에 확인 근거와 반영 커밋은 없다.

실제 버그는 실행 위치/버전·마스킹한 재현 입력·기대/실제 결과·로그·영향을 전달한다. 상대 파일을 대신 수정하지 않는다. 절차는 [COORDINATION](../../../docs/COORDINATION.md), 기준은 [API](../../../docs/API-CONTRACT.md)·[DB](../../../docs/DATA-AND-DB.md)를 따른다.
