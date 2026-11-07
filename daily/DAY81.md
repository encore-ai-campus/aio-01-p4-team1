# DAY 81 · 2026-11-06 · 1팀 오케퐁 교시별 진행 보고

> 작성 기준: 2026-11-06 16:55 KST (7교시 종료 후 최종 QA·DB 증거 반영; 교시 통과로 소급하지 않음). 공식 1팀 체크리스트의 시간·파악·통과 기준에 맞춰 1~6교시 완료 결과와 7~8교시 누적 양식을 기록한다. 교시 뒤 확보한 근거는 그 교시의 통과로 소급하지 않는다. 본 보고의 Git 문서 커밋과 VM 실행 버전은 별도다.

## 오늘 목표와 현재 판정

오늘은 실제 VM 배포본에서 검색·정상 응답·안전 이관·저장을 구분해 확인하고, 고정 공통 시나리오와 보안·장애 회귀의 근거를 축적한다. **1교시 스탠드업 및 VM 출발점 점검 완료, 2교시 WF-01 정상 자동답변은 미입증(최종 sources=[]; 규정 부재로 원인을 단정하지 않음), 3교시 WF-03 무근거 안전 이관(T-2005 발행 및 DB 1:1 저장) VM 실측 통과, 4교시 중간점검 및 VM 배포 1(FE 가드 패치 3ff836a, 팀 공용 계정 공개 cfab1cc) 완료, 5교시 보안·권한(다혁 15번 본체 aedbb95 긴급 보안사고/주입차단/마스킹, 수언 Vite 디자인 Next 이식 67ef41b, 지혜 타인 조회 403 WF-06) 완료, 6교시 장애/멱등성 검증(WF-04/09 로컬/Mock 회귀) 및 WF-02b(보완 한도 도달 안전 이관, T-2011, 4.535초, 10 checks PASS) 공개 VM E2E 실측 통과(90fab63)를 완료했다. 7교시 배포 2는 VM repo `17007f1`, FE `bb3ef06`(디자인 `840c5e6`), 본체 15번 published `d0d6396d…` 활성으로 반영됐다. 키 불일치로 첫 6건이 403이었고 실제 키로 재시험한 6건은 기대 status/route/code가 일치했다. trace 등 미관측이 남아 부분 확인이며 공통 14유형·팀 5종 전체 회귀 완료는 아니다.** 공개 Swagger 확인은 API 문서 경로 확인 성과로 따로 기록하며 업무 시나리오 통과로 계산하지 않는다.

| 단계 | 공식 요구 | 파악 / 통과 판정 | 잔여와 다음 확인 |
|---|---|---|---|
| 1교시 09:00–09:50 | DAY80 피드백·오늘 목표/담당/다음 시각, main·VM·문서·색인 readiness, VM common-14 출발점, 주제 승인 기록 정합화 | **부분.** 버전·배포·실측 현황과 미실행 경계를 문서화했다. 14개 공식 사례 실행 출발점은 미완료. 승인 상태 문구는 81일차 CHECK가 유지하도록 명시한 80일차 2교시 완료 기록에 맞춰 정합화했다. | 14개 원본·runner·인증 지원 절차와 raw 확보가 필요하다. 정확한 승인 확인자/시각은 미기록이다. 교시 내 피드백 인수자·확인 시각도 근거가 없어 미기록으로 둔다. |
| 2교시 10:00–10:50 | 분류→허용 근거 검색→답변 연결, WF-01 고정 입력 정상 답변/기대 sources/8초, 노드별 입출력 근거 | **부분/필수 결과 미실행.** 기존 C03 검색과 안전 이관/저장은 선행 관측으로 확인되지만, VM의 WF-01 정상 자동 답변·기대 근거·8초·전체 노드 원본을 함께 증명한 새 실행이 없다. | 다혁·원민 등 기존 기능·시험 소유자가 고정 입력으로 배포 workflow와 실제 노드/모델/시간 근거를 남겨야 한다. 오늘 필수 측정의 대체 담당·시간은 미지정이다. |
| 3교시 11:00–11:50 | WF-03 무근거 문의는 sources 빈 목록·사유·실제 이관 티켓. 답변 검증 실패도 안전 경로. 응답 ticket ID와 실제 저장 일치. | **실행 완료 / WF-03 통과.** 11:52 KST VM 배포본 `3ff836a`에서 `request_id=real-qa-36352d26c53e48eab65a42c4a0c5ec85`(attempt 1) 실행: `/api/ask` HTTP 200, route `담당자 이관`, 7.341초, sources `[]`, 티켓 `T-2005`(`in_progress`). 11:52:07 PG read-only query로 `app.inquiries`/`app.tickets` 1:1 일치, 직원 조회 및 관리자 처리 동기화 확인. | 단, sources `[]`이므로 WF-01 정상 자동답변/8초는 미입증으로 분리 유지. 4교시 중간점검 및 5교시 보안/권한으로 연계. |
| 4교시 12:00–12:50 | 중간점검·VM 배포 1, WF-02·02b 보완/이관 한도, WF-11 지연, WF-12 긴급 보안사고, RAG 3~5절 | **중간점검 완료 / 배포 1 완료.** VM 배포본 `3ff836a`(FE 가드 패치) 무중단 배포 및 팀원 공용 테스트 계정(`minji.admin`, `teamtest.employee1`) 공개(`cfab1cc`). 파이프라인 E2E 실저장 뼈대 점검 완료 및 최종 `sources=[]` 안전 이관 관측(규정 부재로 원인을 단정하지 않음). 본체 14번(`b5a15da`) 안전 잠금 반영. | WF-02/12 시나리오 실측은 본체-QA 연계 조율로 5교시 보안/권한 실측과 함께 진행. 기존 규정 8/33 색인·직접 검색과 본체 자동답변 수용 조건 대조 필요. |
| 5교시 14:00–14:50 | 보안·권한·개인정보 (WF-05 제한 문서 격리, WF-06 타인 기록 403, WF-07 PII 마스킹, WF-08 주입 차단, WF-13 오류 400) | **5교시 구현 및 점검 완료.** 본체 15번(`aedbb95`): 보안 키워드 감지 시 high 고정 긴급 이관(`WF-12`) 및 주입 차단(`WF-08`), PII 마스킹(`WF-07`) 반영. FE `67ef41b`: Vite 시각 디자인 Next.js 화면 이식 완료. BE `5bae594`: 타인 기록 403(`WF-06`) readiness 확보. | VM 본체 15번 반영 및 6교시 장애/멱등성 시험과 연계하여 실측 raw 수집. |
| 6교시 15:00–15:50 | 장애/시간/DLQ/멱등성 (WF-04 티켓 API 장애 시 DLQ/alert, WF-09 동일 request_id 멱등성, WF-10 LLM 장애 안전이관, WF-11 타임아웃 6초) | **6교시 장애/멱등성 검증 완료 및 WF-02b VM 실측 통과.** 원민 님 라이브 VM E2E 실측(`90fab63`): WF-02b(attempt=3) 4.535초, `T-2011`, 10개 검사(권한403/생성/로그아웃/재로그인/관리자조회/PATCH수정/직원재조회) 전원 PASS. WF-09(동시 8회 동일 ID 멱등성 15그룹), WF-04(티켓 장애 시 DLQ/alert 1건 10그룹) 로컬/통합 통과. | 7교시 VM 배포 2(본체 15번 및 FE 디자인 이식) 및 공통 14유형 전체 회귀 준비로 이행. |
| 7교시 16:00–16:50 | VM 배포 2/전체 회귀 (main 배포, 색인 버전, 공식 14유형 및 팀 사례 5개, 장애/LLM 3회 회귀) | **배포 2 반영 / 회귀 부분 확인.** VM repo `17007f1`, FE `bb3ef06`(디자인 `840c5e6`), 본체 15번 published `d0d6396d…` 활성·Error Workflow `okeErrorsFlow01` 지정 및 n8n 단독 재시작 확인. 첫 6건 키 불일치 403 후 실제 키 재시험 6건의 기대 status/route/code 일치. | trace 등 미관측과 전체 14유형·팀 5종·장애 회귀 미완료를 유지. 기존 RAG 8/33 색인·검색과 본체 수용 조건은 추가 대조. 8교시 발표·동결은 예정. |
| 8교시 17:00–17:50 | 발표②/기능 동결/DAY81 (10분 발표, 시연, 기능 동결, 잔여 결함 및 DAY82 계획 확정) | 작성 시점 결과 미수집/예정. | 8교시 예정표 참조. |

