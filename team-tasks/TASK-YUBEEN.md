# 🔍 [신유빈 님 전용] RAG / `pgvector` 통합 테스트 실행 및 핵심 설계 근거 워크시트 (`TASK-YUBEEN.md`)

- **담당**: 신유빈 님 (`oke-index` · `oke-search` · 사내 규정 8문서/33청크 · `vector(3072)` · `WF-05` 권한 사전 필터링)
- **마감 기한**: **오늘(11/07 토) 18:00까지**
- **제출할 파일 (오직 본인 폴더 `develop/yubeen/` 내부만 수정)**:
  1. `develop/yubeen/runs/rag-search-eval-20261107.json` ([Step 1] 실행 시 자동 생성됨)
  2. `develop/yubeen/Doc/HANDOFF.md` ([Step 2]의 빈칸 3개를 채워 맨 아래에 추가)

---

## 🖥️ [Step 1] 통합 테스트 원클릭 실행하기 (웹 브라우저 불필요 · `.env` 자동 로드)

먼저 [`team-tasks/README.md`](./README.md)의 안내대로 프로젝트 최상위 `.env` 파일에 팀장님이 개인 DM으로 보내주신 `VM_PASSWORD`와 `TEAM_KEY`를 저장해 두세요.

### 방법 A (가장 추천 ⭐): 내 AI 코딩 에이전트(Cursor / Claude Code / Codex)에게 복사해서 시키기
아래 프롬프트 박스를 복사해서 AI 에이전트 창에 그대로 붙여넣으세요!

```text
현재 저장소 루트의 .env 파일을 읽어서 team-tasks/TASK-YUBEEN.md의 [Step 1] 통합 검증을 실행해 줘.
1. N8N_BASE/webhook/oke-search 엔드포인트를 호출하여:
   - 일반 규정 검색(비밀번호 정책, VPN 정책) 시 HTTP 200, evidence 3건 반환 및 코사인 유사도 점수(0.380~0.709 분포)를 실측해.
   - WF-05 권한 격리 검증으로 보안사고 질문을 `access_levels=["all"]`(일반직원)과 `access_levels=["all","it"]`(IT팀)로 각각 호출하여, `all` 조건에서 `security-incident` 문서가 단 1건도 노출되지 않음(wf05_leaked_it_count == 0)을 증명해.
2. `python3 tools/vm_web_terminal.py run "..."`으로 VM PostgreSQL(oke-postgres-1)의 `rag.documents`(8문서: all 7, it 1) 및 `rag.chunks`(33청크: all 30, it 3), `vector(3072)` 차원 무결성을 확인해.
3. 실행 결과를 민감정보(TEAM_KEY, API 키 등) 없이 `develop/yubeen/runs/rag-search-eval-20261107.json`에 저장해 줘.
```

### 방법 B: 터미널에서 직접 복사-붙여넣기 실행 (Mac / Windows 공통)
```bash
# 1) /webhook/oke-search 직접 호출로 C03 검색 + WF-05 권한 격리(all vs it) 실측 및 JSON 저장
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
ts = int(time.time())

queries = [
    {"id": "C03-PASS-POLICY", "query": "비밀번호 최소 길이와 복잡도 기준은?", "type": "policy", "access_levels": ["all"]},
    {"id": "C03-VPN-POLICY",  "query": "재택근무 VPN 연결 끊김 시 점검 절차는?", "type": "network", "access_levels": ["all"]},
    {"id": "WF05-ALL-SCOPE",  "query": "보안사고 및 침해사고 발생 시 내부 보고 및 격리 절차는?", "type": "security", "access_levels": ["all"]},
    {"id": "WF05-IT-SCOPE",   "query": "보안사고 및 침해사고 발생 시 내부 보고 및 격리 절차는?", "type": "security", "access_levels": ["all", "it"]},
]

records = []
for q in queries:
    payload = {"request_id": f"rag-{q['id'].lower()}-{ts}", "query": q["query"], "type": q["type"], "access_levels": q["access_levels"], "top_k": 3}
    req = urllib.request.Request(
        f"{N8N_BASE}/webhook/oke-search",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Team-Key": TEAM_KEY},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    elapsed = round(time.time() - t0, 3)
    ev = body.get("evidence") or []
    docs = [item.get("doc_id") or item.get("doc_key") for item in ev]
    scores = [item.get("score") for item in ev]
    leaked_it = [d for d in docs if d and "security-incident" in str(d)] if q["access_levels"] == ["all"] else []
    records.append({
        "test_id": q["id"],
        "access_levels": q["access_levels"],
        "http_status": resp.status,
        "elapsed_sec": elapsed,
        "evidence_count": len(ev),
        "doc_ids": docs,
        "scores": scores,
        "wf05_leaked_it_count": len(leaked_it),
    })
    print(f"[{q['id']}] access={q['access_levels']} | docs={docs} | scores={scores} | leaked_it={len(leaked_it)}")

out = Path("develop/yubeen/runs/rag-search-eval-20261107.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "target": N8N_BASE, "records": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Saved receipt:", out)
PY

# 2) VM 웹 터미널(https://aio-t1.isitsoft.kr/ssh/)로 pgvector 8문서/33청크 및 vector(3072) 무결성 확인
python3 tools/vm_web_terminal.py run "docker exec -e PGPASSWORD=postgres oke-postgres-1 psql -U postgres -d postgres -c '
SELECT d.access_level, count(DISTINCT d.doc_id) AS docs, count(c.chunk_id) AS chunks,
       min(vector_dims(c.embedding)) AS min_dim, max(vector_dims(c.embedding)) AS max_dim
FROM rag.documents d JOIN rag.chunks c ON d.doc_id = c.doc_id GROUP BY d.access_level ORDER BY d.access_level;'"
```

