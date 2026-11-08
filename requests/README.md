# requests · 시연·벤치마크 요청 제출본

`main-backup` 기준 커밋 `b8448d0`에서 `develop/wonmin/requests/*.json` 13개와 `develop/dahyeok/requests/*.json` 25개를 원문 그대로 복사했다. 파일명 충돌은 없다.

`demo-*.json`·`bench-normal.json`은 시연·측정용이며 `handoff-*.json`·오류 실행 입력은 해당 내부 경로용이다. `input-empty.json`, `input-unknown-user.json`, `input-too-long.json` 등은 의도적으로 잘못된 입력을 담는다. 모든 JSON을 동일 엔드포인트의 정상 요청으로 보내지 않는다.

요청·응답 계약은 [API 계약](../docs/API-CONTRACT.md), 시나리오·대상·실행 순서·결과는 [평가 가이드](../docs/EVALUATION-GUIDE.md), [원민님 실행 안내](../develop/wonmin/README.md), [다혁님 실행 안내](../develop/dahyeok/README.md), [실행 결과](../docs/EXECUTION-RESULT.md)를 따른다. 인증값은 실행 환경에서 별도로 전달한다. 같은 요청의 재시도에는 같은 `request_id`를 사용하고 새 논리 요청에는 새 ID를 사용한다. 보안 시험용 합성 연락처·주입 문자열은 원문 그대로 보존했다.