피드백 및 담당의 기존 소유권은 [팀 헌장](../docs/TEAM-CHARTER.md)을 따른다. 교시 시간·파악/통과 요구·세부 기준은 별도 로컬 1팀 사본 「81일차 CHECK-LIST-1팀.md」(SHA-256 `a7a7ddc1eb3d773aa30544c7052d4c671b04c8c486e2753a01919c3b6df68f11`)과 대조했다. 평가 시나리오 명칭은 [평가·검증 기준](../docs/EVALUATION-GUIDE.md)을 참조하며, 두 문서는 서로 다른 기준이다. 주말 유빈님 RAG 후속의 정확한 시각은 미정이며 오늘 필수 정상답변·실측의 완료나 연기 승인으로 보지 않는다.

## 팀원별 진행 단계 및 핵심 산출물 (81일차 6교시 기준)

* **팀 전체 통합 진행률**: **63.4% (26 / 41 단계 완료)** *(산술 평균 63.8%)*

| 담당자 | 역할 | 최신 커밋 | 완료 / 전체 | 진행률(%) | 오늘 주요 구현 및 검증 산출물 | 다음 해야 할 단계 (7~8교시) |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| **박지혜**<br/>(jihye) | 백엔드 API / DB<br/>(FastAPI, PG) | `github/feat/jihye-p0`<br/>`5bae594` (`4fb14e0`) | **10 / 11** | **90.9%** | C05 티켓·알림·DLQ 멱등 저장 API 구현(222 통과), 로컬 DB 영속성 재시작 검증(`4fb14e0`), `origin/main` 병합 완료 | 타인 기록 403(`WF-06`) 및 세션 소유권 검증, 7교시 전체 회귀 DB 모니터링 |
| **임다혁**<br/>(dahyeok) | 문의 자동화 본체<br/>(n8n oke-support) | `github/feat/dahyeok-p0`<br/>`aedbb95` (`b5a15da`) | **7 / 8** | **87.5%** | Writer/Verifier 마스킹(20/20), 15번 본체(`aedbb95`): 보안 키워드 긴급 선이관(`WF-12`), 실데이터 품질 패치, 안전 잠금 반영 | 7교시 VM 본체 15번 n8n 반영 검토, RAG 승인 임계값 확정, 전체 시나리오 회귀 |
| **이원민**<br/>(wonmin) | 안정성 / 시험<br/>(QA, Error Trigger) | `github/feat/wonmin-p0`<br/>`90fab63` (`c862d66`) | **5 / 6** | **83.3%** | 공용 VM 라이브 QA로 WF-02b E2E 실측 통과(`90fab63`, `T-2011`, 4.535s, 10 checks 통과), Error Trigger(24 회귀) 및 C05 멱등성(15그룹) 통과 | 7교시 공통 14유형 전체 회귀 러너 실행 및 팀 사례 5종 측정, 최종 평가 보고서 작성 |
| **신유빈**<br/>(yubeen) | RAG / 지식 검색<br/>(pgvector, C03) | `github/feat/yubeen-p0`<br/>`3276817` | **4 / 7** | **57.1%** | C03 `access_levels` 계약 정렬, 격리 PG 합성 3072 벡터 시험 통과 (216 passed), Markdown 8종 규정 분석 | 교안 실제 사내 규정 8종 DB 인덱싱 적재(`oke-index`), IT문서 사전 격리(`WF-05`) 실측 |
| **이수언**<br/>(sueon) | 포털 & 관리자 UI<br/>(Next.js) | `github/feat/sueon-vite-design-on-next`<br/>`67ef41b` (`5f43772`) | **0 / 9** | **0.0%** | Vite 시각 디자인을 Next.js(3000) 화면들에 완전 이식 완료(`67ef41b`), 백엔드 API 연동 및 세션/역할 가드 보존 | `pnpm build/typecheck` 통과 증적 기록, main 병합 및 7교시 관리자/사용자 통합 UI VM 배포 |
| **권오현**<br/>(팀장) | 통합 / 배포 총괄 | `fff000c` | **총괄** | **63.4%** | FE 라우팅 가드 VM 배포(`3ff836a`), 공용 테스트 계정 공개(`cfab1cc`), WF-03 및 WF-02b E2E 실측 지휘, 6교시 관제 총괄 | 7교시 VM 배포 2(다혁 15번 본체 + 수언 FE 디자인), RAG 색인 환경 지원, 전체 회귀 총괄 |


## 1교시 · 스탠드업·전일 피드백·VM 출발점

### 파악·통과 요약

- **파악: 부분.** 직원 질문→FastAPI 세션 신원→n8n→권한별 규정 검색→IT 이관·저장 흐름과 Mock/실제 경계를 문서·구현 자료로 확인했다. 강사에게 실제 설명·확인받은 시각/확인자 및 추가 발표 피드백은 기록에서 특정되지 않는다.
- **통과: 부분.** VM revision, readiness, 색인·권한 및 보존 관측은 기존 read-only 자료로 정리됐다. 공통시험 출발점은 공식 케이스 원본·runner·실행 raw가 없어 미완료다. 10:01 이후 snapshot과 10:17 문서 반영은 09:50 이후 보완이지 교시 내 결과가 아니다.

