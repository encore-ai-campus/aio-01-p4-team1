# ⚙️ [임다혁 님 전용] 오케스트레이션(`oke-support` v18) 통합 테스트 실행 및 핵심 설계 근거 워크시트 (`TASK-DAHYEOK.md`)

- **담당**: 임다혁 님 (메인 워크플로우 `oke-support` v18 · Triage 게이트 · FAQ 2노드 · Verifier/Writer · 이관 분기)
- **마감 기한**: **오늘(11/07 토) 18:00까지**
- **제출할 파일 (오직 본인 폴더 `develop/dahyeok/` 내부만 수정)**:
  1. `develop/dahyeok/runs/support-v18-integration-20261107.json` ([Step 1] 실행 시 자동 생성됨)
  2. `develop/dahyeok/Doc/HANDOFF.md` ([Step 2]의 빈칸 3개를 채워 맨 아래에 추가)

---

## 🖥️ [Step 1] 통합 테스트 원클릭 실행하기 (웹 브라우저 불필요 · `.env` 자동 로드)

먼저 [`team-tasks/README.md`](./README.md)의 안내대로 프로젝트 최상위 `.env` 파일에 팀장님이 개인 DM으로 보내주신 `VM_PASSWORD`와 `TEAM_KEY`를 저장해 두세요.

### 방법 A (가장 추천 ⭐): 내 AI 코딩 에이전트(Cursor / Claude Code / Codex)에게 복사해서 시키기
아래 프롬프트 박스를 복사해서 AI 에이전트 창에 그대로 붙여넣으세요!

```text
현재 저장소 루트의 .env 파일을 읽어서 team-tasks/TASK-DAHYEOK.md의 [Step 1] 통합 검증을 실행해 줘.
1. `tools/vm_web_terminal.py`를 통해 공식 웹 터미널(https://aio-t1.isitsoft.kr/ssh/)로 VM 내부의 `http://localhost:5678/webhook/oke-support` 엔드포인트를 호출하여 아래 4대 핵심 분기 시나리오를 실측해:
   - WF-01 (정상 자동답변, attempt=1): 규정 내 질문 호출 시 route, sources, 경과시간 확인
   - WF-02 (보완질문 루프, attempt=1): 모호한 질문 입력 시 티켓 미생성 및 clarify/보완질문 반환 확인
   - WF-02b (보완질문 한도 초과 이관, attempt=3): 3회 도달 시 즉시 담당자 이관 및 티켓(T-xxxx) 발급 확인
   - WF-03 (무근거 즉시 이관, attempt=1): 사내 규정에 없는 질문 입력 시 억지 답변 없이 즉시 이관 및 티켓 발급 확인
2. 실행 결과를 민감정보(TEAM_KEY 등) 없이 `develop/dahyeok/runs/support-v18-integration-20261107.json`에 저장해 줘.
```

### 방법 B: 터미널에서 직접 복사-붙여넣기 실행 (Mac / Windows 공통)
```bash
# 1) tools/vm_web_terminal.py를 통해 VM 내부 localhost:5678/webhook/oke-support 4대 경로 실행
python3 - <<'PY'
import os, json, time, urllib.request
from pathlib import Path

for _p in (Path(".env"), Path("../.env"), Path("../../.env")):
    if _p.is_file():
        for _line in _p.read_text(encoding="utf-8").splitlines():
            if _line.strip() and not _line.lstrip().startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))

N8N_BASE = os.environ.get("N8N_BASE", "https://aio-t1.isitsoft.kr:5678").rstrip("/")
TEAM_KEY = os.environ["TEAM_KEY"]
ts = int(time.time())

cases = [
    {"case_id": "WF-01",  "expect_route": ["자동 답변", "answer"],  "payload": {"request_id": f"v18-wf01-{ts}",  "user": "이준호", "question": "비밀번호 최소 길이와 변경 주기 규정이 어떻게 되나요?", "channel": "web", "attempt": 1}},
    {"case_id": "WF-02",  "expect_route": ["보완 질문", "clarify"], "payload": {"request_id": f"v18-wf02-{ts}",  "user": "이준호", "question": "로그인이 안 돼요 도와주세요", "channel": "web", "attempt": 1}},
    {"case_id": "WF-02b", "expect_route": ["담당자 이관", "handoff"], "payload": {"request_id": f"v18-wf02b-{ts}", "user": "이준호", "question": "로그인이 안 돼요 도와주세요", "channel": "web", "attempt": 3}},
    {"case_id": "WF-03",  "expect_route": ["담당자 이관", "handoff"], "payload": {"request_id": f"v18-wf03-{ts}",  "user": "이준호", "question": "사내 골프장 회원권 대여 규정이 어떻게 되나요?", "channel": "web", "attempt": 1}},
]

