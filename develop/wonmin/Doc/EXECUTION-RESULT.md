# 워크플로우 실행 결과 · 실제 Ubuntu VM 내부 대조 · 2026-11-06

> docs/EXECUTION-RESULT.md의1~6절 구조를 따른 새 보고서다. **이번 직접 실행은 VM 셸·내부 readiness·PostgreSQL 조회·n8n 본체 실행 대조**이며, 새 문의를 다시 생성하거나 모든 품질시험을 완료한 것이 아니다. 이전 외부 API 시험과 이번 내부 조회의 범위를 구별한다.

## 1. 실행 및 환경 관측

| 항목         | 직접 관측                                                                    | 한계                                 |
| ---------- | ------------------------------------------------------------------------ | ---------------------------------- |
| 조작/실행      | 사용자 로그인된 Ubuntu 웹SSH 셸에 Orca Computer Use로 실제 명령 입력                      | 기본 Sky는 native pipe 시작오류, 대체스킬로 진행 |
| 시각         | VM date 2026-11-06T06:48:39Z, metadata 06:49:14Z; 이후SQL/n8n 조회           | 캡처 UTC·해시는 증거JSON에 기록              |
| OS         | Ubuntu26.04.1LTS x86_64, Linux7.0.0-42-generic                           | 로컬 Orb Ubuntu 관측 아님                |
| 배포 HEAD    | 3ff836af8b0be1bc5f81d0483c5b78272fec6c6a                                 | 개인 브랜치/main 최신HEAD와 동일하다고 추정하지 않음  |
| 컨테이너       | VM oke 프로젝트9개 실행, backend/frontend/PostgreSQL/RAG/sandbox API healthy 관측 | 전체 부하/품질 통과 아님                     |
| 내부 HTTP    | backend 컨테이너127.0.0.1:8000/health/ready →200                             | 외부 공개 API의 대체 관측 아님                |
| PostgreSQL | 기존 backend 설정으로 접속, schema0005, READ ONLY·5초 제한·rollback 종료              | DSN/계정암호/문의원문 출력하지 않음              |

[내부 관측 JSON](../runs/vm-internal-observed-20261106.json)은 콘솔 JSON을 화면에서 읽어 전사한 자료다. 자동 stdout 다운로드 원본은 아니다. 원 화면은 사용자 탭 정보가 포함돼 비공개 보존하고 해시를 기록했다. [실행 세부](VM-INTERNAL-VERIFICATION.md).

## 2. 로컬 정적·회귀 검사

이번에는 앱/워크플로우 코드를 바꾸지 않았다. 초기 조회 오류2건을 진단했다: 컨테이너의 .venv/bin/python 경로가 없어 설치된 python을 사용했고, SQLAlchemy가 콜론 문자열을 bind로 해석해 조회 표현식을 chr(58)로 변경했다. 스키마/데이터는 수정하지 않았다. 관련 최종 SQL은 VM에서 실제 실행됐다. 신규JSON·링크·diff·비밀 미포함을 점검했다. 전체 공식tscan 또는 새로운 단위시험 통과 수를 만들지 않는다.

## 3. 시나리오별 실행 판정

### 기존 WF-02b 실제 요청의 직접 SQL/n8n 대조

| 요청 티켓  | PostgreSQL 직접 결과                                                                        | n8n 직접 결과                        |
| ------ | --------------------------------------------------------------------------------------- | -------------------------------- |
| T-2008 | attempt3·in_progress·ticket_rows1·linked/result_matches/reply_matches=true·alerts1·DLQ0 | 요청ID와 본체 실행37 일치·success/webhook |
| T-2009 | 동일 검사항목 통과                                                                              | 본체 실행39 일치·success/webhook       |
| T-2010 | 동일 검사항목 통과                                                                              | 본체 실행42 일치·success/webhook       |
| T-2011 | 동일 검사항목 통과                                                                              | 본체 실행44 일치·success/webhook       |

각 request_id는 내부 증거JSON에 있으며 [기존 API3회](../runs/vm-retest-summary-20261106T054458Z.json) 및 [후속 API1회](../runs/real-qa-WF02b-lead-20261106T060403Z.json)의 값과 대조했다. 이4개는 이번에 새로 생성한4건이 아니다. 이번 새관측은 기존 문의/티켓의 실DB 연결·소유자·저장응답티켓·관리자답변일치·알림/DLQ 관계 및 n8n 실행 연관이다.

