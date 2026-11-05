# 원민 실행 증거 색인

현재 팀 소스 재배포(2026-11-05): [배포/PG48](team-redeploy-20261105T045828Z.json), [최종 HTTP·RAG 도달·index 실행35](team-http-check-20261105T051103Z.json), [브라우저 확인·제약·다음 연결](../Doc/TEAM-REDEPLOY-RESULT.md). 팀 workflow5개 UI 표시,4개 게시/index 수동 Mock 성공. 직원 API/실제 저장/임베딩은 미연결로 업무 통합 성공과 구분한다.

최종 Ubuntu 실환경(2026-11-05): [실제 자동 오류 5조건](ubuntu-errors-matrix.json), [최종 복구·Ollama·PG45](ubuntu-final-restoration.json), [해석·재현·다음 연결](../Doc/UBUNTU-INTEGRATION-RESULT.md). 전용 Mock 4조건의 자동 Error Trigger 수습을 확인했고 실제 backend 조건은 501로 저장 실패다. 매트릭스 종료 시 준비 지연으로 복구 확인이 중단된 사실과 이후 별도 복구 성공을 구분했다. 일반 handoff와 errors 연결 유지, 오류 시험 부모 비활성/404, 로컬 모델 HTTP200, 원민 회귀89 통과. 아래 미실행 표기는 이전 시점 결과다.

지혜님 질의 ACK 검토: [alert-no-key-practice-review.json](alert-no-key-practice-review.json), [회신 기준](../Doc/ALERT-NO-KEY-REVIEW.md). key 없음/null·keyed 순차/동시·practice 같은티켓2회·오류부모ID 없음2회·레거시ACK 소비자행렬8그룹 확인. 실제data-api/PG/n8n은 미실행이다.

최신 P1-3(2026-11-05): [최종89/89 원 출력](p1-3-final-20261105T024732Z.txt), [20개 시나리오의 안전한요청/결과·관측·코드해시](p1-3-final-20261105T024732Z.json), [구현·실제 부모연결 절차](../Doc/P1-3-RESULT.md). 최초 p1-3-local-20261105T024621Z.json/.txt도보존. 실제ErrorTrigger자동발화/부모ID설정·backend/DB는미실행이다.

최신 P1-2(2026-11-05): [원 출력65/65](p1-2-local-20261105T022016Z.txt), [실제 fault HTTP Mock 관측·코드 해시](p1-2-local-20261105T022016Z.json), [구현·후속 가이드](../Doc/P1-2-RESULT.md). 알림 duplicate·DLQ HTTP200 승인 적용. 아래 P1-1/C04/C05는 해당 시점의 기록이며 n8n·실제 backend/DB는 여전히 미실행이다.

최신 C04(2026-11-05): [c04-pair-aac0dbf-review.json](c04-pair-aac0dbf-review.json), [경계 연결 검토](../Doc/C04-PAIR-REVIEW.md). 최신08 요청 생성·응답 매핑과 원민 P1-1의 로컬17개 관측 일치. 실제 C04발신은 Mock이며 n8n·실제backend/DB는 미실행. 아래9bda763/P0-2는 과거 기록이다.

C04 후속 검토: [c04-dahyeok-9bda763-review.json](c04-dahyeok-9bda763-review.json), [연결 대조 설명](../Doc/C04-CONNECTION-REVIEW.md). 최신 P0-2 로컬6건의 골격 상태 및 SPEC 표본1개 수신 적합 확인. C04 발신 노드·응답 mapper는 미구현이며 실제 연결 PASS가 아니다.

C05 후속 검토: [c05-jihye-4bbbf49-review.json](c05-jihye-4bbbf49-review.json), [모델 대조 설명](../Doc/C05-MODEL-REVIEW.md). 실제 DTO 검증 7/7 적합, 중복 알림 응답 직렬화 불일치 1건이며 실제 API·DB/n8n 호출 결과는 아니다.

최신 상태: **P1-1 로컬 구현·HTTP Mock 검증 40개 통과 / 공식 check·n8n·실제 백엔드/DB 미실행**. 최종 검증은 [p1-1-final-20261104T093145Z.txt](p1-1-final-20261104T093145Z.txt), 코드 해시와 실제 관측은 [p1-1-final-20261104T093145Z.json](p1-1-final-20261104T093145Z.json) 참조. 아래 P0 기록은 당시 상태다.

2026-11-04 P0 입력 준비. 브랜치 `feat/wonmin-p0`, 기준 `origin/main` = `ffff63689cc532c9789a3e56b51e6306e66c1d44`. 산출물 커밋은 이 색인을 포함하는 `feat(wonmin): prepare P0 reliability scenarios and demo requests` 커밋으로 식별한다.

## P0 당시 기록

