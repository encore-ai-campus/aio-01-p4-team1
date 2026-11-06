# Ubuntu Compose·로컬 모델·실제 Error Trigger 결과 · 2026-11-05

로컬 Ubuntu VM에 로그인해 Docker Compose로 n8n·지혜님 backend·PostgreSQL·전용 Mock을 실행했다. n8n의 실제 부모 Error workflow 설정과 자동 오류 발화, 독립 알림/DLQ 수습을 확인했다. Ollama 로컬 모델도 실제 호출했다. **지혜님 저장 API는 HTTP 501이므로 실제 API→DB 저장 성공으로 처리하지 않는다.** 팀 공용 원격 서버 배포 결과가 아니다.

## 환경과 변경 파일

- OrbStack의 기존 Ubuntu 26.04.1 LTS arm64 VM, Docker 29.1.3, Compose 2.40.3, n8n 2.46.6. `orb -m ubuntu`로 로그인/실행했다. 기존 SSH 별칭은 연결되지 않아 공용 서버 SSH 로그인 완료로 기록하지 않는다.
- `deploy/compose.lab.yaml`: 전용 프로젝트 `wonmin-p13-lab`, n8n·backend·PostgreSQL/pgvector·Mock 4개 서비스. DB와 n8n은 named volume을 유지한다. 호스트 포트는 loopback에 한정했다. `compose.lab.app.yaml`은 실제 backend 연결 시험용이다.
- `deploy/Backend.lab.Dockerfile`, `tools/prepare-linux-lab.py`: 지혜님 `c6e42df05737d4b36b0904ca5ae07cae8dd8b2a3`의 변경 없는 실행용 snapshot과 잠금 의존성으로 빌드했다. 원민의 ignored `.runtime/`에서만 실행 준비했고 상대 소스나 루트는 수정하지 않았다.
- `tools/materialize-n8n-lab.py`, `linux-lab.py`, `linux-errors-matrix.py`, `verify-linux-restoration.py`: 전용 배포 사본 생성, CLI import/publish, 실제 HTTP 발화, 안전한 실행 메타데이터 관측과 복구 확인. 공식 80일차 flow.py 대체 도구가 아니다.
- `workflows/oke-handoff.json`, `tests/handoff.test.mjs`: 누락된 webhookId와 회귀 검증을 추가했다. 실제 n8n에서 계약 경로 `/webhook/oke-handoff`가 등록됨을 확인했다.
- 비밀값은 `.runtime/lab.env`와 private Credential import 파일에만 두며 Git에서 제외했다. 값은 보고서에 출력하지 않았다.

## 실제 ID 연결과 자동 발화

| 용도 | 실제 workflow ID | 최종 상태 |
| --- | --- | --- |
| oke-errors | wmerr84aab85722 | 게시됨 |
| 일반 oke-handoff | wmhanecca84e267 | 게시됨, errorWorkflow=wmerr84aab85722 |
| 비민감 오류 시험 부모 | wmfai82080ebab7 | 인증/정상 코드 복원 후 게시 해제 |
| 로컬 Ollama API probe | wmllm12c4cbcae0 | 게시됨, errors 연결 |

시험 부모의 production webhook을 HTTP로 호출해 H03에서 의도한 오류를 발생시켰다. 수동 Execute나 합성 Error Trigger item 주입 결과가 아니다. 부모 HTTP 500·error 상태를 유지하면서 아래 handler는 `mode=error`로 자동 실행됐다. 각 사례에서 handler 1회, 티켓 호출 0회, 알림/DLQ 각각 1회였다.

| 저장 대상·조건 | 부모→errors 실행 ID | alerted / dlq | 수습 결과 |
| --- | --- | --- | --- |
| 전용 Mock 정상 | 10 → 11 | true / true | success |
| 전용 Mock alerts 503 | 12 → 13 | false / true | partial_failure |
| 전용 Mock DLQ 503 | 14 → 15 | true / false | partial_failure |
| 전용 Mock 둘 다 503 | 16 → 17 | false / false | failed, 재귀 없이 종료 |
| 지혜님 실제 backend | 18 → 19 | false / false | API 미구현으로 failed, 저장 성공 아님 |

handler 실행 자체의 n8n status=success는 오류를 다시 던지지 않고 종료했다는 뜻이다. 저장 성공 여부는 Outcome의 alerted/dlq로 별도 판정했다. request_id는 null이고 execution_ref는 실제 부모 ID다. 원문 메시지·stack·headers는 공유 보고서/DLQ로 복사하지 않았다.

근거: [실제 오류 매트릭스](../runs/ubuntu-errors-matrix.json). 이 실행은 복구 직후 인증 점검에서 일시적 HTTP 500으로 중단되어 `runtime_restored=false`를 보존했다. 이후 같은 인증 요청의 403·정상 요청의 200을 확인했고, 별도 [최종 복구 보고서](../runs/ubuntu-final-restoration.json)에서 게시 해제·404와 일반 경로 인증/정상 응답까지 확인했다. 앞선 실패 보고서를 PASS로 덮어쓰지 않았다.

## 로컬 모델 API

n8n 컨테이너에서 호스트 Ollama의 `/api/chat`으로 연결했다. 이미 설치된 `qwen2.5-coder:latest`(7.6B Q4_K_M)를 사용했고 모델 다운로드나 외부 유료 API 호출은 하지 않았다. Compose의 `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`로 연결한다. 현재 Mac에서 `http://127.0.0.1:15678`의 n8n health 응답도 확인했다.

