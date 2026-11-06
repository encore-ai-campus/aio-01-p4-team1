# DAY 81 · 2026-11-06 · 1팀 오케퐁 교시별 진행 보고

> 작성 기준: 2026-11-06 10:57 KST. 공식 1팀 체크리스트의 시간·파악·통과 기준에 맞춰 1·2교시 결과와 3~8교시 누적 양식을 기록한다. 교시 뒤 확보한 근거는 그 교시의 통과로 소급하지 않는다. 본 보고의 Git 문서 커밋과 VM 실행 버전은 별도다.

## 오늘 목표와 현재 판정

오늘은 실제 VM 배포본에서 검색·정상 응답·안전 이관·저장을 구분해 확인하고, 고정 공통 시나리오와 보안·장애 회귀의 근거를 축적한다. **1교시 보고자료 작성은 완료했으나 공통시험 출발점은 미완료다. 2교시 WF-01 자동 근거 답변과 8초 기준은 미실행/미입증이다. 3교시 WF-03 무근거 안전 이관 경로(빈 근거 목록, 티켓 T-2005 발행, DB 1:1 저장 및 직원/관리자 조회)는 실제 VM(3ff836a)에서 검증 완료했다. 4교시 중간점검 및 VM 배포 1(FE 가드 패치 배포 3ff836a, 팀 공용 계정 공개 cfab1cc)을 완료했다. 5교시 보안·권한(다혁 15번 본체 aedbb95 긴급 보안사고/주입차단/마스킹 반영, 수언 Vite 디자인 Next 이식 67ef41b, 지혜 타인 조회 403 WF-06 점검)을 완료했으며, 현재 6교시(장애·시간·DLQ·멱등성 WF-04/09/10/11)를 진행 중이다.** 공개 Swagger 확인은 API 문서 경로 확인 성과로 따로 기록하며 업무 시나리오 통과로 계산하지 않는다.

