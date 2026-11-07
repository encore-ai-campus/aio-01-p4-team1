# DAY 82 · 최종 제출 준비 및 실서버 통합 검증 완료 요약 (2026-11-07 20:38 KST 갱신)

> 본 문서는 2026-11-07(토) 20:38 KST 기준 실서버(`https://aio-t1.isitsoft.kr`) 복구·검증 및 3인(신유빈·임다혁·이원민) 실서버 영수증 `main` 병합·루트 `runs/` 취합 결과를 반영한 최종 제출 준비 기록이다.

## 1. 목표 및 통합 달성 현황

- **목표:** `08-SUBMISSION.md` 표준 규격 정합성 100% 달성, 3인(유빈·다혁·원민) 실서버 검증 영수증 루트 `runs/` 취합, VM n8n `oke-handoff` 웹훅 복구 및 멱등성(`T-2033`) 검증, 핵심 3대 산출물(`WORKFLOW-DESIGN.md`, `RAG-ARCHITECTURE.md`, `EXECUTION-RESULT.md`) 수치 1:1 동기화.
- **현재 판정:** **실서버 통합 및 문서/영수증 정합성 완료 (Ready for Final Presentation & Submission)**.
  - `08-SUBMISSION.md` 규격 10대 루트 폴더 및 공통 14종 시나리오(`cases/common.json`) `main` 정식 안착(`8fda3f7`).
  - `.env.example` 계열 4개 파일 Git 추적 영구 제거(`9348083`) 및 GitHub Actions CI baseline 점검 Green 통과(`8cd50b5`).
  - 신유빈(`b60227f`), 임다혁(`b1e4523`), 이원민(`aa1fc02`) 실서버 검증 브랜치 `main` 무충돌 병합 및 루트 `runs/` 4대 영수증 취합 완료.
  - 실서버 VM n8n `oke-handoff` H01 웹훅 노드 유실(29노드) 진단 ➔ 정본 **30개 노드 재게시(Publish)** 완료 후 1차 호출(`T-2033`, `duplicate: false`) 및 2차 동일 `request_id` 재호출(`T-2033`, `duplicate: true`) HTTP 200 OK 실측 완료.

## 2. 역할별 마감 및 통합 현황

| 담당 | 확인된 실서버/통합 근거 | 상태 및 잔여 일정 |
|---|---|---|
| 오현님 · 통합/총괄 | `08-SUBMISSION` 규격 `main` 단일화, `.env.example` 보안 조치 및 CI 복구, VM n8n `oke-handoff` 30노드 재게시 및 `T-2033` 멱등성 복구, 핵심 3대 산출물 최종 동기화 | 일요일(11/08) 슬라이드·발표 리허설 점검 및 월요일(11/09 14:50) 최종 태그/제출 |
| 수언님 · FE/슬라이드 | FE 실서버 배포(`https://aio-t1.isitsoft.kr/login`) 및 세션/역할 가드 정상 가동, `slides/OUTLINE.md`(15장 구상) 반영 | 일요일(11/08) 12:00~18:00 실서버 UI 4종 캡처(`ui-01`~`ui-04`) 및 발표장표 최종본 마감 |
| 지혜님 · API/DB | PostgreSQL `app`/`rag` 스키마(`0005`), 티켓/알림/DLQ 멱등 저장(`T-2033`, `T-2030`, `T-2011`, `T-2005`), 컨테이너 재시작 영속성 검증 완료 | 실서버 DB 및 백엔드 안정 운영 유지 |
| 다혁님 · Support | `oke-support` v18 (63노드, N12 `0.40`) 실서버 검증 영수증([`runs/support-v18-integration-20261107.json`](../runs/support-v18-integration-20261107.json)) 및 HANDOFF 설계 근거 제출 완료 | 일요일(11/08) 12:00~18:00 20분 발표 대본 및 Q&A 방어 리허설 |
| 유빈님 · RAG | 사내 규정 8문서 33청크(`all` 7/30, `it` 1/3), `vector(3072)`, WF-05 권한 격리 실측 영수증([`runs/rag-search-eval-20261107.json`](../runs/rag-search-eval-20261107.json)) 제출 완료 | 완료 (`main` 병합 및 `RAG-ARCHITECTURE.md` 반영 완료) |
| 원민님 · QA/Handoff | 실서버 QA 진단 영수증([`runs/live-integration-qa-20261107.json`](../runs/live-integration-qa-20261107.json)), 검색 관측([`runs/vm-search-observed-20261106.json`](../runs/vm-search-observed-20261106.json)) 및 HANDOFF 제출 완료 | 완료 (`main` 병합 및 `oke-handoff` 30노드 재게시 후 `T-2033` 정상화 확인) |

