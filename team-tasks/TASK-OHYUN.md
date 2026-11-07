# 👑 [권오현 팀장님 전용] 팀원 산출물 검수 · 루트 3대 문서 통합 · `submission` 최종 패키징 가이드 (`TASK-OHYUN.md`)

- **담당**: 권오현 팀장 (총괄 아키텍트 · VM 인프라 · 최종 제출/통합)
- **목적**:
  1. **오늘(11/07 토)**: 4인 개발자(박지혜, 임다혁, 신유빈, 이원민)가 `main` 브랜치의 각자 폴더(`develop/<이름>/`)에 푸시한 `runs/*.json` 영수증과 `Doc/HANDOFF.md` 3대 빈칸을 **1분 만에 자동 검수**하고 루트 `docs/` 3대 문서에 통합합니다.
  2. **내일(11/08 일)**: 이수언 님이 `develop/sueon/images/`에 올린 웹 화면 캡처 4장을 수거해 루트 `docs/images/` 및 슬라이드에 반영하고, 프런트엔드 기술 검증·방어 논리는 팀장님과 AI 비서(`oc:0.2` / `w:0.2`)가 직접 작성하여 `submission` 브랜치로 최종 봉인합니다.

---

## 🔍 [Phase 1] 팀원 제출물 1분 자동 검수 스크립트 (Verification Gate)

팀원들이 푸시를 완료하면 터미널(또는 AI 비서)에서 아래 명령어로 **파일 존재 여부, JSON 파싱 무결성, 평문 비밀키(`tscan`) 유출 여부**를 한 번에 검사합니다.

```bash
cd ~/port-cli/Aio-4pj-1team
git checkout main && git pull origin main

python3 - <<'PY'
import json, re
from pathlib import Path

checks = [
    ("박지혜 (BE/DB)",   "develop/jihye/Doc/HANDOFF.md",   "develop/jihye/runs"),
    ("임다혁 (메인n8n)", "develop/dahyeok/Doc/HANDOFF.md", "develop/dahyeok/runs"),
    ("신유빈 (RAG)",     "develop/yubeen/Doc/HANDOFF.md",  "develop/yubeen/runs"),
    ("이원민 (QA/안정)", "develop/wonmin/Doc/HANDOFF.md",  "develop/wonmin/runs"),
    ("이수언 (일요일UI)", "develop/sueon/Doc/HANDOFF.md",   "develop/sueon/images"),
]

secret_pat = re.compile(r"(63KvIc0|eXn_\*0|sk-or-v1-|sk-proj-)")

for label, handoff_path, artifact_dir in checks:
    hp = Path(handoff_path)
    ap = Path(artifact_dir)
    files = sorted(ap.glob("*")) if ap.exists() else []
    leaks = []
    if hp.exists() and secret_pat.search(hp.read_text(encoding="utf-8", errors="ignore")):
        leaks.append(str(hp))
    for f in files:
        if f.is_file() and f.suffix in {".json", ".md", ".txt"}:
            txt = f.read_text(encoding="utf-8", errors="ignore")
            if secret_pat.search(txt):
                leaks.append(str(f))
            if f.suffix == ".json":
                json.loads(txt)  # JSON 문법 무결성 검증
    print(f"[{label}] HANDOFF={hp.exists()} | 산출물수={len(files)} | 평문유출={len(leaks)}건 {leaks}")
PY
```