| 단계 | 공식 요구 | 파악 / 통과 판정 | 잔여와 다음 확인 |
|---|---|---|---|
| 1교시 09:00–09:50 | DAY80 피드백·오늘 목표/담당/다음 시각, main·VM·문서·색인 readiness, VM common-14 출발점, 주제 승인 기록 정합화 | **부분.** 버전·배포·실측 현황과 미실행 경계를 문서화했다. 14개 공식 사례 실행 출발점은 미완료. 승인 상태 문구는 81일차 CHECK가 유지하도록 명시한 80일차 2교시 완료 기록에 맞춰 정합화했다. | 14개 원본·runner·인증 지원 절차와 raw 확보가 필요하다. 정확한 승인 확인자/시각은 미기록이다. 교시 내 피드백 인수자·확인 시각도 근거가 없어 미기록으로 둔다. |
| 2교시 10:00–10:50 | 분류→허용 근거 검색→답변 연결, WF-01 고정 입력 정상 답변/기대 sources/8초, 노드별 입출력 근거 | **부분/필수 결과 미실행.** 기존 C03 검색과 안전 이관/저장은 선행 관측으로 확인되지만, VM의 WF-01 정상 자동 답변·기대 근거·8초·전체 노드 원본을 함께 증명한 새 실행이 없다. | 다혁·원민 등 기존 기능·시험 소유자가 고정 입력으로 배포 workflow와 실제 노드/모델/시간 근거를 남겨야 한다. 오늘 필수 측정의 대체 담당·시간은 미지정이다. |
| 3교시 11:00–11:50 | WF-03 무근거 문의는 sources 빈 목록·사유·실제 이관 티켓. 답변 검증 실패도 안전 경로. 응답 ticket ID와 실제 저장 일치. | **실행 완료 / WF-03 통과.** 11:52 KST VM 배포본 `3ff836a`에서 `request_id=real-qa-36352d26c53e48eab65a42c4a0c5ec85`(attempt 1) 실행: `/api/ask` HTTP 200, route `담당자 이관`, 7.341초, sources `[]`, 티켓 `T-2005`(`in_progress`). 11:52:07 PG read-only query로 `app.inquiries`/`app.tickets` 1:1 일치, 직원 조회 및 관리자 처리 동기화 확인. | 단, sources `[]`이므로 WF-01 정상 자동답변/8초는 미입증으로 분리 유지. 4교시 중간점검 및 5교시 보안/권한으로 연계. |
| 4교시 12:00–12:50 | 중간점검·VM 배포 1, WF-02·02b 보완/이관 한도, WF-11 지연, WF-12 긴급 보안사고, RAG 3~5절 | **중간점검 완료 / 배포 1 완료.** VM 배포본 `3ff836a`(FE 가드 패치) 무중단 배포 및 팀원 공용 테스트 계정(`minji.admin`, `teamtest.employee1`) 공개(`cfab1cc`). 파이프라인 E2E 실저장 뼈대 점검 완료 및 RAG 지식 문서 부재(`sources=[]`) 원인 식별. 본체 14번(`b5a15da`) 안전 잠금 반영. | WF-02/12 시나리오 실측은 본체-QA 연계 조율로 5교시 보안/권한 실측과 함께 진행. 실제 RAG 규정 8종 색인 적재 필요. |
| 5교시 14:00–14:50 | 보안·권한·개인정보 (WF-05 제한 문서 격리, WF-06 타인 기록 403, WF-07 PII 마스킹, WF-08 주입 차단, WF-13 오류 400) | **5교시 구현 및 점검 완료.** 본체 15번(`aedbb95`): 보안 키워드 감지 시 high 고정 긴급 이관(`WF-12`) 및 주입 차단(`WF-08`), PII 마스킹(`WF-07`) 반영. FE 67ef41b: Vite 시각 디자인 Next.js 화면 이식 완료. BE 5bae594: 타인 기록 403(`WF-06`) readiness 확보. | VM 본체 15번 반영 및 6교시 장애/멱등성 시험과 연계하여 실측 raw 수집. |
| 6~8교시 | 6교시 장애/시간/DLQ/멱등성(WF-04/09/10/11) ~ 8교시 발표②/기능 동결 | **6교시 진행 중.** 7~8교시 예정표 참조. | 6교시: WF-04(티켓 장애 시 DLQ/alert), WF-09(동일 request_id 멱등 재사용), WF-10(LLM 장애 안전이관), WF-11(타임아웃 6초) 진행 중. |

피드백 및 담당의 기존 소유권은 [팀 헌장](../docs/TEAM-CHARTER.md)을 따른다. 교시 시간·파악/통과 요구·세부 기준은 별도 로컬 1팀 사본 「81일차 CHECK-LIST-1팀.md」(SHA-256 `a7a7ddc1eb3d773aa30544c7052d4c671b04c8c486e2753a01919c3b6df68f11`)과 대조했다. 평가 시나리오 명칭은 [평가·검증 기준](../docs/EVALUATION-GUIDE.md)을 참조하며, 두 문서는 서로 다른 기준이다. 주말 유빈님 RAG 후속의 정확한 시각은 미정이며 오늘 필수 정상답변·실측의 완료나 연기 승인으로 보지 않는다.

## 팀원별 진행 단계 및 핵심 산출물 (81일차 5교시 기준)

* **팀 전체 통합 진행률**: **61.0% (25 / 41 단계 완료)** *(산술 평균 60.4%)*