| 항목 | 상태/근거 |
| --- | --- |
| 로컬 정적 확인 | [p0-validation.txt](p0-validation.txt): JSON 파싱·ID/입력 계약·요청 대응·필수 명세 확인. 서비스 기능 판정이 아님 |
| 팀 사례 | [team.json](../cases/team.json): 12개, TM-01~08 및 관리자 양성/음성·분류·검증 거절 추가. 전부 not_run |
| handoff 사례 | [handoff.json](../cases/handoff.json): 13개, TM-09/10 및 신규/중복/400/401/403/404/429/500/timeout/지연 저장. 전부 not_run |
| app 수동 확인 | [app-integration.md](../cases/app-integration.md): 11개 절차, 전부 미실행 |
| 시연 요청 | requests/demo-normal·demo-clarify·demo-handoff·demo-urgent·demo-failure.json 및 bench-normal.json |
| 80일차 flow.py | 저장소에서 미발견, 출처/버전/실행 위치/--help 확인 대기. 대체 도구 작성 안 함 |
| common.json 원본·SHA-256 | 미확보. 파일 생성/복원/기대 재구성 안 함. 반입 후 원본 경로·배포 버전·양쪽 SHA-256 기록 |
| suite 호환성 | 현재 P0 JSON은 wonmin-p0-review-v1 수동 검토 명세. 공식 flow.py에 바로 넣을 수 있다고 보장하지 않음. 키트 --help/코드 확인 후 팀 suite만 변환하고 기대 보존 |
| 모드·배포·서비스 대상 | 미설정/미호출. n8n/저장/fault/ops 동일 인스턴스 검증 대기 |
| 색인/모델/LLM | 버전·실제 호출 미확인. LLM 3회·bench·VM 모두 미실행 |
| 실제 규정 원본 | 8종 및 관리자 문서 실제 원문/권한/인증 미확인. 지혜·유빈·오현 연결 필요 |
| 워크플로우 | oke-handoff=P1-1, oke-errors=P1-3 예정. 공식 check·n8n 게시·실행 전부 미실행 |

## 이후 실행 기록 필수 항목

실행 시각/ID, practice 또는 app, 배포·워크플로우 커밋, 키트 버전/해시, 색인/모델, 실제 호출·fault·ops의 비밀값 없는 별칭, 사전/사후/지연 후 건수, 명령, raw 보고서 경로, 기대/실제/판정, n8n 실행 ID, 실패→수정 소유자/커밋→동일 조건 재시험, 정리/복구 결과를 기록한다.

P0 당시 기능 PASS/실패 수와 처리시간은 집계하지 않았다. 실제 서버 호출·장애 주입·저장·LLM 실행은 0회였다. P0 준비 완료와 키트 반입 대기를 구분한다.

## P1-1 · p1-1-local-20261104T092738Z

최종 코드 재확인: `WONMIN_TEST_REPORT_BASENAME=p1-1-final-20261104T093145Z.json node --test` — 40/40, 종료0. 최종 JSON에는 workflow·Mock·테스트 소스 SHA-256을 기록했다. 아래 최초 통과 보고서는 보존한다. 이후 수정은 Mock 동시 연결 backlog를 명시한 것과 증거 해시 추가이며, 최종 보고서에서도 같은 정상/중복/동시 관측을 확인했다.

- 실행: 2026-11-04, 코드 기준 P0 `5410bf8` 이후 P1-1 작업. 산출물 버전은 본 색인을 포함하는 `feat(wonmin): implement P1-1 handoff and C05 HTTP mock` 커밋으로 식별한다. 워크플로우의 정확한 SHA-256은 아래 JSON에 자동 기록했다.
- 환경: Node v26.12.1, Python 3.15.1, 두 개의 독립 ephemeral HTTP Mock. practice/app은 로컬 설정 분기 시험을 위한 별도 Mock이며 실제 data-api/backend가 아니다. 서버는 loopback 임의 포트에 기동 후 종료했고 공유 환경·원격 서비스·DB/LLM은 호출하지 않았다.
- 명령: 저장소 루트 `WONMIN_TEST_REPORT_BASENAME=p1-1-local-20261104T092738Z.json node --test`. stdout/stderr는 Python subprocess로 캡처했다. 원 보고서는 덮어쓰지 않았다.
- 원 출력: [p1-1-local-20261104T092738Z.txt](p1-1-local-20261104T092738Z.txt) — tests 40 / pass 40 / fail 0 / 종료0. 경과시간은 로컬 검사 소요 시간으로 서비스 bench/응답시간 실측에 합산하지 않는다.
- 실제 관측: [p1-1-local-20261104T092738Z.json](p1-1-local-20261104T092738Z.json) — 정상 응답, 순차 2회 동일 ticket_id·duplicate 전환·저장1건, 동시8회 신규1/중복7·저장1건, app Mock의 티켓1·알림1·practice 관측 불변. 실제 응답/관측에서 추출했으며 n8n 실행 ID는 없다.
- 추가 실제 확인: Mock `--help` 종료0; Python AST, 워크플로우/요청 JSON 파싱, 15개 노드 ID 유일성·연결 대상 참조 확인. 공식 flow.py 검사가 아니다.
- 구현 전 실패 확인: workflow 파일이 없는 상태에서 시험은 `P1-1 workflow must exist`로 실패했다. 구현 후 28개 통과. 로컬 Code VM에서 URL 전역을 제공하지 않는 회귀에서는 정상 요청이 503으로 실패했고, 모드 선택을 외부 모듈/URL 전역에 의존하지 않는 origin 검사로 수정한 뒤 관련 회귀와 전체40개를 통과했다. 이 개발 중 실패 원 출력은 별도 파일로 보존하지 않았고 실제 서비스 장애/공통 실패2건 증거로 집계하지 않는다.
- 미확인/대기: 공식 flow.py check·common 원본/해시, n8n import/게시/Header Auth/Executions/동시 실행, 실제 data-api 인증·저장 및 app PostgreSQL 거래·권한·영속성, support 실제 연결, LLM3회·bench·VM. n8n 게시·시험은 사람이 수행한다.
- 정책 경계: WM-03 practice 알림 중복 건수, WM-04 부분실패 ok/입력 오류 외형·app duplicate ACK는 미확정/실연결 미확인이다. P1-2 retry·DLQ, P1-3 errors는 미구현. P0 사례 기대·common 원본을 바꾸지 않았다.
- 다음 연결: 다혁님 C04 입력·응답 매핑, 지혜님 C05/ACK/동시 거래, 오현님 키트·Credential·n8n 환경. 상대의 동의/실제 연동 완료로 해석하지 않는다.
