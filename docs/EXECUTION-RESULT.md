# 워크플로우 실행 결과 · DAY 80 · 2026-11-05

> 이 문서는 VM/로컬 관측과 미실행 범위를 함께 기록한다. HTTP 응답·Mock·로컬 검사만으로 DB 영속 저장이나 종단 간 성공을 추정하지 않는다. 민감값은 포함하지 않는다.

## 1. 실행 및 환경 관측

| 시각/버전 경계 | 확인 항목 | 실제 결과 | 범위와 한계 |
|---|---|---|---|
| 2026-11-05 관제 기록 | 웹 터미널 파일 전송 | 8,192 byte 파일 put/get 후 내용 일치 | 전송 무결성만 확인; 배포/서비스 기능 검증과 별개 |
| VM 통합 관측, main `952f704` | PostgreSQL·마이그레이션 | PostgreSQL healthy, Alembic `0005`; role catalog 조회 | DB readiness와 revision 관측. 색인·검색용 로그인 권한의 실제 연결/최소 권한 검증 결과는 별도 확인 필요 |
| 동일 관측 | 데이터 행 수·운영 모드 | `rag.documents=0`, `rag.chunks=0`, `app.tickets=0`; `practice` | 해당 시점 관측값. `app` 모드 영속 저장 결과가 아니며 기존 볼륨은 유지 |
| workflow 본체 실행 ID `manual-38042b9550d14ce3b3b447a1bdbef2c8` | 질문 `비밀번호 초기화 절차를 알려주세요` | HTTP 200; 응답 `reason=search_unavailable`, `route=담당자 이관`, ticket `T-2001`, `sources=[]` | 이관 응답이 사용자에게 반환된 사실만 확인. practice 경로의 응답이며 C05 DB 기록/영속성 증거가 아님. 실행은 이후 최신 main `952f704` 재배포/검증보다 앞선 버전 경계이며 최신본에서 재실행한 결과로 취급하지 않음 |
| 후속 배포 후, VM main `952f704` | C03 검색 요청 | HTTP 000, connection reset | 응답 본문·근거 결과 없음. 정상 검색으로 집계하지 않음 |
| 후속 배포 후, VM main `952f704` | 서비스/스모크 | RAG 검색 컨테이너 0개, 8765 listener 없음; deploy 전체 스모크 미완료 | n8n 재시작과 주요 workflow 활성은 확인했으나 deploy 스모크 PASS는 아님 |

## 2. 로컬 정적·회귀 검사

| 검사 | 결과 | 적용 범위 |
|---|---|---|
| `python3 -m json.tool` — root support/search JSON | 통과 | JSON 문법만 확인 |
| `git diff --check` | 통과 | 공백/patch 오류 점검 |
| VM 배포 스크립트 `bash -n` | 통과 | shell 문법. VM 서비스 정상성은 확인하지 않음 |
| 원민 `node --test develop/wonmin/tests/*.test.mjs` | 일부 실패 | Mock startup timeout과 외부 C05 응답 계약 오류가 발생. 성공 건수/실패율을 공식 공통 통과 수로 환산하지 않음 |
| 유빈 `6780432`의 기록된 Fake 경계 검사 | Python 190개·JavaScript 3개 통과 기록 | 해당 커밋의 Fake/Mock 범위. 이 문서 작성 중 재실행하지 않았고 PostgreSQL/n8n/VM 실제 검색 결과가 아님 |

## 3. 시나리오별 실행 판정

