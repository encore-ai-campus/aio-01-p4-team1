# 오케퐁 팀 헌장 · 주 담당 배정 반영

> 상태: 팀장이 확정한 주 담당 배정 반영. 지원 담당·첫 통합 시각·나머지 협업 규칙은 추가 조율한다. 강사 승인 완료를 의미하지 않는다.

## 팀과 역할

| 역할 | 주 담당 | 담당 범위 | 주 소유 경로 | 완료 기준 |
| --- | --- | --- | --- | --- |
| 기획·통합 | 오현님 | 범위·계약 관리, PR 병합, 팀 VM 배포, 발표·문서 취합 | `develop/ohyun/`, `README.md`, `docs/TOPIC.md`, `docs/TEAM-CHARTER.md`, `docs/daily/` | 기본 브랜치와 VM이 일치하고 배포 후 공통 시나리오 결과를 기록 |
| 직원·관리자 화면 | 수언님 | 로그인, 질문, 답·근거, 내 문의, 관리자 티켓·알림 화면과 API 연결 | `develop/sueon/` | 직원과 관리자가 FastAPI만 호출해 주요 흐름을 끝까지 시연 |
| 업무 API·DB | 지혜님 | Pydantic 계약, 로그인·세션·권한, 계정 생성, 문의·티켓·알림·상태 저장, 중복 방지, 공통 실행 설정 | `develop/jihye/`, `develop/jihye/migrations/`, `develop/jihye/deploy/` | 화면·n8n API와 인증 API가 계약대로 응답하고 재시작 뒤 기록이 유지 |
| 문의 처리 자동화 | 다혁님 | 웹훅 입력 검사, 분류, 보완 질문, 답변·검증, 자동 답변·이관 분기 | `develop/dahyeok/workflows/oke-support.json` | 공통 요청·응답 형식을 지키고 정상·정보 부족·근거 없음 경로가 동작 |
| 지식 검색(RAG) | 유빈님 | 문서 청킹·임베딩·색인, 권한별 검색, 출처·점수 측정 | `develop/yubeen/workflows/oke-index.json`, `develop/yubeen/workflows/oke-search.json` | 규정 8종의 색인·재색인과 권한별 근거 검색을 실제 결과로 확인 |
| 안정성·시험 | 원민님 | 티켓 연동, Error Workflow, 재시도·DLQ·알림·중복·보안 시험, 팀 시나리오와 결과 기록 | `develop/wonmin/workflows/oke-handoff.json`, `develop/wonmin/workflows/oke-errors.json`, `develop/wonmin/cases/`, `develop/wonmin/requests/`, `develop/wonmin/runs/` | 공통 14유형·팀 5개 이상, LLM 3회 반복과 실패 후 재시험 기록 |

## 목표와 범위

오케퐁 직원 6명의 사내 IT 문의에 권한이 허용된 규정의 근거로 답하고, 근거가 없거나 긴급한 문의는 IT팀 티켓·알림으로 이관한다.
문의 범위·계정·저장은 [TOPIC](TOPIC.md), API·실행 설정은 [API 계약](API-CONTRACT.md)을 따른다.
공개 회원가입은 없고 관리자가 계정을 발급한다. 텔레그램은 필수 기능·시험·시연이 끝난 뒤 검토한다.

## 협업 규칙

- 각 담당자는 자기 TODO를 이해한 말로 고치고 SPEC·IMP-PLAN을 작성한다. 공통 계약을 적용해 한 단계씩 구현·확인·커밋한다. 계약 변경이 필요할 때만 지정 상대와 협의한다.
- 일반 개발 담당자는 자기 폴더만 수정한다. 상대/공통 파일 변경은 자기 HANDOFF로 요청하고 소유자가 수정한다. 공통 계약·제출 문서는 오현님이 반영하고 각자는 자기 SPEC·코드를 갱신한다.
- PR에는 변경·확인 결과·남은 문제를 적는다. 공통 기본 브랜치 병합과 팀 VM 배포는 리드가 관리한다.
- VM 배포 후 공통 회귀 시험을 한다. 키·비밀번호·연락처를 문서·JSON·로그·캡처에 노출하지 않는다.
- 81일차 8교시 기능 동결, 이후 시험·수정·문서·발표에 집중한다.
- 막힘은 30분 안에 팀에 공유하고, 1시간이면 강사에게 도움을 구한다. 이 공유 시간은 강사 템플릿의 제안 규칙이며 팀이 확인한다.

## 팀이 확정할 항목

- [x] 사람별 주 역할·주 소유 경로 배정
- [ ] 지원 담당과 세부 구현 파일 경계
- [ ] 각 역할 SPEC 검토 시점과 첫 통합 날짜·시각
- [ ] API 계약의 서비스명·포트 기준으로 실제 실행 명령 검증
- [ ] 협업 절차에 따른 GitHub 보호 설정·마일스톤과 실제 PR 운영 확인
- [ ] 80일차 주제 승인 내용 반영

저장소: https://github.com/hyunport/Aio-4pj-1team · 웹훅: `oke-support`.
팀 VM 주소·비밀번호는 문서에 쓰지 않고 팀장이 관리한다. 매일 1교시 처음 10분에 진행·막힘·다음 작업을 공유한다.

## 변경 기록

| 날짜 | 변경 | 확인 상태 |
| --- | --- | --- |
| 2026-11-03 | 기존 대화와 강사 양식에 맞춰 초안 준비 | 팀 검토 전 |
| 2026-11-03 | 팀장 지시로 6명 주 담당 배정 반영 | 주 담당 확정, 지원 담당 미정 |

지원 담당은 아직 배정하지 않았다. 워크플로우는 각자 이름 폴더/workflows/ 아래에 구현한다. 제출용 루트 경로는 develop/ohyun/SUBMISSION.md에 따라 취합한다.

원본: [팀 헌장 템플릿](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/templates/TEAM-CHARTER-TEMPLATE.md).

상세 협의 책임과 단계별 연결 기준은 [COORDINATION](COORDINATION.md)을 따른다. 지원 담당은 파일 수정 권한을 자동으로 받지 않는다.

## 제출 문서별 자료 제공

| 문서 | 내용을 제공할 역할 |
| --- | --- |
| `docs/WORKFLOW-DESIGN.md` | 문의 처리 자동화, 업무 API·DB, 안정성·시험 |
| `docs/RAG-ARCHITECTURE.md` | 지식 검색(RAG) |
| `docs/EXECUTION-RESULT.md` | 안정성·시험, 각 기능 담당의 실행 결과 |

각 담당자는 자기 Doc/SUBMISSION-NOTES.md에 실제 설계·측정·보고서를 정리하고 오현님이 공통 제출 문서로 취합한다. 지원 담당 지정은 자동으로 상대 파일 편집 권한을 부여하지 않는다.
