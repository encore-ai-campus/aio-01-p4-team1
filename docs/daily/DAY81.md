# DAY 81 일일 진행 기록 · 1교시 기준

> 작성 기준: 2026-11-06 09:00–09:50 1교시 제출 범위. 공개 FE 재확인은 10시대, VM DB/workflow/자원 snapshot은 관제의 읽기 전용 10:01 KST 측정이다. 이후 교시의 수행·통과를 이 보고에 앞당겨 적지 않는다.

## 1. 오늘 목표와 1교시 요약

공식 81일차 체크리스트 1교시 요구는 전일 피드백과 오늘 목표·담당·다음 확인 시각 정리, main/VM/문서/색인 readiness 구분, 공통 14유형 시험 출발점, 80일차 주제 승인 기록 정합화다. 오늘의 후속 목표에는 WF-01 정상 근거 답변, 보완·이관·권한·장애 검증이 포함되며, 이 1교시 보고는 이를 완료로 표시하지 않는다.

| 체크리스트 항목 | 1교시 관측·판정 | 잔여 / 담당·다음 확인 |
|---|---|---|
| 피드백·오늘 목표·담당·다음 시각 | 공식 81일차 체크리스트와 팀 헌장의 주 담당을 기준으로 범위를 정리했다. 기존 피드백은 실문서 검색·권한·동일 VM 정상/이관 증거를 요구한다. | WF-01 응답과 8초 기준 등 당일 필수 항목은 후속 시험에서 확인. 각 교시 결과·시간은 실제 실행 후 기록한다. 세부 일정·미지정 대체담당은 팀장 확인 대상. |
| main / VM / 문서 / 색인 readiness | repo main `997ea60`; VM repo `a3dd276`; VM runtime 구현 `c1a4c8b`로 구분. VM app/DB ready, 기존 색인 `8 documents / 33 chunks`; 공개 로그인 진입 성공. | main `997ea60`은 VM에 배포된 것으로 보지 않는다. 정상 자동답변 품질·threshold, 로그인 사용자 흐름과 공통 14 판정은 미완료. |
| 공통 14 출발점 | 저장소 `docs/EVALUATION-GUIDE.md`에 WF-01~WF-13 및 WF-02b 기준 14유형이 정의돼 있다. 공식 `cases/common.json` 원본은 저장소와 수업 79 디렉터리에서 찾지 못했다. 79 `flow.py`는 `Content-Type`만 보내며 `X-Team-Key`를 지원하지 않는다. | 공식 케이스 원본·호환 runner 미확인으로 이번 출발점의 실행 결과, pass/total, raw 경로는 없음(N/A). 14 PASS 또는 0/14 실패로 집계하지 않는다. 원민님은 공식 원본·해시·인증 지원 절차를 확인하고, 기능 담당은 기준에 맞는 시험을 준비한다. |
| 주제 승인 기록 | 81일차 공식 체크리스트는 80일차 2교시 네 팀의 최종 주제 승인 완료 기록을 유지하라고 명시한다. TOPIC/헌장의 과거 “승인 전” 표기를 아래처럼 정합화했다. | 확인자와 정확한 승인 시각은 제공된 기록에서 특정하지 않아 기입하지 않았다. 별도 기능 예외 판정과는 구분한다. |

### 기준·범위 구분