| 담당자 | 역할 | 최신 커밋 | 완료 / 전체 | 진행률(%) | 오늘 주요 구현 및 검증 산출물 | 다음 해야 할 단계 (5~8교시) |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **박지혜**<br/>(jihye) | 백엔드 API / DB<br/>(FastAPI, PG) | `github/feat/jihye-p0`<br/>`5bae594` (`4fb14e0`) | **10 / 11** | **90.9%** | C05 티켓·알림·DLQ 저장 API 구현(222 통과), 로컬 DB 영속성 재시작 검증(`4fb14e0`), `origin/main` 병합 완료 | 격리 DB 백업/복원 시험, 5교시 타인 기록 403(`WF-06`) 및 소유권 검증 |
| **임다혁**<br/>(dahyeok) | 문의 자동화 본체<br/>(n8n oke-support) | `github/feat/dahyeok-p0`<br/>`aedbb95` (`b5a15da`) | **7 / 8** | **87.5%** | Writer/Verifier 마스킹(20/20), 15번 본체(`aedbb95`): 보안 키워드 긴급 선이관(`WF-12`), 실데이터 품질 패치, 안전 잠금 반영 | 6교시 장애 시 DLQ/alert(`WF-04`) 및 멱등성(`WF-09`), RAG 승인 임계값 확정 |
| **이원민**<br/>(wonmin) | 안정성 / 시험<br/>(QA, Error Trigger) | `github/feat/wonmin-p0`<br/>`c862d66` | **4 / 6** | **66.7%** | tickets/alerts/DLQ 로컬 Mock 65개 통과, Error Trigger 자동발화 24 회귀 통과, 공용 VM QA 러너 개발 및 attempt 1 실측 | 6교시 장애/DLQ/멱등성(WF-04, WF-09, WF-10, WF-11) 실측, TM-02 보완 재시험 |
| **신유빈**<br/>(yubeen) | RAG / 지식 검색<br/>(pgvector, C03) | `github/feat/yubeen-p0`<br/>`3276817` | **4 / 7** | **57.1%** | C03 `access_levels` 계약 정렬, 격리 PG 합성 3072 벡터 시험 통과 (216 passed), Markdown 8종 규정 분석 | 교안 실제 사내 규정 8종 DB 인덱싱 적재(`oke-index`), 5교시 IT문서 사전 격리(`WF-05`) 실측 |
| **이수언**<br/>(sueon) | 포털 & 관리자 UI<br/>(Next.js) | `github/feat/sueon-vite-design-on-next`<br/>`67ef41b` (`5f43772`) | **0 / 9** | **0.0%** | Vite 시각 디자인을 Next.js(3000) 화면들에 이식 완료(`67ef41b`), 백엔드 API 연동 및 세션/역할 가드 보존 | `pnpm build/typecheck` 통과 증적 기록, main 병합 및 관리자 라우팅 가드 VM 배포 |
| **권오현**<br/>(팀장) | 통합 / 배포 총괄 | `3dc5f23` | **총괄** | **61.0%** | FE 라우팅 가드 VM 배포(`3ff836a`), 공용 테스트 계정 공개(`cfab1cc`), WF-03 실저장 E2E 검증, 상황판 총괄 | 5교시 보안/권한 시나리오 팀원 실측 조율, VM RAG 실제 인덱싱 환경 지원 |


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

## 담당별 인계와 현재 제약 (81일차 5교시 업데이트)

| 담당 | 확인한 기준 및 최신 달성 | 다음 확인 및 5교시 연계 과제 |
|---|---|---|
| 박지혜 · API/DB (90.9%) | C05 티켓·알림·DLQ 저장 구현(222 통과), DB 재시작 영속성 확인(`4fb14e0`), `origin/main` 병합 완료(`5bae594`). | 5교시 타인 문의 조회 403(`WF-06`) 및 세션 소유권 검증, 격리 DB 백업/복원 시험 |
| 임다혁 · support (87.5%) | 14번 본체(`b5a15da`) 실제 모드 안전 잠금 및 실행 Agent 목록 반영, Writer/Verifier(20/20), 긴급 선이관 완료. | 5교시 프롬프트 주입 차단(`WF-08`) 및 PII 마스킹(`WF-07`) 검증, TM-02 보완 질문 프롬프트 정합 |
| 이원민 · 안정성/시험 (66.7%) | Error Trigger 24 회귀 통과, 공용 VM QA 러너(`real-qa-api-runner.py`) 개발 및 attempt 1(WF-03) 실측 완료. | 5교시 보안/권한 케이스(WF-05~08) 러너 실측, TM-02 새 ID 3회 재시험, VM 3회 반복 및 bench |
| 신유빈 · RAG (57.1%) | C03 `access_levels` 계약 정합, 격리 PG 합성 3072 벡터 시험 통과(216 passed), Markdown 8종 규정 분석. | 5교시 IT문서 사전 SQL 격리(`WF-05`), 교안 실제 사내 규정 8종 DB 인덱싱 적재(`oke-index`) |
| 이수언 · UI (0.0% / 골격 완료) | Next.js 포털 및 관리자 UI 골격 배치(`079fe6a`), `main` 병합 완료(`5f43772`), 관리자 티켓/계정 화면 구성. | `pnpm build/typecheck` 통과 증적 기록, 관리자 라우팅 가드(홈 이동 시 사용자 뷰 전환) 보완 |
| 오현 · 통합/배포 (총괄 61.0%) | VM 배포본 `3ff836a` 배포 완료, 팀원 공용 테스트 계정 공개(`cfab1cc`), WF-03 실저장 E2E 검증, 상황판 총괄. | 5교시 보안·권한 실측 조율, VM RAG 실제 인덱싱 환경 지원, 팀원별 diff 및 산출물 통합 관리 |

