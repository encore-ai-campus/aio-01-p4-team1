# DAY 80 · 2026-11-05 · 설계와 첫 통합

> 11월 5일의 작업·관측 기록이다. 아래 미완료·진행률은 당시 상태이며, 이후 결과는 [DAY81](DAY81.md)과 [DAY82 사전 준비](DAY82.md)에서 구분한다. 문서 정리 과정에서 새 VM 시험·배포를 수행하지 않았다.

## 1. 오늘의 숫자

| 항목 | 아침 | 저녁 |
| --- | --- | --- |
| 공통 시나리오 통과 /14 | 당시 집계 미기록 | 당시 집계 미기록 |
| 팀 시나리오 통과 /전체 | 당시 집계 미기록 | 당시 집계 미기록 |
| 장애 시나리오 통과 /전체 | 당시 집계 미기록 | 당시 집계 미기록 |
| 정상 문의 p50 (`bench -n 5`) | 당시 집계 미기록 | 당시 집계 미기록 |

집계 미기록은 전체 실패나 미실행을 뜻하지 않는다. 개별 검색·이관·입력 차단 관측은 아래에 보존하되, 원본 집계가 없는 값을 /14 또는 p50으로 환산하지 않는다.

## 2. 팀원별 한 일

- main에 팀 공통 워크플로우·설계 문서와 팀 사례를 통합하고, 유빈 C03 권한 계약 및 지혜 P1-1 로그인·세션, P1-2 문의 저장/C02 변경을 반영했다. 원민 `90f02aa`는 통째로 병합하지 않고 담당 소유의 handoff/errors 시험 도구·사례·검토 자료만 선별했다.
- 최초 DAY80 통합 기준은 `952f704`였다. 후속 `unified-vm-finish-2` 통합 커밋 `3e0f701`을 main에 푸시하고 VM도 같은 커밋까지 fast-forward했다. 아래 VM 결과는 `3e0f701`에서 별도로 수행한 관측이며 최초 스냅샷과 구분한다.
- 팀 진행 체크는 **23/41 = 56.1%**다. 이는 역할 단계 수를 균등 합산한 지표로 Mock·로컬 완료를 포함하며 VM 성공률이나 공식 시나리오 통과율이 아니다.

> 이 표와 아래 최초 통합 관측은 2026-11-05 당시 스냅샷이다. 이후 수언 UI 커밋, 공개 FE 경로, 관리자 선택 등 후속 결과는 [DAY81](DAY81.md)과 [VM 팀 사용·시험 안내](../VM-TEAM-TESTING.md)를 참조한다. 아래의 0/9와 당시 막힘은 이력이며 현재 상태로 읽지 않는다.

| 담당 | 단계 | 오늘 반영된 커밋·근거 | 남은 일 |
|---|---:|---|---|
| 이수언 · UI | 0/9 (0%) | 원격 브랜치/커밋 없음. 상태 보고에는 로컬 화면 작업 공유만 있음. | 화면 골격 첫 커밋, 실제 백엔드 프록시·로그인·문의 연결 |
| 박지혜 · API/DB | 9/11 (81.8%) | `6348b87` P1-1 로그인·세션·계정, `2e64cd1` P1-2 문의 저장/C02. 전용 DB·MockTransport 검증 기록은 개인 문서에 있음. | P1-3 티켓·알림·DLQ 영속 저장 및 실연결 |
| 임다혁 · support | 7/8 (87.5%) | 본체 `b975286` (이미 main 반영), WF-12 및 접수 불확실 응답 로컬 보완. | 실제 C03·Writer/Verifier·공식 공통/팀 회귀·bench |
| 신유빈 · RAG | 4/7 (57.1%) | `6780432` C03 `access_levels` 계약 정렬. 기록상 Python Fake 190개·JavaScript Fake 3개 통과; VM 실검색은 아님. | 서비스 기동, 실문서 색인/검색, 권한과 청킹 품질·시간 실측 |
| 이원민 · handoff/QA | 3/6 (50%) | `90f02aa`에서 고유 tools/tests/cases/review 산출물만 선별 통합. root 사본과 소유 폴더 워크플로우를 분리 보존. | app 저장 연결, 공식·팀 회귀, 반복·bench 및 VM 검증 |
| 오현 · 통합/배포 | 개발 역할 합산 분모 제외 | 팀 브랜치 통합, 배포·관측 보고와 제출 문서 정리. main 기준 `952f704`. | VM C03 경로/서비스, 색인·정상/이관 종단 증거 확보 |

