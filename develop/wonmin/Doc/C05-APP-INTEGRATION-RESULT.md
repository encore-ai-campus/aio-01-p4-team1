# C05 P1-3 실제 app 연동 결과 · 2026-11-05

지혜님 `origin/feat/jihye-p0`의 `ec6a735`를 원민 브랜치에 병합했다(병합 커밋 `496385f`). 해당 Git 원본으로 backend를 재빌드하고 PostgreSQL 마이그레이션 `0005`를 적용했다. **실제 n8n → app FastAPI → PostgreSQL 연동 15개 시험 그룹을 통과했다.** 앞선 1902a2b/501 보고서는 당시 실패 기록으로 보존하며, 현재 구현 판정은 이 문서를 따른다. 원격 push는 하지 않았다.

## 환경과 연결 범위

- 로컬 OrbStack Ubuntu 26.04.1 LTS에 로그인하여 Docker Compose에서 실행했다. 팀 공용 VM 시험은 아니다.
- `deploy/compose.c05.yaml`에 실제 저장 backend와 HTTP 장애 주입 프록시를 추가했다. 정상 요청은 원문 body를 실제 FastAPI로 전달하며 저장 Mock을 사용하지 않는다. 프록시의 지정된 실패 요청만 503으로 응답한다.
- 별도 DB `wonmin_c05_app`에 계약 직원 6명의 합성 시험 fixture를 명시적으로 seed했다. 실제 data-api 수집 및 관리자 계정 생성은 하지 않았다. 기존 기본 DB `wonmin_integration`의 employees/tickets/alerts/dlq는 모두 0→0으로 유지했다.
- 정본 `workflows/oke-handoff.json`의 30개 노드를 사용하는 전용 app 시험 사본을 게시했다. 변경점은 H03의 app 모드·프록시 주소, 전용 ID/웹훅 경로, 실제 Credential ID뿐이다. 원본 SHA-256은 실행 보고서에 기록했다.
- n8n에서 [wonmin-c05-app-real 열기](http://127.0.0.1:15678/workflow/wmc05livecf8ca714f5). 웹훅은 `/webhook/wonmin-c05-app-real`이며 기존 X-Team-Key Credential을 사용한다. 원래 handoff의 전역 practice 설정은 유지했다.

## 실제 결과

전체 요청·응답 및 SQL 관측은 [실행 JSON](../runs/c05-app-integration-20261105T095248Z.json)에 있다. `count`만으로 성공을 판단하지 않고 신규 `stored=1, duplicate=false`, 중복 `stored=0, duplicate=true`와 실제 행 수를 대조했다.

| 확인 항목 | 실제 결과 |
| --- | --- |
| API 인증 | 세 endpoint 각각 키 누락/오류 401, 총 6회 거절 |
| `/tickets` 신규·중복 | 신규 201/duplicate=false, 재요청 200/duplicate=true, 동일 ID·DB 1건 |
| `/tickets` 동시 8회 | 신규 1·중복 7, ID 동일·DB 1건. 다른 직원의 동일 key 사용은 403 |
| `/alerts` 순차·동시 8회 | 순차 신규/중복 ACK 유지. 동시 신규 1·중복 7·DB 1건 |
| `/alerts` event_key 없음/null | 각 2회씩 모두 신규 ACK, 별도 4건 저장 |
| `/dlq` | request_id 값 있음/null 모두 HTTP 200·stored=1 및 실제 저장 확인 |
| 실제 알림 실패 | 존재하지 않는 ticket_id의 알림은 404, 이미 저장한 정상 티켓은 유지 |
| n8n 정상·중복·긴급 | 정상/중복 모두 ok=true·alerted=true, 티켓/알림 각 1건. 긴급 priority=high 저장 |
| n8n 동일 키 동시 8회 | 신규 1·중복 7, 동일 ticket_id, 티켓/알림 각각 1건 |
| alerts_down | 티켓 1건 유지, ok=false·alerted=false·dlq=true. 복구 후 같은 티켓 ID·알림 1건 유지 |
| tickets_down | 티켓 0건, 제한 재시도 2회, alerted=true·dlq=true |
| 티켓+DLQ 실패 | 티켓 0건, alerted=true·dlq=false |
| 알림+DLQ 실패 | 티켓 1건 유지, alerted=false·dlq=false |
| 전체 실패 | 티켓 0건, alerted=false·dlq=false, 유한 종료 |
| 일시 티켓 실패 | 첫 503 후 2차 실제 저장 성공, 티켓 1건 |
| PostgreSQL 재시작 | 시험 티켓 8·알림 13·DLQ 4건이 전후 동일. 재요청도 기존 ID·중복 ACK, 추가 행 없음 |

표의 여러 검증을 15개 시험 그룹으로 묶었다. 장애 수습에서는 프록시 호출/전달/주입 횟수와 DB를 함께 확인했다. 503 주입은 실제 PostgreSQL 고장이나 팀 VM 네트워크 장애 재현과 구별한다. DLQ에는 시험 문의 원문·직원명·인증키가 없는 것도 검사했다. 알림은 `/alerts` 저장 성공이며 외부 메신저 수신 시험은 아니다.

## 회귀 시험과 발견 사항

- 원민 Node 97개, Python 8개(기존 배포 출처 3 + 프록시 실제 HTTP 5) 통과. [회귀 집계](../runs/c05-app-regression-20261105.json).
- 지혜 전체 시험은 최초 **221 통과·1 실패**했다. [최초 실패 기록](../runs/jihye-ec6a735-full-20261105T094636Z.json)을 보존했다. `test_unimplemented_endpoints_do_not_claim_success`의 Settings가 컨테이너의 INTERNAL_API_KEY를 상속해서, 설정 없음 503 대신 인증 거절 401을 반환한 환경 의존 문제다.
- 실행 중 서버의 키는 유지하고 **pytest 자식 프로세스에서만** `env -u INTERNAL_API_KEY`로 격리하여 재실행했다. 실제 PostgreSQL 시험을 포함해 [222 통과·기존 경고 1건](../runs/jihye-ec6a735-isolated-tests-20261105T094954Z.json). 지혜 소스/테스트를 직접 수정하지 않았다. 지혜님께 해당 테스트의 `internal_api_key=None` 명시를 제안한다.
- 시험 후 장애 계획을 `{}`로 복구했다. [최종 상태](../runs/c05-app-final-state-20261105.json): app 시험 workflow 게시 중, 컨테이너 7개 실행, n8n·두 backend 건강 확인 HTTP 200. 시험 DB 행은 검토·영속성 근거로 보존했고 볼륨을 삭제하지 않았다. 성공/실패 execution body 저장은 꺼 두었으므로 n8n execution 이력 대신 실제 HTTP 응답·프록시 관측·SQL 근거를 남겼다.

## 재실행

현재 기동된 전용 실습 환경에서 Ubuntu 터미널로 프로젝트의 `develop/wonmin` 폴더에 이동한 뒤 실행한다.

```bash
python3 tools/test-c05-app-integration.py
```

필요 조건은 `.runtime/lab.env`의 기존 Credential, `workflow-ids.json`, ec6a735 Git 원본 snapshot, `0005`로 마이그레이션된 `wonmin_c05_app` 및 직원 fixture 6명, 두 Compose 파일의 서비스다. 스크립트는 기존 행을 지우지 않고 매번 새 접두사를 사용한다. 실행 중 n8n/프록시와 PostgreSQL 재시작이 있으므로 다른 시험과 동시에 실행하지 않는다. 시험 성공 시 전용 app workflow를 게시 상태로 남기고, 실패 시 게시 해제하며, 장애 계획은 종료 시 복구한다.

backend 전체 시험 재실행은 같은 폴더에서 아래 명령이다. `env -u`는 시험 자식에만 적용된다.

```bash
docker compose --env-file .runtime/lab.env -f deploy/compose.lab.yaml exec -T -e OKE_RUN_DB_TESTS=1 backend env -u INTERNAL_API_KEY uv run pytest -q
```

기존 `tools/verify-c05-live.py`는 저장 미구현 버전의 진단용이다. 현재 ec6a735의 `AlertStoredResponse`와 실제 저장 인수 시험에는 위 새 도구를 사용한다.

## 다음 연결과 전달

지혜님께: 원민 app workflow의 실제 연결 결과는 정상·중복·동시 요청과 부분 실패 모두 통과다. event_key 없음/null은 매번 신규이며, keyed 중복 ACK를 workflow가 정상 성공으로 처리했다. 실패 테스트의 환경 격리 보완을 부탁드린다. practice 실제 data-api는 이번 결과에 포함하지 않는다.

오현님께: 확인한 `origin/main=41644de`에서 `docs/API-CONTRACT.md`의 최근 변경은 `db14b79`이다. C05 알림 예시는 아직 stored/count만 있고 duplicate와 DLQ HTTP 200이 명시되지 않아, 사용자 전달 승인 및 ec6a735 실제 구현을 공통 문서에 반영할 후속 커밋이 필요하다. 공통 문서는 원민이 수정하지 않았다.

다음 업무는 실제 data-api 직원/권한 확보 → 본체 C04와 동일 app 저장 환경 연결 → 팀 VM·공통 원본/공식 flow.py·LLM 3회·bench 검증이다. Error Trigger의 실제 app 저장 수습 전체 재시험은 이번 handoff 결과와 별도로 진행한다.

공유용: 변경 파일은 원민의 C05 Compose·장애 프록시·통합 실행기·시험/결과 문서다. 확인은 실제 n8n webhook HTTP와 PostgreSQL SQL 대조로 수행했다. 실제 결과는 15개 그룹 통과, 동시 8회 티켓/알림 각 1건, PG 재시작 보존이다. 다음 연결 상대는 지혜님(시험 격리), 오현님(공통 C05 명시), 다혁님(본체 app 연결)이다.
