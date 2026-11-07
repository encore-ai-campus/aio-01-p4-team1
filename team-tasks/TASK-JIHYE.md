# 🗄️ [박지혜 님 전용] 백엔드 & DB 통합 테스트 실행 및 핵심 설계 근거 워크시트 (`TASK-JIHYE.md`)

> ⚠️ **[절대 주의] 실서버 VM 내부 설치 · 파일 수정 · 컨테이너 재시작 절대 금지**
> - 실서버 VM(`aio-t1`)은 공용 실서비스 환경입니다.
> - **VM 내부에서 `pip install`, `npm install`, `apt`, 소스코드 직접 수정, `docker compose down/restart` 등을 절대 실행하지 마세요!** (서버가 망가질 수 있습니다)
> - 패키지 설치(`pip install websockets`)는 오직 **본인 개인 로컬 PC**에서만 수행하셔야 합니다.

- **담당**: 박지혜 님 (FastAPI 백엔드 · PostgreSQL + `pgvector` · 세션 인증 · DB 1:1 영수증)
- **마감 기한**: **오늘(11/07 토) 18:00까지**
- **제출할 파일 (오직 본인 폴더 `develop/jihye/` 내부만 수정)**:
  1. `develop/jihye/runs/be-db-integration-20261107.json` ([Step 1] 실행 시 자동 생성됨)
  2. `develop/jihye/Doc/HANDOFF.md` ([Step 2]의 빈칸 3개를 채워 맨 아래에 추가)

---

## 🖥️ [Step 1] 통합 테스트 원클릭 실행하기 (웹 브라우저 불필요 · `.env` 자동 로드)

먼저 [`team-tasks/README.md`](./README.md)의 안내대로 프로젝트 최상위 `.env` 파일에 팀장님이 개인 DM으로 보내주신 비밀번호/키를 저장해 두세요.

### 방법 A (가장 추천 ⭐): 내 AI 코딩 에이전트(Cursor / Claude Code / Codex)에게 복사해서 시키기
아래 프롬프트 박스를 복사해서 AI 에이전트 창에 그대로 붙여넣으세요!

```text
현재 저장소 루트의 .env 파일을 읽어서 team-tasks/TASK-JIHYE.md의 [Step 1] 통합 검증을 실행해 줘.
1. `python3 tools/vm_web_terminal.py run "..."` 또는 API_BASE(https://aio-t1.isitsoft.kr)를 대상으로 아래 Step 1 파이썬 스크립트를 실행해:
   - 비로그인 `/api/auth/me` 호출 시 401 확인
   - 직원 계정(EMP_USER) `/api/auth/login` 로그인 및 `oke_session` 쿠키 발급(200) 확인
   - 직원 세션으로 관리자 전용 `/api/admin/tickets` 호출 시 HTTP 403 차단(WF-06) 확인
   - 직원 세션으로 `/api/ask` 및 `/api/my-requests`(200) 호출 확인
   - 관리자 계정(ADM_USER) 로그인 후 `/api/admin/tickets`(200) 조회 확인
   - VM PostgreSQL(oke-postgres-1)에서 `app.inquiries` ↔ `app.tickets` ↔ `app.alerts` 1:1 조인 영수증 행수 확인
2. 실행 결과를 민감정보(비밀번호, 쿠키 원문) 없이 `develop/jihye/runs/be-db-integration-20261107.json`에 저장해 줘.
```