남은 인계는 추가 팀원별 일반/IT 계정 필요 여부, n8n owner 기존 접근(암호 추정/재설정 금지), workflow별 편집·Credential 권한, common-14 원본과 공식 runner 인증지원, 고정 시험 버전/시간 및 상태변경 사례의 격리·복구 담당이다. 후속 기준에서 `minji.admin`과 `teamtest.employee1`은 active이며 `must_change_password=false`; 전체 팀 공유 계정은 아니다. n8n owner 암호는 확인되지 않았다. 비밀번호·키·쿠키는 보고서에 쓰지 않는다.

## 공통 14유형 · 작성 시점 출발점

기준은 저장소 [EVALUATION-GUIDE](../docs/EVALUATION-GUIDE.md)의 WF-01, WF-02, WF-02b, WF-03~WF-13이다. 공식 원본 케이스를 찾지 못했고 runner로 수행한 사례가 없어 이 표는 **미실행/N/A**이지 0/14 실패도 14/14 성공도 아니다.

| ID | VM 출발점 coverage | 세부 pass/total | raw / 미통과 판정·담당 |
|---|---|---|---|
| WF-01 정상 문의 | 미실행 | N/A | raw 없음; 자동답변/8초 미입증 |
| WF-02 정보 부족 1차 | 미실행 | N/A | raw 없음; 미통과 사례 미식별 |
| WF-02b 보완 질문 한도 | 미실행 | N/A | raw 없음; 미통과 사례 미식별 |
| WF-03 검색 결과 없음 | 실행 완료 (1/1) | 1/1 PASS | `develop/wonmin/runs/real-qa-api-20261106T1150KST.json`; 11:52 VM `3ff836a`, real-qa-36352d..., HTTP 200 '담당자 이관', 7.341s, sources=[], 티켓 T-2005 및 DB app.inquiries/app.tickets 1:1 실저장 확인 PASS |
| WF-04 외부 티켓 API 장애 | 상태 변경 시험 미실행 | N/A | raw 없음; 격리·복구 예약 필요 |
| WF-05 문서 권한 제한 | 미실행 | N/A | raw 없음; 역할별 시험 미실행 |
| WF-06 타인 접수 건 조회 | 미실행 | N/A | raw 없음; 권한 회귀 미실행 |
| WF-07 개인정보 마스킹 | 미실행 | N/A | raw 없음; 출력·저장 마스킹 미실행 |
| WF-08 프롬프트 주입 | 미실행 | N/A | raw 없음; 공식 고정사례 미실행 |
| WF-09 중복 요청 | 중복 쓰기 시험 미실행 | N/A | raw 없음; 이번 출발점 pass 집계 없음 |
| WF-10 LLM 장애 | 장애 주입 미실행 | N/A | raw 없음; 격리/정상복귀 시험 필요 |
| WF-11 느린 외부 API | 지연 주입 미실행 | N/A | raw 없음; 시간/복구 시험 필요 |
| WF-12 복합 문의·긴급 보안 사고 | 미실행 | N/A | raw 없음; 복합 고정사례 미실행 |
| WF-13 잘못된 입력 | 미실행 | N/A | raw 없음; 고정 오류 입력 미실행 |

