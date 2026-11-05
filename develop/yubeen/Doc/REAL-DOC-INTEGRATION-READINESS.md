# 실제 Markdown 8개 색인 사전 점검 · 2026-11-05

상태: PREPARED. 코스 킷 원본 파일은 읽기 전용으로 확인했다. DB·OpenAI·n8n·VM 실연결은 미실행. 본문 전체 및 비밀값은 이 문서에 기록하지 않는다.

회귀 확인: Python 전체 171개, JavaScript 전체 16개 통과. `git diff --check` 통과. 기존 Fake HTTP/Mock 시험은 실제 DB·OpenAI·n8n 검증으로 해석하지 않는다.

원본 위치(읽기 전용): `/home/yubeen/aio-01d4-stu/Last3Mon/79/data-api/data/docs/`. 팀 VM 컨테이너의 `/data/docs/`와 동일한 바이트인지는 미확인. SHA256은 파일 원본 바이트 기준이며 이번 8개는 기존 LF 정규화 해시와 일치했다. 청크는 기존 `rag_prepare.chunk_document(..., "section")`의 로컬 결과이며 DB 적재 수가 아니다.

| 파일 | 제목 | `##` 수 | 예상 청크 | SHA256 | 권한 초안 | 질문 |
| --- | --- | ---: | ---: | --- | --- | --- |
| `device-issue-return.md` | 업무용 장비 지급·반납 규정 | 4 | 5 | `be876969812aa0abdd8ae818fdce9d44b38ba444fc22ed274ed75934420d49e0` | 검토 필요 (기존 일반 8종 all 기본안과 새 민감 기준 대조) | Q07 |
| `email-and-documents.md` | 메일·문서 보안 규정 | 3 | 4 | `4ddfb066c71e1eef4a96f25d0cb99e5fec782ffc50bcc759fa0420df871baaec` | 검토 필요 (기존 일반 8종 all 기본안과 새 민감 기준 대조) | Q06 |
| `meeting-room.md` | 회의실 이용 규정 | 3 | 4 | `a57aea3bb6a3085d056bbdc690dd3a32d152e0872c88b9c84938accef0639cb5` | 검토 필요 (기존 일반 8종 all 기본안과 새 민감 기준 대조) | Q11 |
| `password-policy.md` | 비밀번호·계정 보안 규정 | 4 | 5 | `8c2cab8523fb61937eed939fda8d26e74d42e07a9961fb3a21db6661a4c377fd` | 검토 필요 (기존 일반 8종 all 기본안과 새 민감 기준 대조) | Q01–Q03 |
| `privacy.md` | 개인정보 처리 지침 | 3 | 4 | `3798a7435cf5068a60d578d8fe3fcc0402fb28e5e563dcae721ef18fc4eb2678` | 검토 필요 (기존 일반 8종 all 기본안과 새 민감 기준 대조) | Q09 |
| `remote-work-vpn.md` | 원격근무·VPN 이용 규정 | 3 | 4 | `26d2c8580b321fadca2d0244e0bb2ebd05246c99407057b460b134e3940fc869` | 검토 필요 (기존 일반 8종 all 기본안과 새 민감 기준 대조) | Q04–Q05 |
| `security-incident.md` | 보안 사고 대응 절차 | 2 | 3 | `d9f57a7ae422f303cd2310f489f09138fdf1c8c5e88bf2f7873bf33ab0086c29` | it (오현님 명시) | Q08 |
| `software-usage.md` | 소프트웨어 사용 규정 | 3 | 4 | `82c0f4e9ca271d572d43e4df1de761616d78bc5808fd8a71aa56baacfb4ed849` | 검토 필요 (기존 일반 8종 all 기본안과 새 민감 기준 대조) | Q10 |

8개 모두 청크 준비 상태 complete, 합계 예상 청크 33개. 이 계산에서 권한 인수는 청킹 형식 검사를 위한 임시값이며 공개 권한 확정/색인을 뜻하지 않는다. 원본에서 `access_level` 표기는 확인되지 않았다. API의 권한 메타데이터는 미확인이다. 단순 비밀값·연락처 패턴 검사에서 탐지된 값은 없었지만 내용 민감도 판정은 완료되지 않았다.

