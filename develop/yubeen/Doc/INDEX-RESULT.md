# P0-1 원본 확인 실행 기록

- 단계/SPEC: P0-1 / RAG-01·02, 2026-11-04, 실행 ID p0-1-local-01.
- 환경: Python 3.14, 표준 라이브러리. 원본은 cases/source-inventory-mock.json의 합성 자료이며 실제 규정의 대체물이 아니다.
- 구현: tools/rag_prepare.py, cases/source-inventory-mock.json, tests/test_rag_prepare.py, Doc/SOURCE-MANIFEST.md, 이 문서.
- 작업 디렉터리: develop/yubeen. 외부 API·DB·임베딩·n8n 실행 없음.
- 명령: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`
- 결과: 정상·빈 문서·중복·권한 누락, LF 해시 동일성·코드 펜스 경계, 권한 충돌·본문 누락, 제한 정보 비노출의 4개 테스트 통과(종료 0).
- 최초 실행은 저장소 루트에서 수행해 tests 경로 ImportError(종료 1). 담당 폴더에서 같은 명령을 다시 수행해 위 결과를 확인했다.
- 명령: `python3 tools/rag_prepare.py inventory --source mock --input cases/source-inventory-mock.json --output Doc/SOURCE-MANIFEST.md`
- 결과: 종료 0, 목록 6건 중 후속 준비 가능 2건·거절 4건. 중복 키 두 항목 모두 거절. 미확인 권한 문서도 해시·길이는 조사했다. HTTP 결과는 해당 없음.
- 증거: SOURCE-MANIFEST.md 및 재현 가능한 테스트/Mock. 본문은 대장에 출력하지 않으며 it·미확인 문서 제목과 절 이름도 숨긴다.
- API 모드는 승인 없는 호출을 막고 안내 오류로 종료한다. 추후 승인 후 DATA_API_URL/DATA_API_KEY 기반 실제 응답 어댑터가 필요하다. 현재 Mock 구조는 참고 예제 기준이며 실제 API 구조 확인 완료가 아니다.
- 미실행: 실제 규정 8종·관리자 문서 확보, 실제 권한 근거 확인, 색인·검색·flow.py 검사. 워크플로우는 이번 단계 생성 대상이 아니다.
- 다음: P0-2에 로컬 대장/해시 규칙 전달 가능. 지혜님에게 실제 원본 응답과 권한 메타데이터 제공 여부 확인 필요(C06). 원민님·오현님에게 실제 8종 및 관리자 문서·권한 출처 미확인 전달 필요(H-Y02). 외부 전송·상대 동의 없음.

## P0-1 결함 보완 · 2026-11-04 · p0-1-local-02

기존 기록은 첫 구현 당시의 결과다. 위의 'API 모드 안내 종료'는 아래 구현으로 대체되었다. 실제 연동 미검증 상태는 유지한다.

### 기준 대조와 범위

GitHub main의 IMP-PLAN P0-1, SPEC RAG-01·02, HANDOFF H-Y02, API-CONTRACT, DATA-AND-DB를 읽고 로컬과 대조했다. 공통 DATA-AND-DB 4절에는 메타데이터 부재 시 일반 규정 8종 all 매핑이 확정되어 있다. H-Y02의 별도 버전 관리 매핑표는 제안 상태다. 일반 규정의 정확한 8개 doc_key는 공통 EVALUATION-GUIDE 1절을 사용한다. 관리자 문서는 실제 식별자가 확정되지 않아 제목/키워드로 추정하지 않는다. 메타데이터 충돌·알 수 없는 값은 매핑으로 덮지 않고 거절한다.

IMP-PLAN 확정 요구사항, 공통 파일, 다른 팀원 파일은 수정하지 않았다. 브랜치는 feat/yubeen-p0. P0-2 이후 구현, commit/push/merge, 실제 API/DB/LLM/n8n 호출 없음. 기준 대조를 위한 GitHub 읽기만 수행했다.

### 수정 파일과 동작

- tools/rag_prepare.py: 펜스 상태를 추적한 절 분석으로 변경. 실제 제목이 없으면 본문, 실제 절 앞 유효 내용만 서문. 빈 절 제목/순서를 길이 0으로 보존한다. 청크를 생성하지 않으므로 빈 절의 색인 가능 여부를 이 단계에서 확정하지 않는다. LF와 전체 본문 SHA-256 유지.
- 같은 도구: 환경변수 DATA_API_URL/DATA_API_KEY 기반 GET 수집과 주입 가능한 전송 계층 구현. 문서 키는 URL 경로 단위 인코딩, 타임아웃 10초, 재시도 없음, 리다이렉트 금지. 목록 실패는 실행 실패로, 문서별 HTTP/JSON/본문 오류는 해당 문서 거절로 기록한다. 원본 오류 본문/예외 문자열은 출력하지 않는다.
- 같은 도구: 문서별 조회 시각, 권한 출처·필드·값, 원본 경로와 해시 기록. Mock 파일의 원시 바이트 SHA-256을 대장에 기록한다. API 모드는 수집 스냅샷의 정렬 JSON 해시를 사용한다. 제한/미확인 제목·절 이름은 마스킹하며 본문은 어떤 문서도 출력하지 않는다. 설정된 API 키가 메타데이터에 반사되어도 대장에서 제거한다.
- tests/test_rag_prepare.py: 기존 4개 유지, 회귀·가짜 HTTP·CLI·표준 전송 계층 Mock 검사 22개 추가.
- Doc/SOURCE-MANIFEST.md: 같은 합성 입력으로 재생성. 조사 6항목, 준비 가능 2항목, 거절 4항목. 실제 색인 성공 수가 아니다.
- Doc/INDEX-RESULT.md: 결함, 구현 범위, 검증 및 미확인 사항 추가.

### 실제 검증

작업 디렉터리 develop/yubeen, Python 3.14, 표준 라이브러리. 입력은 cases/source-inventory-mock.json과 테스트 내 합성 HTTP 응답이다.

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`: 26개 통과, 종료 0. 최초 26개 실행에서 HTTPError 시험 객체의 ResourceWarning이 보여 시험 객체 close 처리를 추가했다. 아래 최종 재실행 결과를 기준으로 한다.
- 회귀 목록: 펜스 안 제목만 있는 문서, 제목 없는 문서, 빈 절 연속, 서문+정상 절, 공백 서문 제외, 펜스 길이/종류, LF/CR 정규화, 권한 충돌·누락 및 8종 매핑, 권한 출처 필드, 고정 시각의 대장 결정성, HTTP 성공/500/401/403, 타임아웃, JSON 오류, 목록/본문 형식·누락 필드, 설정 오류, URL 인코딩, 제한 정보·API 키 비노출, CLI 가짜 전송, urllib 오류 마스킹, 네트워크 없는 표준 전송과 리다이렉트 금지.
- `python3 tools/rag_prepare.py inventory --source mock --input cases/source-inventory-mock.json --output Doc/SOURCE-MANIFEST.md`: 종료 0.
- `git diff --check`: 종료 0. 최종 경로 검사로 수정/미추적 파일이 develop/yubeen 내부임을 확인한다.

