# 수언님 · 구현 계획

[README](../README.md) → [TODO](TODO.md) → [SPEC](SPEC.md) → **IMP-PLAN**. 기준대로 바로 시작하고 변경 필요분만 [HANDOFF](HANDOFF.md)에 기록한다. 아래 파일·명령·확인 결과물은 전부 **구현 예정·미실행**이다.

## 실행 위치와 확인 명령의 전제

향후 모든 프론트 명령의 workdir는 저장소 루트 기준 `develop/sueon`이다. 다른 폴더·공통 설정을 고치지 않는다. 현재 package.json·스크립트·테스트·lockfile이 없으므로 아래 명령은 지금 실행할 수 있는 명령이 아니다.

P0-1에서 Node/npm 환경과 Next.js·React의 공식 호환 조건을 확인해 TypeScript/App Router 프로젝트를 이 폴더에 구성한다. create-next-app을 사용하면 기존 Markdown·AGENTS를 덮어쓰지 않도록 생성 목록을 먼저 확인한다. 자동 생성이 기존 파일 때문에 실패하면 자기 폴더 안의 필요한 설정 파일만 직접 구성하며 README/Doc를 이동·삭제하지 않는다. 버전은 설치 검증 후 package.json·lockfile과 README에 실제 값으로 기록한다. Next.js 버전별로 달라지는 설정 파일 확장자는 설치한 버전 기준으로 확인한다.

예정 npm 스크립트는 dev=`next dev --port 3000`, build=`next build`, typecheck=`tsc --noEmit`, test=선정한 시험 도구의 비대화식 실행, test:e2e=선정한 브라우저 시험 실행이다. 테스트 도구·버전·정확한 명령은 P0-2에서 검증한다. `next lint`가 있다고 가정하지 않는다. 서버 시작과 외부 호출은 향후 실제 구현 확인 단계의 작업이며 이번에는 하지 않는다.

## P0-1 · 가장 먼저 실행 골격 만들기

- [ ] 연결 SPEC: FE-05, FE-06.
- 생성 예정: `package.json`, 검증된 패키지 관리자의 lockfile(여기서는 `package-lock.json` 예정), `tsconfig.json`, `next-env.d.ts`, `next.config.ts`(지원 여부 검증 후), `.gitignore`, `src/app/layout.tsx`, `src/app/page.tsx`, `src/app/globals.css`.
- 작업: 기본 화면에는 서비스명·다음 로그인 경로 안내만 둔다. 아직 없는 API를 호출해 성공으로 가정하지 않는다. 자기 `.gitignore`에 node_modules·빌드 산출물·실제 환경파일을 제외하고 루트 설정은 수정하지 않는다. npm scripts와 실제 설치 명령·도구 버전을 README에 기록한다.
- 확인 예정: `node --version`, `npm --version`으로 환경 기록, 실제 설치 후 `npm run typecheck`, `npm run build`. 생성 목록과 workdir가 자기 폴더인지 확인한다. 이 단계에서는 backend·n8n·DB가 필요 없다.
- 다음 단계에 넘길 결과: 같은 폴더에서 재현 가능한 설치/빌드 명령, 실제 버전, 골격 파일 목록. 실패하면 오류·미완료를 기록하고 완료 체크하지 않는다.
- 현재 결과: 미구현·미실행.

## P0-2 · 계약 어댑터·Mock·로그인

