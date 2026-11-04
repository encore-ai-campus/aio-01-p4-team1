# app 통합 확인 절차 · P0 준비

현재 모든 항목은 미실행이다. C01/C04/C05, API-CONTRACT §8, DATA-AND-DB §3을 적용한다.

사전 준비: 지혜님이 제공한 전용 시험 계정·세션·내부 Credential을 사용한다. 키·비밀번호·세션 쿠키를 요청 파일이나 실행 보고서에 저장하지 않는다. `SERVICE_MODE=app`은 서버 설정에서 선택한다. 실제 handoff URL이 backend를 가리키는지 확인하고 practice 저장소에 같은 요청이 쓰이지 않는지 대조한다.

| ID | 입력/조건 | 기대 및 관측 | 정리 |
| --- | --- | --- | --- |
| APP-01 | 로그인 없이 `/api/my-requests` 호출 | 401, 문의·티켓 미노출 | 응답의 안전한 상태 요약만 보관 |
| APP-02 | 일반 직원 세션으로 `/api/admin/tickets`, `/api/admin/alerts` 호출 | 각각 403, 타인 정보 미노출 | 로그아웃 |
| APP-03 | 최초 비밀번호 미변경 세션으로 `/api/ask` 호출 | 403 password_change_required. me/change-password/logout만 허용 | 비밀번호 변경은 계정 소유자 수행 |
| APP-04 | 정상 직원으로 새 ID 이관 요청 및 동일 body 재요청 | 같은 ticket_id, 같은 request_key 티켓 1. 관리자 목록과 본인 목록 연결 확인 | 전후 건수·실행 ID 보존, 공유 DB 삭제 금지 |
| APP-05 | 다른 직원이 APP-04 request_id 재사용 | 타인 티켓·문의·응답 노출 없이 거절. 소유자 티켓 건수 유지 | 원문·연락처 없는 응답 요약 |
| APP-06 | 같은 직원·동일 ID·동일 body를 동시 2회 전송 | 저장 1건, 두 ticket_id 동일. 실제 UNIQUE·거래 근거와 HTTP 상태 대조 | 병렬 실행 ID 둘 다 보존 |
| APP-07 | 내부 `/tickets`, `/alerts`, `/dlq`에 X-Api-Key 누락/오류 | 401/403 인증 거절, 쓰기 0. 웹 세션을 내부 API 인증으로 사용하지 않음 | Credential 출력 금지 |
| APP-08 | TM-05 긴급 요청 | high 티켓 1, 실제 알림 ACK, 권한 있는 관리자만 조회 | 안전한 DB/관리자 관측과 실행 ID 연결 |
| APP-09 | 전용 설정에서 tickets 장애 후 alerts/DLQ 개별 장애 | C04 tickets_down·ticket=null, 실제 ACK대로 플래그. 알림만 실패하면 생성 티켓 유지. WM-03/04 미정 필드는 미판정 | 담당자가 장애 해제, 새 정상 요청으로 복구 확인 |
| APP-10 | APP-04 티켓 저장 뒤 지혜님이 서버/DB 재시작 | 재로그인·재조회 후 동일 ticket_id 및 저장 1건, 영속성 유지 | 재시작은 지혜님 수행. 볼륨 삭제 금지 |
| APP-11 | 동일 ID에 다른 body 또는 직원 | 충돌/권한 거절, 기존 레코드 내용 불변, 타인 정보 미노출 | 기존 레코드 안전한 요약 대조 |

관측은 `/api/admin/tickets`, `/api/admin/alerts`, `/api/my-requests`와 지혜님이 제공하는 마스킹 DB 조회를 사용한다. 내부 ops 상세 경로는 WM-02가 미확정이므로 만들어 있다고 가정하지 않는다. app 결과를 data-api ops로 판정하지 않는다.

매 실행마다 모드·배포 커밋·저장소 별칭·전후 건수·HTTP/필수 필드·n8n 실행 ID·정리 결과를 runs에 남긴다. 실패 시 원 보고서와 동일 조건 재시험 보고서를 각각 보관한다. P0 문서 준비 확인은 이 통합 시험 통과가 아니다.
