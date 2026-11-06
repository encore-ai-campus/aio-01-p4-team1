# P1-2 STEP 1 · 검색 요청 수신 진단

- 상태: 로컬 JSON·Code 정적 검사 완료. n8n Import·화면 수동 실행·Webhook HTTP 확인은 사용자 확인 전 미실행.
- 근거 파일: `workflows/oke-search.json`. 기존 `oke-index.json`과 `Doc/INDEX-RESULT.md`는 수정하지 않았다.
- 선택 이유: C03의 POST `oke-search` 경로를 유지하면서 워크플로우를 비활성화하고, `step`·`mock`·`diagnostic_only`로 임시 응답을 실제 검색 결과와 구분한다. 인증·권한 판정 전에는 프로덕션 활성화하지 않는다.

| 노드 | 입력 → 출력 | 목적 |
| --- | --- | --- |
| 검색 요청 수신 (STEP 1 테스트 전용) | POST JSON → n8n Webhook item의 `body` | 테스트 Webhook 수신. 인증 미구현 |
| 요청 구조 확인 (STEP 1) | `body` → `body_is_object`, `received`의 5개 필드 | 필드 전달과 JSON 객체 형태만 관찰. 검증·권한 판정 없음 |
| 진단 응답 반환 (HTTP 200) | 진단 item → HTTP 200 JSON | STEP 1 응답. C03 최종 evidence 응답 아님 |

- 로컬 검증: JSON 파싱, 비활성 상태, POST·responseNode 설정, 3노드·2연결 검사 통과. Code를 예시 JSON으로 별도 실행해 5개 필드 전달과 추가 필드 제외 확인. 실제 n8n 노드 실행 결과는 아니다.
- 보안 제한: 테스트 요청에 비밀값·실제 연락처·관리자 문서 본문을 넣지 않는다. 현재는 요청의 `query`와 `access_levels` 값을 진단 응답에 되돌리므로 외부 공개하지 않는다.
- 오류·미측정: 실제 n8n Import/실행 오류 없음으로 주장하지 않는다. HTTP·인증·권한·임베딩·DB·검색 품질·시간·비용은 미실행 또는 미측정.
- 다음 증거: 사용자가 n8n 화면의 노드 연결, Test URL 요청 결과, HTTP 상태, 실행 ID와 마스킹한 출력, 실패 시 오류를 확인해 전달하면 이 기록에 실제/실패를 구분해 추가한다. 최종 RAG 설계서의 구현·검증 근거로 연결하되 수치 성과로 해석하지 않는다.