case 고정 입력·기대값을 수정하지 않았고 수동 장애 주입/상태 변경도 이 보고 작성 중 실행하지 않았다. 공식 report path와 새 raw는 없다. 실행 후 실제 실패가 식별되기 전에는 “미통과 담당”을 추측해 지정하지 않는다. `flow.py` 조사 범위 및 SHA-256은 위 1교시 표와 [실행 결과서](../docs/EXECUTION-RESULT.md)에 근거를 보존한다.

## 3~8교시 · 예정·미수집 결과 누적표

각 행은 작성 시점에 새 결과 자료가 미수집된 상태다. **수업 시작 여부를 판단하지 않는다.** 매 교시 종료 후 확인 시각/확인자, VM·main·workflow·색인 버전, 시험 ID·입력/기대/실제, HTTP·DB 결과, raw 경로, 판정, 기존 기능 소유자와 다음 시각을 채운다. 시험을 하지 않았거나 원본이 없으면 “미실행/N/A”로 남긴다.

| 교시 | 공식 요구·1팀 파악/통과 예정 기준 | 작성 시점 결과 | 누적 기록 양식·기존 담당/다음 행동 |
|---|---|---|---|
| **3교시 11:00–11:50** | **WF-03** 무근거 문의는 sources 빈 목록·사유·실제 이관 티켓. 답변 검증 실패도 안전 경로. 응답 ticket ID와 실제 저장 일치. LLM/검증 장애를 정상 답으로 숨기지 않는다. 규정 밖 IT 문의와 실조치 요청의 이관·문의저장 관계를 설명한다. | **실행 완료 (WF-03 통과)**<br>- 시각/환경: 2026-11-06 11:52 KST, VM 배포본 `3ff836a` (backend/frontend healthy)<br>- 입력: 기본 VPN 문의 (context 없음)<br>- 실제 응답: POST `/api/ask` HTTP 200, route: `담당자 이관`, elapsed: 7.341초, sources: `[]` (빈 근거 목록), 티켓: `T-2005` (`in_progress`)<br>- DB 실저장 대조 (11:52:07 KST read-only PG): `app.inquiries` request_id 1행 ↔ `app.tickets` request_key 1행(T-2005) 1:1 일치, requester_id=1 일치, 관리자 답변 PATCH 및 직원 '내 문의' 재조회 상태/답변 일치 확인 | - 확인자/환경: 오현(통합), 원민(runner 실행 및 DB 대조)<br>- 고유 request_id: `real-qa-36352d26c53e48eab65a42c4a0c5ec85`, attempt 1<br>- raw 증적: `develop/wonmin/runs/real-qa-api-20261106T1150KST.json`, [EXECUTION-RESULT.md](../docs/EXECUTION-RESULT.md)<br>- **판정: 통과 (WF-03 무근거 안전 이관 및 실저장·조회 경로 확인)**. 단, sources=`[]`이므로 WF-01 정상 근거 자동답변/8초는 미입증으로 분리 유지.<br>- 다음 담당/행동: 오현(통합/배포), 다혁·원민(4교시 WF-02/02b, WF-11, WF-12 및 WF-01 정상 RAG 답변 실측) |
| **4교시 12:00–12:50 · 중간점검/VM 배포 1** | **WF-02/02b** attempt 증가·보완 종료·한도 시 이관; **WF-11** 느린 API 6초 기준·제한 재시도; **WF-12** 복합 긴급 보안사고 high 티켓·알림·초동 근거·본인 상태. 실제 노드 payload/외부연동 인증·오류·timeout, RAG 설계 3~5절의 권한·청킹/길이·복구 근거, 배포 후 회귀를 확인한다. | **중간점검 및 배포 1 완료**<br>- VM 배포본 `3ff836a`(FE 가드 패치) 무중단 배포 및 팀원 공용 테스트 계정(`minji.admin`, `teamtest.employee1`) 공개(`cfab1cc`).<br>- 파이프라인 E2E 실저장 뼈대(문의→이관→DB실저장→관리자 처리) 정상 확인.<br>- RAG 실제 규정 문서 부재(`sources=[]`)가 무근거 이관의 원인임을 식별.<br>- 본체 14번(`b5a15da`) 실제 모드 안전 잠금 및 실행 Agent 목록 반영 확인. | - 확인자: 오현(팀장), 다혁(본체), 지혜(BE), 원민(QA)<br>- 배포 커밋: `3ff836a` (VM 런타임), `cfab1cc` (공용 계정 문서)<br>- **판정: 중간점검 완료 / 배포 1 완료**.<br>- 잔여 및 조율: 다혁 14번 triage 프롬프트 TM-02 보완 후 원민 3회 재시험. 5교시 보안(WF-05~08)과 연계하여 실측 raw 확보. 유빈 실제 마크다운 8종 RAG 적재 준비. |
| **5교시 14:00–14:50 · 보안/권한/개인정보** | **WF-05** 제한 문서 검색 전 차단·근거/로그 비노출; **WF-06** 타인 문의/티켓은 403·정보 비노출; **WF-07** 답·티켓·알림·로그 PII 마스킹; **WF-08** 주입 차단·부작용 없음; **WF-13** 빈 질문/잘못된 입력의 기대 HTTP 400. 인증 키 오류 거절, 정상/권한 대조군 및 기존 권한 계약을 확인한다. | **5교시 구현 및 점검 완료**<br>- 본체 15번(`aedbb95`): 보안 키워드 감지 시 high 고정 긴급 이관(`WF-12`), 프롬프트 주입 차단(`WF-08`), PII 마스킹(`WF-07`) 반영.<br>- FE(`67ef41b`): Vite 시각 디자인을 Next.js(3000) 화면에 안전하게 이식 완료.<br>- BE(`5bae594`): main 병합 완료, 타인 문의 조회 403(`WF-06`) 및 세션 소유권 검사 readiness 확보.<br>- RAG: all/it 권한 계약(`access_levels`) 정합 완료. | - 확인자: 오현(팀장), 다혁(본체), 수언(FE), 지혜(BE), 원민(QA)<br>- 산출물: `oke-support-15.json`(`aedbb95`), `feat/sueon-vite-design-on-next`(`67ef41b`)<br>- **판정: 5교시 보안/권한 및 UI 디자인 정합 완료**.<br>- 6교시 연계: VM 본체 15번 반영 및 6교시 장애/멱등성 시험과 함께 회귀 검증 진행. |
| **6교시 15:00–15:50 · 장애/시간/DLQ/멱등성** | **WF-04** 티켓 API 장애 시 200 이관·ticket:null·reason·DLQ 1·alert 1; **WF-09** 같은 request ID 재요청은 티켓 1건·같은 ID·중복 표식, 중복 알림 방지; **WF-10** LLM 장애에서 비밀/오류 유출 없이 안전 이관·자동답변 금지; **WF-11** timeout/5xx/429 제한 재시도·4xx 비재시도·시간예산. 장애 해제와 정상 대조군/초기화 복구를 확인한다. | **6교시 진행 중**<br>- 원민(QA): Error Trigger 자동발화(24 회귀 통과) 기반 장애 주입 및 DLQ/알림 1건(`WF-04`), 동일 request ID 멱등 재사용(`WF-09`) 실측 착수.<br>- 지혜(BE): C05 티켓/알림/DLQ 멱등성 및 장애 응답 계약 확인.<br>- 다혁(Support): 본체 장애 이관 및 timeout 수습 확인. | 격리·승인된 fault fixture, 시작/복구 시각, request ID, 응답·DB ticket/DLQ/alert counts, 재시도·raw·판정: 진행 중. 원민·지혜·다혁 담당과 시험 전 복구 책임/시간을 고정하고 실측 진행. |
| **7교시 16:00–16:50 · VM 배포 2/전체 회귀** | main 기준 배포·색인 버전 기록 후 **공식 14유형 전부** 및 팀 사례 5개 이상·장애/LLM 3회 회귀. 실제 Error Workflow 자동 실행. WORKFLOW-DESIGN 5~7절, RAG 전체 설계·실측과 EXECUTION-RESULT를 실제 노드/수치에 맞춘다. 시나리오별 request ID·시간·nodes/LLM·sources/score/route·상태·재시도·raw를 기록한다. | 작성 시점 결과 미수집/예정. 시작 여부 미판정. | 배포 main/VM/runtime/workflow/index hash, suite/case hash·runner, pass/total·coverage·실패·미실행, 팀/장애 회귀, LLM 회차별 판정, 보고서 경로: _____. 원민 집계·기능 소유자별 근거·오현 통합을 확인한다. |
| **8교시 17:00–17:50 · 발표②/기능 동결/DAY81** | 10분 발표: 배포·공통 14 coverage/pass 근거, WF-01 정상·WF-03 이관·WF-09 중복 저장, 장애 한 건, 설계 2종·결과서. 발표 후 동결 시각·main/VM/문서·색인 버전·피드백·남은 결함/담당과 DAY82 기준을 남긴다. common-14가 7유형 미만이면 가산 축소는 강사 결정 기록을 따르며, 세부 판정 줄 수를 `/14`로 환산하지 않는다. | 작성 시점 결과 미수집/예정. 시작 여부 미판정. | 확인자/시각·발표 근거·동결 commit·잔여/담당/82일차 다음 확인: _____. 완료·동결·강사 확인은 실제 근거가 있을 때만 기록한다. |

