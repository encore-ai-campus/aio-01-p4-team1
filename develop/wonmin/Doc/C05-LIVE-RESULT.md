# C05 실제 저장 검증 · 2026-11-05

세 팀원의 최신 원격 브랜치를 다시 가져와 원민 `feat/wonmin-p0`에 반영했다. **실제 HTTP와 PostgreSQL로 검증했지만 C05 저장은 미구현으로 차단됐다. Mock 통과나 DB 스키마 준비를 실제 저장 성공으로 처리하지 않는다.** 이번에는 원격 push를 하지 않는다.

## 브랜치와 소스

| 담당 | 최신 HEAD | 반영 |
| --- | --- | --- |
| 지혜 feat/jihye-p0 | 4fdc3136c1cf643a094bef4bbb9fc872be444571 | 이미 병합된 최신 상태 |
| 유빈 feat/yubeen-p0 | 1b0c3b54ef118f7637404060f2d8907a560fb985 | 새3개 커밋을 충돌 없이 병합, 병합 커밋 afe6bea |
| 다혁 feat/dahyeok-p0 | 859e3afb10a13baed6f9a0ea0477c4470577c8db | 이미 병합된 최신 상태 |

원격 브랜치 목록도 재조회해 별도 feat/jihye/yubeen/dahyeok 후속 브랜치가 없는 것을 확인했다. 원민의 직전 main 병합과 기존 개발 소스를 보존했다. 이번 새 반영은 유빈의 검색 평가·MRR·실행 준비 문서/의존성 파일이다. 그 RAG 이미지를 새 버전으로 재배포한 것은 아니다.

C05 대상 backend의 deps·tickets/alerts 라우터·알림 모델 4개 파일 SHA-256을 병합된 지혜 소스와 실제 실행 컨테이너에서 대조해 일치함을 확인했다. backend 소스가 이미 최신이므로 불필요한 재빌드는 하지 않았다.

## 실제 확인 방법과 결과

`tools/verify-c05-live.py`를 Ubuntu에서 실행했다. 호출 대상은 실제 backend이며 practice 메모리 Mock을 사용하지 않았다. DB 관측은 읽기 전용 연결로 새 시험 접두사에 해당하는 행만 집계했다. 표본 알림은 실제 발급 티켓이 없으므로 ticket_id=null을 사용했다.

| 확인 | 실제 결과 | 판정 |
| --- | --- | --- |
| /health/live | HTTP200 | 프로세스 확인 |
| 세 저장 API 키 누락 | 각각 HTTP401, 총3회 | 누락 거절 확인 |
| 세 저장 API 잘못된 키 | 각각 HTTP501 | 실제 키 대조 미구현. 정상 인증 확인 아님 |
| 티켓 동일 키 순차2회·동시8회·high | 모두 HTTP501 | 신규/중복 ACK 및 1건 저장 검증 차단 |
| 알림 동일 event_key 순차2회·동시8회 | 모두 HTTP501 | 신규/중복 ACK 및 동시성 검증 차단 |
| 알림 event_key 없음2회·null2회 | 모두 HTTP501 | 매번 신규 저장 정책 검증 차단 |
| DLQ request_id 문자열/null 각1회 | 모두 HTTP501 | HTTP200·stored=1 ACK 검증 차단 |
| 직접 HTTP 총33회 | **401 3회, 501 30회** | 실제 저장 성공0회 |
| 시험 전→후 DB 행 | tickets 0→0, alerts 0→0, dlq 0→0 | 중복 억제 성공이 아니라 저장되지 않은 상태 |
| DB 기반 | revision0004, employees 총0건 | 직원 seed와 실제 저장 처리가 별도 필요 |

별도의 인증된 `wonmin-c05-app-check` 배포 사본에서만 mode=app으로 고정해 실제 n8n HTTP도 호출했다. 일반 lab의 practice 모드와 기존 업무 workflow는 유지했다. 결과는 HTTP200이지만 `ok=false, ticket=null, reason=tickets_down, alerted=false, dlq=false`였다. C04의 안전한 실패 응답 확인이며 실제 접수 성공이 아니다. 시험 사본은 게시 해제했고 경로의 HTTP404까지 확인했다. DB를 직접 쓰거나 초기화하지 않았다.

알림 응답 모델도 실제 backend에서 다시 확인했다. `StoredResponse`는 여전히 stored/count만 있고 `duplicate=true`는 직렬화 과정에서 제거된다. 팀장이 승인한 중복 ACK 필드 유지가 아직 반영되지 않았다. DLQ 라우터의 기본 HTTP200 선언은 유지되지만 실제 저장 ACK는 받지 못했다.

근거: [실제 요청·DB 전후·소스 해시·n8n app 결과](../runs/c05-live-20261105T053604Z.json). 비밀값은 private lab.env와 n8n Credential에만 두고 보고서에는 기록하지 않았다.

## 다음 연결 상대와 재시험 조건

**지혜님에게 요청할 구현:** require_internal_key의 실제 키 대조, UnavailableBackend 대신 /tickets·/alerts·/dlq 실제 DB 저장, StoredResponse duplicate 필드, 필요한 직원 seed/신원 매핑이다. 현재 deps의 키가 있는 경우와 기본 backend.execute가 모두501로 종료한다. 상대 파일은 원민이 대신 수정하지 않았다.

구현 반영 후 원민이 같은 조건으로 신규201/중복200·동일 key 티켓1건, 알림 stored=1/duplicate=false 및 stored=0/duplicate=true, 키 없음/null, DLQ200 ACK를 재시험한다. **티켓 저장 후 알림 실패 시 티켓 유지·실제 거래/동시성·재시작 영속성은 이번에 성공 전제에 도달하지 못했으므로 미검증**이다. 실제 C05 구현 후 장애 주입·복구를 추가 실행해야 한다.

병합 후 회귀는 원민 **89 passed**, 유빈 **172 tests OK**였다. 이는 C05 실제 저장 성공 판정과 별개다. 기존5개 컨테이너는 실행 중이며, 소스 변경/검증 자료는 로컬 원민 브랜치에만 반영한다.
