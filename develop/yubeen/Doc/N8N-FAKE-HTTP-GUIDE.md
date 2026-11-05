# 개인 n8n용 RAG Fake HTTP 검증

상태: **VERIFIED_FAKE**. `tools/fake_http.py`는 기존 `search_http.make_handler`와 `index_http.make_handler`의 인증·입력 검사를 재사용하고, 합성 결과 함수만 주입한다. PostgreSQL, OpenAI, Markdown 원본을 읽지 않는다. 실제 색인·검색·VM 통합 증거가 아니다.

## 실행

`develop/yubeen`에서 Fake 전용 키 두 개를 터미널에 비공개로 입력한다. 실제 서비스 키를 재사용하지 않는다.

```bash
read -rsp 'Fake search team key: ' SEARCH_TEAM_KEY; echo
read -rsp 'Fake index team key: ' INDEX_TEAM_KEY; echo
export SEARCH_TEAM_KEY INDEX_TEAM_KEY
.venv/bin/python tools/fake_http.py --host 0.0.0.0 --search-port 8765 --index-port 8766
```

`0.0.0.0` 바인딩은 개인 Docker n8n에서 접근하기 위한 임시 설정이다. 테스트가 끝나면 `Ctrl-C`로 종료하고 키 환경변수도 해당 셸에서 해제한다. 실제 `index_http.py`나 `search_http.py`를 이 Fake 검증에 사용하지 않는다.

현재 개인 n8n 컨테이너 `day65-n8n-n8n-1`에서 **읽기 전용 도달성 검사** 결과, 아래 두 주소는 인증 없는 POST에 예상대로 401을 반환했다. WSL 인터페이스 주소 직접 접속은 시간 초과였다. Docker 환경이 바뀌면 주소를 다시 확인한다.

| 워크플로우 HTTP 노드 | n8n에서 사용할 URL |
| --- | --- |
| `oke-index.json` · 실제 색인 서비스 호출 | `http://host.docker.internal:8766/internal/oke-index` |
| `oke-search.json` · 실제 검색 서비스 호출 | `http://host.docker.internal:8765/webhook/oke-search` |

현재 `INDEX_SERVICE_URL`이 설정되지 않았으므로 **개인 n8n UI에서** 색인 HTTP 노드의 URL을 위 주소로 지정한다. `SEARCH_SERVICE_URL`도 미설정이면 검색 HTTP 노드에 위 주소를 지정한다. 컨테이너 환경변수로 제공하려면 별도 Docker 설정/재시작 승인이 필요하며 이 작업에서는 변경하지 않았다. 테스트용 UI URL 변경은 VM 배포 전에 실제 내부 서비스 URL로 되돌려야 한다.

두 HTTP Request 노드에 각각 `HTTP Header Auth` Credential을 연결한다. Header 이름은 `X-Team-Key`, 값은 터미널에서 입력한 대응 Fake 키다. `oke-search`의 **인바운드 Webhook**에도 별도의 Header Auth Credential이 필요하다. 인바운드 Credential은 Python Fake 서버의 키와 직원 IT 권한 증명이 아니다. 키를 JSON이나 실행 로그에 기록하지 않는다.

## 검증 사례

| 대상 | 입력/조작 | 기대 결과 |
| --- | --- | --- |
| 색인 | 수동 실행 | 200, `mode=mock`, 8개 합성 문서 `indexed` |
| 색인 | HTTP Credential 제거/불일치 | 401, 색인 함수 미호출 |
| 색인 | HTTP 노드에 본문 추가 | 400 `invalid_request` |
| 색인 | Fake 서버를 `--index-outcome unavailable`로 재실행 후 수동 실행 | 503 `index_unavailable` (워크플로우 결과는 안전한 일반 실패) |
| 검색 | `access_levels:["all"]`, `top_k:3`, 일반 질의 | 200, 합성 일반 근거 1개 |
| 검색 | 질의 `__fake_empty__` | 200, 빈 `evidence`, `no_evidence` |
| 검색 | 질의 `__fake_503__` | 503 `search_unavailable` |
| 검색 | HTTP Credential 제거/불일치 | 401 `unauthorized` |
| 검색 | `top_k` 오류 또는 필수값 누락 | 400 `invalid_request` |
| 검색 | `access_levels:["all","it"]` | 403 `forbidden` (신뢰 가능한 직원 권한 제공자 미연결) |

검색 Webhook 요청 예시는 `{ "request_id":"fake-1", "query":"합성 질문", "type":"test", "access_levels":["all"], "top_k":3 }`이다. n8n의 테스트 URL/운영 URL은 활성 상태에 따라 달라지므로 UI가 보여주는 주소를 사용한다. 색인 워크플로우는 수동 트리거라 인바운드 Webhook URL이 없다.

Python 로컬 HTTP 및 JavaScript 워크플로우 테스트는 Fake 응답 계약을 확인한다. n8n UI 실제 실행 결과는 사용자가 직접 확인 후 기록해야 한다. `flow.py check`는 정적 검사이며 n8n 실행 증거가 아니다.