- **1교시 보고자료 작성 완료:** 오늘 기준·버전 경계·읽기 전용 VM 상태·공통시험 도구 제한·승인 기록을 정리하고 팀 사용 안내를 작성했다. **공통시험 출발점은 미완료**이며 공식 원본·실행 결과·raw가 없다.
- **현재 VM readiness:** 관제 snapshot(2026-11-06 01:01 UTC / 10:01 KST, VM repo `a3dd276`)에서 Compose `oke` 컨테이너 9개가 실행 중, PostgreSQL revision `0005`, backend readiness `ready`/`app`, 내부 FE `/login` 200, 자원 RAM 2646 MiB total/1436 MiB available, swap 2965 MiB total/224 MiB used였다. PostgreSQL 행 수는 employees/users/tickets/alerts/DLQ `6/1/3/4/1`, RAG documents/chunks `8/33`. `minji.admin`은 활성 admin이며 `must_change_password=true`다. 해당 계정·비밀번호 상태는 변경하지 않았다.
- **Workflow runtime:** SQLite 읽기 전용 metadata에서 `oke-support`, `oke-search`, `oke-handoff`, `oke-errors` 활성 4개, `oke-index` 비활성/manual 1개, credential 레코드 6개를 확인했다. 활성 version ID는 [VM 시험 안내](../VM-TEAM-TESTING.md)의 관측 표에 기록했다. 이 n8n 버전 ID들은 Git commit이 아니다.
- **공개 경로 확인:** read-only curl에서 `http://aio-t1.isitsoft.kr/login` 301 → HTTPS 최종 200, FE HTML 200 및 Next static JS asset 200, no-cookie `https://aio-t1.isitsoft.kr/api/auth/me` 401, `https://aio-t1.isitsoft.kr:5678/healthz` 200을 확인했다. FastAPI 공개 origin/prefix는 `https://aio-t1.isitsoft.kr/api`; 내부 `http://backend:8000`은 팀원 PC 직접 주소가 아니다. 초기 확인에서는 `/api/docs`, `/api/openapi.json`, `/docs`, `/openapi.json`이 404였다. 아래 Swagger 후속 배포에서 `/docs`와 `/openapi.json`을 지원하도록 보완했다. 이전 문서의 외부 FE 502/3000 timeout은 당시 역사 관측이며 현재 외부 FE 미연결 상태로 쓰지 않는다. 로그인 페이지/401/health만으로 직원 로그인·질문·저장 완료를 주장하지 않는다.
- **비밀 인계 분리:** 팀장 전용 기존 VM 관리자 인계는 저장소 밖 `orchestrator/private/VM-TEAM-ACCESS.txt`에 권한 600 파일/700 디렉터리로 보관한다. 공개 문서에는 주소와 절차만 남기며 이 파일은 팀 전체 공유물이 아니다. n8n owner 암호는 확보되지 않아 현재 운영자 인계가 필요하다.
- **이 보고가 다루지 않는 완료 주장:** 공통 14 전체 실행, WF-01 자동답변/8초, 오늘 필수 실측, 4교시 중간 점검, 7회귀, 8교시 동결·발표는 완료되지 않았다. 주말은 기능 동결·최종 제출 후 이어질 RAG 후속 인계이며 오늘 필수 마감의 대체나 연기 승인이 아니다.

## 2. 담당별 현재 기준과 다음 확인

기능 소유자는 [팀 헌장](../TEAM-CHARTER.md)의 기존 담당을 따른다. 개인별 보고와 당일 교시 마감은 별도 증거로 확인한다. 수언/지혜/다혁/원민의 교시별 실행 마감은 공식 체크리스트에 따르고, 아래의 다음 시각은 해당 요구를 다시 확인할 체크포인트다. 새 담당자를 임의 지정하지 않았다.

| 담당 | 1교시에서 확인한 기준 | 후속 확인 / 인계 필요 |
|---|---|---|
| 오현님 | 공통 기준·병합·VM·제출 취합 담당. VM은 `a3dd276`/runtime `c1a4c8b`; repo main `997ea60`. | 매 교시 배포본·시험 예약·결과 취합. 일반/IT 시험 계정 및 팀원 접근 범위를 안전하게 인계할 필요가 있다. |
| 수언님 | FE 공개 진입 경로 확인 가능; 인증된 사용자 UI end-to-end는 미검증. | 계정이 발급된 환경에서 로그인→질문/내 문의→로그아웃 경로를 확인. 사용자 데이터가 저장됐다고 UI 표시만으로 판정하지 않는다. |
| 지혜님 | VM backend `app` readiness, DB `0005`, 직원 6명·사용자 1명 확인. | 일반/IT 시험 계정, 권한·본인/타인 조회와 C05 저장 증거를 후속 검증. 계정/비밀 인계는 팀장이 관리한다. |
| 다혁님 | VM support workflow 활성. 정상 자동답변 품질·실제 8초 판정은 아직 없음. | 공식 81일차의 WF-01 정상 근거 답변과 후속 보완/이관 분기를 실제 입력으로 검증하고 raw를 남긴다. |
| 유빈님 | 부재 확정, 기존 VM RAG 8/33 및 검색 근거는 앞선 실행 결과에 기록. | 유빈님은 **주말 RAG 후속**으로 둔다. 오늘 교시 마감 담당으로 배정하거나 오늘 미실측을 완료 처리하지 않는다. 오늘 기준으로 미검증된 정상답변/점수·청크 실측은 미완료로 남기고, 필요 시 팀장이 오늘 대체 측정 담당과 시간을 정한다(현재 미지정). 주말 후속은 기능 동결·최종 제출 이후 일정이며 오늘 필수 기준을 연기하는 승인이 아니다. |
| 원민님 | 시험/결과 담당. official common-14 원본 JSON과 공식 키트가 현재 checkout에서 없음. | 공식 키트 입수·원본 hash·인증 지원 여부와 실행 raw 경로 확인. 공통 판정 미실행을 실패나 통과로 바꾸지 않는다. |