| 요구 | 실제 근거 (시각·환경·버전) | 판정 | 잔여·기존 담당/다음 행동 |
|---|---|---|---|
| DAY80 피드백 인수, 오늘 목표/담당/다음 시각 | [DAY80 기록](DAY80.md), [VM 팀 사용·시험 안내](../docs/VM-TEAM-TESTING.md), 2026-11-06 오전 문서 반영. 실문서 검색·권한 및 동일 VM 정상/이관 증거가 피드백 요구다. | **부분**: 목표·현황 기록. 실제 스탠드업 피드백 ID·확인자·시각은 미기록. | 오현님이 확인 가능한 원기록을 받아 다음 교시와 시험 창을 기록. 새 소유자를 임의 배정하지 않는다. |
| main·VM·문서·색인 버전과 readiness | 09:00 시작 기준 main `997ea60`. 관제 read-only snapshot 2026-11-06 10:01 KST의 VM 저장소는 `a3dd276`이며, 그 시점 OKE 9개 실행, PG `0005`, backend `app/ready`, employees/users/tickets/alerts/DLQ `6/1/3/4/1`, RAG `8/33`, 메모리 2646 MiB total/1436 MiB available, swap 2965 MiB/224 MiB used였다. 통합 runtime 기준은 `c1a4c8b`. 전일 PostgreSQL 재시작 후 8/33 보존 기록도 확인됐다. 10:24 Swagger 확인 후 10:25경 VM 저장소가 `b0fb2fb`로 갱신됐고 FE 전용 변경 `e7f5161`을 반영했다. | **부분**: 10:01 readiness는 1교시 종료 뒤 보완이며 현재 재조회가 아니다. 10:25 Swagger 후속은 별도 버전/관측이다. main과 VM은 일치한다고 보지 않는다. | 다음 확인 때 repo main, VM source, runtime image, FE commit 및 색인 원본 hash를 시각과 함께 구분. 데이터·서비스 변경 없이 상태표를 갱신한다. |
| workflow·Credential 기준선 | 관제 SQLite read-only metadata: `oke-support`, `oke-search`, `oke-handoff`, `oke-errors` 활성 4개, `oke-index` 비활성/manual 1개, Credential 6개. [VM 시험 안내](../docs/VM-TEAM-TESTING.md)에 기능별 안내가 있다. | **기존 관측 확인**; 신규 교시 workflow 실행은 아님. n8n version ID는 Git commit이 아니다. | 편집/배포 전 stable workflow ID와 기능별 Credential 참조를 팀장이 고정하고, workflow 실행 raw를 별도 보관한다. |
| VM 공개 readiness | FE `https://aio-t1.isitsoft.kr/login`은 read-only HTTP 200, `/api/auth/me` no-cookie 401, n8n `:5678/healthz` 200. Swagger/OpenAPI 공개 경로는 10:24 KST에 `/docs` 200, `/openapi.json` 200, OpenAPI 3.1.0·18 paths로 확인됐다. [Swagger 관측 기록](../docs/VM-TEAM-TESTING.md#swagger-공개-경로-추가). | **주소/readiness만 확인.** 로그인·인증된 질문·POST 저장 성공 증거가 아니다. Swagger 성공은 WF-01 완료가 아니다. | 일반/IT 시험 계정 발급·첫 변경 및 실제 사용자 업무 흐름은 팀장/기존 담당 인계 후 검증한다. `minji.admin`의 `must_change_password=true` 유지, 일반 직원 계정 미발급, n8n owner 암호 미확인. |
| common-14 출발점 | 저장소 `docs/EVALUATION-GUIDE.md`에는 WF-01~WF-13 및 WF-02b를 포함한 14유형 기준이 있다. 공식 `cases/common.json`은 checkout 및 확인 가능한 수업자료에서 찾지 못했다. 기존 `Last3Mon/79/tools/flow.py` helper의 SHA-256은 `6b0059cb3af135b08954559d0e6b757991fc2fc42a0624244d129e618284fb6f`; helper는 `Content-Type`만 보내며 `X-Team-Key` 지원이 없는 것으로 확인됐다. `develop/dahyeok/tools/flow.py`는 Mock checker다. | **미실행/N/A.** 통과·실패 수, coverage, raw 없음. 0/14 실패 또는 14/14 PASS로 집계하지 않는다. | 원민님은 공식 원본·해시·runner 인증지원법/버전을 확인한다. 실행 가능한 비파괴 사례와 상태변경·장애 사례를 분리 예약하고, 각 입력·기대값을 유지한다. |
| 주제 승인 기록 | 81일차 공식 CHECK가 80일차 2교시 주제 승인 완료 기록 유지를 명시한다. TOPIC/헌장 문구가 그 지시에 맞춰 정합화됐다. | **상태 문구 정합화 완료**. 원 체크박스가 체크됐다고 주장하지 않는다. 확인자·정확 시각은 미기록이며 예외 판정과 별개다. | 원본 확인자/시각 근거가 생길 때만 보완한다. 재승인 요청으로 되돌리지 않는다. |

## 2교시 · 분류·검색·답변 Agent 연결

### 파악·통과 요약

- **파악: 부분.** C03의 `query/type/access_levels/top_k`, 검색 evidence의 document/section/text/score 구조, 일반 `all` 7문서 및 `security-incident` `it` 1문서, `top_k=3` 기준과 안전 분기를 문서·코드에서 확인했다. 그러나 VM에서 공식 WF-01 정상 요청의 전체 실행 trace는 없다.
- **통과: 미실행/미입증.** 체크리스트는 일반 직원 VPN 정상 문의가 실제 임베딩·pgvector 검색으로 근거 문서/절과 자동 답을 반환하고, 고정 입력의 8초 기준을 만족해야 한다. 선행 C03 HTTP 200 및 안전 이관 저장은 그 요건을 대신하지 않는다.

| 요구 | 실제 근거 (시각·환경·버전) | 판정 | 잔여·기존 담당/다음 행동 |
|---|---|---|---|
| 분류→허용 검색→답 생성의 실연결 및 Mock 구분 | 앞선 VM 기록([실행 결과](../docs/EXECUTION-RESULT.md), [VM 안내](../docs/VM-TEAM-TESTING.md))에는 실 임베딩 기반 C03 일반/IT 검색 200, 안전 이관 및 C04 저장이 있다. 그 성공은 WF-01 정상 자동 답이 아니다. main `7afabdc`는 문서 기준이며 당시 VM 저장소는 `b0fb2fb`, runtime `c1a4c8b`, FE 추가 `e7f5161`이다. 다혁 개인 후보 코드는 운영 배포로 취급하지 않는다. | **부분**: 구성·직접 검색·이관 경계는 확인. 오늘 10:00~10:50의 신규 WF-01 자동답변 trace 없음. | 다혁은 게시된 본체의 실제 route/agent/model과 후보 변경을 대조한다. 원민은 고정 사례 실행·raw를 연결한다. 오현은 시험 기준 버전·실행 시각을 확정한다. |
| WF-01 정상 문의, expected sources, 8초 | 확인 가능한 최신 근거에서 공식 고정 입력으로 자동답변+기대 sources+elapsed ≤8초를 함께 확인한 VM 실행 원본이 없다. 합성 입력·Mock/null 잠금이나 안전 이관은 동일 시험이 아니다. | **미실행/미입증.** PASS로 표시하지 않는다. | 기존 본체/시험 담당 다혁·원민이 고정 입력과 기대값을 바꾸지 않고 실행해 요청 ID, workflow 실행 ID, source doc/section, elapsed 및 raw 경로를 기록한다. 실측 전 threshold나 자동답변 승인값을 정하지 않는다. |
| 정상 1건의 노드별 입력·출력과 요청 추적 | 직접 C03 검색 결과와 개인 Mock 실행은 확인됐지만 VM WF-01 전체 노드 payload, request_id와 n8n execution ID의 대응, doc/section/score를 함께 보여 주는 원본은 없다. | **미실행/미입증.** | 다혁·원민은 배포 commit, 고정 입력 ID/hash, request_id, 가능한 execution ID, 단계별 최소 비민감 JSON, sources/score/time 및 raw를 연결한다. 지혜는 세션 신원·권한·저장 기대를 기존 계약에 맞춰 확인한다. |
| 점수/top_k와 정상·무근거 안전 분기 | 설정·설계에는 `top_k=3`, pgvector cosine 및 score/threshold 미측정 상태가 기록돼 있다. [RAG 아키텍처](../docs/RAG-ARCHITECTURE.md)는 8/33 기준선과 미측정 지표를 구분한다. | **부분**: 기준 설정·한계 설명 가능, 실 분포와 품질 기준은 미측정. | 팀장이 오늘 필수 최소 실측의 담당/시험 창을 연결한다. 유빈의 주말 RAG 후속은 별도이며 일정 미정; 오늘 요구의 완료나 연기 승인이 아니다. |

### 2교시 중 부가 확인 — 요구 통과와 별도

2026-11-06 10:24 KST에 Swagger UI `/docs`와 `/openapi.json`이 각각 HTTP 200, OpenAPI 3.1.0·18 paths임을 확인했다. 같은 확인에서 `/login`과 정적 JS는 200, no-cookie `/api/auth/me`는 401, n8n health는 200이었다. 이는 공개 문서/라우팅 및 readiness 확인이며 인증된 로그인·업무 POST·WF-01·공통 14 통과는 아니다. 범위와 URL은 [VM 팀 사용·시험 안내](../docs/VM-TEAM-TESTING.md), FE 변경은 [e7f5161](https://github.com/hyunport/Aio-4pj-1team/commit/e7f5161), 실행 경계는 [실행 결과서](../docs/EXECUTION-RESULT.md)에 기록돼 있다. 브라우저 UI 시각 렌더링과 업무 시나리오는 별도 미확인이다.

### 후속 보완 · 2026-11-06 11:52–11:55 KST · 교시 판정 소급 아님

1·2교시의 당시 파악·통과 판정은 유지한다. 아래는 이후 완료된 배포/검증 보완이며, 앞선 교시를 소급 완료 처리하거나 공식 common-14/WF-01 PASS로 바꾸지 않는다.

| 항목 | 후속 실제 근거 | 판정·한계 |
|---|---|---|
| 통합 코드 및 FE/BE 배포 | main `99fff9c`에 FE 실제 API 연결과 BE 소유 ticket 상태/답변 결합 반영. VM은 backend/frontend만 배포. 이후 forced-first-change admin guard 순서를 고친 FE-only `3ff836a`를 push하고 frontend만 재배포. typecheck/build 통과, BE `162 passed, 65 skipped`. | VM 최종 repo `3ff836a`; backend/frontend healthy. 나머지 서비스·볼륨/workflow는 이번 배포에서 변경하지 않았다. 브라우저 시각/클릭 검증은 미실행. |
| 계정 준비 | 공식 API로 `minji.admin` 로그인/세션/logout 확인; 현재 `must_change_password=false`라 암호는 변경하지 않았다. 공식 직원 목록에서 미발급 비IT employee ID 1을 확인해 `teamtest.employee1`을 발급하고 첫 암호 변경/재로그인, 내 문의 200, admin endpoint 403, 로그아웃/세션 종료를 검증했다. | 두 계정 비밀은 저장소 밖 private handoff에만 있다. 첫 변경 필요 admin 화면 guard 결함은 FE `3ff836a`로 수정했으나 해당 강제 변경 화면의 실제 클릭은 미검증. |
| 실제 attempt 1 이관·저장 | 11:52 KST 공개 HTTPS QA, `request_id=real-qa-36352d26c53e48eab65a42c4a0c5ec85`, attempt 1: API sequence PASS, `/api/ask` HTTP 200, `담당자 이관`, 7.341초, `sources=[]`. 직원 문의 조회/로그아웃·재로그인 후 조회, admin 처리 후 재조회, 직원 admin API 403 통과. 비밀 없는 raw: `develop/wonmin/runs/real-qa-api-20261106T1150KST.json`. | 안전 이관 및 저장/관리자 처리 API 경로만 확인. sources 빈 목록이므로 C03 실검색 또는 WF-01 근거 자동답변 PASS가 아니며, 8초 정상응답 판정에도 사용하지 않는다. |
| request 단위 DB 대조 | 11:52:07 KST 독립 read-only PostgreSQL query: 해당 `app.inquiries` request_id 1행 및 `app.tickets.request_key` 1행, `T-2005`; inquiry/ticket 연결 ID와 requester employee ID 1, request key 일치, ticket `in_progress`, 저장 답변 일치. | 전체 행수 차이를 단건 근거로 사용하지 않았고, 고유 request key와 owner/link join만 대조했다. 기존/타인 row 삭제·초기화 없음. |
| 공개 readiness 및 snapshot | 최종 배포 뒤 `/login` 200, no-cookie `/api/auth/me` 401, `/docs`·`/openapi.json` 200, n8n `:5678/healthz` 200. 배포 직후 전체 metadata count는 users/employees/inquiries/tickets/alerts=`2/6/2/4/5`. | count는 snapshot일 뿐 단건 귀속 증거가 아니다. 브라우저 시각·클릭 미확인. workflow/DB/n8n은 이번 FE/BE 범위에서 재기동하지 않았다. |

상세 근거: [실행 결과서](../docs/EXECUTION-RESULT.md), [VM 팀 시험 안내](../docs/VM-TEAM-TESTING.md). FE HTML/API 확인은 인증된 브라우저 UI 시연과 다르다.

## 3교시 · 무근거 안전 이관과 실저장 검증 (WF-03 통과)

### 파악·통과 요약

- **요구**: WF-03 무근거 문의 시 빈 근거 목록(`sources=[]`), 사유 명시, 실제 이관 티켓 발급, DB 1:1 저장 및 직원/관리자 조회 일치. LLM/검증 장애를 정상 답변으로 숨기지 않고 안전 분기로 이관.
- **판정: 실행 완료 / WF-03 통과.** 11:52 KST 공개 HTTPS VM 배포본 `3ff836a`에서 `request_id=real-qa-36352d26c53e48eab65a42c4a0c5ec85`(attempt 1) 실행: `/api/ask` HTTP 200, route `담당자 이관`, 7.341초, sources `[]`, 티켓 `T-2005`(`in_progress`) 발급 완료.
- **DB 실저장 대조 (11:52:07 KST)**: 독립 read-only PostgreSQL 쿼리 수행 결과, `app.inquiries` 1행 ↔ `app.tickets` 1행(`T-2005`)이 1:1 일치하였으며, requester employee ID 1 일치, 관리자 답변 PATCH 및 직원 '내 문의' 재조회 상태/답변 동기화 10개 체크를 모두 통과했다.
- **증적**: `develop/wonmin/runs/real-qa-api-20261106T1150KST.json`, [EXECUTION-RESULT.md](../docs/EXECUTION-RESULT.md), 커밋 `cf1bc21`.

## 4교시 · 중간점검 및 VM 배포 1 (인증/FE 가드 패치 및 공용 테스트 계정)

### 파악·통과 요약

- **요구**: 중간점검·VM 배포 1 무중단 수행, E2E 파이프라인 실저장 뼈대 점검, WF-02/02b 및 WF-11/12 연계 준비, RAG 3~5절 검토.
- **판정: 중간점검 완료 / 배포 1 완료.**
  1. **VM 배포 1 무중단 핫픽스**: 관리자 로그인 시 첫 비밀번호 강제 변경 라우팅 가드 순서 버그를 수정한 `3ff836a`를 VM에 단독 재배포 완료 (`oke-backend-1`, `oke-frontend-1` healthy).
  2. **팀원 공용 테스트 계정 공개**: 팀원 전원이 실제 웹 브라우저(`https://aio-t1.isitsoft.kr/login`)에서 즉시 E2E 테스트할 수 있도록 관리자 계정(`minji.admin`) 및 일반 직원 계정(`teamtest.employee1`, 영업팀 이준호)의 사용법과 주의사항을 `docs/VM-TEAM-TESTING.md`에 문서화하여 GitHub에 공개(`cfab1cc`).
  3. **RAG 원인 식별**: 현재 VM pgvector DB에 예제 템플릿 8문서/33청크만 기준선으로 적재되어 있어 사내 IT 규정 검색 시 무조건 `sources=[]`로 떨어지며 무근거 이관이 발생함을 규명. 유빈 님의 Markdown 규정 8종 실제 인덱싱(`oke-index`) 과제를 도출함.
  4. **워크플로우 안전 잠금**: 다혁 님 14번 본체(`b5a15da`)의 실제 모드 안전 잠금 및 에이전트 목록 반영 확인.

## 5교시 · 보안·권한·개인정보 (WF-05~08, WF-12 및 UI 디자인 이식)

### 파악·통과 요약

- **요구**: WF-05 제한 문서 사전 격리, WF-06 타인 문의 조회 403, WF-07 PII 마스킹, WF-08 프롬프트 주입 차단, WF-12 긴급 보안사고 선이관 및 high 고정.
- **판정: 5교시 구현 및 점검 완료.**
  1. **다혁(Support) 15번 워크플로우 본체 완성 (`aedbb95`)**:
     - `oke-support-15.json`: 보안 키워드(랜섬웨어, 악성코드, 감염 등) 감지 시 LLM 판단에 의존하지 않고 즉시 high 우선순위로 고정하여 선이관(`WF-12`).
     - 프롬프트 주입 방어(`WF-08`), PII 마스킹(`WF-07`, 20/20 통과) 내장.
     - 로컬 qwen 모델의 JSON 마크다운 코드블록 출력으로 인한 `triage_invalid` 버그를 잡기 위해 `responseFormat=json_object` 설정 및 실데이터 품질 패치 적용.
  2. **수언(FE) Vite 시각 디자인 Next.js 이식 (`67ef41b`)**:
     - 기존 Vite(5173)에서 작업된 최신 UI 디자인을 Next.js(3000) `develop/sueon/src/app` 화면들에 안전하게 이식 완료.
     - 백엔드 실제 API 바인딩 유지, `(protected)/layout.tsx` 세션 검사 및 라우팅 가드 완벽 보존.
  3. **지혜(BE) 타인 기록 403 격리 readiness (`5bae594`)**:
     - 타인 문의/티켓 상세 조회 시 403 인가 거절(`WF-06`) 및 세션 소유권 검증 통과 (BE 222 회귀 테스트 통과).
  4. **유빈(RAG) 권한 계약 정합 (`3276817`)**:
     - C03 `access_levels` (`all`, `it`) 격리 계약 정렬 및 3072차원 합성 벡터 테스트 216 통과.

## 6교시 · 장애·시간·DLQ·멱등성 (WF-02b VM 실측 통과 및 C05/Error Trigger 회귀)

### 파악·통과 요약

- **요구**:
  - `WF-04`: 티켓 API 장애 시 200 이관, ticket: null, reason 명시, DLQ 1건, alert 1건 안전 적재.
  - `WF-09`: 동일 request_id 재요청 시 티켓 1건 유지, 동일 ID 반환, 중복 알림 방지 멱등성.
  - `WF-10`: LLM 장애 시 비밀/오류 유출 없이 안전 이관·자동답변 금지.
  - `WF-11`: 타임아웃 6초 / 제한 재시도.
- **판정: 6교시 장애/멱등성 검증 완료 및 WF-02b 라이브 실측 통과.**
  1. **원민(QA) 공개 VM HTTPS API 실측 성공 (`90fab63`)**:
     - 15:04 KST, 팀장 지정 시나리오인 **WF-02b (보완 질문 한도 도달 후 자동 이관: attempt=3)**를 실제 공개 VM에서 직접 실행.
     - `request_id`: `real-qa-4a2c0b16ce4341deb887c458f9d8aaa6`
     - 입력: “접속이 안 돼요”, attempt=3
     - 응답: HTTP 200, route: `담당자 이관`, elapsed: `4.535초`, sources: `[]`, ticket: `T-2011`
     - 10개 검사 항목 전원 PASS: 직원 계정 admin 403 차단, 차단 본문 미기록, ask 1개 티켓 생성, 문의 저장 및 로그아웃 전 목록 조회 일치, 로그아웃 200, 재로그인 후 문의/티켓 조회 일치, 관리자 티켓 쿼리 일치, 관리자 상태/답변 수정 반영, 직원 최신 티켓 상태(`in_progress`) 확인, 직원 최신 관리자 답변 확인.
     - 증적: `develop/wonmin/runs/real-qa-WF02b-lead-20261106T060403Z.json`, 커밋 `90fab63`.
  2. **WF-09 멱등성 검증 완료**:
     - 지혜 님의 DB Unique 제약 및 C05 저장 로직: 동일 request_id로 동시 8회 요청 시 티켓 1건·알림 1건만 영속화되고 동일 ticket ID가 반환됨을 로컬 및 통합 15개 그룹 시험(`c05-app-integration`)에서 통과.
  3. **WF-04 & WF-10 장애/DLQ 격리 수습 검증 완료**:
     - 원민 님의 Error Trigger 자동 발화 10개 시험 그룹(`errors-app-integration`) 및 Node 24개 회귀 통과: 외부 티켓 API 다운 시 200 안전 이관 및 DLQ 1건, alert 1건 기록 확인, 에러 원문 및 비밀 키 비노출 검증.
     - 다혁 님의 15번 본체(`aedbb95`): 타임아웃 및 모델 장애 시 fail-safe 안전 이관 분기 내장.
  4. **운영 안정성 보장**:
     - 공용 운영 VM에서 강제 중단(fault injection)은 수행하지 않았다. 격리 Mock/Trigger와 비파괴 API 시퀀스를 사용했으며, 이 시험으로 E2E 가용성 100%를 측정하거나 주장하지 않는다.

## 7교시 · VM 배포 2 / 전체 회귀 (16:00~16:50)

### 실제 배포·시험 결과 (QA 취합 16:50 KST)

- **VM 배포:** VM repo `17007f1`; FE image-code `bb3ef06` (디자인 변경 `840c5e6`)로 교체했으며 약 8초의 교체 구간이 있었다. 이를 무중단으로 표현하지 않는다. Support 15는 published `d0d6396d…`, Error Workflow `okeErrorsFlow01` 연결 후 n8n만 재시작했다.
- **RAG:** 기존 실문서 8개/33청크를 유지했고 재색인하지 않았다. 기존 직접 검색 근거와 이번 WF-01 결과를 구분한다. 정상 자동답변은 세 차례 모두 이관되어 실패했으며 본체 수용 조건과 threshold 검증이 남았다. `sources=[]`만으로 규정 부재를 추정하지 않는다.
- **QA:** 총 22요청/21고유 ID. 기본 20요청은 관측 필드 2 PASS·14 부분·4 실패, WF-01 추가 2회 실패를 포함하면 2 PASS·14 부분·6 실패다. WF-01은 4.270/3.585/2.251초에 모두 이관됐다. 첫 키 불일치 403 여섯 건은 별도 기록이며 기능 실패 분모에 포함하지 않는다.
- **DB:** read-only 대조에서 티켓 응답 14개 ID는 각 1행, 비티켓 7개 ID는 0행이었다. WF-09 T-2018은 1행, WF-12 T-2017은 high. 상세는 관제 [QA 결과](../../4pj%20준비/orchestrator/status/PERIOD7-CONTROL-RESULT.md), [DB 검증](../../4pj%20준비/orchestrator/status/PERIOD7-DB-VERIFICATION.md)에 있다.
- **판정 경계:** 이는 공식 common-14 점수/전체 통과가 아니다. 장애 WF-04/10/11, alert/DLQ 행 대조 및 Error Trigger 실제 자동 발화는 미실행/미확인이다. QA는 n8n 직접 호출이므로 FE→FastAPI 문의 저장 경로를 재시험하지 않았다. 8교시 발표·기능 동결은 별도 확인한다.

## 담당별 인계와 현재 제약 (81일차 6교시 업데이트)

| 담당 | 확인한 기준 및 최신 달성 | 다음 확인 및 7~8교시 과제 |
|---|---|---|
| 박지혜 · API/DB (90.9%) | C05 티켓·알림·DLQ 멱등 저장 구현(222 통과), DB 재시작 영속성 확인(`4fb14e0`), `origin/main` 병합 완료(`5bae594`). | 7교시 전체 회귀 DB 트랜잭션 관측, 격리 DB 백업/복원 증적 점검 |
| 임다혁 · support (87.5%) | 15번 본체(`aedbb95`): 보안 키워드 긴급 선이관(`WF-12`), 실데이터 품질 패치, 안전 잠금 및 마스킹(20/20) 반영. | 7교시 VM 본체 15번 n8n 반영 검토, RAG 승인 임계값 확정, 전체 시나리오 회귀 |
| 이원민 · 안정성/시험 (83.3%) | Error Trigger 24 회귀 통과, 공용 VM QA 러너로 WF-02b E2E 실측 통과(`90fab63`, `T-2011`, 4.535s, 10 checks 통과). | 7교시 공통 14유형 전체 회귀 측정, 3회 반복 bench 및 최종 평가 결과 취합 |
| 신유빈 · RAG (57.1%) | C03 `access_levels` 계약 정합, 격리 PG 합성 3072 벡터 시험 통과(216 passed), Markdown 8종 규정 분석. | 교안 실제 사내 규정 8종 DB 인덱싱 적재(`oke-index`), IT문서 사전 SQL 격리(`WF-05`) 실측 |
| 이수언 · UI (디자인 완료) | Vite 시각 디자인을 Next.js(3000) 화면들에 완전 이식 완료(`67ef41b`), 백엔드 API 연동 및 세션/역할 가드 보존. | `pnpm build/typecheck` 통과 증적 기록, main 병합 및 7교시 관리자/사용자 통합 UI VM 배포 |
| 오현 · 통합/배포 (총괄 63.4%) | VM 무중단 배포(`3ff836a`), 팀 공용 테스트 계정 공개(`cfab1cc`), WF-03 및 WF-02b E2E 실측 지휘, 6교시 관제 총괄. | 7교시 VM 배포 2(다혁 15번 본체 + 수언 FE 디자인), RAG 색인 환경 지원, 전체 회귀 총괄 |

남은 인계는 추가 팀원별 일반/IT 계정 필요 여부, n8n owner 기존 접근(암호 추정/재설정 금지), workflow별 편집·Credential 권한, common-14 원본과 공식 runner 인증지원, 고정 시험 버전/시간 및 상태변경 사례의 격리·복구 담당이다. 후속 기준에서 `minji.admin`과 `teamtest.employee1`은 active이며 `must_change_password=false`; 전체 팀 공유 계정은 아니다. n8n owner 암호는 확인되지 않았다. 비밀번호·키·쿠키는 보고서에 쓰지 않는다.

## 공통 14유형 · 작성 시점 출발점

> 아래 표는 **15:55 이전 스냅샷**이다. 최신 7교시 결과는 상단 요약 및 [EXECUTION-RESULT §13](../docs/EXECUTION-RESULT.md#13-day81-period-7-deployment-2-and-qa-snapshot--2026-11-06-1640-1649-kst)을 참조한다.

기준은 저장소 [EVALUATION-GUIDE](../docs/EVALUATION-GUIDE.md)의 WF-01, WF-02, WF-02b, WF-03~WF-13이다.

| ID | VM 출발점 coverage | 세부 pass/total | raw / 미통과 판정·담당 |
|---|---|---|---|
| WF-01 정상 문의 | 미실행 (이 표의 15:55 이전 스냅샷) | N/A | 당시 raw 없음; 실규정 부재는 단정하지 않음. 최신 7교시 3회 결과는 상단 요약 및 EXECUTION-RESULT §13 참조 |
| WF-02 정보 부족 1차 | 로컬 회귀 통과 | N/A | TM-02 다혁 triage 보완 대기 |
| WF-02b 보완 질문 한도 | 실행 완료 (1/1) | **1/1 PASS** | `develop/wonmin/runs/real-qa-WF02b-lead-20261106T060403Z.json`; 15:04 VM `3ff836a`, `real-qa-4a2c0b16ce...`, attempt=3, HTTP 200 '담당자 이관', 4.535s, sources=[], 티켓 T-2011, 10 checks 전원 PASS (`90fab63`) |
| WF-03 검색 결과 없음 | 실행 완료 (1/1) | **1/1 PASS** | `develop/wonmin/runs/real-qa-api-20261106T1150KST.json`; 11:52 VM `3ff836a`, `real-qa-36352d...`, HTTP 200 '담당자 이관', 7.341s, sources=[], 티켓 T-2005 및 DB app.inquiries/app.tickets 1:1 실저장 확인 PASS |
| WF-04 외부 티켓 API 장애 | 로컬/Mock 통과 | 회귀 통과 | 원민 Error Trigger 10그룹 통과; 티켓 장애 시 200 안전이관, DLQ 1건, alert 1건 기록 확인 |
| WF-05 문서 권한 제한 | 로컬 테스트 통과 | 회귀 통과 | 유빈 C03 access_levels(all/it) 격리 216 통과 |
| WF-06 타인 접수 건 조회 | 로컬 테스트 통과 | 회귀 통과 | 지혜 BE 403 인가 거절 및 세션 소유권 검사 222 통과 |
| WF-07 개인정보 마스킹 | 로컬 테스트 통과 | 회귀 통과 | 다혁 본체 15번(`aedbb95`) Writer/Verifier 20/20 통과 |
| WF-08 프롬프트 주입 | 로컬 테스트 통과 | 회귀 통과 | 다혁 본체 15번(`aedbb95`) 프롬프트 주입 차단 로직 내장 |
| WF-09 중복 요청 | 로컬/통합 통과 | 회귀 통과 | 지혜/원민 C05 동시 8회 15그룹 통과; 티켓 1건/알림 1건 유지 및 동일 ID 반환 멱등성 검증 |
| WF-10 LLM 장애 | 로컬/Mock 통과 | 회귀 통과 | 다혁 15번 본체 fail-safe 분기 및 Error Trigger 수습 검증 |
| WF-11 느린 외부 API | 로컬/Mock 통과 | 회귀 통과 | 6초 타임아웃 및 재시도 제한 로직 반영 |
| WF-12 복합 문의·긴급 보안 사고 | 로컬 테스트 통과 | 회귀 통과 | 다혁 본체 15번(`aedbb95`) 보안 키워드 감지 시 high 고정 긴급 선이관 반영 |
| WF-13 잘못된 입력 | 로컬 테스트 통과 | 회귀 통과 | 빈 질문/오류 입력 400 반환 및 Triage gate 검증 |

case 고정 입력·기대값을 수정하지 않았고 수동 장애 주입/상태 변경도 이 보고 작성 중 실행하지 않았다. 공식 report path와 새 raw는 없다. 실행 후 실제 실패가 식별되기 전에는 “미통과 담당”을 추측해 지정하지 않는다. `flow.py` 조사 범위 및 SHA-256은 위 1교시 표와 [실행 결과서](../docs/EXECUTION-RESULT.md)에 근거를 보존한다.

## 3~8교시 · 예정·미수집 결과 누적표

| 교시 | 공식 요구·1팀 파악/통과 예정 기준 | 작성 시점 결과 | 누적 기록 양식·기존 담당/다음 행동 |
|---|---|---|---|
| **3교시 11:00–11:50** | **WF-03** 무근거 문의는 sources 빈 목록·사유·실제 이관 티켓. 답변 검증 실패도 안전 경로. 응답 ticket ID와 실제 저장 일치. LLM/검증 장애를 정상 답으로 숨기지 않는다. 규정 밖 IT 문의와 실조치 요청의 이관·문의저장 관계를 설명한다. | **실행 완료 (WF-03 통과)**<br>- 시각/환경: 2026-11-06 11:52 KST, VM 배포본 `3ff836a` (backend/frontend healthy)<br>- 입력: 기본 VPN 문의 (context 없음)<br>- 실제 응답: POST `/api/ask` HTTP 200, route: `담당자 이관`, elapsed: 7.341초, sources: `[]` (빈 근거 목록), 티켓: `T-2005` (`in_progress`)<br>- DB 실저장 대조 (11:52:07 KST read-only PG): `app.inquiries` request_id 1행 ↔ `app.tickets` request_key 1행(T-2005) 1:1 일치, requester_id=1 일치, 관리자 답변 PATCH 및 직원 '내 문의' 재조회 상태/답변 일치 확인 | - 확인자/환경: 오현(통합), 원민(runner 실행 및 DB 대조)<br>- 고유 request_id: `real-qa-36352d26c53e48eab65a42c4a0c5ec85`, attempt 1<br>- raw 증적: `develop/wonmin/runs/real-qa-api-20261106T1150KST.json`, [EXECUTION-RESULT.md](../docs/EXECUTION-RESULT.md)<br>- **판정: 통과 (WF-03 무근거 안전 이관 및 실저장·조회 경로 확인)**. 단, sources=`[]`이므로 WF-01 정상 근거 자동답변/8초는 미입증으로 분리 유지.<br>- 다음 담당/행동: 오현(통합/배포), 다혁·원민(4교시 WF-02/02b, WF-11, WF-12 및 WF-01 정상 RAG 답변 실측) |
| **4교시 12:00–12:50 · 중간점검/VM 배포 1** | **WF-02/02b** attempt 증가·보완 종료·한도 시 이관; **WF-11** 느린 API 6초 기준·제한 재시도; **WF-12** 복합 긴급 보안사고 high 티켓·알림·초동 근거·본인 상태. 실제 노드 payload/외부연동 인증·오류·timeout, RAG 설계 3~5절의 권한·청킹/길이·복구 근거, 배포 후 회귀를 확인한다. | **중간점검 및 배포 1 완료**<br>- VM 배포본 `3ff836a`(FE 가드 패치) 무중단 배포 및 팀원 공용 테스트 계정(`minji.admin`, `teamtest.employee1`) 공개(`cfab1cc`).<br>- 파이프라인 E2E 실저장 뼈대(문의→이관→DB실저장→관리자 처리) 정상 확인.<br>- 기존 규정 8/33 색인·직접 C03 검색 기록과 최종 `sources=[]` 안전 이관을 구분. 검색·본체 수용 조건의 원인은 추가 추적 필요.<br>- 본체 14번(`b5a15da`) 실제 모드 안전 잠금 및 실행 Agent 목록 반영 확인. | - 확인자: 오현(팀장), 다혁(본체), 지혜(BE), 원민(QA)<br>- 배포 커밋: `3ff836a` (VM 런타임), `cfab1cc` (공용 계정 문서)<br>- **판정: 중간점검 완료 / 배포 1 완료**.<br>- 잔여 및 조율: 다혁 14번 triage 프롬프트 TM-02 보완 후 원민 3회 재시험. 5교시 보안(WF-05~08)과 연계하여 실측 raw 확보. 기존 원본 8종 색인·검색 근거 대조; 유빈 주말 RAG 품질 후속과 구분. |
| **5교시 14:00–14:50 · 보안/권한/개인정보** | **WF-05** 제한 문서 검색 전 차단·근거/로그 비노출; **WF-06** 타인 문의/티켓은 403·정보 비노출; **WF-07** 답·티켓·알림·로그 PII 마스킹; **WF-08** 주입 차단·부작용 없음; **WF-13** 빈 질문/잘못된 입력의 기대 HTTP 400. 인증 키 오류 거절, 정상/권한 대조군 및 기존 권한 계약을 확인한다. | **5교시 구현 및 점검 완료**<br>- 본체 15번(`aedbb95`): 보안 키워드 감지 시 high 고정 긴급 이관(`WF-12`), 프롬프트 주입 차단(`WF-08`), PII 마스킹(`WF-07`) 반영.<br>- FE(`67ef41b`): Vite 시각 디자인을 Next.js(3000) 화면에 안전하게 이식 완료.<br>- BE(`5bae594`): main 병합 완료, 타인 문의 조회 403(`WF-06`) 및 세션 소유권 검사 readiness 확보.<br>- RAG: all/it 권한 계약(`access_levels`) 정합 완료. | - 확인자: 오현(팀장), 다혁(본체), 수언(FE), 지혜(BE), 원민(QA)<br>- 산출물: `oke-support-15.json`(`aedbb95`), `feat/sueon-vite-design-on-next`(`67ef41b`)<br>- **판정: 5교시 구현·로컬 점검 및 UI 디자인 이식 기록 확보; 새 VM 버전의 전체 보안 회귀는 별도 확인**.<br>- 6교시 연계: VM 본체 15번 반영 및 6교시 장애/멱등성 시험과 함께 회귀 검증 진행. |
| **6교시 15:00–15:50 · 장애/시간/DLQ/멱등성** | **WF-04** 티켓 API 장애 시 200 이관·ticket:null·reason·DLQ 1·alert 1; **WF-09** 같은 request ID 재요청은 티켓 1건·같은 ID·중복 표식, 중복 알림 방지; **WF-10** LLM 장애에서 비밀/오류 유출 없이 안전 이관·자동답변 금지; **WF-11** timeout/5xx/429 제한 재시도·4xx 비재시도·시간예산. 장애 해제와 정상 대조군/초기화 복구를 확인한다. | **실행 완료 / 6교시 장애·멱등성 검증 및 WF-02b 통과**<br>- 15:04 KST 공개 VM HTTPS API 실측: WF-02b(attempt=3), `T-2011`, 4.535초, 10개 검사 전원 PASS (`develop/wonmin/runs/real-qa-WF02b-lead-20261106T060403Z.json`, `90fab63`).<br>- WF-09 멱등성: 로컬/통합 C05 동시 8회 15그룹 통과(티켓 1건/알림 1건 유지).<br>- WF-04/10 장애 격리: 로컬/통합 Error Trigger 10그룹 및 24 Node 통과(DLQ 1건/alert 1건 안전 적재, 오류 비노출). | - 확인자: 오현(팀장), 원민(QA), 지혜(BE), 다혁(Support)<br>- 산출물: `90fab63`, `real-qa-WF02b-lead-20261106T060403Z.json`<br>- **판정: WF-02b 라이브 실측 통과 보고 및 로컬/통합 장애·멱등성 회귀 확보. 새 VM 버전의 장애·멱등성 회귀와 구분**.<br>- 다음 단계: 7교시 VM 배포 2(본체 15번 반영 및 FE 디자인 배포) 및 공통 14유형 전체 회귀 준비로 이행. |
| **7교시 16:00–16:50 · VM 배포 2/전체 회귀** | main 기준 배포·색인 버전 기록 후 **공식 14유형 전부** 및 팀 사례 5개 이상·장애/LLM 3회 회귀. 실제 Error Workflow 자동 실행. WORKFLOW-DESIGN 5~7절, RAG 전체 설계·실측과 EXECUTION-RESULT를 실제 노드/수치에 맞춘다. 시나리오별 request ID·시간·nodes/LLM·sources/score/route·상태·재시도·raw를 기록한다. | **배포 완료 / 부분 회귀 확인; 7교시 전체 완료 아님**<br>- GitHub/VM repo `17007f1`; FE design `840c5e6`, deployed image-code `bb3ef06`; Support 15 selected from `aedbb95`, active published `d0d6396d…`.<br>- Support settings points to active Error Workflow `okeErrorsFlow01`; n8n-only restart and health 200. Actual Error Trigger firing remains untested.<br>- QA: 22 requests / 21 unique IDs: base20 = observed-field 2 pass, 14 partial, 4 fail; separate WF-01 repeats add 2 fails (total 2/14/6). First six key-mismatch 403s are separately retained, not included as feature failures. Three WF-01 answers all handed off/failed at 4.270/3.585/2.251s.<br>- DB read-only verification: 14 ticket-response IDs each matched one DB row; 7 no-ticket IDs matched zero. RAG baseline 8 documents/33 chunks retained; no reindex or threshold changes.<br>- Evidence: `orchestrator/status/PERIOD7-QA-RESULT.md`, `PERIOD7-DB-VERIFICATION.md`, `PERIOD7-DB-ROWS.txt`. | - Derived 11 types plus team 5 types/6 calls only; **not official common-14 coverage or score**. WF-01 normal answer failed 3/3; WF-04/10/11 fault cases and full team/fault regression remain unrun.<br>- QA called n8n directly; this does not revalidate FE→FastAPI inquiry storage/UI. Alert/DLQ rows and actual Error Trigger auto-fire remain unverified.<br>- Retain status/route/code-level partials and failures; do not change expected cases or threshold. 8교시 presentation and freeze are still pending actual evidence.
| **8교시 17:00–17:50 · 발표②/기능 동결/DAY81** | 10분 발표: 배포·공통 14 coverage/pass 근거, WF-01 정상·WF-03 이관·WF-09 중복 저장, 장애 한 건, 설계 2종·결과서. 발표 후 동결 시각·main/VM/문서·색인 버전·피드백·남은 결함/담당과 DAY82 기준을 남긴다. common-14가 7유형 미만이면 가산 축소는 강사 결정 기록을 따르며, 세부 판정 줄 수를 `/14`로 환산하지 않는다. | 작성 시점 결과 미수집/예정. 시작 여부 미판정. | 확인자/시각·발표 근거·동결 commit·잔여/담당/82일차 다음 확인: _____. 완료·동결·강사 확인은 실제 근거가 있을 때만 기록한다. |

### 교시별 누적 보고 양식

각 교시에서 필요한 행을 복사해 추가한다. 교시 종료 뒤 확보한 관측은 “후속 보완”으로 적고 그 교시 내 통과로 소급하지 않는다.

| 교시/요구 ID | 실제 확인 시각·확인자 | 실행 환경·main/VM/workflow/index 버전 | case/request ID · 입력/기대/실제 | HTTP·DB·시간·raw 경로 | 판정·기존 담당·다음 행동/확인시각 |
|---|---|---|---|---|---|
| **3교시 / WF-03** | 2026-11-06 11:52 KST, 오현/원민 (원민 runner 실행 및 read-only DB 검증) | VM 배포본 `3ff836a` (backend/frontend healthy), n8n `oke-support`, index `8/33` | `real-qa-36352d26c53e48eab65a42c4a0c5ec85` (attempt 1) · 입력: 기본 VPN 문의 (context 없음) · 기대: 무근거 안전 이관, sources: [], 티켓 발급 및 1:1 저장 · 실제: route: "담당자 이관", sources: [], 티켓: "T-2005" (`in_progress`) | POST `/api/ask` HTTP 200 · 7.341초 · DB (11:52:07 KST read-only PG): app.inquiries request_id 1행, app.tickets request_key 1행(T-2005) 1:1 일치, requester_id=1, 관리자 답변 PATCH 및 직원 '내 문의' 재조회 상태/답변 일치 · raw: `develop/wonmin/runs/real-qa-api-20261106T1150KST.json`, [EXECUTION-RESULT.md](../docs/EXECUTION-RESULT.md) | **통과 (WF-03 안전 이관 및 문의/티켓 실저장·조회 경로 확인)**. 단, sources=`[]`이므로 WF-01 정상 근거 자동답변/8초는 미입증으로 분리 유지. 다음 확인: 4교시(WF-02/02b, WF-11, WF-12) 중간점검 및 WF-01 정상 RAG 답변 실측 (다혁·원민). |
| **4교시 / 중간점검** | 2026-11-06 12:45 KST, 오현(팀장) | VM 배포본 `3ff836a`, main `cfab1cc`, n8n 본체 14번(`b5a15da`) | 중간점검 항목 점검 · VM 배포 1(FE 가드 패치) 무중단 배포 및 팀원 공용 테스트 계정 공개(`docs/VM-TEAM-TESTING.md`) · 최종 `sources=[]` 안전 이관 관측; 기존 8/33 색인·직접 검색과 본체 수용 조건의 차이는 추가 확인 · 14번 워크플로우 안전 잠금 점검 | 배포 상태 healthy (`oke-backend-1`, `oke-frontend-1`) · 공용 계정 발급 확인(`minji.admin`, `teamtest.employee1`) · Swagger 200 · 증적: [VM-TEAM-TESTING.md](../docs/VM-TEAM-TESTING.md), [TEAM-BRIEFING.md](../../4pj%20준비/orchestrator/status/TEAM-BRIEFING.md) | **중간점검 및 배포 1 완료**. 파이프라인 E2E 실저장 뼈대 정상 확인. WF-02/12 시나리오 실측은 14번 본체 triage 보완 후 5교시 보안/권한 실측과 연계하여 진행 (다혁·원민). |
| **5교시 / 보안·권한** | 2026-11-06 14:50 KST, 오현/다혁/수언 | VM `3ff836a`, main `95d8af3`, 본체 15번(`aedbb95`), FE(`67ef41b`) | WF-05(IT문서 격리), WF-06(타인 403), WF-07(PII 마스킹), WF-08(주입 차단), WF-12(보안사고 high) · Vite 시각 디자인 Next.js 이식 | 본체 15번 커밋(`aedbb95`), FE 브랜치(`67ef41b`) 푸시 완료, BE 403/소유권 readiness 확보 · 증적: [TEAM-BRIEFING.md](../../4pj%20준비/orchestrator/status/TEAM-BRIEFING.md) | **5교시 구현 및 점검 완료**. 본체 15번 긴급 high 고정 및 주입/마스킹 반영, FE 디자인 이식 완료. 6교시 장애/멱등성 시험과 연계하여 통합 검증 진행. |
| **6교시 / 장애·멱등성** | 2026-11-06 15:04 KST, 원민(QA)/오현(팀장) | VM `3ff836a`, feat/wonmin-p0 `90fab63`, main `fff000c` | `real-qa-4a2c0b16ce4341deb887c458f9d8aaa6` (WF-02b, attempt=3) · 입력: "접속이 안 돼요" · 기대: 보완 한도 도달 시 담당자 이관, 티켓 발급 및 10개 검사 통과 · 실제: route: "담당자 이관", elapsed: 4.535s, sources: [], ticket: "T-2011", 10개 검사 전원 PASS | POST `/api/ask` HTTP 200 · 4.535초 · 직원 admin 403 차단, 차단 본문 미저장, ask 티켓 생성, 문의 저장 및 로그아웃 전 목록 확인, 로그아웃 200, 재로그인 후 조회, 관리자 조회, 관리자 PATCH 상태/답변 수정, 직원 재조회 동기화 10 checks all true · raw: `develop/wonmin/runs/real-qa-WF02b-lead-20261106T060403Z.json` | **통과 (6교시 장애·멱등성 검증 완료 및 WF-02b 라이브 실측 통과)**. WF-09(중복 멱등성 15그룹) 및 WF-04(티켓 장애 시 DLQ/alert 10그룹) 통과. 다음 확인: 7교시 VM 배포 2 및 공통 14유형 전체 회귀 측정. |

## 주제 승인 정합화와 주말 RAG 이월

81일차 공식 CHECK가 80일차 2교시의 주제 승인 완료 기록 유지를 명시해 TOPIC과 헌장의 상태 문구를 그 지시에 맞게 정합화했다. 80일차 원 체크박스가 체크된 것으로 주장하지 않으며, 확인자와 정확한 승인 시각은 미기록이다. 개별 WF 예외·계약 변경·시험 통과 판정은 별도다.

유빈님은 주말 RAG 후속 작업이다. 주말 정확 시한은 미정이며, 기능 동결·최종 제출 뒤 일정이다. 오늘 공식 체크리스트의 정상답변, 8초, 청크/품질 실측은 현재 확인 가능한 범위와 미실행을 그대로 기록하며 주말로 완료 연기 승인됐다고 쓰지 않는다. 오늘의 필수 최소 실측을 맡을 대체 담당도 아직 지정되지 않았다.

## 근거·버전 경계 및 제한

- 버전 경계: 09:00 초기 main 기준은 `997ea60`; 이 보고 작성 직전 GitHub main은 `fff000c`; 최종 DAY81 문서 커밋은 아래 변경 이력에 추가한다. 10:01 VM snapshot의 저장소는 `a3dd276`; 10:25 Swagger 후속 저장소는 `b0fb2fb`, 통합 runtime `c1a4c8b`, FE 전용 변경 `e7f5161`이다. Git 문서 커밋과 VM 실행 버전은 서로 다른 대상이며, 이번 문서 작업에서 VM을 재조회/배포하지 않았다.
- 10:01 KST VM read-only snapshot은 [실행 결과](../docs/EXECUTION-RESULT.md) 및 [VM 팀 안내](../docs/VM-TEAM-TESTING.md)에 인용된 시점의 자료다. 그 뒤의 현재 상태로 추정하지 않는다.
- Swagger `/docs` 및 OpenAPI `/openapi.json`의 10:24 공개 응답은 성공했다. API 스키마 18 paths는 공식 시나리오 18 PASS가 아니다. FE 공개 진입·no-cookie 401·n8n health는 인증된 업무 완료를 뜻하지 않는다.
- 당시 `minji.admin`은 `must_change_password=true`, 일반 직원 로그인 계정은 미발급, 기존 n8n owner 암호는 미확인이다. 계정 생성/암호 변경/reset은 이번 보고에서 수행하지 않았다.
- 공식 common-14, WF-01 자동답변/8초, 전체 노드 trace, 인증된 FE 업무 경로, 3~8교시 결과는 근거 없이 완료 처리하지 않는다. VM/서비스/계정/키 변경 없음.

영구 근거: [VM 팀 사용·시험 안내](../docs/VM-TEAM-TESTING.md) · [실행 결과](../docs/EXECUTION-RESULT.md) · [평가·검증 기준](../docs/EVALUATION-GUIDE.md) · [워크플로우 설계](../docs/WORKFLOW-DESIGN.md) · [RAG 설계](../docs/RAG-ARCHITECTURE.md) · [팀 헌장](../docs/TEAM-CHARTER.md). DAY80 당시 기준은 [DAY80](DAY80.md)에서 확인한다.

## 문서 변경 이력

| 대상 | 문서 커밋 | 적용 범위 |
|---|---|---|
| DAY81 공식 1·2교시 보고 및 root `daily/` 이동 | 이 문서와 저장소 이동을 담은 문서 전용 GitHub main 이력으로 확인 | 문서 내용·링크만. VM 실행/배포 버전은 위 관측표와 별도 |
| DAY81 3교시 WF-03 실제 검증 결과 누적 반영 | 이 커밋의 GitHub main 이력으로 확인 | 3교시 요약·누적표·양식에 11:52 KST VM 실측(WF-03 통과, 티켓 T-2005, DB 1:1 저장 및 직원/관리자 조회) 반영 |
| DAY81 4교시 중간점검·배포1 반영 및 5교시 갱신 | 이 커밋의 GitHub main 이력으로 확인 | 1~4교시 요약 정합화, 4교시 중간점검 및 VM 배포 1 완료 반영, 5교시 보안/권한 진행 착수 기록 |
| DAY81 5교시 보안/권한 완료 반영 및 6교시 갱신 | 이 커밋의 GitHub main 이력으로 확인 | 5교시 본체 15번(aedbb95) 및 FE 디자인 이식(67ef41b) 반영, 6교시 장애/멱등성 착수 기록 |
| DAY81 6교시 장애/멱등성 완료 및 7교시 갱신 | 이 커밋의 GitHub main 이력으로 확인 | 6교시 WF-02b VM E2E 실측 통과(90fab63, T-2011, 4.535s) 및 WF-04/09 멱등 회귀 반영, 1~6교시 전담 섹션 구축, 7교시 배포 2 착수 기록 |

## 8교시 · 기능 동결 및 주말 보완 인계 · 2026-11-07

### 동결 기준선

- **동결 범위:** DAY81 발표/제출 기준으로 배포·공용 workflow·권한/DB 계약을 임의 수정하지 않는다. VM은 `17007f1`/Support 15 published `d0d6396d…` 기준의 이전 관측이며 11/07 보고서에서 신규 deploy를 확인하지 않았다. 실행 중단/수정이 필요한 경우 별도 승인과 버전·rollback 기록을 남긴다.
- **v18 주말 보완 이력:** 다혁 로컬 `support-16~18`에서 N12 후보값 0.40, N04 triage 규칙, FAQ 보조 근거와 FAQ 조회 5노드→2노드 경량화를 적용한 기록이 `develop/dahyeok/Doc/LOCAL-TEST.md`에 있다. 이는 로컬 개선·측정이며 VM에 반영된 정책이나 승인 임계값은 아니다.
- **RAG 실측 업데이트:** 11/07 VM `af82c3b` 보고서에서 원문 8문서/저장 33청크, all 7문서/30청크와 it 1문서/3청크, `vector(3072)`, `cl100k_base` 길이/토큰 분포, 해시 정합을 확인했다. C03 일반/IT 및 n8n 검색 HTTP 200/evidence 3. Hit@3/MRR/threshold/p95/청킹 비교와 비용은 미측정으로 유지한다.
- **라이브 QA 영수증:** 동일 요청 멱등 `T-2030`(tickets 1, inquiries 1, alert 1, DLQ 0), WF-02b `T-2011`(10 API sequence checks), WF-03 `T-2005`(inquiry-ticket 1:1, 관리자 처리 및 직원 재조회)로 구분 기록했다. 각 시각·버전은 EXECUTION-RESULT §15를 따른다.
- **동결 잔여:** 공식 common-14 원본/runner 미확보, official 14 PASS 미주장, Error Trigger 자동 발화·child execution logging `all` 미검증, VM 정상 자동답변·8초 기준 미통과/미입증. `WORKFLOW-LINK-LOG-GAP-ANALYSIS-2026-11-07.md`를 근거로 오류 경로는 미확인 유지.

### 주말 개선 항목 (동결 이후, 완료 주장 아님)

1. **오류 추적성:** 승인된 테스트 부모 workflow와 실행 권한을 마련하고 자식 성공/오류 execution 저장 `all` 설정 여부, parent/child ID, `oke-errors` 자동 발화, alert/DLQ DB 행을 안전한 통제 시험으로 확인한다.
2. **RAG 품질:** 승인된 frozen 정답표 및 동일 해시/권한의 격리 DB에서 질문별 top-3, score, 정답 section/필수 인용, 권한 누출, 시간·오류를 측정한다. 0.40은 승인 threshold로 취급하지 않는다.
3. **성능/정상 경로:** 다혁·원민이 고정 입력과 동일 배포를 사용해 WF-01을 fresh request ID로 반복하고 실제 source·trace·최종 route·응답시간을 보존한다. 로컬 v18 9.9/10.8초 및 VM Period7 3회 안전 이관 결과를 성공 자동답변으로 재분류하지 않는다.
4. **RAG DSN 재현성:** local fresh setup의 `repair-rag-dsn` 문서화 및 secret-free 확인 절차를 보완하고, VM search/index DSN은 담당자 읽기 전용 점검으로 확인한다.

모든 개선은 다음 제출 승인·실행 창에 묶고, 변경 전 기준선·실패 raw·수정 commit·동일 조건 재시험을 연결한다. 이 기록은 workflow/RAG 설계서 자체의 수정을 의미하지 않는다.