n8n은 SQLite이며 readOnly로 열었다. 전체 실행행20개를 관측했고4개 request ID에 해당하는 본체 실행을 찾았다. support의 저장설정은 default, handoff/search/errors는 성공·오류 저장none이었다. index는 성공none/오류all이었다. 설정을 변경하지 않았다. 따라서 **본체 실행4개 대조는 확인됐지만 하위 workflow 개별 실행·노드 payload·LLM 호출수 전체 추적은 미완료**다. 상세노드조회 시도 후 GitHub탭으로 이동된 화면을 확인해 추가입력을 중단했고 해당 시도는 성공으로 집계하지 않았다.

### 공식/팀 품질시험 범위

이번 직접대조4/4는 공식14개 또는 팀5개 전체 통과율이 아니다. WF-02b 관련 저장·추적 근거만 보강했다. WF-01 정상근거답변, WF-02 독립3회, WF-03 무근거질문 원입력, WF-04 장애, WF-05 문서권한, WF-06 타인조회, WF-07 PII, WF-08 주입, WF-09 동일ID멱등, WF-10 LLM중단, WF-11 지연, WF-12 복합긴급, WF-13 입력경계와 팀≥5 전체는 이번에 새로 실행하지 않았다. 공식suite 성공/전체와 예외처리율은 N/A, p50/p95·벤치는 미측정이다.

## 4. 제출·시연 요구와 피드백 추적

- ‘VM 내부를 직접 실행했는가’에 대해 이번에는 실제 셸 명령과 컨테이너내 HTTP/SQL/SQLite 관측이 있다. 이전 외부 API client 실행을 내부 실행으로 이름만 바꾸지 않았다.
- 대표이관근거: 기존 WF-02b API raw와 이번 SQL·실행ID 대조. 정상근거답변/VM 장애 대표로그3종과 전체7단계 리허설은 아직 없다.
- 과거 실패1은 로컬 TM-02 질문누락이다([원 실패](../runs/llm-fresh-app-20261105.json)). 이후 VM UI1회3항목 표시는 [관측](../runs/vm-browser-WF02-retest.json)에 있지만 동일 환경/모델의3회 수정검증 완료로 확대하지 않는다.
- 과거 실패2는 로컬 긴급 JSON코드블록/triage_invalid였다([최초](../runs/c04-app-integration-20261105T103935Z.json)). 사본 JSON 출력 설정 후 [재시험](../runs/c04-app-integration-20261105T104124Z.json) urgent_security high 확인. 현재 VM 복합WF-12의3회 안정성은 별도다.

## 5. 알려진 한계와 다음 검증 순서

1. 하위 성공 실행 로그가 저장되지 않는 범위는 팀장과 보존정책/한정시험 관측방법을 정한 뒤 node trace를 확보한다. 임의로 운영 설정을 바꾸지 않는다.
2. 현재 VM 실제 승인문서·권한과 WF-01 근거답변 확인 후 공식14/팀≥5·LLM3회·bench5회·정상/예외/이관 캡처·7단계 리허설을 수행한다.
3. fault/reset/재시작/복원·동일ID 재요청과 SQL 추가관측은 예약범위에서 별도 수행한다. 이번4개 DB행은 유지했고 티켓/알림/DLQ를 삭제하지 않았다.
4. 전체공식tscan·가이드 원본15개 제출체크·강사 피드백 확인 전 최종품질 승인을 표시하지 않는다.

## 6. 버전 및 근거

- 템플릿: docs/EXECUTION-RESULT.md. 기준: docs/EVALUATION-GUIDE.md, docs/VM-TEAM-TESTING.md, 사용자 제공 시험품질_담당자_가이드.pdf.
- 실제 배포 HEAD3ff836a는 이번 VM에서 직접 git 조회했다. 기존 raw client의 로컬main95d8af3과 구별한다.
- [VM 내부 증거](../runs/vm-internal-observed-20261106.json), [세부 절차](VM-INTERNAL-VERIFICATION.md), [SQL 준비본](../requests/verify-team-vm-wf02b.sql). 화면 원본은 비공개 보존, 해시만 신규증거에 포함.
- 결론: **VM 내부 실행·요청4개 PostgreSQL 연결대조·n8n 본체실행ID 대조 완료. 하위 노드 전체추적 및 전체 QA 평가는 진행 중.**
