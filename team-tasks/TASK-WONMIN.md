# 🛡️ [이원민 님 전용] QA / 안정성 · 티켓 멱등성(`WF-09`) · DLQ 통합 테스트 워크시트 (`TASK-WONMIN.md`)

- **담당**: 이원민 님 (`oke-handoff` · `oke-errors` · `WF-09` 중복 요청 멱등성 · `WF-04`/`10`/`11` 장애 격리 및 DLQ/알림 영수증)
- **마감 기한**: **오늘(11/07 토) 18:00까지**
- **제출할 파일 (오직 본인 폴더 `develop/wonmin/` 내부만 수정)**:
  1. `develop/wonmin/runs/live-integration-qa-20261107.json` ([Step 1] 실행 시 자동 생성됨)
  2. `develop/wonmin/Doc/HANDOFF.md` ([Step 2]의 빈칸 3개를 채워 맨 아래에 추가)

---

## 🖥️ [Step 1] 통합 테스트 원클릭 실행하기 (웹 브라우저 불필요 · `.env` 자동 로드)

먼저 [`team-tasks/README.md`](./README.md)의 안내대로 프로젝트 최상위 `.env` 파일에 팀장님이 개인 DM으로 보내주신 `VM_PASSWORD`와 `TEAM_KEY`를 저장해 두세요.

### 방법 A (가장 추천 ⭐): 내 AI 코딩 에이전트(Cursor / Claude Code / Codex)에게 복사해서 시키기
아래 프롬프트 박스를 복사해서 AI 에이전트 창에 그대로 붙여넣으세요!

```text
현재 저장소 루트의 .env 파일을 읽어서 team-tasks/TASK-WONMIN.md의 [Step 1] 통합 검증을 실행해 줘.
1. N8N_BASE/webhook/oke-handoff 엔드포인트를 대상으로 동일한 `request_id`를 연속 2회 호출(WF-09 중복 요청 멱등성 테스트)해:
   - 1차 호출: 신규 티켓 발급(`duplicate: false`) 확인
   - 2차 호출(동일 request_id): 중복 응답(`duplicate: true`) 및 1차와 동일한 `ticket_id`가 반환되는지 확인
2. `python3 tools/vm_web_terminal.py run "..."`으로 VM PostgreSQL(oke-postgres-1)의 `app.tickets`, `app.alerts`, `app.dlq` 행수를 조회해 동일 request_id에 대해 티켓이 정확히 1건만 존재하는지 DB 영수증을 확인해.
3. 실행 결과를 민감정보(TEAM_KEY, 비밀번호 등) 없이 `develop/wonmin/runs/live-integration-qa-20261107.json`에 저장해 줘.
```

### 방법 B: 터미널에서 직접 복사-붙여넣기 실행 (Mac / Windows 공통)
```bash
# 1) WF-09 동일 request_id 2회 연속 호출 멱등성 검증 및 JSON 영수증 자동 저장
python3 - <<'PY'
import os, json, time, urllib.request
from pathlib import Path
import ssl; ssl._create_default_https_context = ssl._create_unverified_context

for _p in (Path(".env"), Path("../.env"), Path("../../.env")):
    if _p.is_file():
        for _line in _p.read_text(encoding="utf-8").splitlines():
            if _line.strip() and not _line.lstrip().startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))

N8N_BASE = os.environ.get("N8N_BASE", "https://aio-t1.isitsoft.kr:5678").rstrip("/")
TEAM_KEY = os.environ["TEAM_KEY"]
req_id = f"wf09-idem-{int(time.time())}"

payload = {
    "request_id": req_id,
    "requester": "이준호",
    "user_id": "emp01",
    "question": "VPN 인증서 만료로 인한 재발급 긴급 요청",
    "title": "VPN 인증서 재발급 요청",
    "summary": "VPN 인증서 만료로 인한 재발급 이관",
    "category": "network",
    "priority": "high",
    "reason": "no_evidence"
}

def send_handoff():
    req = urllib.request.Request(
        f"{N8N_BASE}/webhook/oke-handoff",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Team-Key": TEAM_KEY},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

s1, b1 = send_handoff()
s2, b2 = send_handoff()

t1 = b1.get("ticket_id") or (b1.get("ticket") or {}).get("ticket_id")
t2 = b2.get("ticket_id") or (b2.get("ticket") or {}).get("ticket_id")

report = {
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "target": N8N_BASE,
    "request_id": req_id,
    "first_call": {"http_status": s1, "body": b1},
    "second_call": {"http_status": s2, "body": b2},
    "wf09_same_ticket_id": (t1 is not None and t1 == t2),
}
out = Path("develop/wonmin/runs/live-integration-qa-20261107.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Saved receipt:", out)
print(f"WF-09 Idempotency: 1st={t1}, 2nd={t2}, same_ticket_id={report['wf09_same_ticket_id']}")
PY

# 2) VM 웹 터미널(https://aio-t1.isitsoft.kr/ssh/)로 DB 티켓/알림/DLQ 행수 및 최신 티켓 영수증 확인
python3 tools/vm_web_terminal.py run "docker exec -e PGPASSWORD=postgres oke-postgres-1 psql -U postgres -d postgres -c '
SELECT (SELECT count(*) FROM app.tickets) AS tickets,
       (SELECT count(*) FROM app.alerts)  AS alerts,
       (SELECT count(*) FROM app.dlq)     AS dlq;
SELECT ticket_id, request_id, status, priority, created_at FROM app.tickets ORDER BY id DESC LIMIT 5;'"
```