### 팀원별 합격 판정 기준표 (팀장님 체크리스트)
| 팀원 | 제출 경로 (`develop/<이름>/` 고정) | 핵심 합격 기준 (영수증 확인 포인트) |
| :--- | :--- | :--- |
| **박지혜 님** | • `develop/jihye/runs/be-db-integration-*.json`<br>• `develop/jihye/Doc/HANDOFF.md` | • `wf06_employee_admin_403: true` (직원 세션 관리자 API 403 차단)<br>• `inquiries` ↔ `tickets` ↔ `alerts` 1:1 매칭 확인 및 `[Step 2]` 빈칸 3개 작성 완료 |
| **임다혁 님** | • `develop/dahyeok/runs/support-v18-integration-*.json`<br>• `develop/dahyeok/Doc/HANDOFF.md` | • `WF-01`(자동답변 + `sources` 존재), `WF-02`(보완질문), `WF-02b`(3회 이관), `WF-03`(무근거 이관) 4대 경로 실측 및 `[Step 2]` 빈칸 3개 작성 완료 |
| **신유빈 님** | • `develop/yubeen/runs/rag-search-eval-*.json`<br>• `develop/yubeen/Doc/HANDOFF.md` | • `WF05-ALL-SCOPE`에서 `wf05_leaked_it_count == 0` (일반직원 검색 시 보안사고 문서 0건)<br>• 8문서/33청크 스냅샷 및 `[Step 2]` 빈칸 3개 작성 완료 |
| **이원민 님** | • `develop/wonmin/runs/live-integration-qa-*.json`<br>• `develop/wonmin/Doc/HANDOFF.md` | • `WF-09` 동일 `request_id` 2회 호출 시 `same_ticket_id: true` 및 DB 티켓 +1건 유지<br>• 장애 주입(`WF-04`/`10`/`11`) 영수증 및 `[Step 2]` 빈칸 3개 작성 완료 |
| **이수언 님** *(일요일)* | • `develop/sueon/images/*.png` (화면 캡처 4장만 제출) | • 개인정보 마스킹된 UI 캡처 4장 확인 (빈칸 작성 및 `HANDOFF.md` 면제 — FE 기술 검증/방어 논리는 팀장님과 AI 비서가 직접 작성) |

---

## 🔄 [Phase 2] 팀원 작성 내용 ➔ 루트 공식 문서 4종(`docs/` & `daily/`) 자동 매핑 규칙

팀장님은 직접 타이핑하실 필요 없이, 총괄 비서(`aio-4pj-w:0.2` 및 `ac:0.1 ~ 0.3`)에게 아래 매핑 규칙대로 **자동 취합 지시**만 내리시면 됩니다:

1. **4인 개발자의 `[Step 2-1] 내가 기획한 팀 시나리오 1개씩` + 팀장님/AI 비서 작성 FE 시나리오**
   ➔ 루트 **`docs/EXECUTION-RESULT.md` §15 (팀 고유 시나리오 5종 실측 표)** 및 **`cases/team.json`** 에 통합 반영.
2. **4인 개발자의 `[Step 2-2] 실패 및 해결 사례 6칸 표 1건씩`**
   ➔ 루트 **`docs/EXECUTION-RESULT.md` §16 (실패·개선 사례 6칸 표준 양식)** 에 통합 반영 (채점 가산점 직결).
3. **4인 개발자의 `[Step 2-3] 아키텍처 설계 근거 (Why?)` + 이수언 님 UI 캡처 4장(`develop/sueon/images/`)**
   ➔ 다혁님·지혜님·원민님 근거는 **`docs/WORKFLOW-DESIGN.md`** 에, 유빈님 근거는 **`docs/RAG-ARCHITECTURE.md`** 에, 수언님 UI 캡처 4장은 루트 **`docs/images/` 복사 후 `README.md` 및 발표 슬라이드**에 연결 (FE 기술 설명은 팀장님/AI 비서가 직접 보강).
4. **팀원 전원의 결과물 및 커밋 해시**
   ➔ 루트 **`daily/DAY82.md` §2 (6인 역할별 최종 마감 내역 표)** 에 전원 기록.

---

## 📦 [Phase 3] `submission` 브랜치 최종 단방향 병합 및 봉인 (Final Packaging)

```bash
# 1) main 브랜치 변경사항 커밋 및 푸시
cd ~/port-cli/Aio-4pj-1team
git add docs/ daily/ workflows/ README.md SUBMISSION.md
git commit -m "docs(release): integrate team final receipts and complete 3 core design/result docs"
git push origin main

# 2) submission 브랜치로 main 단방향 병합 및 루트 9대 폴더 승격 후 푸시
git checkout submission
git merge --no-edit main
git push origin submission
git checkout main
```