### 완료 기준 판정

| 기준 | 판정 | 근거/남은 사항 |
| --- | --- | --- |
| 정상·빈 문서·중복·권한 누락 Mock 검사 | 충족 | 기존 4개 포함 회귀 통과 |
| 식별자·원본 경로·조회시각·LF 해시·절/길이 | Mock에서 충족 | 대장, 빈 절 포함; 실제 원본 미확인 |
| 권한 값·근거 또는 거절 사유 | Mock에서 충족 | 필드 출처 분리, 충돌 거절, 공통 매핑과 제안 구분 |
| 제한 본문·비밀값 비노출 | Mock에서 충족 | 보고서·오류/가짜 HTTP 검사; 실제 환경 미관측 |
| API 옵션·환경변수·구조 검증·오류 처리 | 구현 및 Mock 검증 충족 | 실제 네트워크 미사용 |
| 실제 응답 구조·8종 원본·관리자 문서 대조 | 미충족/미검증 | 실제 호출 금지, 관리자 키/제공 여부 미확인 |
| 누락/거절을 성공 건수에서 제외 | 충족 | Mock 2/4 분리, 실제 확보 성공으로 기록하지 않음 |

따라서 P0-1 코드 보완·Mock 검증은 완료했으나 실제 원본 확인을 포함한 P0-1 전체 완료는 선언하지 않는다. 어댑터는 참고 예제의 docs/name/title/text와 시험용 access_level을 명시적으로 지원하며 실제 응답 구조가 다르면 거절한다. X-Api-Key 헤더는 실제 data-api 계약으로 실측 확인되지 않은 어댑터 가정이다. 실제 승인 후 응답 구조/인증 방식 확인이 필요하다.