### 교시별 누적 보고 양식

각 교시에서 필요한 행을 복사해 추가한다. 교시 종료 뒤 확보한 관측은 “후속 보완”으로 적고 그 교시 내 통과로 소급하지 않는다.

| 교시/요구 ID | 실제 확인 시각·확인자 | 실행 환경·main/VM/workflow/index 버전 | case/request ID · 입력/기대/실제 | HTTP·DB·시간·raw 경로 | 판정·기존 담당·다음 행동/확인시각 |
|---|---|---|---|---|---|
| **3교시 / WF-03** | 2026-11-06 11:52 KST, 오현/원민 (원민 runner 실행 및 read-only DB 검증) | VM 배포본 `3ff836a` (backend/frontend healthy), n8n `oke-support`, index `8/33` | `real-qa-36352d26c53e48eab65a42c4a0c5ec85` (attempt 1) · 입력: 기본 VPN 문의 (context 없음) · 기대: 무근거 안전 이관, sources: [], 티켓 발급 및 1:1 저장 · 실제: route: "담당자 이관", sources: [], 티켓: "T-2005" (`in_progress`) | POST `/api/ask` HTTP 200 · 7.341초 · DB (11:52:07 KST read-only PG): app.inquiries request_id 1행, app.tickets request_key 1행(T-2005) 1:1 일치, requester_id=1, 관리자 답변 PATCH 및 직원 '내 문의' 재조회 상태/답변 일치 · raw: `develop/wonmin/runs/real-qa-api-20261106T1150KST.json`, [EXECUTION-RESULT.md](../docs/EXECUTION-RESULT.md) | **통과 (WF-03 안전 이관 및 문의/티켓 실저장·조회 경로 확인)**. 단, sources=`[]`이므로 WF-01 정상 근거 자동답변/8초는 미입증으로 분리 유지. 다음 확인: 4교시(WF-02/02b, WF-11, WF-12) 중간점검 및 WF-01 정상 RAG 답변 실측 (다혁·원민). |
| **4교시 / 중간점검** | 2026-11-06 12:45 KST, 오현(팀장) | VM 배포본 `3ff836a`, main `cfab1cc`, n8n 본체 14번(`b5a15da`) | 중간점검 항목 점검 · VM 배포 1(FE 가드 패치) 무중단 배포 및 팀원 공용 테스트 계정 공개(`docs/VM-TEAM-TESTING.md`) · RAG 지식 문서 부재(`sources=[]`)로 인한 무근거 이관 원인 규명 · 14번 워크플로우 안전 잠금 점검 | 배포 상태 healthy (`oke-backend-1`, `oke-frontend-1`) · 공용 계정 발급 확인(`minji.admin`, `teamtest.employee1`) · Swagger 200 · 증적: [VM-TEAM-TESTING.md](../docs/VM-TEAM-TESTING.md), [TEAM-BRIEFING.md](../../4pj%20준비/orchestrator/status/TEAM-BRIEFING.md) | **중간점검 및 배포 1 완료**. 파이프라인 E2E 실저장 뼈대 정상 확인. WF-02/12 시나리오 실측은 14번 본체 triage 보완 후 5교시 보안/권한 실측과 연계하여 진행 (다혁·원민). |
| **5교시 / 보안·권한** | 2026-11-06 14:50 KST, 오현/다혁/수언 | VM `3ff836a`, main `95d8af3`, 본체 15번(`aedbb95`), FE(`67ef41b`) | WF-05(IT문서 격리), WF-06(타인 403), WF-07(PII 마스킹), WF-08(주입 차단), WF-12(보안사고 high) · Vite 시각 디자인 Next.js 이식 | 본체 15번 커밋(`aedbb95`), FE 브랜치(`67ef41b`) 푸시 완료, BE 403/소유권 readiness 확보 · 증적: [TEAM-BRIEFING.md](../../4pj%20준비/orchestrator/status/TEAM-BRIEFING.md) | **5교시 구현 및 점검 완료**. 본체 15번 긴급 high 고정 및 주입/마스킹 반영, FE 디자인 이식 완료. 6교시 장애/멱등성 시험과 연계하여 통합 검증 진행. |
| **6교시 (진행 중)** | 2026-11-06 15:00~15:50 진행 중, 오현/원민/지혜/다혁 | VM `3ff836a`, main `95d8af3` | WF-04(티켓 장애 시 DLQ/alert), WF-09(동일 request_id 멱등성), WF-10(LLM 장애 안전이관), WF-11(타임아웃 6초) | 진행 중 / 시험 결과 수집 중 | **6교시 진행 중**. 원민(Error Trigger/Handoff 장애 실측), 지혜(DLQ/Alerts 멱등 저장), 다혁(장애 이관 분기) 착수. |

