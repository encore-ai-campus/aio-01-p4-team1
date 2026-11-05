# P0-2 실행 기록 · 2026-11-04 · p0-2-local-01

## 선행 확인

환경: /home/yubeen/Aio-4pj-1team, WSL AIO, feat/yubeen-p0, HEAD 1069db79ce3f056d7d73be944aad6ec35fd6e575. 시작 시 미커밋 변경 없음. 상위 /·/home·/home/yubeen의 AGENTS.md는 존재하지 않았다. 루트와 develop/yubeen AGENTS.md, 팀/개인 README·TODO·SPEC·IMP-PLAN·HANDOFF·P0-1 결과와 공통 API·DB·평가·RAG·협업·헌장, 실제 .github PR 템플릿/CI를 읽었다. 별도 브랜치 전략 문서는 발견하지 않았고 문서에 없는 규칙을 만들지 않았다. 개인 브랜치 유지, 개인 폴더만 편집, 공통/상대 폴더 읽기 전용, 오현님 리뷰·병합·배포 원칙을 따른다.

공통 DB/RAG 문서와 개인 SPEC/H-Y02의 오래된 권한 매핑 설명 차이는 HANDOFF에 기록했다. 기존 P0-1 공통 매핑을 변경하지 않았다. 실제 정답표 고정·관리자 문서 기대 생성은 보류하고 Mock 구현을 진행했다. 실제 호출/DB/임베딩/LLM/n8n/워크플로우 생성/commit/push/P1 구현은 수행하지 않았다.

## 구현

- tools/rag_prepare.py: P0-1 기능을 보존하면서 section_ranges, chunk_document, compare_snapshot 및 compare-chunks CLI 추가. API 모드도 원문이 일시적으로 존재하는 수집 내부에서 비교하고 안전한 보고서만 반환한다. 두 방식에서 별도 재수집하지 않는다.
- 원본은 LF 전체 text다. 원본 제목 행·## 행·목록·표·코드를 보존하며 문자 범위는 [start,end)다. section 기본 1청크/overlap0, 빈 절 분석 보존/청크 제외. 비교는 유니코드 300자/overlap0, 제목 접두어는 별도 길이로 기록한다. 기본과 비교의 content는 제목+LF+포함 절 제목+LF+원문 범위다. chunk_no는 문서별 0부터, content_hash는 실제 content UTF-8 SHA-256이며 이것을 향후 임베딩에 그대로 전달한다.
- UTF-8 8000바이트 초과 content는 별도 검토 거절로 기록한다. 잘라 버리지 않으며, 토큰 한도 실측/운영 한도 확정이 아니다. 빈 절·공백 제외/거절을 합친 원문 범위 보존과 순서를 검사한다. 원문과 content 실제 값은 메모리 반환용이며 보고서에는 원문 content 대신 비출력 표지를 명시한다.
- cases/rag-search.json: 질문 16개와 이력/확정 상태, 품질 질문과 분리한 F01~04 계약 예시. Q01~11 초안, Q12~13 답 근거 없음, Q14~16 질문·기대 원문 null/미실행. verified_required_quotes는 원문 전이라 비어 있다. 실제 정답/품질 PASS로 취급하지 않는다.
- cases/chunk-comparison-mock.json: 규정 대체가 아닌 합성 전용 5문서. 공개 구조·유니코드·절 없음, 제한 문서, 미확인 권한을 포함한다.
- requests/search-all.json·search-it.json: top_k3의 권한 쌍. 키/관리자 본문 없음.
- Doc/CHUNK-COMPARISON.md: 문서별 건수·본문/content/접두어 길이 최소/중앙/최대, 원본 해시·권한·범위·절 매핑·제외/거절·보존 검사. 실제 미측정값을 0으로 채우지 않았다.
- Doc/SEARCH-EVAL.md: C03 예시와 실제 미실행 상태, 정답표 변경 절차·측정 양식.
- tests/test_chunking.py: P0-2 회귀 16개. 기존 P0-1 tests/test_rag_prepare.py는 수정하지 않았다.
- README.md와 Doc/HANDOFF.md: 검증 명령 및 전달 준비 내용. 이 파일은 실행 이력이며 P0-1 INDEX-RESULT/SOURCE-MANIFEST는 수정하지 않았다.

## 검증과 실제 결과

작업 디렉터리 develop/yubeen, Python 3.14 표준 라이브러리, 합성 Mock과 가짜 HTTP만 사용했다.

