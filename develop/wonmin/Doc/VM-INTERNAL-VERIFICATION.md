# VM 내부 실행 대조 · 2026-11-06

사용자가 로그인한 실제 Ubuntu 셸을 Orca Computer Use로 조작했다. 최초 화면을 다른 SSH 탭과 혼동했으나 이번에는 로그인된 셸에서 date, git, docker 및 컨테이너 내부 Python/Node 명령을 실제 실행했다. 배포/재시작/설정변경/DB쓰기 없음.

- [x] 실제 Ubuntu 셸·UTC 시각·배포HEAD·컨테이너9개 직접 확인
- [x] VM backend 내부 health/ready HTTP200·DB0005 직접 확인
- [x] T-2008~2011 고유 요청4개를 PostgreSQL READ ONLY 조회: 티켓각1·연결/소유권/답변일치·알림각1·DLQ0
- [x] n8n SQLite readOnly 조회: 요청4개와 본체 실행37/39/42/44 일치·success
- [ ] 하위handoff/search/errors 별도 노드/실행 로그 전체: 성공저장none, 설정변경하지 않음. 추가 상세조회는 UI 탭변경으로 결과미확인·입력중단

명령의 초기 오류(실행파일경로·SQLAlchemy colon bind)는 데이터/서비스 수정 없이 조회 명령만 고쳐 재실행했다. requests/verify-team-vm-wf02b.sql은 PostgreSQL 직접 콘솔용 준비본이고, 실제 backend SQLAlchemy 조회에서는 event_key 구분자를 chr(58)로 표현했다.

콘솔에 출력된 JSON을 화면에서 읽어 runs/vm-internal-observed-20261106.json에 전사했다. 자동 stdout 다운로드 원본이라고 주장하지 않는다. 비공개 원 화면은 .runtime/backups에 보존하고 해시만 공개 증거에 기록했다. 결과서: Doc/EXECUTION-RESULT.md.
