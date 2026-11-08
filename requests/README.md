# requests · 시연·벤치마크·오류 요청

정상·보완·이관·장애·중복·보안 입력 JSON 38개를 포함한다. `demo-*.json`·`bench-normal.json`은 시연·측정용이며 `handoff-*.json`·오류 실행 입력은 해당 내부 경로용이다. `input-empty.json`, `input-unknown-user.json`, `input-too-long.json`은 의도적인 잘못된 입력이다. 모든 파일을 동일 엔드포인트의 정상 요청으로 보내지 않는다.

요청·응답은 [API 계약](../docs/API-CONTRACT.md), 시험 판정은 [평가 가이드](../docs/EVALUATION-GUIDE.md), 기존 결과는 [실행 결과](../docs/EXECUTION-RESULT.md)를 따른다. 로컬 Mock 재현은 [eval/](../eval/README.md)에 있다. 인증값은 실행 환경에서 전달하며 같은 논리 요청 재시도에는 같은 `request_id`, 새 요청에는 새 ID를 사용한다. 보안 시험용 합성 연락처·주입 문자열은 원문 그대로 보존했다.