| 경로 | 현재 관측 | 판정 |
|---|---|---|
| 본체 정상 형식 요청 | 위 실행에서 HTTP 200 응답이지만 C03 `search_unavailable` 후 이관 | HTTP 응답은 관측. 정상 검색·근거 답변 시연은 미확인 |
| 검색 C03 | 최신 배포 뒤 HTTP 000/reset; 검색 서비스 없음 | 실패/미완료 |
| 이관 C04 | `manual-38042b9550d14ce3b3b447a1bdbef2c8`에서 T-2001 응답 | 이관 응답 관측. 실제 저장 API·DB 영속성·재시작 보존은 미증명 |
| practice/app 저장 모드 | VM practice, app tickets 관측 0 | app 저장 검증 미실행 |
| 입력 400·주입 차단 | 해당 8교시 VM HTTP/실행ID 근거 없음 | VM 시연 미확인 |
| WF-08/WF-13 본인·타인 조회 | 동일 VM의 본인 성공/타인 403 근거 없음 | 미실행/미확인 |
| 공식 `flow.py test cases/common.json` | 공식 키트·실행 결과 미확인 | 공통 14개는 미실측. `0/14`는 이전 템플릿 문자열일 뿐 결과값이 아님 |
| 일반/IT 권한별 실제 문서 검색 | DB 문서/청크 0/0, 권한 근거·서비스 경로 미완성 | 미실행. 권한 위반 0건이나 hit@3 수치를 주장하지 않음 |

## 4. 제출·시연 요구와 피드백 추적

공식 8교시 체크리스트의 7개 항목은 WORKFLOW-DESIGN 1~4절, RAG 설계와 청크 실측, 팀 VM 라이브 시연, 400·주입 차단, WF-08/WF-13, 공통 14개 실행 결과, DAY80 기록 및 강사 피드백이다. WORKFLOW-DESIGN 1~4절은 저장소에 있으나 나머지 실행/실측 항목은 위 증거로 미완료 또는 미확인이다. 공식 표의 미체크 양식과 본 실행 결과 판정은 구분한다.

사용자가 전달한 7교시 피드백은 “실문서 DB 검색 한 경로”, “실제 색인 수·청크 길이·권한별 결과”, “`security-incident` 권한 및 인증 계약 정렬”, “동일 VM의 정상 및 이관 근거”를 요구한다. 현재 색인 0/0, C03 HTTP 000/reset, 이관은 과거 practice 응답만 확인됐으므로 피드백 요구를 완료하지 못했다. 본 기록은 강사 승인·검토를 뜻하지 않는다.

## 5. 알려진 한계와 다음 검증 순서

1. Python search listener가 없고 n8n과의 네트워크/URL 경로가 정렬되지 않았다. root URL `/search`와 서비스 수신 경로 `/webhook/oke-search`가 일치하지 않는 관측이 있다. 검색 프로세스의 실제 실행 정의·도달 주소·접근 통제를 확정한 뒤 동일 VM에서 HTTP 응답/본문을 확인한다.
2. 실제 규정 권한 근거와 검색용 환경 설정이 검증되기 전에는 색인하지 않는다. 승인된 실제 문서로 색인 후 문서 수·청크 수·청크 길이 최소/중앙/최대와 일반/IT 결과를 기록한다.
3. `practice`의 응답과 `app` 모드 C05 영속 저장은 별도다. 앱 티켓/알림/DLQ API의 저장·ACK·멱등/재시작 검증 전에는 T-2001 응답을 DB 기록으로 해석하지 않는다.
4. 이후 동일 VM 버전에서 정상 답변과 이관의 실행ID·요청·HTTP·본문·근거를 각각 저장하고, 입력400·주입 차단·WF-08/WF-13 및 공식 common 14개를 실제 도구로 실행한다. 미실행·실패를 별도 행으로 남긴다.

## 6. 버전 및 근거

- main 통합 기준: `952f704` (기존 통합 및 선택 반영 커밋 `36e01ce`, `eb3e8a4`, `7b9b383`, `e03833b`, `952f704`). 팀별 구현은 `develop/jihye/Doc/IMP-PLAN.md`, `develop/dahyeok/Doc/IMP-PLAN.md`, `develop/yubeen/Doc/IMP-PLAN.md`, `develop/wonmin/Doc/`의 P1 결과/HANDOFF를 참조한다.
- 실제 반영 커밋과 문서 정리 커밋은 구분한다. 이 보고서 갱신은 코드/워크플로우 변경이나 VM 재배포가 아니다.
- 기록에 없는 workflow execution ID, 처리시간, 청크 분포, hit@3/MRR, 비용, LLM 호출 수는 미기록/미측정으로 둔다.
