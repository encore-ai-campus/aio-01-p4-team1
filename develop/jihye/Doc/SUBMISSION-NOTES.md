# 지혜님 · P1-4 통합·제출 기록

## 상태

P1-4 로컬 web-flow·PostgreSQL/backend 재시작 유지시험은 확인했다. 백업/복원, 팀 VM, frontend, 실제 RAG 원본/OpenAI, n8n 본체 전체 연결, 공식 평가 키트 시험은 아직 끝나지 않았다. 받은 팀원 보고는 전달 결과로 표시하고 직접 실행·검증으로 바꾸지 않는다.

## 지혜님 로컬 전용 DB 확인

작업 위치는 `develop/jihye`다. 로컬 전용 `oke-jihye-p0` Compose PostgreSQL/backend만 사용했다.

| 확인 | 명령/대상 | 결과 |
| --- | --- | --- |
| 회귀 | `uv run python deploy/check_db.py --all` | 223 passed, 2 skipped, 기존 경고 1건, 종료0 |
| web-flow | 전용 db-check 컨테이너의 `tests/integration/test_web_flow.py` | 1 passed, C02는 HTTP Mock, PostgreSQL은 실제 전용 DB |
| 재시작 유지 | `uv run python deploy/check_persistence.py --confirm-private-db` | fixture seed 1 passed → postgres/backend 재시작 및 healthy → 데이터 verify 1 passed → fixture cleanup 1 passed |

재시작 전후 employee/inquiry/ticket/alert/DLQ와 RAG synthetic document/chunk, metadata·hash·3072차원 vector가 유지됐다. 시험 데이터는 고유 P1-4 marker로 생성 후 정리했다. 최초 전체 실행에서 phase 설정·fixture FK 정리 결함이 드러났고 보완했다. 재실행은 이전 실패가 남긴 자체 fixture로 인한 기존 빈 DB 전제 시험 실패가 있었으며, 해당 prefix만 정리 후 최종 전체 시험이 통과했다. Starlette TestClient의 HTTPX deprecation warning 1건은 남는다.

## 팀원에게 전달받은 결과

- **원민님 보고 (Discord 전달):** `ec6a735` 병합·재배포 뒤 로컬 Ubuntu의 전용 시험 DB/직원 fixture에서 실제 n8n→FastAPI→PostgreSQL 15개 그룹 통과. 동시 8회 티켓·알림 건수, 티켓 신규201/중복200, 알림 ACK, event_key 누락/null, DLQ200, 부분 실패/재시도, PostgreSQL 재시작 데이터 유지 확인을 보고받았다. 실행 코드 commit `6896952`는 push 전이라고 전달받았다. 직접 checkout·재실행하지 않았다. 실제 data-api, 전체 C04, 팀 VM과 공통 C05 문서 반영은 남았다고 보고받았다.
- **유빈님 보고 (Discord 전달):** Python 216/217 통과(독립 DB 1 skip), PostgreSQL17/pgvector0.8.7 SQL 시험, JavaScript 3개, n8n 정적 검사 오류0·각 경고1. 임시 컨테이너 exit137로 PostgreSQL 재시작 후 유지 시험은 미확인. 실제 규정 적재·OpenAI 호출·VM 연결도 미실행이라고 보고받았다. 직접 재실행하지 않았다.

## 미완료 및 다음 연결

1. **DB 관리자 확인:** VM `0005`/pgvector 버전은 rag 계정에서 migration history 조회가 거절되어 확인 불가. `oke_rag_user`는 documents/chunks SELECT·INSERT·UPDATE·DELETE가 허용됨을 직접 확인했다. 색인 계정으로 적합한지, 검색 전용 LOGIN/SELECT 권한을 별도 제공할지와 비밀 전달 경로를 오현님과 확정한다.
2. **백업/복원:** `tests/integration/test_backup_restore.py`는 명시적 opt-in, 동일 호스트의 서로 다른 DB, `*_p1_4_restore` 빈 대상, pg_dump/pg_restore가 없으면 skip한다. 현재 호스트에 두 도구가 없고 복원용 DB도 승인/준비되지 않아 실행하지 않았다.
3. **RAG:** 유빈님이 승인된 실제 문서 적재·임베딩·검색 및 복원 뒤 권한별 검색을 VM에서 수행한다. 계정·문서 기준·OpenAI 사용 준비를 먼저 확인한다.
4. **전체 서비스 연결:** 수언 frontend→FastAPI, 다혁 본체의 C02/C03/C04, 원민 C05→app의 팀 VM 시험은 아직 미확인이다. 원민 C05 로컬 연결 보고와 팀 VM 결과를 구분한다.
5. **공식 평가:** 키트/관측 대상 준비 후 common 14 시나리오, LLM 반복 3회, 지연·품질 원자료 및 실패 2건 이상을 해당 담당자가 기록한다. 평가 키트가 현재 준비됐다는 증거는 없다.

공통 API/DB 문서 수정, 팀 VM 배포, n8n push/test는 수행하지 않았다. VM 운영·공통 문서 취합은 오현님 관리 범위다.
