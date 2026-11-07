# 📢 [1팀 오케퐁] 최종 통합 테스트 및 개인 산출물 제출 워크시트 (`team-tasks/`)

> ⚠️ **[절대 주의] 실서버 VM 내부 설치 · 파일 수정 · 컨테이너 재시작 절대 금지**
> - 실서버 VM(`aio-t1`)은 공용 실서비스 환경입니다.
> - **VM 내부에서 `pip install`, `npm install`, `apt`, 소스코드 직접 수정, `docker compose down/restart` 등을 절대 실행하지 마세요!** (서버가 망가질 수 있습니다)
> - 패키지 설치(`pip install websockets`)는 오직 **본인 개인 로컬 PC**에서만 수행하셔야 합니다.

팀원 여러분, 고생 많으셨습니다! 이제 각자 로컬에서 개발한 결과물이 `main` 브랜치와 실서버 VM(`https://aio-t1.isitsoft.kr`)에 하나로 통합되었습니다.
복잡한 문서를 다 읽으실 필요 없이, **아래에서 본인 이름이 적힌 파일 딱 1개만 열어서 [Step 1] ➔ [Step 2] ➔ [Step 3] 순서대로 따라 하시면 15분 안에 끝납니다.**

---

## 📌 내 작업 파일 바로가기 (일정별 분리)

### 🟢 오늘 (11/07 토요일 · 18:00 마감) — 4인 핵심 개발자 통합 테스트 집중
1. **박지혜 님 (백엔드 & DB)**: [TASK-JIHYE.md](./TASK-JIHYE.md)
2. **임다혁 님 (오케스트레이션 / 메인 n8n)**: [TASK-DAHYEOK.md](./TASK-DAHYEOK.md)
3. **신유빈 님 (RAG / 벡터 검색)**: [TASK-YUBEEN.md](./TASK-YUBEEN.md)
4. **이원민 님 (QA / 안정성 · 티켓 · DLQ)**: [TASK-WONMIN.md](./TASK-WONMIN.md)

### 🟡 내일 (11/08 일요일 · 12:00 ~ 18:00 집중) — 프런트엔드 캡처 & 발표 슬라이드
5. **이수언 님 (프런트엔드 / 발표 슬라이드)**: [TASK-SUEON.md](./TASK-SUEON.md) *(※ 수언 님은 오늘(토) 작업이 없으며 일요일 12시부터 진행합니다!)*

### 👑 총괄 검증 및 최종 통합 (권오현 팀장님 전용)
6. **권오현 팀장님 (검수 · 3대 문서 통합 · `submission` 패키징)**: [TASK-OHYUN.md](./TASK-OHYUN.md)

---

## 🔐 [Step 0] 시작 전 딱 1번만 하는 `.env` 파일 세팅 (Mac / Windows 공통)

웹 브라우저나 터미널에 매번 아이디/비밀번호를 칠 필요가 없습니다!
권오현 팀장님이 **카카오톡/슬랙 개인 DM**으로 보내드린 값을 프로젝트 최상위 **`.env` 파일**에 딱 1번만 저장해 두면, 모든 테스트 스크립트와 [`tools/vm_web_terminal.py`](../tools/vm_web_terminal.py)가 자동으로 `.env`를 읽어서 실행합니다.
*(※ `.gitignore`에 `.env`가 등록되어 있어 깃허브에 절대 올라가지 않으므로 보안 감점 위험이 0%입니다.)*

```bash
# 1) 최신 main 브랜치 받기 및 웹소켓 패키지 설치 (최초 1회)
git checkout main
git pull origin main
pip install websockets

# 2) 프로젝트 최상위 폴더(Aio-4pj-1team/.env)에 아래 내용으로 .env 파일 저장
```

```dotenv
# Aio-4pj-1team/.env (팀장님이 개인 DM으로 보내주신 실제 값으로 채워 저장하세요)
VM_WEB_URL=https://aio-t1.isitsoft.kr/ssh/
VM_USER=toor
VM_PASSWORD=<팀장님이_개인DM으로_전달한_VM_비밀번호>
API_BASE=https://aio-t1.isitsoft.kr
N8N_BASE=https://aio-t1.isitsoft.kr:5678
TEAM_KEY=<팀장님이_개인DM으로_전달한_TEAM_KEY>
EMP_USER=user1
EMP_PASS=<팀장님이_개인DM으로_전달한_직원_비밀번호>
ADM_USER=admin
ADM_PASS=<팀장님이_개인DM으로_전달한_관리자_비밀번호>
```

### 연결 1초 확인 (`tools/vm_web_terminal.py`)
`.env` 저장 후 터미널(또는 Cursor / Claude Code / Codex 에이전트)에서 아래 명령을 실행하면 브라우저 없이도 공식 웹 터미널(`https://aio-t1.isitsoft.kr/ssh/`)을 통해 VM 내부 컨테이너 상태가 즉시 출력됩니다:
```bash
python3 tools/vm_web_terminal.py run "docker ps"
```

---

## 🚀 4인 개발자 공통 3단계 진행 요약 (Git 충돌 0% 규칙)

1. **[Step 1] 실행**: 본인 `TASK-<이름>.md`에 있는 **[🤖 AI 에이전트 프롬프트]** 를 본인 Cursor / Claude Code / Codex 창에 복붙하거나, 터미널 명령어를 복붙해 실행합니다 (`develop/<내이름>/runs/*.json` 영수증 자동 생성).
2. **[Step 2] 내 생각 빈칸 3개 채우기**: 엔코아 100점 채점 만점을 위해 본인 `TASK-<이름>.md`에 있는 **3개의 빈칸 표(① 내가 기획한 팀 시나리오 1개, ② 실패·해결 사례 6칸 표 1건, ③ 아키텍처 설계 근거 Why 2줄)** 를 채워 `develop/<내이름>/Doc/HANDOFF.md` 맨 아래에 붙여넣습니다.
3. **[Step 3] 내 폴더만 푸시**: 팀원 간 Git 충돌을 막기 위해 **오직 본인 폴더(`develop/<내이름>/`)만** `git add / commit / push` 합니다!