results = []
for c in cases:
    req = urllib.request.Request(
        f"{N8N_BASE}/webhook/oke-support",
        data=json.dumps(c["payload"], ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Team-Key": TEAM_KEY},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    elapsed = round(time.time() - t0, 3)
    route = body.get("route")
    results.append({
        "case_id": c["case_id"],
        "request_id": c["payload"]["request_id"],
        "http_status": resp.status,
        "elapsed_sec": elapsed,
        "route": route,
        "expected_route": c["expect_route"],
        "matched": route in c["expect_route"],
        "sources_count": len(body.get("sources") or []),
        "sources": body.get("sources") or [],
        "ticket": body.get("ticket"),
        "reason": body.get("reason"),
    })
    print(f"[{c['case_id']}] {elapsed}s | route={route} | sources={len(body.get('sources') or [])} | ticket={body.get('ticket')}")

out = Path("develop/dahyeok/runs/support-v18-integration-20261107.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "target": N8N_BASE, "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Saved receipt:", out)
PY

# 2) VM 웹 터미널(https://aio-t1.isitsoft.kr/ssh/)로 n8n 최근 실행 로그 확인
python3 tools/vm_web_terminal.py run "docker logs oke-n8n-1 --tail 25"
```

---

## ✍️ [Step 2] 내 생각 채우기 (엔코아 100점 채점 만점용 3대 빈칸)

아래 섹션을 복사해서 `develop/dahyeok/Doc/HANDOFF.md` 맨 아래에 붙여넣고, `[빈칸]` 부분을 다혁 님의 말로 채워주세요!

```markdown
## [최종 통합 제출] 임다혁 (오케스트레이션 · 메인 워크플로우 v18) 핵심 검증 및 설계 근거

### 1. [팀 시나리오 1개] 내가 직접 기획·검증한 오케스트레이션 분기 시나리오
| 항목 | 작성 내용 (`[빈칸]`을 지우고 작성해 주세요) |
| :--- | :--- |
| **시나리오 이름** | `[빈칸 예시: 모호한 질문 반복 시 무한 루프 방지를 위한 attempt >= 3 한도 도달 자동 이관(WF-02b) 및 Verifier 환각 차단 게이트]` |
| **기획 의도 (왜 필요한가?)** | `[빈칸 예시: 사용자가 맥락 없는 짧은 질문을 반복할 때 챗봇이 끝없이 되묻기만 하는 무한 루프를 막고, 3회차에는 즉시 담당자 티켓(T-xxxx)으로 안전 이관하기 위함]` |
| **입력 조건 및 테스트 방법** | `[빈칸 예시: 동일 모호 질문("로그인이 안 돼요")을 attempt=1~2와 attempt=3으로 각각 호출하여 분기 전환 비교]` |
| **기대 결과 vs 실제 검증 결과** | • **기대 결과**: `attempt 1~2는 보완 질문(티켓 미생성), attempt 3은 즉시 담당자 이관 및 티켓 발급`<br>• **실제 결과**: `[빈칸: Step 1 실행으로 확인한 실제 route, 티켓 번호, 응답 시간 기록]` |

### 2. [실패 및 해결 사례 6칸 표] 메인 워크플로우 개발·통합 중 겪은 난관과 해결책 (1건)
| ① 현상 (문제점) | ② 재현 조건 | ③ 원인 및 근거 | ④ 조치 내용 (해결책) | ⑤ 재시험 결과 | ⑥ 잔여 위험 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `[빈칸 예시: 초기 버전(v14~v15)에서 APPROVED_MIN_SCORE=0.80 설정 및 다단계 FAQ 노드로 인해 정상 규정 질문(WF-01)까지 전부 low_confidence로 이관되거나 지연시간 초과 발생]` | `[빈칸: 어떤 질문/점수 분포에서 발생했는지]` | `[빈칸: 실제 C03 pgvector 코사인 유사도 실측치(0.380~0.709)와 초기 임계값(0.80) 간 괴리 및 불필요한 HTTP 왕복]` | `[빈칸: v18에서 임계값을 0.40으로 실측 기반 보정하고 data-api FAQ 보조 조회를 5노드 -> 2노드로 경량화]` | `[빈칸: 수정 후 WF-01 자동답변 통과율 및 응답시간 개선 수치 작성]` | `[빈칸: 경계 영역(0.38~0.40) 질문에 대한 Verifier 2차 검증 유지 등 1줄]` |

### 3. [아키텍처 설계 근거 (Why?)] 심사위원 질의응답 방어용 2줄
- **Q1. 단일 거대 프롬프트(Monolithic LLM) 대신 `Triage ➔ Search(C03) ➔ Writer ➔ Verifier ➔ Handoff(C04)` 다단계 파이프라인으로 분리한 이유는?**
  - **내 답변**: `[빈칸 예시: 입력 검증·프롬프트 주입 차단(Triage)과 실제 규정 근거 기반 작성(Writer), 그리고 허용된 출처만 인용했는지 검증하는 환각 차단(Verifier)의 책임을 분리해 무근거 답변(Hallucination)을 0건으로 통제하기 위함입니다.]`
- **Q2. `oke-support` 본체에서 검색(`oke-search`)과 이관(`oke-handoff`), 에러(`oke-errors`)를 하위 워크플로우로 분리한 이유는?**
  - **내 답변**: `[빈칸 예시: 팀원 간 동시 개발 시 단일 JSON 충돌을 방지하고, 검색(4초)과 티켓 이관(5초)의 타임아웃 예산 및 장애 격리(DLQ)를 독립적으로 제어하기 위해 모듈형 아키텍처를 채택했습니다.]`
```

---

## 📤 [Step 3] 내 폴더(`develop/dahyeok/`)만 깃허브에 제출하기

```bash
git add develop/dahyeok/runs/ develop/dahyeok/Doc/HANDOFF.md
git commit -m "docs(dahyeok): 메인 워크플로우 v18 통합 영수증 및 HANDOFF 핵심 설계 근거 제출"
git push origin main
```