## 권한·평가 충돌

- 오현님이 `security-incident.md`를 `it`로 지정했다. 공통 DATA-AND-DB/RAG-ARCHITECTURE의 메타데이터 부재 시 일반 8종 `all` 기본안과 달라 공통 문서 반영이 필요하다. 새 명시 기준을 우선 고려하되 실제 색인은 권한 매핑 확정 전까지 차단한다.
- 나머지 7개를 일괄 `all`로 확정하지 않았다. 특히 `privacy.md`는 내용 민감도 검토가 필요하다. 문서별 API 메타데이터와 오현님 승인 매핑을 받아야 한다.
- Q01–Q11은 위 표의 문서와 초안상 연결된다. Q08은 현재 `all` 질문인데 대상 문서는 `it`로 지정되어 기존 기대가 권한상 불가능하다. Q09도 privacy 권한 확정 전까지 평가 판정 보류다. Q12–Q13은 규정 밖/답 없음, Q14–Q16은 관리자 원문·질문/정답 미확정이다. `cases/rag-search.json`은 draft_not_frozen이고 원문 근거/절/필수 문구도 고정되지 않았다. 기대값을 성능 결과에 맞춰 바꾸지 않는다.

## DDL·실행 준비

- 현재 체크아웃의 `develop/jihye/migrations/`에는 README만 있고 0004 DDL 파일은 없다. 지혜님 공유 상태는 전달 정보이며 이 환경에서 테이블·권한·제약을 독립 확인하지 못했다. 공통 계약의 `rag.documents`/`rag.chunks` 컬럼과 `PostgresStore`의 UPSERT·청크 교체 SQL, `PgvectorSearchAdapter`의 권한 선필터·`<=>`·top3 SQL은 설계상 대응하지만 실제 카탈로그와 실행계획 검증은 미완료다.
- 기존 `rag_prepare`는 원본 검증/절 청킹, `rag_index`는 중복 건너뜀/문서 단위 트랜잭션·실패 보존, `rag_search`와 `search_http`는 임베딩→권한 SQL→C03 HTTP 경로를 제공한다. 코스 킷 로컬 파일에서 색인용 신뢰 가능한 API 스냅샷을 만드는 어댑터/실행 CLI는 아직 없다. `SOURCE-MANIFEST.md`는 Mock 대장으로 실제 원본이 아니다.
- 사전 조사 당시 이 셸에서 `DATABASE_URL`, `OPENAI_API_KEY`, `SEARCH_TEAM_KEY`는 설정되지 않았고 `psycopg`도 설치되지 않았다. 후속 실행 환경 점검에서 담당 폴더의 `.venv`에 `psycopg`를 설치하고 `requirements-runtime.txt`에 기록했다. 팀 공통 환경은 변경하지 않았다. 실제 API 호출, DB 연결/쓰기, HTTP 실검색, n8n import/test는 미실행.
- 다음 게이트: 지혜님 0004 DDL·격리 DB의 색인/검색 계정 및 안전한 접속 경로, 오현님 문서별 권한 최종표·비밀 키 전달, 8개 원본 버전 확인, 대상 DB 쓰기 승인. 이후 읽기 전용 카탈로그/건수 확인, 원본→임베딩→색인, 중복 재실행/실패 보존, 일반/검증된 IT 검색, HTTP·n8n 순으로 수행한다. 현재 IT 권한 전달 계약도 미확정이므로 IT 양성 검색은 차단 상태다.

## 전달

지혜님: 0004 revision/DDL과 실제 `rag.documents`/`rag.chunks` 카탈로그, vector(3072), FK/UNIQUE/JSONB, 역할 GRANT, 격리 DB 접속 및 쓰기 대상 확인을 요청한다. 다혁님: Q08의 all 기대와 security-incident it 지정이 충돌하며 현재 C03 서비스는 all 검색만 가능하다. 검증된 IT 권한 전달 계약과 본체의 503/권한 경계를 함께 확인해야 한다. 오현님: 공통 문서의 8종 기본 all 규칙과 새 보안 문서 it 기준을 정합화하고 나머지 7개 매핑을 승인해야 한다.