팀 차원의 추가 인계: (1) 김민지 지정관리자/팀장이 기존 `must_change_password=true` 계정을 정식 화면에서 첫 변경한 뒤 제공 직원 중 필요한 일반/IT 시험 계정을 개별 발급하고 각 사용자에게 비공개 전달할 담당·시점, (2) n8n owner email은 팀장 전용 private handoff만 사용하고 현재 owner가 인계할 암호/접근권한을 확인(암호 추정/reset 금지), (3) n8n 편집 및 webhook별 credential 사용 권한과 비밀 전달 방식, (4) 공통 키트 원본·지원되는 인증 절차, (5) VM 시험 시간대·배포본 고정·fixture 초기화 및 쓰기 시험 복귀 책임, (6) 오늘 필수 측정 이후 주말 RAG 잔여 범위. 개인별 ID·비밀번호·API key 값은 저장소에 기록하지 않는다.

## 3. 공통 14유형 출발점 판정

판정 기준 목록은 `docs/EVALUATION-GUIDE.md`의 WF-01, WF-02, WF-02b, WF-03~WF-13이다. runner로 수행한 사례는 없으므로 다음 표는 “미실행” 상태를 보여 주며, failure count나 pass ratio가 아니다.

| ID (EVALUATION-GUIDE 기준명) | VM 출발점 coverage | 세부 pass/total | raw / 미통과 담당 |
|---|---|---|---|
| WF-01 정상 문의 | 실행 미확인 | N/A | raw 없음; 미통과 아님(미실행). |
| WF-02 정보 부족 (1차) | 실행 미확인 | N/A | raw 없음; 미통과 아님(미실행). |
| WF-02b 보완 질문 한도 도달 | 실행 미확인 | N/A | raw 없음; 미통과 아님(미실행). |
| WF-03 검색 결과 없음 | 실행 미확인 | N/A | raw 없음; 미통과 아님(미실행). |
| WF-04 외부 티켓 API 장애 | 상태 변경 시험 미실행 | N/A | raw 없음; 실패 없음으로 집계하지 않음. 격리 환경/예약 필요. |
| WF-05 문서 권한 제한 | 실행 미확인 | N/A | raw 없음; 미통과 아님(미실행). |
| WF-06 타인 접수 건 조회 | 실행 미확인 | N/A | raw 없음; 미통과 아님(미실행). |
| WF-07 개인정보 마스킹 | 실행 미확인 | N/A | raw 없음; 미통과 아님(미실행). |
| WF-08 프롬프트 주입 공격 | 실행 미확인 | N/A | raw 없음; 미통과 아님(미실행). |
| WF-09 중복 요청 | 중복 쓰기 시험 미실행 | N/A | raw 없음; 재요청/저장 결과 집계 없음. 예약 필요. |
| WF-10 LLM 장애 | 장애 주입 시험 미실행 | N/A | raw 없음; 실패 없음으로 집계하지 않음. 격리 환경/예약 필요. |
| WF-11 느린 외부 API | 지연 주입 시험 미실행 | N/A | raw 없음; 실패 없음으로 집계하지 않음. 격리 환경/예약 필요. |
| WF-12 복합 문의 · 긴급 보안 사고 | 실행 미확인 | N/A | raw 없음; 미통과 아님(미실행). |
| WF-13 잘못된 입력 | 실행 미확인 | N/A | raw 없음; 미통과 아님(미실행). |