역할별 단계 수는 당시 관제 상태의 0/9, 9/11, 7/8, 4/7, 3/6을 따른다. 합계 23/41은 단계 수 합산이며 개인 퍼센트 평균이 아니다.

## 3. 막힌 것과 해결

| 막힌 것 | 원인·확인 범위 | 당일 해결 또는 남은 상태 |
| --- | --- | --- |
| C03 연결 실패, RAG 0문서·0청크 | 최초 `952f704` 관측에서 RAG 컨테이너·8765 수신 경로 미구성 | 후속 `3e0f701`에서 실규정 8문서·33청크 색인 및 일반·IT 검색 HTTP 200 확인 |
| 정상 질문도 안전 이관 | 지원 요청이 `low_confidence`, `sources=[]`로 종료 | 실제 티켓 `T-2002` 저장은 확인. 근거 자동답변 품질은 당일 미입증 |
| 공개 화면 접속 실패 | 외부 루트 502, 3000 포트 시간 초과 관측 | 당일 런타임 정리에서도 미해결. 후속 공개 경로 확인은 DAY81 기록 |
| 공식 시험 집계 확보 | 당시 공식 사례 파일을 찾지 못했고 runner 인증 지원에도 제약이 있었음 | 공통 14개 전체 재현은 당일 미완료. 기대값을 수정해 통과시키지 않음 |

## 4. 다음 날 할 일

아래는 DAY80 종료 당시의 계획이다. 이후 완료 여부는 [DAY81](DAY81.md)에서 확인한다.

1. 공개 로그인 경로의 502·시간 초과를 해결하고 직원·관리자 접속을 확인한다.
2. 첫 관리자 선택과 직원 계정 발급 후 로그인·로그아웃·재로그인, 본인 조회와 타인 조회 거절을 확인한다.
3. 고정 정상 질문 1건의 근거·자동답변·응답 시간을 확보하고, 검색 성공과 안전 이관 결과를 별도로 기록한다.
4. 공통 14개·팀 사례·장애 사례의 실행 원본과 집계를 확보한다. 당시 목표 통과 수와 완료 시각은 미기록이므로 소급해 채우지 않는다.

## 5. 강사 피드백과 전달 사항

강사가 직접 작성한 피드백 원문·확인자·시각은 이 일지에 수록되어 있지 않다. 다음 내용은 팀장이 전달한 7교시 피드백 요지이며 강사의 직접 작성·승인 기록과 구분한다.

- 실문서 DB 검색을 연결하고 색인 건수·청크 길이·권한 검색 결과를 기록한다.
- `security-incident` 권한과 인증 계약을 정렬한다.
- 같은 VM에서 정상 문의와 이관의 실행 근거를 남긴다.

후속 `3e0f701`에서 8문서·33청크와 일반·IT 검색, 안전 이관 저장을 확인했지만 정상 자동답변 품질과 전체 공식 시험은 당일 미입증이었다.

공식 일정은 7교시 VM에서 **WF-08 인젝션 차단·WF-13 잘못된 입력**, 8교시 설계 초안·VM 동작 발표와 피드백·일지 제출이다. **타인 접수 건 조회 차단은 WF-06**이며 별도 시험으로 구분한다.

## 상세 이력

<details>
<summary>최초 관측 → 통합 → 런타임 정리 기록</summary>

### 최초 VM 관측 · `952f704`