## 3. 검증 수치와 DB 영수증 (최종 확정 기준)

| 항목 | 실측 확인된 값 | 근거 영수증 / 문서 |
|---|---|---|
| VM RAG 코퍼스 및 차원 | **8문서 / 33청크** (`all` 일반 7문서·30청크, `it` 전용 1문서·3청크), `text-embedding-3-large`, `vector(3072)` 전 청크 일치 | [`runs/rag-search-eval-20261107.json`](../runs/rag-search-eval-20261107.json), [`docs/RAG-ARCHITECTURE.md`](../docs/RAG-ARCHITECTURE.md) |
| 토큰 및 길이 분포 | 문서 본문 240–433자(`195–375 tokens`), 청크 13–156자(`10–163 tokens`), 임베딩 입력 26–182자(`22–192 tokens`, `cl100k_base`) | [`docs/RAG-ARCHITECTURE.md`](../docs/RAG-ARCHITECTURE.md) §1 |
| WF-05 권한 격리 실측 | 동일 보안사고 질의 시 `access_levels=["all"]`에서 `security-incident` 누출 **0건**(`wf05_leaked_it_count: 0`), `["all","it"]`에서 **2건** 정상 반환(HTTP 200) | [`runs/rag-search-eval-20261107.json`](../runs/rag-search-eval-20261107.json) |
| WF-01 / WF-02 메인 v18 실측 | `oke-support` v18 (63노드, 기준값 `0.40`): WF-01 자동 답변(`password-policy`, 4회 연속 재측정 **7.0s · 4.3s · 6.2s · 4.0s** ≤ 8s), WF-02 보완 질문 **2.01s** PASS | [`runs/support-v18-integration-20261107.json`](../runs/support-v18-integration-20261107.json) |
| WF-09 멱등성 및 핸드오프 복구 | `oke-handoff` 정본 **30노드(H01 복구)** 재게시 후 실서버 1차 호출 HTTP 200 (`T-2033`, `duplicate: false`, `alerted: true`), 2차 동일 키 재전송 HTTP 200 (`T-2033`, `duplicate: true`); `/api/ask` 경유 `T-2030` 멱등성 통과 | [`runs/live-integration-qa-20261107.json`](../runs/live-integration-qa-20261107.json), [`docs/EXECUTION-RESULT.md`](../docs/EXECUTION-RESULT.md) §15–16 |
| WF-02b / WF-03 E2E 영수증 | `T-2011`(WF-02b attempt=3 이관, 4.535s, 10 checks PASS), `T-2005`(WF-03 안전 이관 및 관리자 PATCH → 직원 재조회 일치) | `develop/wonmin/runs/real-qa-WF02b-lead-20261106T060403Z.json`, `real-qa-api-20261106T1150KST.json` |

## 4. 통합 마감 기입란 (2026-11-07 20:38 KST 확정)

