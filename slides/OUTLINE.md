# 오케퐁(OKE-Pong) 최종 발표 슬라이드 개요 (15장 · 20분 구성)

- **기준 문서:** `docs/TOPIC.md`, `docs/TEAM-CHARTER.md`, `docs/WORKFLOW-DESIGN.md`, `docs/RAG-ARCHITECTURE.md`, `docs/EXECUTION-RESULT.md`
- **발표 시간 배분 (20분 발표 + 5분 질의응답):**
  1. 업무 시나리오 · 범위 · 팀 역할 (3분, Slide 1~3)
  2. 워크플로우 설계 · 에이전트 역할 · 분기 · 루프 · 페이로드 계약 (5분, Slide 4~7)
  3. RAG 아키텍처 · 청킹 실험 · 임베딩 · 사전 권한 필터 · 재색인 (4분, Slide 8~10)
  4. 팀 VM 라이브 시연 (5분, Slide 11~12)
  5. 실행 결과 측정치 · 실패 및 개선 사례 · 잔여 위험 및 회고 (3분, Slide 13~15)

---

## 슬라이드 15장 목차

| 번호 | 슬라이드 제목 | 핵심 내용 및 시각 자료 | 대응 산출물 |
| :---: | :--- | :--- | :--- |
| **Slide 1** | 표지 · 오케퐁(OKE-Pong) 사내 IT 헬프데스크 자동화 | 프로젝트명, 1팀 6인 역할 요약, 아키텍처 핵심 키워드 | `docs/TEAM-CHARTER.md` |
| **Slide 2** | 문제 정의 · 사내 IT 지원 병목과 해결 목표 | 반복 문의·근거 없는 답변·권한 노출 문제 정의 및 해결 목표 | `docs/TOPIC.md` §1 |
| **Slide 3** | 처리 범위(6대 유형) · 5대 라우트 결정 계약 · 팀 역할 분담 | 자동 답변 / 보완 질문 / 담당자 이관 / 권한 없음 / 차단 경계 및 6인 R&R | `docs/WORKFLOW-DESIGN.md` §1 |
| **Slide 4** | 전체 시스템 및 5대 워크플로우 아키텍처 | FastAPI · Next.js · n8n 5종(`oke-support/search/index/handoff/errors`) · PostgreSQL/pgvector 구조도 | `docs/ARCHITECTURE.md` |
| **Slide 5** | 메인 워크플로우(`oke-support` v18) 상세 흐름도 | 결정론적 게이트(입력/보안/재전송/접수조회) → Triage → FAQ 2노드 → RAG → Writer → Verifier | `docs/WORKFLOW-DESIGN.md` §2~3 |
| **Slide 6** | 상태·분기·보완 질문 루프(`attempt` 1~3) 및 장애 격리 | `attempt >= 3` 자동 이관 루프(`T-2035`), 하위 호출 실패 시 `tickets_down`/`llm_down` 안전 폴백 | `docs/WORKFLOW-DESIGN.md` §4~5 |
| **Slide 7** | 워크플로우 간 페이로드 계약 및 에러 워크플로우(`oke-errors`) | `oke-support` ↔ `oke-search`/`oke-handoff`/`oke-errors` 표준 JSON 스키마, 3대 워크플로우 `settings.errorWorkflow = "okeErrorsFlow01"` 영구 바인딩(`0b848e7`) 및 DLQ/알림 처리 | `docs/WORKFLOW-DESIGN.md` §1, §6 |
| **Slide 8** | RAG 데이터 파이프라인 및 3종 청킹 전략 비교 실험 | 사내 규정 8문서 33청크(`all` 7문서/30청크, `it` 1문서/3청크), `section_split` 절 단위 청킹 채택 정량 근거 | `docs/RAG-ARCHITECTURE.md` §1~2 |
| **Slide 9** | 3072차원 임베딩 · 하이브리드 검색 · 0.40 임계값 산정 근거 | `text-embedding-3-large`(3072d), 범위 내(0.380~0.709, 중앙값 0.571) vs 범위 밖 상단(0.383) 실측 분포 및 N12 `0.40` 보정 | `docs/RAG-ARCHITECTURE.md` §3~4 |
| **Slide 10** | 검색 전 RBAC 권한 필터(`access_level`) 및 멱등 재색인(`oke-index`) | SQL `WHERE access_level = ANY(...)` 사전 차단(WF-05 일반 범위 누출 0건 vs IT 범위 2건) 및 해시 기반 재색인 | `docs/RAG-ARCHITECTURE.md` §5~6 |
| **Slide 11** | 웹 서비스 화면 구성 및 컨테이너·런타임 보안 방어벽 | 실서버 UI 캡처 4종(`ui-01-login` ~ `ui-04-admin-tickets`), `HttpOnly` 세션/RBAC(`401/200/403/200`), FE 컨테이너 `init=true`·`pids_limit=100`·`tmpfs(noexec,nosuid)`(`EACCES`) 및 Next 15.5.29 / React 19.1.10 / sharp 0.35.5 / PostCSS 8.5.32 취약점 0건(`e09d3f9`, `d23642f`, `15ab6c9`) | `docs/PREVIEW.md` / `images/` |
| **Slide 12** | 팀 VM 라이브 시연 시나리오 (7단계 E2E 데모 순서) | 정상 자동답변(`password-policy#4`, 6.9s·4.8s·3.8s) → 보완질문(1.812s) → 보완한도 이관(`T-2035`, 2.188s) → 무근거 이관(`T-2036`, 3.004s) → 권한제한(WF-05) → 관리자 티켓 처리 | `docs/EXECUTION-RESULT.md` §14~15 |
| **Slide 13** | 실행 결과 요약 · 실서버 영수증 7종 및 처리시간(SLA 8초 PASS) | WF-01 실서버 3회 연속 6.9s·4.8s·3.8s(콜드스타트 제외 전원 8초 이내 PASS), WF-02b `T-2035`·WF-03 `T-2036` PASS, WF-09 멱등성 `T-2034` 7/7 PASS(2.257s `duplicate=false` → 0.594s `duplicate=true`, 중복 0건) 및 스모크 `T-2033` | `docs/EXECUTION-RESULT.md` §14~15 |
| **Slide 14** | 핵심 4대 실패 · 개선 사례 표준 표 (원인 → 조치 → 동일 조건 재시험) | `docs/EXECUTION-RESULT.md` §16 6칸 표준 표 4건 전원 해결: ① N12 코사인 임계값 `0.40` 보정, ② PostgreSQL `+psycopg` DSN 스키마 복구, ③ VM `oke-handoff` 29→30노드(H01 웹훅) 복구 후 `T-2033`~`T-2036` 발급 성공, ④ 웹 터미널 DB 읽기 전용 트랜잭션 오류 해결(`app.inquiries` `status="completed"` 검증) | `docs/EXECUTION-RESULT.md` §16 |
| **Slide 15** | 한계점 · 잔여 위험 · 100배 확장 설계 및 Q&A | 100배 용량 산술 추정(800문서/3,300청크/38.67MiB), 11/8 00:04 KST 실서버 12개 보안·안정화 검증 완결, KSM-REQ §6 15항목 체크리스트 및 질의응답 | `docs/EXECUTION-RESULT.md` §17~18 |