1. 최초 전체 unittest 48개 중 비노출 테스트 1개 실패: 합성 절 이름 '제한 절'이 보고서의 일반 설명 문구에도 있어 오탐했다. 원본 유출이 아니라 문구 충돌임을 출력에서 확인했고 설명을 '비공개 표제'로 수정했다. 같은 테스트 유지 후 48개 통과했다.
2. 직접 청킹 함수의 미확인 권한 거절을 추가하고 최종 unittest 실행: 총 49개(기존33+신규16) 모두 통과, 종료 0.
3. `python3 tools/rag_prepare.py compare-chunks --source mock --input cases/chunk-comparison-mock.json --baseline section --candidate 300 --output Doc/CHUNK-COMPARISON.md`: 종료 0. 같은 입력 CLI 두 번의 바이트 동일성을 테스트했다.
4. 보고서 요약 추출을 저장소 루트에서 실행해 경로 FileNotFoundError가 한 번 발생했다. 담당 디렉터리에서 재실행해 아래 실제 수치를 확인했다. 원본·보고서는 손상되지 않았다.
5. git diff --check, git status -sb, git diff 검토 및 신규 JSON 구문 확인을 최종 수행한다. 검사 모두 통과, JSON 구문 정상. 변경은 develop/yubeen 내부이며 스테이징/커밋/푸시는 하지 않는다.

| 합성 문서 | 권한 | 기본 청크 | 300자 청크 |
| --- | --- | --- | --- |
| mock-structure | all | 3 | 1 |
| mock-unicode | all | 2 | 2 |
| mock-plain | all | 1 | 1 |
| mock-it | it | 1 | 1 |
| mock-unknown | 미확인 | 거절 | 거절 |
| 합계(허용4문서) | all/it | 7 | 5 |

구조 문서의 빈 절 1개는 기본에서 제외했다. 허용 문서 모두 두 방식의 제외 범위 포함 coverage/order 검사가 true이며 실제 원문 손실·중복은 검출되지 않았다. 이는 합성 원본의 로컬 분석 결과이며 실제 색인/권한 SQL/검색 품질 검증이 아니다. 세부 길이 분포는 CHUNK-COMPARISON에 있다.

## 완료 기준과 인계

Mock 구현/비교·길이 통계·범위·권한/정보 보호·초안과 계약 예시 준비는 충족했다. 실제 원본 검증, Q01~11 정답표 확정, Q14~16 관리자 질문/기대, 실제 두 색인 비교·검색 품질·시간·토큰·비용은 미검증/미실행이다. 전체 실제 P0-2 완료로 선언하지 않는다.

P1-1에 청크 매핑/기본 설정, 다혁님에 정상·빈·장애 C03 예시, 원민님에 권한 쌍/고정 합성 기대·미확정 실제 정답표를 넘길 준비가 됐다. HANDOFF에 자세히 기록했으며 실제 전송·상대 확인은 없다. 승인 전 commit/push하지 않는다.

최종 경로 자동 검사의 첫 실행은 git ls-files가 담당 디렉터리 기준 상대 경로를 반환해 AssertionError가 발생했다. git -C 저장소 루트로 기준을 통일해 재실행했고 모든 변경이 허용 폴더 내부임을 확인했다. 스테이징은 비어 있고 기존 P0-1 테스트·INDEX-RESULT·SOURCE-MANIFEST가 기준 커밋과 바이트 단위로 동일함을 확인했다.

## 독립 평가 결함 보완 · 2026-11-04 · p0-2-local-02

### 선행 규칙·범위 확인

환경은 AIO, /home/yubeen/Aio-4pj-1team, feat/yubeen-p0, HEAD 1069db7이며 이전 수정3/미추적8개를 보존하고 시작했다. 상위 경로의 추가 AGENTS.md 부재 및 루트/개인 AGENTS, 팀/개인 README, 협업·헌장·PR 규칙과 공통 API·DB·RAG·평가 계약을 재확인했다. 개인 폴더만 수정, 공통/상대 파일은 읽기 전용, 리뷰·병합·배포는 리드 관리다. 별도 브랜치 전략을 만들어 적용하지 않았다. 개인 SPEC/H-Y02와 공통 문서의 권한 매핑 차이는 기존 HANDOFF에 기록된 상태이며 이번에는 정책을 변경하지 않았다. 실제 API 허용 옵션은 개인 도구의 안전장치로 공통 API 입출력/환경변수 계약을 바꾸지 않는다.

### P1/P2 수정