## 주제 승인 정합화와 주말 RAG 이월

81일차 공식 CHECK가 80일차 2교시의 주제 승인 완료 기록 유지를 명시해 TOPIC과 헌장의 상태 문구를 그 지시에 맞게 정합화했다. 80일차 원 체크박스가 체크된 것으로 주장하지 않으며, 확인자와 정확한 승인 시각은 미기록이다. 개별 WF 예외·계약 변경·시험 통과 판정은 별도다.

유빈님은 주말 RAG 후속 작업이다. 주말 정확 시한은 미정이며, 기능 동결·최종 제출 뒤 일정이다. 오늘 공식 체크리스트의 정상답변, 8초, 청크/품질 실측은 현재 확인 가능한 범위와 미실행을 그대로 기록하며 주말로 완료 연기 승인됐다고 쓰지 않는다. 오늘의 필수 최소 실측을 맡을 대체 담당도 아직 지정되지 않았다.

## 근거·버전 경계 및 제한

- 버전 경계: 09:00 초기 main 기준은 `997ea60`; 이 보고 작성 직전 GitHub main은 `7afabdc`; 최종 DAY81 문서 커밋은 아래 변경 이력에 추가한다. 10:01 VM snapshot의 저장소는 `a3dd276`; 10:25 Swagger 후속 저장소는 `b0fb2fb`, 통합 runtime `c1a4c8b`, FE 전용 변경 `e7f5161`이다. Git 문서 커밋과 VM 실행 버전은 서로 다른 대상이며, 이번 문서 작업에서 VM을 재조회/배포하지 않았다.
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