- 당시 VM main 커밋 `952f704`; n8n 컨테이너 재시작 후 주요 workflow 4개 활성. PostgreSQL healthy, Alembic `0005`.
- 관측 시 `rag.documents/chunks=0/0`, `app.tickets=0`. mode는 `practice`. 8 KiB 파일 put/get 내용 일치가 확인된 관제 기록이 있다.
- 이전 본체 실행 `manual-38042b9550d14ce3b3b447a1bdbef2c8`: 질문 `비밀번호 초기화 절차를 알려주세요`, HTTP 200, `search_unavailable`, 이관 응답의 ticket `T-2001`, `sources=[]`. 이는 응답 관측이지 실제 DB 티켓 저장·영속성의 증거가 아니다. 최신 `952f704`에서 그 요청을 재검증한 것도 아니다.
- 이후 검색 C03 확인은 HTTP 000/connection reset, RAG 컨테이너 및 8765 listener 미구성으로 실패했다. 배포 스모크는 미완료다. 실제 문서 색인·성공 검색 1건·이관 1건 종단 검증은 없다.
- 원민 로컬 회귀 일부는 Mock startup timeout 및 기대 응답 계약 오류로 실패했다. 통과로 집계하지 않았다. JSON 파싱·`git diff --check`·배포 스크립트 `bash -n`은 해당 점검 범위에서 통과했다.

### 후속 VM 통합 · `3e0f701`

- 변경 커밋 `3e0f701`을 `github/main`에 푸시하고 VM `main`에 반영했다. VM mode는 backend/n8n/runners 모두 `app`; PostgreSQL named volume과 n8n 데이터/암호화 키는 유지했다. Compose config 검증 후 backend, FE, RAG search를 순차 빌드했다. n8n에 typed credential 4종을 용도별로 연결하고 기존 OpenAI credential을 재사용해 support/search/handoff/errors를 stable ID로 import/publish했다. index workflow는 수동 실행이라 비활성이다.
- 공식 CLI `seed-employees` 결과 `created=6`; DB employees=6, users=0이다. 최초 관리자 선택은 김민지/minji.admin 또는 정우성/woosung.admin 중 관제 답변 대기라 계정은 만들지 않았다.
- RAG manifest는 read-only 원본 8개와 SHA-256을 검증했다. access level은 승인된 기준대로 일반 문서 7개=`all`, `security-incident` 1개=`it`. 실색인 HTTP 200, indexed=8, rejected=0, failed=0, 청크=33; DB 실측 `rag.documents/chunks=8/33`이다. 색인/검색 LOGIN은 각각 최소권한 그룹만 상속한다.
- 검색서비스 직접 요청: 일반 `all` 접근으로 비밀번호 정책 3개 근거, HTTP 200; IT 접근으로 보안사고 문서 근거 포함, HTTP 200. n8n `/webhook/oke-search`에서도 일반 문서 근거 3개와 HTTP 200을 확인했다. 점수 threshold/hit@3 품질 승인은 아직 없다.
- n8n `/webhook/oke-handoff` 요청 `vm-fin2-handoff-20261105-01`은 C04 저장 `T-2001`, HTTP 200, alert 성공. 동일 요청을 다시 보내 같은 `T-2001`과 `duplicate=true`를 확인했다. 정상 지원 요청 `vm-fin2-support-20261105-01`은 HTTP 200, `low_confidence` 이관, 실제 `T-2002` 저장; 응답 근거는 비어 있어 자동답변 PASS로 보지 않았다. 빈 질문은 HTTP 400/question_required. 주입 입력은 HTTP 200이지만 `route=차단`, `reason=prompt_injection`, ticket=null로 정책 차단됐다. 현재 워크플로우 계약은 입력 검증 400과 차단 응답 200을 구분한다.
- PostgreSQL을 재시작한 뒤 healthy, backend readiness 200, FE `/login` 200을 재확인했다. 이후 DB counts는 employees=6/users=0/tickets=2/alerts=3/DLQ=1, RAG=8/33이었고 `T-2001` 및 `all=7,it=1`가 유지됐다. 총 메모리 2646 MiB 중 available 1344 MiB, disk free 41 GiB, 주요 컨테이너 OOM=false다.
- 당시 공개 FE 관측은 `https://aio-t1.isitsoft.kr/` 502, 외부 `:5678/healthz` 200, `:3000/login` timeout이었다. 이는 2026-11-05의 역사적 상태다. 후속 확인에서 공개 `/login`, `/docs`, `/openapi.json`이 200으로 응답했으며 현재 URL과 경계는 [VM 팀 사용·시험 안내](../VM-TEAM-TESTING.md)에 기록했다.
- 공식 `Last3Mon/79/tools/flow.py`의 check는 팀 root source의 배포 credential placeholder와 course 전용 `openAiCourse0001` ID 기대 때문에 오류를 냈다. VM에서 실제 credential은 용도별로 import했고 n8n C03/C04 실호출은 성공했다. runner `http()`는 Authorization header를 전송하지 않아 credential 인증이 필요한 custom team cases 실행은 부적절했다. 공식 common 14개 case file은 수업 경로에서 찾지 못해 실행하지 않았다.

