# P1-2 STEP 2 · X-Team-Key 인증 준비

- 범위: `workflows/oke-search.json` Webhook에 n8n Header Auth(`headerAuth`) 적용. STEP 1의 요청 구조 확인·HTTP 200 진단 응답 노드와 연결은 유지한다. 워크플로우는 비활성이다.
- 근거: C03은 `POST /webhook/oke-search`와 `X-Team-Key` 인증을 요구한다. 설치된 n8n 2.42.6의 Webhook 구현을 읽기 전용으로 확인한 결과, Header Auth는 `httpHeaderAuth` Credential의 Name/Value를 사용하며 누락·불일치 헤더를 후속 노드 실행 전 HTTP 403으로 거절한다. Credential 미연결은 HTTP 500이다.
- 안전 설정: JSON에 키 또는 Credential ID를 저장하지 않는다. n8n 화면에서 Header Auth Credential을 비공개로 생성하고 Name=`X-Team-Key`, Value=팀이 정한 키로 입력해 Webhook에 연결한다. 테스트 요청의 키도 저장소·문서·화면 캡처에 남기지 않는다.
- 진단 응답: 인증 성공 시 기존 `step=P1-2 STEP 1`, `mock=true`, `diagnostic_only=true`, `received` 응답을 유지한다. C03 검색 결과가 아니다. 인증 실패는 n8n의 기본 HTTP 403이며 H-Y01의 상세 JSON 제안을 확정 계약으로 사용하지 않는다.
- 검증 상태: 로컬 JSON·연결·기존 Python 테스트만 확인. 업데이트된 파일의 n8n Import/기존 워크플로우 반영, Credential 연결, 실제 성공·누락·오류 HTTP 요청은 사용자 실행 전 미검증이다.
- 이후 기록: 사용자가 Test URL로 세 경우의 HTTP 상태, 성공 시 3개 노드 실행, 실패 시 후속 노드 실행 없음과 마스킹된 실행 근거를 확인하면 실제 결과·실패 원인을 이 문서에 추가한다. 키 값과 요청 원문은 기록하지 않는다.
- 미구현: STEP 3 입력·권한 목록 검증, STEP 4 임베딩·DB/pgvector 검색, STEP 5 C03 evidence·장애 응답. 모델·점수·검색 품질·비용·시간은 미측정.