- [ ] 연결 SPEC: FE-01, FE-05, FE-06 / S01~03,S16.
- 생성 예정: `src/lib/api/types.ts`, `src/lib/api/client.ts`, `src/lib/api/auth.ts`, `src/lib/api/errors.ts`, `src/lib/session.tsx`, `src/mocks/fixtures.ts`, `src/mocks/transport.ts`, `src/components/AppShell.tsx`, `src/components/Feedback.tsx`, `src/components/SessionGate.tsx`, `src/app/login/page.tsx`, `src/app/(protected)/layout.tsx`, `src/app/(protected)/change-password/page.tsx`.
- 시험 파일 예정: `tests/auth.test.ts`, `tests/api-client.test.ts`, 시험 도구 설정(선정 후 `vitest.config.ts` 등), package.json의 검증된 test 스크립트. 도구 버전을 검증 없이 고정하지 않는다.
- 작업: 전송 계층과 화면 모델을 분리한다. 실제 전송은 상대 /api 경로·쿠키 포함 호출, Mock은 동일 함수 인터페이스와 상태 코드를 반환한다. H02/H03 미확정 필드는 Mock용 타입에 제안임을 적고 실제 어댑터와 섞지 않는다. Mock 전환은 개발/시험 전용 주입으로 하고 일반 사용자에게 운영 중 Mock 성공을 제공하지 않는다. Mock 상태 선택은 시험 fixture/test에서 수행하고 별도 안내 페이지를 만들지 않는다.
- 작업: 로그인·로그아웃·비밀번호 확인·역할별 메뉴·401/403을 연결한다. 루트 page.tsx는 세션 확인 후 SPEC 경로로 이동하도록 수정한다. 비밀번호를 fixture 원문·저장소·출력 로그에 넣지 않는다.
- 확인 예정: `npm run typecheck`, `npm run test -- tests/auth.test.ts tests/api-client.test.ts`, `npm run build`(선정 도구가 파일 인자를 받는지 먼저 확인). S01~03의 이동·불일치 전송 0회, HTTP 오류 두 형식, 비JSON, 지연과 중복 전송 방지를 검사한다.
- 다음 담당자 지혜님에게 넘길 결과: 로그인·변경 요청 예시(비밀번호 제외), H02/H03 해당 필드 목록, 역할별 화면 기대. API 제공을 기다리는 동안 Mock UI는 계속 진행한다.
- 현재 결과: 미구현·미실행.

## P0-3 · 질문·근거·보완·이관

- [ ] 연결 SPEC: FE-02, FE-05 / S04~09,S16.
- 생성 예정: `src/lib/api/ask.ts`, `src/lib/inquiry-state.ts`, `src/components/AskForm.tsx`, `src/components/AnswerPanel.tsx`, `src/components/SourceList.tsx`, `src/components/TicketSummary.tsx`, `src/app/(protected)/ask/page.tsx`, `tests/inquiry-state.test.ts`, `tests/ask.test.ts`.
- 작업: question·request_id·attempt·context와 전송 상태를 한 곳에서 관리한다. M01~M07을 Mock transport에 연결한다. 보완 새 ID·재시도 동일 ID를 구현한다. sources=[] 자동 답변·미정 route·필수 필드 누락은 확인 오류로 처리한다. ticket=null은 접수 완료로 쓰지 않는다.
- 확인 예정: `npm run test -- tests/inquiry-state.test.ts tests/ask.test.ts`, `npm run typecheck`, `npm run build`. 백엔드 없이 M01 정상→M02 보완→M03 이관, M04 티켓 장애, M05 권한 없음, M06 차단을 확인한다. 공백/1/500/501자, attempt 1→2→3, 연타, timeout 뒤 동일 ID를 비교한다. Mock 연속 응답은 실제 서버의 판단 성공으로 기록하지 않는다.
- 다음 담당자 지혜님·원민님에게 넘길 결과: S04~09 입력·기대 route·UI 오류 처리, 동일 ID 재시도 관찰 기준. 다혁님 워크플로우를 대신 고치지 않는다.
- 현재 결과: 미구현·미실행.

## P0-4 · 내 문의

- [ ] 연결 SPEC: FE-03, FE-05 / S10~11.
- 생성 예정: `src/lib/api/requests.ts`, `src/lib/ticket-labels.ts`, `src/components/RequestList.tsx`, `src/app/(protected)/my-requests/page.tsx`, `tests/my-requests.test.ts`.
- 작업: items 형식을 읽고 로딩/빈 목록/오류를 구별한다. 목록 응답으로 행을 펼친다. 새 웹 티켓 status만 매핑하고 기존 상태는 유지한다. Mock 두 직원의 결과를 분리하고 세션 교체 때 이전 화면 상태를 지운다.
- 확인 예정: `npm run test -- tests/my-requests.test.ts`, `npm run typecheck`, `npm run build`. 빈 items, 이관 실패, 복수 문의, 세션 변경, 조회 오류를 확인한다. 타인 데이터 차단의 실제 서버 증명은 P1-3까지 미확인이다.
- 다음 담당자 지혜님에게 넘길 결과: H02 목록 어댑터 요구와 S10~11 기대·Mock 예시.
- 현재 결과: 미구현·미실행.