### 후속 VM 런타임 정리 · `c1a4c8b`

통합 스냅샷 `3e0f701` 뒤에 승인된 OKE 명명 전환을 별도로 수행했다. 런타임 구현 커밋은 `c1a4c8b`이며 VM은 이를 배포 기준으로 fast-forward했다. 후속 문서 전용 커밋 `1519135`도 GitHub main에 push하고 VM 저장소를 fast-forward했다. 문서 동기화는 컨테이너를 재시작하지 않았다.

- Compose 프로젝트를 `day65-n8n`에서 `oke`로 바꾸고 서비스 DNS는 유지했다. 기존 `day65-n8n_default` 네트워크와 정확한 external volumes (`day65-n8n_n8n-data`, `oke-jihye-p0_postgres_data`, sandbox TLS/DinD)를 재사용했다. 구 컨테이너는 중지 후 보존했고, 볼륨·이미지·credential·백업·수업 파일은 삭제하지 않았다.
- 기본 기동에서 SearXNG를 `optional-search` 프로필로 제외했다. RAG index는 기존 `indexing` 수동 프로필로만 실행하며 search는 유지했다. SearXNG와 index가 멈춘 뒤에도 direct C03 일반/IT 검색 및 n8n `oke-search`가 HTTP 200, evidence 3을 반환했다.
- 신규 C04 검증 요청 `oke-runtime-cleanup-20261105-c04-1`은 HTTP 200으로 티켓 `T-2003` 1건을 만들었다. 동일 요청키 재시도는 같은 ID, `duplicate=true`, alert=true, DLQ=false였다. DB 건수는 기존 employees/users/tickets/alerts/DLQ `6/1/2/3/1`에서 `6/1/3/4/1`; RAG는 `8/33` 그대로였다.
- `minji.admin`은 로그인/재로그인 성공 후에도 `must_change_password=true`였다. 강제변경 전 보호 API 403, 로그아웃 200, 이전 세션 401을 확인했다. 비밀번호는 바꾸지 않았다. 5개 OKE workflow 중 support/search/handoff/errors 활성, index 비활성; 6개 credential 보존, 16개 참조 모두 존재했다.
- localhost n8n health/backend ready/FE login은 모두 HTTP 200이고 기존 외부 n8n `:5678/healthz`도 200이었다. FE 외부 루트 502/3000 timeout 문제는 이 작업에서 수정하지 않았다. 공식 flow.py/common-14는 실행하지 않았다.
- 자원은 전환 전 available RAM 1347 MiB에서 전환 후 1433 MiB, 디스크 여유 41 GiB였다. SearXNG와 index 및 모든 기존 `day65-n8n-*` 컨테이너는 삭제 없이 중지 상태로 남겼다. 체크섬 검증된 롤백 백업은 VM `/home/toor/backups/oke-runtime-cleanup-20261105-final`에 보관했다.

세부 볼륨 매핑, 운영/롤백 명령과 실제 시험 표는 [배포 운영 기록](../../deploy/README.md) 및 [실행 결과 8절](../EXECUTION-RESULT.md#8-oke-runtime-cleanup-and-project-rename--2026-11-05)에 있다. 이 확인은 강사 검토/승인이나 자동 답변 품질 PASS를 뜻하지 않는다.

</details>

당시 개인 개발 경로 `develop/{jihye,dahyeok,yubeen,wonmin}/Doc/`의 단계 결과·HANDOFF는 과거 참조 위치다. 현재 main에 포함되지 않은 원본은 이 일지만으로 독립 재확인할 수 없다. 현재 실행 경로는 [독립 제출본 안내](../../SUBMISSION.md), 당시 상세 관측은 [실행 결과서 부록](../EXECUTION-RESULT.md#부록--당시-관측-기록)을 따른다.