---

## ✍️ [Step 2] 내 생각 채우기 (엔코아 100점 채점 만점용 3대 빈칸)

아래 섹션을 복사해서 `develop/wonmin/Doc/HANDOFF.md` 맨 아래에 붙여넣고, `[빈칸]` 부분을 원민 님의 말로 채워주세요!

```markdown
## [최종 통합 제출] 이원민 (QA · 안정성 · 티켓/DLQ/Error) 핵심 검증 및 설계 근거

### 1. [팀 시나리오 1개] 내가 직접 기획·검증한 장애 복구/멱등성 시나리오
| 항목 | 작성 내용 (`[빈칸]`을 지우고 작성해 주세요) |
| :--- | :--- |
| **시나리오 이름** | `[빈칸 예시: 네트워크 재시도·더블클릭으로 인한 동일 request_id 중복 이관 시 단일 티켓 보장(WF-09) 및 티켓 DB 장애 시 DLQ/알림 독립 격리(WF-04)]` |
| **기획 의도 (왜 필요한가?)** | `[빈칸 예시: 사용자가 응답 지연 중 버튼을 두 번 누르거나 상위 워크플로우가 재시도할 때 동일 문의로 티켓과 알림이 중복 폭주하는 운영 사고를 막고, 티켓 저장소 장애 시에도 문의 유실 없이 DLQ에 격리하기 위함]` |
| **입력 조건 및 테스트 방법** | `[빈칸 예시: 동일한 request_id로 /webhook/oke-handoff를 2회 연속 호출하고 PostgreSQL app.tickets / app.alerts / app.dlq 행수 비교]` |
| **기대 결과 vs 실제 검증 결과** | • **기대 결과**: `1차 duplicate=false 신규 티켓 발급, 2차 duplicate=true 및 동일 ticket_id 반환, DB 티켓 +1건만 유지`<br>• **실제 결과**: `[빈칸: Step 1 실행으로 확인한 실제 ticket_id, duplicate 플래그, DB 행수 결과 작성]` |

### 2. [실패 및 해결 사례 6칸 표] 안정성·QA 개발 및 통합 중 겪은 난관과 해결책 (1건)
| ① 현상 (문제점) | ② 재현 조건 | ③ 원인 및 근거 | ④ 조치 내용 (해결책) | ⑤ 재시험 결과 | ⑥ 잔여 위험 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `[빈칸 예시: 초기 C04 이관 및 라이브 QA 호출 시 헤더 키 불일치로 403이 발생하거나, 하위 워크플로우(oke-handoff/oke-errors)의 saveDataSuccessExecution='none' 설정으로 실행 이력 추적(Execution ID)이 누락됨]` | `[빈칸: 언제 발생했는지]` | `[빈칸: 왜 발생했는지 (예: 테스트 하네스 키와 VM 웹훅 Credential 차이 및 n8n 기본 로깅 설정 누락)]` | `[빈칸: 어떻게 고쳤는지 (예: 전 워크플로우 실행 로깅 'all' 활성화 af82c3b, 부모 워크플로우 통제된 Error Hook 9bdb9c6 연결 및 멱등 키 검증)]` | `[빈칸: 수정 후 WF-09 동일 ticket_id(T-2030 등) 유지 및 DB 1:1 영수증 일치 확인]` | `[빈칸: DLQ 적재 건 재처리(Replay) 배치 운영 절차 고도화 등 1줄]` |

### 3. [아키텍처 설계 근거 (Why?)] 심사위원 질의응답 방어용 2줄
- **Q1. 티켓 생성 실패(`tickets_down`) 시 에러를 그대로 던지지 않고 `oke-handoff` 내부에서 알림(`alerts`)과 실패 격리 큐(`dlq`)를 독립 분기로 시도하는 이유는?**
  - **내 답변**: `[빈칸 예시: 티켓 DB가 일시 중단되더라도 고객 문의 원문(마스킹 요약)을 잃어버리지 않고 DLQ에 보존하여 사후 복구(Replay)할 수 있게 하고, 하나의 수습 Sink가 실패해도 다른 Sink(운영자 알림)는 끝까지 실행되도록 Fail-Safe 격리 구조를 설계했습니다.]`
- **Q2. 예상된 비즈니스 장애(`WF-04` 티켓 장애 등)와 예상 밖 런타임 예외(`oke-errors` Error Trigger)를 이원화하여 처리한 이유는?**
  - **내 답변**: `[빈칸 예시: 하위 API 503/타임아웃처럼 예측 가능한 장애는 워크플로우 내 정상 제어 흐름(HTTP 200 안전 안내 + DLQ 적재)으로 수습하고, 노드 크래시 같은 비예측 예외만 Error Workflow(oke-errors)가 포착하도록 분리해 무한 재귀 호출 없이 100% 관측성을 확보했습니다.]`
```

---

## 📤 [Step 3] 내 폴더(`develop/wonmin/`)만 깃허브에 제출하기

```bash
git add develop/wonmin/runs/ develop/wonmin/Doc/HANDOFF.md
git commit -m "docs(wonmin): QA 멱등성·장애격리 통합 영수증 및 HANDOFF 핵심 설계 근거 제출"
git push origin main
```