## P0-5 · 관리자 티켓

- [ ] 연결 SPEC: FE-04T, FE-05 / S12~13.
- 생성 예정: `src/components/AdminGate.tsx`, `src/app/(protected)/admin/layout.tsx`, `src/lib/api/admin-tickets.ts`, `src/components/TicketEditor.tsx`, `src/app/(protected)/admin/tickets/page.tsx`, `tests/admin-tickets.test.ts`.
- 작업: 관리자 메뉴·직접 URL 안내, 목록 행 편집·status/assignee/reply 저장. ticket_id와 경로 id를 분리하고 오류 때 편집값을 유지한다. 성공 객체와 재조회로 저장 상태를 확인한다. assignee는 IT팀 `app.employees.id` 정수 또는 `null`로 처리한다.
- 확인 예정: `npm run test -- tests/admin-tickets.test.ts`, `npm run typecheck`, `npm run build`. Mock 접수→처리 중→완료, 담당자/답변, 400/403/404·저장 실패, 직원 관리자 URL을 확인한다. 메뉴 차단만으로 서버 권한 통과라고 쓰지 않는다.
- 다음 담당자 지혜님·원민님에게 넘길 결과: PATCH 요청·표시 매핑·S12~13 권한/저장 확인 절차.
- 현재 결과: 미구현·미실행.

## P0-6 · 관리자 계정·알림

- [ ] 연결 SPEC: FE-04U, FE-04A, FE-05 / S14~15.
- 생성 예정: `src/lib/api/admin-users.ts`, `src/lib/api/admin-alerts.ts`, `src/components/UserEditor.tsx`, `src/components/AlertList.tsx`, `src/app/(protected)/admin/users/page.tsx`, `src/app/(protected)/admin/alerts/page.tsx`, `tests/admin-users.test.ts`, `tests/admin-alerts.test.ts`.
- 작업: `GET /api/admin/employees`, `GET /api/admin/users` 및 기존 POST/PATCH/reset 경로와 알림 GET을 적용한다. 발급 성공 후 비밀번호 입력을 지운다. 비활성화/초기화 대상 확인과 실패 안내를 둔다. 백엔드 미기동 시에는 계약 Mock으로 진행한다. 알림 ticket_id=null도 유지하며 확인/삭제 API를 만들지 않는다.
- 확인 예정: `npm run test -- tests/admin-users.test.ts tests/admin-alerts.test.ts`, `npm run typecheck`, `npm run build`. 발급·중복 오류·비활성화·초기화·빈 알림·긴급 알림·티켓 없음·403을 확인한다. 비밀번호가 결과/로그에 남지 않는지 확인한다.
- 다음 담당자 지혜님·오현님에게 넘길 결과: H01~03 반영 필요 목록, 기존 API로 가능한 범위와 Mock에 남은 부분, S14~15 기대.
- 현재 결과: 미구현·미실행.

## P1-1 · 실제 프록시·로그인 연결

- [ ] 연결 SPEC: FE-01, FE-05, FE-06 / S01~03,S16.
- 수정 예정: `next.config.ts`(설치 버전 기준), `src/lib/api/client.ts`, `src/lib/api/auth.ts`, `src/lib/session.tsx`, `README.md`. 생성 예정: `.env.example`(확정된 이름만, 값 없음). Dockerfile 필요 시 `Dockerfile`, `.dockerignore`를 자기 폴더에만 생성한다.
- 작업: 공통 C07대로 브라우저 상대 /api를 프론트 서버에서 FastAPI로 프록시한다. 서버 전용 `BACKEND_ORIGIN`으로 로컬 backend(`http://127.0.0.1:8000`)와 컨테이너(`http://backend:8000`)를 구별한다. 키나 backend 내부 주소를 NEXT_PUBLIC 변수로 노출하지 않는다. Compose 파일은 지혜님 소유로 읽기만 한다.
- 전제: 지혜님 실제 FastAPI 인증 API와 안전하게 발급된 시험 계정. H02/H03 반영분 또는 실제 OpenAPI 응답을 어댑터에 적용한다. 미반영 부분은 연결 미완료로 남긴다.
- 확인 예정: P0 검사를 다시 실행한 뒤 향후 담당자가 `npm run dev`로 프론트만 실행해 localhost:3000 로그인·변경·로그아웃·새로고침·401/403을 확인한다. DevTools에서 요청 경로·쿠키 속성만 확인하고 비밀번호·쿠키 원문을 캡처하지 않는다. 실제 확인 명령·버전은 README에 갱신한다.
- 다음 담당자 지혜님·오현님에게 넘길 결과: 프록시 설정 경로·검증된 실행 명령·Mock 잔여 목록. C07을 바꾸지 않는 부분은 사전 협의 없이 진행한다.
- 현재 결과: 미구현·미실행.