---

## ✍️ [Step 2] 내 생각 채우기 (엔코아 100점 채점 만점용 3대 빈칸)

아래 섹션을 복사해서 `develop/yubeen/Doc/HANDOFF.md` 맨 아래에 붙여넣고, `[빈칸]` 부분을 유빈 님의 말로 채워주세요!

```markdown
## [최종 통합 제출] 신유빈 (RAG · 벡터 인덱스 및 검색) 핵심 검증 및 설계 근거

### 1. [팀 시나리오 1개] 내가 직접 기획·검증한 RAG 권한 격리/검색 품질 시나리오
| 항목 | 작성 내용 (`[빈칸]`을 지우고 작성해 주세요) |
| :--- | :--- |
| **시나리오 이름** | `[빈칸 예시: 일반 직원(access_level='all') 검색 시 IT 전용 보안사고 대응 규정(security-incident) 원천 격리(WF-05 노출 0건)]` |
| **기획 의도 (왜 필요한가?)** | `[빈칸 예시: LLM 프롬프트에서만 문서를 숨기면 프롬프트 주입이나 요약 과정에서 비인가 사내 보안 규정이 유출될 수 있으므로, 벡터 검색 SQL 단계에서 아예 후보군에서 제외해야 함]` |
| **입력 조건 및 테스트 방법** | `[빈칸 예시: 동일한 보안사고 질의를 access_levels=["all"]과 ["all","it"]로 각각 호출하여 반환되는 evidence doc_id 비교]` |
| **기대 결과 vs 실제 검증 결과** | • **기대 결과**: `all 호출 시 security-incident 노출 0건(Leak=0), all+it 호출 시에만 정상 반환`<br>• **실제 결과**: `[빈칸: Step 1 실행으로 확인한 실제 doc_ids, scores, wf05_leaked_it_count 결과 작성]` |

### 2. [실패 및 해결 사례 6칸 표] RAG 파이프라인 개발·통합 중 겪은 난관과 해결책 (1건)
| ① 현상 (문제점) | ② 재현 조건 | ③ 원인 및 근거 | ④ 조치 내용 (해결책) | ⑤ 재시험 결과 | ⑥ 잔여 위험 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `[빈칸 예시: 고정 글자수(300자/500자) 단순 청킹 시 마크다운 표나 조항 제목과 본문이 절단되어 유사도 점수가 하락하거나, 로컬 rag-search 컨테이너 기동 시 postgresql+psycopg:// DSN 스킴 오류로 503 발생]` | `[빈칸: 언제 발생했는지]` | `[빈칸: 왜 발생했는지 (예: 문맥 단절 또는 psycopg.connect()의 SQLAlchemy DSN 비호환 등)]` | `[빈칸: 어떻게 고쳤는지 (예: 문단·절 헤더 보존 청킹 8문서/33청크 채택 및 문서 제목/섹션 메타데이터 결합 임베딩, DSN 정규화 등)]` | `[빈칸: 33청크 전수 적재, 16문항 In-scope Top-1 0.380~0.709 확보 및 C03 HTTP 200 확인]` | `[빈칸: 문서 100배 확장(800문서/3,300청크) 시 HNSW 인덱스 도입 필요 등 1줄]` |

### 3. [아키텍처 설계 근거 (Why?)] 심사위원 질의응답 방어용 2줄
- **Q1. 고정 글자수(300자=45청크, 500자=28청크) 대신 '문단·절(Section) 단위 청킹(8문서 33청크, 평균 73.06 토큰)'을 최종 채택한 이유는?**
  - **내 답변**: `[빈칸 예시: 사내 규정 문서 특성상 조항(## 절) 단위로 정책 조건이 완결되므로, 절 경계를 보존하고 상위 문서 제목·절 제목을 임베딩 입력(평균 95.12 토큰)에 함께 주입해야 표·조건절 절단 없이 가장 높은 검색 정확도와 명확한 출처(doc_id + section) 인용을 얻을 수 있기 때문입니다.]`
- **Q2. 검색 후 사후 필터링(Post-filtering) 대신 PostgreSQL `WHERE d.access_level = ANY(...)` 사전 필터링(Pre-filtering)을 선택한 이유는?**
  - **내 답변**: `[빈칸 예시: 사후 필터링은 Top-K(3건)가 모두 비인가 문서일 때 정상 허용 문서까지 누락되는(Empty Recall) 문제가 발생하므로, SQL 사전 필터링으로 보안 격리(노출 0건)와 Top-3 재현율을 동시에 보장했습니다.]`
```

---

## 📤 [Step 3] 내 폴더(`develop/yubeen/`)만 깃허브에 제출하기

```bash
git add develop/yubeen/runs/ develop/yubeen/Doc/HANDOFF.md
git commit -m "docs(yubeen): RAG 통합 검색 평가 영수증 및 HANDOFF 핵심 설계 근거 제출"
git push origin main
```