다음 연결: 지혜님(C06)은 실제 API 응답·인증 및 DB 매핑 입력의 적합성을, 원민님/오현님은 실제 8종과 관리자 문서의 식별자·권한 출처·누락을 확인해야 한다. H-Y02의 별도 매핑표는 승인/반영 완료로 처리하지 않았다. 결과는 이 문서와 SOURCE-MANIFEST이며 외부 전달·상대 확인은 수행하지 않았다.

## P0-1 최종 보안 점검 · 2026-11-04 · p0-1-local-03

이 절이 최신 상태이며 앞선 실행 이력은 보존한다. 담당 범위는 develop/yubeen의 P0-1이며 입력은 합성 Mock/가짜 HTTP, 출력은 안전한 원본 대장이다. 실제 서비스 호출은 하지 않는다.

- 발견: collect_api(environ=...)에서 주입한 키와 render의 os.environ 키가 다르면 제목 등에서 키가 노출될 수 있었다. 원본 응답 자체를 스냅샷 해시 입력으로 직렬화하는 것도 보완했다.
- 수정: 원본 본문으로 LF 해시·절 길이와 권한을 먼저 계산한다. 그 후 출력 허용 필드만 선택해 수집에 실제 사용한 키와 전역 키를 제거하고, 제한 문서 제목/절을 가린 안전한 대장 투영만 API 반환 스냅샷에 보관한다. 원문은 반환 스냅샷·출력·해시 입력용 JSON에 넣지 않는다. Mock 출력에도 직렬화 전에 같은 보호를 적용한다. 완성된 보고서의 문자열 치환에 의존하지 않는다.
- 스냅샷 해시 의미 변경: 원시 Mock 바이트/원본 API JSON 대신 안전한 대장 투영의 정렬 JSON SHA-256이다. 문서 source_hash는 원본 전체 본문의 LF 정규화 SHA-256 그대로다. 대장 투영 해시에는 조회시각이 포함되므로 시각이 바뀌면 달라진다. 고정 시각으로 결정성을 검증했다.
- 코드: tools/rag_prepare.py. 기존 26개 테스트를 유지하고 tests/test_rag_prepare.py에 보안 회귀 7개 추가. 주입/전역 키 불일치, 기본 환경 경로, 제목·권한 메타데이터·오류 반사, 제한 정보, Mock 직렬화 전 보호, 본문 해시 보존을 가짜 전송으로 확인한다.
- 실제 검증 명령(작업 디렉터리 develop/yubeen): `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`. 결과 33/33 통과, 종료 0.
- Mock 대장 재생성: `python3 tools/rag_prepare.py inventory --source mock --input cases/source-inventory-mock.json --output Doc/SOURCE-MANIFEST.md`. 조사 6항목/준비 가능 2항목/거절 4항목. 실제 확보·색인 성공 건수가 아니다.
- 최종 검사: git diff --check, git status, git diff 및 새 파일 내용 검토. 허용 경로 내 P0-1 파일만 반영 대상이다. IMP-PLAN은 이전 작업의 상태 안내 수정만 있고 확정 요구사항은 변경하지 않았다.

| P0-1 기준 | 최종 판정 |
| --- | --- |
| 정상·빈 문서·중복·권한 누락/충돌 | Mock 충족 |
| 식별자·조회 경로/시각·해시·절/빈 절/길이 | Mock 충족 |
| 권한 출처·필드·거절 근거 및 확정 매핑/제안 구분 | Mock 충족 |
| 누락/거절을 준비 가능 건수에서 제외 | Mock 충족 |
| API 환경변수·수집·오류 처리 | 구현 및 가짜 전송 검증 충족 |
| 수집 키 불일치·반사 및 제한 정보 비노출 | Mock 충족, 실제 환경 미관측 |
| 실제 응답 구조·인증·규정 8종·관리자 문서 | 미검증, 전체 완료 선언 불가 |

실제 API/DB/LLM/n8n 실행, P0-2 구현 없음. 규정 8종의 실제 본문/권한과 관리자 문서 식별자/제공 여부는 미확인이다. 지혜님에게 응답/인증 확인, 원민님·오현님에게 원본/권한 출처 확인이 필요하다. 외부 팀원에게 전송하거나 상대 동의를 기록하지 않았다. commit/push 결과는 실제 Git 명령 결과로 별도 보고한다.