실제 시험 경로는 `POST http://127.0.0.1:15678/webhook/wonmin-local-llm`이며 고정 비민감 prompt를 전송한다. 결과는 HTTP 200, `{"ok":true,"model":"qwen2.5-coder:latest","content":"OK","done":true}`였다. **로컬 모델 API 연결 smoke 시험이며 다혁님 본체의 업무 LLM 호출·RAG 답변 품질·독립 3회 검증은 아니다.** 지혜님 backend에는 해당 업무 구현을 대신 추가하지 않았다.

## backend·실제 PostgreSQL

| 항목 | 실제 결과 | 의미 |
| --- | --- | --- |
| GET /health/live | 200 | 프로세스 liveness |
| GET /health/ready | 404 | 해당 revision에는 미구현. DB readiness 성공으로 표시하지 않음 |
| POST /tickets·/alerts·/dlq | 각각 501 not_implemented | 실제 API/인증/저장 성공 미확인 |
| Alembic upgrade head | 0002 적용 성공 | 실제 PostgreSQL에 스키마 생성 |
| backend tests/integration | **45 passed**, 경고 1건 | PostgreSQL 연결·migration·스키마/제약조건/rollback 등 |
| 원민 Node 회귀 | **89 passed** | [handoff·수습·errors 로컬 회귀 출력](../runs/ubuntu-node-regression.txt) |

45개는 실제 PostgreSQL을 연결한 지혜님 테스트다. HTTP 저장·알림 duplicate 응답·같은 키 API 순차/동시 요청·티켓 저장 후 알림 실패 보존까지 검증한 것은 아니다. 경고는 Starlette TestClient의 httpx 폐기 예정 안내다.

## 발견·수정·복구

1. webhookId가 없으면 n8n이 workflow/노드가 포함된 fallback 경로를 등록했다. 원본 handoff에 ID를 추가하고 재가져오기/게시/재시작 후 계약 경로 HTTP 200을 확인했다.
2. 이 설치본 n8n 2.46.6은 inactive errors를 실행할 수 없다고 거절했다. errors를 게시한 뒤 실제 자동 발화가 성공했다. 기존 문서의 일반적인 게시 불필수 설명보다 **설치본 실측을 우선**한다. 다른 환경에서는 해당 버전에서 확인한다.
3. Ollama 요청의 인접 닫는 중괄호가 n8n expression 파싱을 깨뜨렸다. 표현식을 수정하고 실제 모델 HTTP 200을 확인했다.
4. CLI publish 후 실행 중 프로세스에 반영하려면 재시작이 필요했다. `/healthz` 200 직후에도 인증 초기화가 끝나기 전 500이 발생해 제한된 준비 대기를 추가했다.
5. 최종 상태는 practice→전용 정상 Mock, 일반 handoff 인증 없음 403·인증 있음 200, 시험 부모 비활성/404, 의도한 throw 제거다. private import bundle도 정상 부모로 교체했다. 실제 DB/n8n 볼륨을 삭제하지 않았다. errors 실행 데이터 저장은 비민감 시험의 관측을 위해 전용 lab 사본에서만 켰으며 일반 원본은 저장 안 함 설정을 유지한다.

초기 실패 근거도 보존했다: [첫 실행](../runs/ubuntu-actual-first.json), [재시작 후](../runs/ubuntu-actual-after-restart.json), [웹훅 수정 후](../runs/ubuntu-actual-fixed-webhook.json), [errors 게시 후](../runs/ubuntu-actual-errors-published.json).

## 재현과 다음 연결

저장소 루트에서 아래 변수로 실행 위치를 지정한다. 서비스는 현재 실행 중이며 재준비는 필요할 때만 한다. private 파일은 공유하지 않는다.

```bash
LAB_HOST_DIR="$PWD/develop/wonmin"
LAB_VM_DIR="/mnt/mac${LAB_HOST_DIR}"
orb -m ubuntu -u root docker compose --env-file "$LAB_VM_DIR/.runtime/lab.env" -f "$LAB_VM_DIR/deploy/compose.lab.yaml" ps
orb -m ubuntu -u root docker compose --env-file "$LAB_VM_DIR/.runtime/lab.env" -f "$LAB_VM_DIR/deploy/compose.lab.yaml" exec -T -e OKE_RUN_DB_TESTS=1 backend uv run pytest -q tests/integration
node --test develop/wonmin/tests/*.test.mjs
```

초기 구성은 prepare-linux-lab.py → materialize-n8n-lab.py → compose up/build → backend Alembic upgrade → n8n CLI Credential/workflow import 순서다. 오류 매트릭스를 다시 실행하려면 전용 lab에서 시험 사본을 다시 생성/import하고 `linux-lab.py --output <새파일명.json>`으로 게시/발화한 다음 `linux-errors-matrix.py --output <새파일명.json>`을 실행한다. 실패하더라도 시험 부모를 unpublish하고 상태를 확인한다. 일반적인 서비스 기동에 오류 주입을 포함하지 않는다. `verify-linux-restoration.py`는 최종 보고서 파일이 이미 있으면 덮어쓰지 않는다.

- **지혜님:** 저장/내부 인증 구현과 alert duplicate 필드, DLQ HTTP 200 반영 후 동일 요청으로 API→DB 재시험. 순차/동시 같은 키·키 없음/null·티켓 보존·재시작 영속성은 실제 구현 후 확인한다.
- **다혁님:** 본인 C04 실제 HTTP 발신 및 업무 LLM을 로컬 모델에 연결하고 본체→handoff→errors를 함께 확인한다. 이번에 상대 workflow는 수정하지 않았다.
- **오현님/원민:** 공식 flow.py/common 원본 확보 후 공통14종·팀 사례·LLM3회·bench·공용 VM 회귀 진행. 지금의 로컬 Ubuntu lab 성공을 공용 VM 검증이나 전체 업무 통합 완료로 대체하지 않는다.