공식 원본·해시·runner가 없어 위 표의 실제 실행 coverage는 **미실행/N/A**다. 수동 고장 주입·상태 변경을 하지 않았다. 현재 미통과 사례는 없다고 단정할 수 없으며, 테스트를 실행하지 않아 미통과 사례/담당이 아직 식별되지 않았다. 결과 수집 담당은 원민님 역할이지만 각 기능 결함 담당은 실행 후 소유 경로와 근거로 특정한다.

### 공식 runner 조사 결과

- `cases/common.json`은 저장소에 없다. `develop/wonmin/cases/`에는 handoff/errors/team 등 팀 자체 입력 파일이 있지만 이를 공식 공통 14 원본으로 간주하지 않는다.
- 수업 디렉터리 `Last3Mon/79/tools/flow.py` SHA-256 `6b0059cb3af135b08954559d0e6b757991fc2fc42a0624244d129e618284fb6f`; 해당 코드의 HTTP request helper는 `Content-Type: application/json`만 설정하고 custom team header를 보내지 않는다. 검사 전용 `develop/dahyeok/tools/flow.py`는 Mock checker라 공식 runner 대체가 아니다.
- 따라서 공식 14의 `coverage`, 세부 pass/total, test-run raw 결과는 **미실행/N/A**. 유효한 공통 report path는 아직 없다. case 정의·기대값을 만들어 내거나 runner 제한을 없애기 위해 인증을 제거하지 않는다.

## 4. 주제 승인 정합화·다음 단계

80일차 2교시의 네 팀 주제 최종 승인 완료는 81일차 공식 checklist가 유지 대상으로 명시한다. `TOPIC.md`와 헌장의 상태를 그 사실에 맞게 고쳤다. 승인 확인자/시각은 미기록으로 둔다. 개별 WF 예외 판정, 공통 기준 변경 또는 시험 결과는 이번 승인 정합화와 별도다.

다음 우선순위는 오늘의 공식 교시별 목표를 그대로 수행하고 증거를 모으는 것이다. 실제 정상 답변·8초 기준, 공통 14 실행, 권한 및 저장·장애 회귀는 각각 시험 ID/배포·workflow 버전/시각/입력/기대/실제/HTTP·DB/raw를 남긴 뒤에만 판정한다. 주말 RAG 인계는 오늘 요구를 완료 처리하거나 미루는 근거로 사용하지 않는다.

## 5. 근거·버전 경계

- Repo main 기준: `997ea60` (VM 미반영). VM repository snapshot: `a3dd276`; VM runtime implementation: `c1a4c8b`. 각 버전은 다른 실행 대상을 가리킨다.
- VM current snapshot은 관제 read-only 결과 `DAY81-VM-READONLY-SNAPSHOT.txt` (UTC 2026-11-06 01:01)에서 인용했다. VM 설정·서비스·계정·데이터를 변경하지 않았다.
- 공개 FE 상태는 본 보고 작성 시점의 read-only HTTP 관측이다. 로그인 비밀정보를 사용하거나 로그인 시도하지 않았다.
- 다음 교시에서 추가 관측이 생기면 시간과 배포 commit을 함께 적고, 과거 관측을 소급해 덮어쓰지 않는다.

## 후속 작업 · Swagger 공개 경로

2026-11-06T10:24:37.289524+09:00 · `vm-public-swagger-1`, FE 코드 `e7f5161`. frontend에 `/docs`와 `/openapi.json` rewrite만 추가해 공개 Swagger UI/JSON 스키마를 각각 HTTP200으로 확인했다. VM frontend만 재빌드/재생성했고 다른 OKE 서비스 ID/시작시각은 유지됐다. login/정적JS200, no-cookie me401, n8n health200 회귀 확인. 계정·업무 API·DB·workflow·외부포트/ingress 변경이나 업무 POST 시험은 하지 않았다. 정확한 주소와 한계는 [VM 사용 안내](../VM-TEAM-TESTING.md#swagger-공개-경로-추가)를 따른다.
