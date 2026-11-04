# 원민 실행 증거 색인

2026-11-04 P0 입력 준비. 브랜치 `feat/wonmin-p0`, 기준 `origin/main` = `ffff63689cc532c9789a3e56b51e6306e66c1d44`. 산출물 커밋은 이 색인을 포함하는 `feat(wonmin): prepare P0 reliability scenarios and demo requests` 커밋으로 식별한다.

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

현재 기능 PASS/실패 수와 처리시간은 집계하지 않는다. 실제 서버 호출·장애 주입·저장·LLM 실행은 0회다. P0 준비 완료와 키트 반입 대기를 구분한다.