### 방법 B: 터미널에서 직접 복사-붙여넣기 실행 (Mac / Windows 공통)
```bash
python3 - <<'PY'
import os, json, time, subprocess, urllib.request, urllib.error, http.cookiejar
from pathlib import Path
import ssl; ssl._create_default_https_context = ssl._create_unverified_context

# 1) 루트 .env 자동 로드 (매번 비밀번호 입력 불필요)
for _p in (Path(".env"), Path("../.env"), Path("../../.env")):
    if _p.is_file():
        for _line in _p.read_text(encoding="utf-8").splitlines():
            if _line.strip() and not _line.lstrip().startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))

BASE = os.environ.get("API_BASE", "https://aio-t1.isitsoft.kr").rstrip("/")
EMP_U = os.environ.get("EMP_USER") or os.environ.get("OKE_EMP_USER", "user1")
EMP_P = os.environ.get("EMP_PASS") or os.environ.get("OKE_EMP_PASS", "")
ADM_U = os.environ.get("ADM_USER") or os.environ.get("OKE_ADM_USER", "admin")
ADM_P = os.environ.get("ADM_PASS") or os.environ.get("OKE_ADM_PASS", "")

def make_session():
    cj = http.cookiejar.CookieJar()
    return cj, urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def call(opener, method, path, body=None):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    try:
        with opener.open(req, timeout=25) as r:
            raw = r.read().decode("utf-8")
            return r.status, (json.loads(raw) if raw.startswith(("{", "[")) else {"raw": raw})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        return e.code, (json.loads(raw) if raw.startswith(("{", "[")) else {"raw": raw})

emp_cj, emp = make_session()
adm_cj, adm = make_session()
req_id = f"jihye-int-{int(time.time())}"

s_unauth, _    = call(emp, "GET",  "/api/auth/me")
s_emp_login, _ = call(emp, "POST", "/api/auth/login", {"login_id": EMP_U, "password": EMP_P})
s_emp_me, _    = call(emp, "GET",  "/api/auth/me")
s_wf06_403, _  = call(emp, "GET",  "/api/admin/tickets")  # WF-06 권한 차단 (403 기대)
s_ask, b_ask   = call(emp, "POST", "/api/ask", {"request_id": req_id, "question": "VPN 접속 오류가 발생합니다.", "attempt": 3})
s_myreq, _     = call(emp, "GET",  "/api/my-requests")
s_adm_login, _ = call(adm, "POST", "/api/auth/login", {"login_id": ADM_U, "password": ADM_P})
s_adm_list, _  = call(adm, "GET",  "/api/admin/tickets")

report = {
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "target_base": BASE,
    "request_id": req_id,
    "checks": {
        "unauth_me_401": s_unauth == 401,
        "employee_login_200": s_emp_login == 200,
        "employee_cookie_issued": any(c.name == "oke_session" for c in emp_cj),
        "employee_me_200": s_emp_me == 200,
        "wf06_employee_admin_403": s_wf06_403 == 403,
        "ask_http_200": s_ask == 200,
        "ask_route": b_ask.get("route") if isinstance(b_ask, dict) else None,
        "ask_ticket": b_ask.get("ticket") if isinstance(b_ask, dict) else None,
        "my_requests_200": s_myreq == 200,
        "admin_login_200": s_adm_login == 200,
        "admin_tickets_200": s_adm_list == 200,
    }
}
out = Path("develop/jihye/runs/be-db-integration-20261107.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Saved receipt:", out)
print(json.dumps(report["checks"], ensure_ascii=False, indent=2))
PY

# VM 웹 터미널(https://aio-t1.isitsoft.kr/ssh/)을 통해 DB 1:1 조인 영수증 즉시 확인
python3 tools/vm_web_terminal.py run "docker exec -e PGPASSWORD=postgres oke-postgres-1 psql -U postgres -d postgres -c '
SELECT i.id AS inquiry_id, i.route, i.ticket_id AS inq_ticket,
       t.ticket_id AS db_ticket, t.request_id, t.status AS ticket_status,
       a.id AS alert_id, a.status AS alert_status
FROM app.inquiries i
LEFT JOIN app.tickets t ON i.ticket_id = t.ticket_id
LEFT JOIN app.alerts  a ON t.ticket_id = a.ticket_id
ORDER BY i.id DESC LIMIT 10;'"
```

---

## ✍️ [Step 2] 내 생각 채우기 (엔코아 100점 채점 만점용 3대 빈칸)

아래 섹션을 복사해서 `develop/jihye/Doc/HANDOFF.md` 맨 아래에 붙여넣고, `[빈칸]` 부분을 지혜 님의 말로 채워주세요!