| 확인 항목 | 당일 실행 결과 및 확보 증거 |
|---|---|
| 시각·확인자·고정 VM/repo/workflow 버전 | **2026-11-07 20:38 KST** · 권오현(팀장) 및 총괄 집무실(`oc:0.1`/`oc:0.2`/`w:0.2`) · `main` 통합본(`oke-support` v18 63노드, `oke-handoff` 30노드, `oke-search` 7노드, `oke-errors` 14노드) |
| 08-SUBMISSION 규격 및 `cases/common.json` | 10대 필수 규격 폴더(`backend/`, `frontend/`, `rag/`, `eval/`, `prompts/`, `slides/`, `runs/`, `requests/`, `knowledge/`, `data/`) 및 **공통 14종 시나리오(`cases/common.json`: WF-01 ~ WF-13 + WF-02b)** `main` 정식 안착(`8fda3f7`) |
| 3인(유빈·다혁·원민) 실서버 영수증 취합 | 루트 [`runs/`](../runs/)에 4대 실서버 영수증(`rag-search-eval-20261107.json`, `support-v18-integration-20261107.json`, `live-integration-qa-20261107.json`, `vm-search-observed-20261106.json`) 취합 및 [`runs/README.md`](../runs/README.md) 인덱싱 완료 |
| VM n8n 핸드오프 웹훅 복구 및 멱등성 검증 | VM `oke-handoff` H01 웹훅 노드 유실(29노드, HTTP 500) 진단 후 **30노드 정본 재게시(Publish)** 완료 ➔ 실서버 1차 `T-2033`(`duplicate: false`) 및 2차 재전송 `T-2033`(`duplicate: true`) **HTTP 200 OK** 통과 |
| 보안 감사 조치 및 CI 상태 | `.env.example` 계열 4개 파일 Git 추적 제거 및 `.gitignore`에 `*env.example*` 등록(`9348083`), `.github/workflows/ci.yml` 필수 파일 목록 정합화(`8cd50b5`)로 **GitHub Actions CI Green 통과** |
| 핵심 3대 산출물 동기화 | [`docs/RAG-ARCHITECTURE.md`](../docs/RAG-ARCHITECTURE.md), [`docs/WORKFLOW-DESIGN.md`](../docs/WORKFLOW-DESIGN.md), [`docs/EXECUTION-RESULT.md`](../docs/EXECUTION-RESULT.md)(§15 영수증 매핑, §16 6칸 표준 표 3건, §18 15항목 체크리스트 `[x]`) 최종 갱신 완료 |

## 5. 운영 및 보안 준수 원칙

- N12 코사인 기준값 `0.40`은 단독 정답 판정기가 아니며, 반드시 SQL 사전 권한 필터(`access_levels`), Writer(`answerable` 판정), Verifier(문장 단위 근거·정책 2차 검증)와 결합하여 운영한다.
- 모든 API 키, DB 비밀번호, 웹훅 인증 헤더 값은 Git 저장소·문서·영수증 JSON에 일절 기록하지 않으며, `.gitignore`의 `*env.example*` 차단 정책을 유지한다.

## 6. 참조 증거

- [`runs/README.md`](../runs/README.md): 루트 실서버 검증 영수증 4종 인덱스.
- [`docs/EXECUTION-RESULT.md`](../docs/EXECUTION-RESULT.md) §14–18: v18 로컬/실서버 실행 결과, Common 14/Team 5 표, 실서버 DB 영수증 매핑, 6칸 실패·개선 사례, KSM-REQ §6 15항목 체크리스트.
- [`docs/RAG-ARCHITECTURE.md`](../docs/RAG-ARCHITECTURE.md): 8문서 33청크 3072차원 실측, 절 단위 청킹 및 SQL 사전 필터 선정 근거, WF-05 권한 격리 검증.
- [`docs/WORKFLOW-DESIGN.md`](../docs/WORKFLOW-DESIGN.md): v18 63노드 아키텍처, 다단계 안전 파이프라인, 하위 워크플로우 타임아웃 및 `oke-handoff` 30노드 실서버 복구 명세.
