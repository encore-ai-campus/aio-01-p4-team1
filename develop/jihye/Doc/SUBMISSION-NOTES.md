# 지혜님 · P1-4 통합·제출 기록

## 상태

P1-4 로컬 web-flow·PostgreSQL/backend 재시작 유지시험과 **별도 로컬 DB 백업·복원은 확인했다.** 백업·복원 원본의 RAG documents/chunks는 0건이므로 실제 문서·벡터 복원과 복원 후 권한별 검색은 미검증이다. 팀 VM·frontend·실제 RAG 원본/OpenAI·n8n 본체의 전체 연결 및 공식 평가 키트 시험은 아직 끝나지 않았다. 받은 팀원 보고는 전달 결과로 표시하고 직접 실행·검증으로 바꾸지 않는다.

## 지혜님 로컬 전용 DB 확인

작업 위치는 `develop/jihye`다. 로컬 전용 `oke-jihye-p0` Compose PostgreSQL/backend만 사용했다.

| 확인 | 명령/대상 | 결과 |
| --- | --- | --- |
| 회귀 | `uv run python deploy/check_db.py --all` | 223 passed, 2 skipped, 기존 경고 1건, 종료0 |
| web-flow | 전용 db-check 컨테이너의 `tests/integration/test_web_flow.py` | 1 passed, C02는 HTTP Mock, PostgreSQL은 실제 전용 DB |
| 재시작 유지 | `uv run python deploy/check_persistence.py --confirm-private-db` | fixture seed 1 passed → postgres/backend 재시작 및 healthy → 데이터 verify 1 passed → fixture cleanup 1 passed |
| 별도 DB 백업·복원 · 2026-11-06 | `uv run python deploy/check_backup_restore.py --confirm-private-db` | 컨테이너 내부 PostgreSQL 클라이언트 16.15로 백업·복원, revision·확장·행 수·해시/벡터 구조 비교 일치, 임시 DB·archive 정리. RAG 행 0건으로 실제 문서·벡터 복원은 미검증 |

재시작 전후 employee/inquiry/ticket/alert/DLQ와 RAG synthetic document/chunk, metadata·hash·3072차원 vector가 유지됐다. 시험 데이터는 고유 P1-4 marker로 생성 후 정리했다. 최초 전체 실행에서 phase 설정·fixture FK 정리 결함이 드러났고 보완했다. 재실행은 이전 실패가 남긴 자체 fixture로 인한 기존 빈 DB 전제 시험 실패가 있었으며, 해당 prefix만 정리 후 최종 전체 시험이 통과했다. Starlette TestClient의 HTTPX deprecation warning 1건은 남는다.

