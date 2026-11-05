# 병합 소스의 Ubuntu n8n·Compose 재배포 · 2026-11-05

`feat/wonmin-p0`의 병합 기준 `3f8eb11`에서 팀 소스를 현재 로컬 Ubuntu VM에 재배포했다. 기존 사용자·로그인·Assistant 모델 설정·n8n/DB named volume을 유지했고, n8n 화면에서 5개 팀 워크플로우를 확인했다. **워크플로우 배포 완료와 직원 API·실제 저장·RAG 검색의 업무 통합 완료는 구분한다.** 공용 원격 VM/main/submission 배포가 아니다.

## n8n에서 확인할 위치

[워크플로우 목록](http://127.0.0.1:15678/home/workflows)을 새로고침하면 보인다. 총 7개 중 기존 비활성 시험 부모와 로컬 LLM probe도 보존했다. 이름이 같은 handoff는 아래 실제 ID 또는 Published 표시로 구분한다.

| 워크플로우 | 반영 원본 | 상태·직접 열기 |
| --- | --- | --- |
| oke-support | 다혁 859e3af, oke-support-13.json | [게시됨](http://127.0.0.1:15678/workflow/wmsup6dde10727e) |
| oke-search | 유빈 95ef45f, oke-search.json | [게시됨](http://127.0.0.1:15678/workflow/wmsea8d8275d1c1) |
| oke-index | 유빈 95ef45f, oke-index.json | [수동 Mock 실행용](http://127.0.0.1:15678/workflow/wmind533d9aa4ec) |
| oke-handoff | 원민 기존 P1-2 소스 | [게시됨](http://127.0.0.1:15678/workflow/wmhanecca84e267) |
| oke-errors | 원민 기존 P1-3 소스 | [게시됨](http://127.0.0.1:15678/workflow/wmerr84aab85722) |

index의 Execute workflow는 합성 자료로 동작하는 Mock 검증이다. 실제 규정 원본 색인이나 실제 임베딩·DB 저장이 아니다. [실행35](http://127.0.0.1:15678/workflow/wmind533d9aa4ec/executions/35)에서 Succeeded, mode=mock, ok=true, 최초4건/동일 재실행4건 skip을 확인했다.

## 변경 파일과 적용 방식

- `deploy/compose.lab.yaml`, `N8n.lab.Dockerfile`, `Rag.lab.Dockerfile`, `python3.lab.sh`: 기존 n8n·backend·PostgreSQL·Mock에 rag-search 서비스 추가. n8n 2.46.6과 기존 암호화 키/볼륨을 유지하고 Execute Command를 사용하는 index용 Python 3.14.10을 이미지에 추가했다. Python 라이브러리 경로는 Node.js와 분리했다. native Python Code runner를 구성한 것은 아니다. Execute Command는 이 전용 lab에서 허용하며 Local File Trigger는 제외한다.
- backend는 지혜 `4fdc313`, RAG 서비스/엔진은 유빈 `95ef45f`의 변경 없는 Git archive로 빌드/마운트했다. `psycopg[binary]`는 지혜 lock과 같은 3.3.7이다. 상대·루트·공통 파일을 수정하지 않았다.
- `tools/prepare-team-deploy.py`: 원본의 해시를 기록하고 ignored `.runtime/`에 배포 사본만 생성한다. 본체는 버전13 하나만 가져와 웹훅 충돌을 피했다. Credential·webhookId·Error workflow ID·로컬 모델명·관측 설정만 배포 사본에서 연결했다.
- support의 triage/writer/verifier 3개 모델을 `WONMIN_LOCAL_OLLAMA` Credential과 `qwen2.5-coder:latest`로 연결했다. Assistant의 별도 기존 Credential은 덮어쓰지 않았다. n8n 화면에서도 Triage model의 Credential·By ID 모델명을 확인했다.
- `tools/redeploy-team-lab.py`: private SQLite online backup과 PostgreSQL pg_dump 후 빌드→기동→migration→Credential/workflow import→4개 게시→n8n 재시작→기존 설정 보존 검증 순서로 실행했다. 백업/비밀값은 `.runtime/`에만 있고 Git에 포함하지 않았다. 볼륨 삭제나 DB 초기화를 하지 않았다.
- `tools/check-team-lab.py`, `linux-lab.py`: 실제 HTTP와 동적 workflow ID 관측. 비밀값을 보고서에 기록하지 않는다. index의 합성 실행만 저장 설정을 켜고, headers/실제 문의가 들어오는 다른 팀 workflow는 실행 데이터 저장 안 함을 유지했다.

## 확인 방법과 실제 결과

| 확인 | 결과 |
| --- | --- |
| Compose | n8n·backend·postgres·mock-store·rag-search 5개 실행, 기존 postgres healthy |
| DB migration | 실제 기존 볼륨에 0003→0004 적용, `0004 (head)` |
| 지혜 실제 PostgreSQL 시험 | **48 passed**, 기존 TestClient 경고1건 |
| 원민 로컬 회귀 | **89 passed** |
| n8n 브라우저 | 로그인 유지, 목록·support/search/index 캔버스·로컬 모델 선택·index 실행35 Succeeded 확인 |
| support/search/handoff 키 없음 | 각각 HTTP403 |
| support 잘못된 입력 | HTTP400, 계약 codes |
| support 정상 형식 | 직원 API가 없어 HTTP200 + reason=identity_unavailable·ticket=null. 접수 성공 아님 |
| search all 일반 요청 | HTTP503/search_unavailable. 임베딩·검색 DB 연결 미설정으로 실제 검색 성공 아님 |
| search all,it 위조 요청 | HTTP400, 근거 없음 |
| handoff 신규→동일 키 재호출 | HTTP200·같은 티켓 ID, duplicate=false→true. 전용 **메모리 Mock** 저장소 결과 |
| 로컬 Ollama API probe | HTTP200·OK |
| 지혜 실제 /tickets 저장 | HTTP501/not_implemented. 실제 DB 저장 성공 아님 |

원본 보고서: [재배포·PG48](../runs/team-redeploy-20261105T045828Z.json), [최종 HTTP·서비스 도달·workflow 설정·index 실행35](../runs/team-http-check-20261105T051103Z.json). 앞선 HTTP 확인 보고서도 덮어쓰지 않고 보존했다. index 첫 수동 실행은 원본의 저장 안 함 설정으로 실행 결과 조회가 제한되어, 비민감 Mock 사본에만 수동 결과 저장을 켜고 실행35로 재확인했다. 소스의 `actual_api_embedding_db_n8n=not_executed` 문자열은 Mock 함수의 고정 출력이며 실제 n8n 실행 여부는 실행35로 별도 증명한다.

추가 DB 드라이버를 반영한 빌드의 최종 점검에서 RAG 이미지 CMD가 잘려 shell 오류로 컨테이너가 종료된 것을 발견했다. Dockerfile의 현재 내용은 정상이었고, 근본 원인을 단정하지 않았다. `build --no-cache rag-search` 후 이미지 CMD 전체 문자열을 대조하고 재기동해 해결했다. 종전의 C03 503만으로는 실제 서비스 기동을 증명할 수 없으므로, 최종 보고서에는 n8n→rag-search 직접 HTTP401 도달 확인과 정확한 이미지 CMD 검증을 추가했다. 실제5개 컨테이너 실행 상태도 다시 확인했다. 향후 재배포 도구도 CMD가 불일치하면 캐시 없이 재빌드하고, 서비스 도달이 확인되지 않으면 완료로 처리하지 않는다.

## 다음 연결과 재실행

- 다혁/지혜/오현: 직원·기존 티켓 제공 data-api의 실제 URL과 키를 준비한다. lab은 `LAB_DATA_API_URL`(없으면 http://data-api:8800)과 별도 `SUPPORT_DATA_API_X_API_KEY` Credential을 사용한다. 현재 Credential은 전용 개발키이며 실제 서비스 인증 완료가 아니다. private lab.env의 `LAB_DATA_API_KEY`가 있으면 준비 도구가 사용한다.
- 지혜: 내부키·저장 API·알림 duplicate 응답·DLQ200 구현 후 app 모드 API→DB 저장과 동시/재시작 시험. 이번 DB migration/스키마 시험이 업무 저장 API 완료를 뜻하지 않는다.
- 유빈/오현: 실제 원본·권한·검색 DB 계정과 임베딩 계약을 준비한다. 현재 검색 서비스에 DB/유료 임베딩 키를 넣지 않았고 유료 호출도 하지 않았다. 고정 계약 text-embedding-3-large/3072를 로컬 임베딩으로 임의 교체하지 않았다.
- 다혁/원민: 직원 신원 연결 후 본체의 로컬 triage/writer/verifier와 C03→C04 전체 경로를 시험한다. 이번 로컬 모델 API smoke 성공이 본체 3역할 답변 품질 검증은 아니다.

아래 명령은 이미 준비된 현재 lab 전용이다. 원민 경로에서 private 파일을 준비하고 Ubuntu에서 실행한다. 새 비밀값/계정은 출력하지 않는다.

```bash
python3 develop/wonmin/tools/prepare-team-deploy.py
LAB_VM_DIR="/mnt/mac$PWD/develop/wonmin"
orb -m ubuntu -u root python3 "$LAB_VM_DIR/tools/redeploy-team-lab.py"
# n8n 화면에서 oke-index의 Execute workflow 실행 후
orb -m ubuntu -u root python3 "$LAB_VM_DIR/tools/check-team-lab.py"
```

재배포는 해당 시점의 private 백업을 추가로 남긴다. 공용 VM 반영/공식 flow.py/common·LLM3회/bench는 별도 확인 대상이다.