1. 기능 사례: 기존 F01~04를 보존하고 F05~10 동점 정렬·일반 입력 불량·DB 오류·임베딩 오류·시간 초과·관리자 주장 무시를 추가했다. 장애는 공통 503/search_unavailable, 입력 오류 상세는 null/미확정으로 유지했다. 품질 질문과 계속 분리한다.
2. 상태/통계: 방식별 complete/partial/rejected와 실제 청크 커버리지, 의도적 제외 범위, 거절 범위, 전체 원문 범위 장부를 구분했다. 비교 문서의 reasons에도 방식별 거절 사유를 반영한다. 완전 성공·부분 생성·거절의 문서/청크 수 및 본문/content 길이 통계를 별도 집계한다. 데이터가 없으면 길이 통계는 미측정이다. 빈 절 제외만 있으면 정상 complete일 수 있지만 covers_entire_source는 false일 수 있음을 명시한다.
3. API 승인 차단: collect_api는 기본 transport=None이면 allow_network=True 없이는 api_network_not_authorized로 차단한다. 두 CLI는 --allow-network를 명시할 때만 실제 전송 선택이 가능하다. 명시 옵션은 사용자의 실제 승인을 대체하지 않는다. 기본 오류는 종료2/고정 코드만 출력하며 키/URL을 포함하지 않는다. 주입 가짜 전송과 기존 P0-1 API 어댑터 테스트는 유지했다. 저수준 HTTP 함수는 기존 전송 구현이며 두 CLI는 반드시 승인 검사된 collect_api 경로를 거친다.
4. 경계 테스트: 정확히 한글/이모지 300자 → [300], 301자 → [300,1] 회귀 추가.
5. 정답표: 질문·상태·권한·기존 기대값을 변경하지 않고 evidence_review의 미검증/미분리 상태를 추가했다. 실제 절 제목·답 문구 확정 없음. 버전 p0-2-draft-v2, 검색 전 history 추가.

### 실제 검증

작업 디렉터리 develop/yubeen, Python3 표준 라이브러리. 실제 API/DB/LLM/임베딩/n8n 없이 합성 자료·가짜 전송만 사용했다.

- 전체 unittest: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` → 63/63 통과, 종료0. 기존49개 삭제/약화 없이 신규14개 추가. 기존 P0-1 33개도 모두 통과했다.
- Mock 비교 CLI: `python3 tools/rag_prepare.py compare-chunks --source mock --input cases/chunk-comparison-mock.json --baseline section --candidate 300 --output Doc/CHUNK-COMPARISON.md` → 종료0. 허용 합성4문서 section7/300자5 유지. 미확인 권한1문서는 rejected. 정상 fixture의 완전 성공 통계와 부분 성공 통계는 분리되어 있다.
- 혼합 입력 `"## good\nok\n## long\n" + "가"*3000`: 기본 partial/1청크, 실제 청크 [0,11), 거절 [11,3019), 청크 커버 문자11/3019. 300자 complete/11청크, 실제 커버3019/3019, 거절0. source_hash는 두 방식 동일. 전체 범위 장부 true와 실제 청크 전체 보존 false를 구분한다.
- 승인 차단: 두 CLI 기본 경로에서 전송 호출0·종료2·api_network_not_authorized 확인. --allow-network 경로 역시 표준 전송 함수를 가짜로 교체한 상태에서만 실행했다. 실제 요청0.
- 신규 회귀: 혼합 부분 거절, 전부 거절, 의도적 제외, 상태별 통계, 한글/이모지300/301, 어댑터 기본 차단, 두 CLI 기본 차단, 허용 경로 가짜 검증, 차단 메시지 비노출, 기능10종, 동점 기대 정렬, 관리자 주장 권한 유지, 정답표 미확정 상태.

### 판정·미검증·인계

지적된 P1 3건/P2 2건은 Mock 구현·검증 범위에서 보완했다. P0-2 Mock 완료 기준은 충족한다. 실제 API 인증/응답, 규정8종/관리자 문서 원문·권한, Q01~11 원문 정답 고정, Q14~16 실제 질문/기대, 실제 검색·SQL·품질·시간·토큰·비용은 계속 미검증/미실행이다. 기능 사례 검사 통과는 실제 search 기능 통과가 아니다.

P1-1은 Mock 기반 준비 작업에 조건부 착수 가능하지만, 실제 색인 연결은 실제 원본/권한·DB 준비와 길이 검토 기준 확인이 필요하다. 이번 작업에서 P1-1 구현은 시작하지 않았다. 청크 매핑/부분 상태는 P1-1, C03 예시는 다혁님, 권한 쌍·기능 사례·미확정 정답표는 원민님에게 전달 준비했다. 실제 전달/상대 확인 없음. 사용자 확인 전 commit/push/merge하지 않는다.

최종 추가 검사 결과: Mock CLI 재생성 보고서가 같은 입력의 메모리 결과와 동일했고 7/5 수치를 재현했다. 청크 범위/본문 길이/content 해시/source 해시를 독립 재계산해 일치했다. JSON5개 구문 정상, 제한 표제/본문 비노출 및 일반 키 패턴 검사 통과, git diff --check 종료0. 변경 총11개가 모두 develop/yubeen 내부이며 P0-1 테스트·대장·실행 기록은 기준 커밋과 동일하다. 기존 수정3/미추적8 상태를 유지하고 스테이징은 비어 있다.