별도 백업·복원은 재시작 유지시험과 다른 실행이다. 원본 `oke_jihye_p0`의 업무 fixture를 빈 `oke_jihye_p1_4_restore`에 복원했고, 원본/복원본의 migration `0005`·PostgreSQL 16.15·pgvector 0.8.6 및 `vector(3072)` 타입이 일치했다. RAG 행이 0건이어서 문서/청크 해시와 저장 벡터 차원 비교 목록은 비어 있었다. 원본 상태 유지와 임시 복원 DB 삭제도 사후 조회했다. 상세 근거는 [IMP-PLAN의 2026-11-06 실행 기록](IMP-PLAN.md#p1-4-별도-db-백업복원-실행--2026-11-06)을 따른다. 이 문서 갱신에서 백업·복원이나 전체 회귀를 다시 실행하지 않았다.

## 병합 후 현재 VM·화면 근거 · 2026-11-06

- main `5b7d597`을 `8b18ff1`로 병합했다. 백업 기준 `1f0da49`와 병합 직후 개인 폴더 내용은 동일했다. 로컬 백업 브랜치는 `backup/jihye-before-main-1f0da49`다.
- 공통 EXECUTION-RESULT 12절은 WF-02b 직원 문의·관리자 처리·직원 재조회 API 10개 검사 통과를 보고한다. 13절은 VM repo `17007f1`, 본체 15번 게시, frontend 배포 및 n8n 직접 QA를 보고한다. 정상 자동답변 3회는 모두 이관으로 실패했고, 공식 common-14 전체·장애 WF-04/10/11·alert/DLQ 행·실제 Error Trigger 발화는 미확인이다. 직접 코드 시험이나 VM 재실행으로 집계하지 않는다.
- 사용자 대화·캡처/API 표본: 이준호/영업팀으로 VPN 문의, T-2012 접수, `route=담당자 이관`, `sources=[]`, `agents=[triage]`, `reason=low_confidence`. 사용자 화면 제출·문의/티켓 표시를 확인한 자료이며 에이전트 직접 실행은 아니다. 같은 요청의 본체 버전·검색 실행·개별 저장 ACK는 미확인이다.
- VM의 기존 RAG 8문서/33청크와 과거 실제 색인·직접 C03 검색 기록은 로컬 복원 원본 0/0과 구별한다. 실제 RAG 복원 후 검색·권한·품질 검증 완료로 간주하지 않는다. 최신 기준은 [공통 실행 결과](../../../docs/EXECUTION-RESULT.md)와 [VM 안내](../../../docs/VM-TEAM-TESTING.md)의 시점별 기록을 따른다.

## 과거 팀원에게 전달받은 결과 · 당시 보고 보존

- **원민님 보고 (Discord 전달):** `ec6a735` 병합·재배포 뒤 로컬 Ubuntu의 전용 시험 DB/직원 fixture에서 실제 n8n→FastAPI→PostgreSQL 15개 그룹 통과. 동시 8회 티켓·알림 건수, 티켓 신규201/중복200, 알림 ACK, event_key 누락/null, DLQ200, 부분 실패/재시도, PostgreSQL 재시작 데이터 유지 확인을 보고받았다. 실행 코드 commit `6896952`는 push 전이라고 전달받았다. 직접 checkout·재실행하지 않았다. 실제 data-api, 전체 C04, 팀 VM과 공통 C05 문서 반영은 남았다고 보고받았다.
- **유빈님 보고 (Discord 전달):** Python 216/217 통과(독립 DB 1 skip), PostgreSQL17/pgvector0.8.7 SQL 시험, JavaScript 3개, n8n 정적 검사 오류0·각 경고1. 임시 컨테이너 exit137로 PostgreSQL 재시작 후 유지 시험은 미확인. 실제 규정 적재·OpenAI 호출·VM 연결도 미실행이라고 보고받았다. 직접 재실행하지 않았다.

## 미완료 및 다음 연결

1. **DB 권한 근거 대조:** 사용자 제공 RAG 계정의 migration history 조회 거절은 당시 권한 관측이다. 공통 VM snapshot에는 migration `0005`가 기록돼 있어 VM revision 전체가 미확인이라는 뜻은 아니다. 역할별 권한·별도 검색 전용 로그인과 인계 상태는 승인된 관리자 자료로 대조한다. 비밀값은 제출 자료에 포함하지 않는다.
2. **실제 RAG 데이터 복원·검색:** 별도 로컬 DB 백업·복원은 위 실행 기록으로 완료했다. 호스트 PATH의 도구 부재는 컨테이너 내부 `pg_dump`·`pg_restore` 사용으로 해결했고 임시 복원 DB도 생성·검증 후 정리했다. 남은 범위는 승인된 실제 RAG documents/chunks가 있는 격리 대상에서 문서·청크 해시와 저장 벡터 복원 및 권한별 검색을 확인하는 것이다. 기존 `tests/integration/test_backup_restore.py`와 전체 pytest 회귀를 재실행한 결과로 집계하지 않는다.
3. **RAG:** VM 기존 문서·청크와 직접 검색 근거를 활용하고, 유빈님과 격리 복원 후 권한별 검색·품질/시간 및 본체 정상답변을 대조한다. 실제 문서 적재가 전혀 없었다고 기록하지 않으며 재색인은 별도 승인된 시험으로만 수행한다.
4. **전체 서비스 연결:** 확인된 사용자 화면·공통 API/DB·n8n 직접 호출을 각각 기록하고 정상 근거 답변·개별 호출 trace·alert/DLQ·장애복구의 빈 부분을 확인한다. 전체 연결 미완료를 모든 구간 미실행으로 표현하지 않는다.
5. **공식 평가:** 키트/관측 대상 준비 후 common 14 시나리오, LLM 반복 3회, 지연·품질 원자료 및 실패 2건 이상을 해당 담당자가 기록한다. 평가 키트가 현재 준비됐다는 증거는 없다.

공통 API/DB 문서 수정, 팀 VM 배포, n8n push/test는 수행하지 않았다. VM 운영·공통 문서 취합은 오현님 관리 범위다.