## P1-2 · 실제 질문·목록·관리 연결

- [ ] 연결 SPEC: FE-02~04, FE-05 / S04~15.
- 수정 예정: `src/lib/api/types.ts`, 각 `src/lib/api/*.ts`, 각 페이지의 연결부. 시험 응답은 `tests/`의 마스킹된 fixture로 보완하며 `src/mocks/`의 시험용 응답과 구별한다.
- 전제: 실제 ask/my-requests/admin API, 계정·권한, 지혜님 DB 저장과 n8n 연결 준비. 제공자 준비 여부를 공통 기준 재협의와 혼동하지 않는다.
- 확인 예정: 검증된 단위 검사와 build 후 직원 질문→보완/답/이관→내 문의, 관리자 목록→담당자·답변·상태 변경→직원 재조회. 계정 발급→최초 변경, 비활성화·초기화와 긴급 알림을 확인한다. 각 미준비 API는 Mock임을 명시하고 실제 성공으로 집계하지 않는다.
- 다음 담당자 지혜님·원민님에게 넘길 결과: 요청 ID·기대/실제·실패 재현·연결한 API·Mock 잔여 목록. 상대 코드는 수정하지 않는다.
- 현재 결과: 미구현·미실행.

## P1-3 · 권한·장애·측정·시연 근거

- [ ] 연결 SPEC: FE-01~06 / S01~17.
- 생성 예정: `tests/e2e/helpdesk.spec.ts`, 검증된 브라우저 시험 설정(예: `playwright.config.ts`), `evidence/`의 마스킹된 캡처, `Doc/SUBMISSION-NOTES.md`. test:e2e 스크립트는 실제 도구 확인 후 등록한다.
- 확인 예정: `npm run typecheck`, `npm run test`, `npm run build`, `npm run test:e2e`. backend가 필요한 검사는 전제·계정 준비를 명시한다. 직원/관리자·다른 직원·401·403·없는 티켓·지연·티켓 장애·중복 재시도·비JSON을 SPEC대로 확인한다. FastAPI의 실제 권한·소유권 차단은 지혜님·원민님 근거와 연결한다.
- 측정 예정: SPEC FE-06대로 환경·조건·원자료·표본 수·실제 시간·sources 일치를 기록한다. 공통 고장 시험은 원민님이 실제 호출 모드/관측 대상 일치를 확인한 결과를 받는다. 수언님이 다른 담당자의 fault/reset·n8n push/test를 대신 실행하지 않는다.
- 오현님에게 넘길 결과: FE/S ID별 기대·실제·근거 경로, 실패→조치→동일 조건 재확인, 버전·기준 커밋·Mock/실제 구분, 남은 변경 제안. 실행하지 못한 항목은 이유와 함께 미실행으로 유지한다.
- 현재 결과: 미구현·미실행.

## 기록 방법

각 단계 완료 후 이 문서의 해당 단계에 실행일·실제 명령·종료 상태·시나리오별 기대/실제·Mock 여부·근거 파일·남은 문제를 적는다. 성공 근거가 있을 때만 체크한다. 설치·시험 실패를 완료로 바꾸거나 예시를 실제 응답으로 쓰지 않는다. 일반 PR은 자기 폴더만 포함하고 검토·최종 반영은 상위 담당자가 한다.

## 공통 자료

[주제](../../../docs/TOPIC.md) · [공통 API](../../../docs/API-CONTRACT.md) · [데이터·DB](../../../docs/DATA-AND-DB.md) · [아키텍처](../../../docs/ARCHITECTURE.md) · [시나리오·평가 가이드](../../../docs/EVALUATION-GUIDE.md) · [팀 헌장](../../../docs/TEAM-CHARTER.md) · [협업](../../../docs/COORDINATION.md).