```markdown
## [최종 통합 제출] 박지혜 (백엔드 & 데이터베이스) 핵심 검증 및 설계 근거

### 1. [팀 시나리오 1개] 내가 직접 기획·검증한 백엔드/DB 보안·무결성 시나리오
| 항목 | 작성 내용 (`[빈칸]`을 지우고 작성해 주세요) |
| :--- | :--- |
| **시나리오 이름** | `[빈칸 예시: 일반 직원의 타인 티켓 조회/관리자 API 우회 접근 403 차단(WF-06) 및 첫 로그인 임시 비밀번호 미변경 시 보호 API 차단]` |
| **기획 의도 (왜 필요한가?)** | `[빈칸 예시: 프런트엔드 UI 가드를 우회하여 API로 직접 타인의 인사/IT 문의 내역이나 관리자 엔드포인트를 호출하는 권한 상승 공격을 서버 세션 레벨에서 원천 차단하기 위함]` |
| **입력 조건 및 테스트 방법** | `[빈칸 예시: employee 권한 세션 쿠키(oke_session)로 /api/admin/tickets 및 타인 소유 티켓 ID 조회 호출]` |
| **기대 결과 vs 실제 검증 결과** | • **기대 결과**: `HTTP 403 Forbidden 반환 및 민감 본문 미노출`<br>• **실제 결과**: `[빈칸: Step 1 실행으로 확인한 실제 HTTP 상태코드 및 DB 영수증 결과 작성]` |

### 2. [실패 및 해결 사례 6칸 표] 백엔드·DB 개발 및 통합 중 겪은 난관과 해결책 (1건)
| ① 현상 (문제점) | ② 재현 조건 | ③ 원인 및 근거 | ④ 조치 내용 (해결책) | ⑤ 재시험 결과 | ⑥ 잔여 위험 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `[빈칸 예시: 초기 내 문의 조회(/api/my-requests) 시 n8n이 생성한 티켓 상태/관리자 답변이 문의 목록과 연결되지 않거나 중복 키 충돌 발생]` | `[빈칸: 어떤 API/DB 호출 조건에서 발생했는지]` | `[빈칸: 왜 발생했는지 (예: inquiries와 tickets 간 조인 키/request_key 매핑 조건 차이 등)]` | `[빈칸: 어떻게 고쳤는지 (예: 소유자·request_key·inquiry_id 결합 조회 및 UNIQUE 제약 보정)]` | `[빈칸: 수정 후 pytest 223 passed 및 실서버 1:1 조인 영수증 일치 확인]` | `[빈칸: 대규모 트래픽 시 인덱스/세션 만료 주기 모니터링 등 1줄]` |

### 3. [아키텍처 설계 근거 (Why?)] 심사위원 질의응답 방어용 2줄
- **Q1. 백엔드 인증에서 JWT 로컬스토리지 대신 `HttpOnly` 세션 쿠키(`oke_session`) + DB 세션 검증을 선택한 이유는?**
  - **내 답변**: `[빈칸 예시: XSS 공격으로 인한 토큰 탈취를 막고, 비밀번호 변경이나 관리자 강제 초기화 시 기존 세션을 서버에서 즉시 폐기(Revoke)하기 위해 HttpOnly 세션 쿠키 방식을 채택했습니다.]`
- **Q2. `app.*`(업무 테이블)와 `rag.*`(지식 벡터 테이블) 스키마를 단일 PostgreSQL 안에서 분리 설계한 이유는?**
  - **내 답변**: `[빈칸 예시: 트랜잭션 무결성이 중요한 티켓/문의/DLQ 데이터(app)와 읽기 전용 최소 권한(SELECT)으로 격리해야 하는 벡터 검색 데이터(rag)의 권한 경계를 명확히 분리하면서 운영 복잡도를 낮추기 위함입니다.]`
```

---

## 📤 [Step 3] 내 폴더(`develop/jihye/`)만 깃허브에 제출하기

```bash
git add develop/jihye/runs/ develop/jihye/Doc/HANDOFF.md
git commit -m "docs(jihye): 백엔드·DB 통합 테스트 영수증 및 HANDOFF 핵심 설계 근거 제출"
git push origin main
```
