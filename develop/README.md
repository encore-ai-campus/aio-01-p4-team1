# 개발 작업 폴더

저장소 전체를 내려받고 저장소 루트에서 아래 경로로 이동한다. 개인 폴더만 따로 받으면 공통 계약과 상대 자료가 빠진다.

| 담당자 | 역할 | 저장소 루트에서 이동 | 시작 문서 |
| --- | --- | --- | --- |
| 오현님 | 팀장·통합·배포 | `cd develop/ohyun` | [README](ohyun/README.md) |
| 수언님 | 프론트엔드 | `cd develop/sueon` | [README](sueon/README.md) |
| 지혜님 | 백엔드·DB·실행 환경 | `cd develop/jihye` | [README](jihye/README.md) |
| 다혁님 | 문의 처리 자동화 | `cd develop/dahyeok` | [README](dahyeok/README.md) |
| 유빈님 | RAG·지식 검색 | `cd develop/yubeen` | [README](yubeen/README.md) |
| 원민님 | 안정성·이관·시험 | `cd develop/wonmin` | [README](wonmin/README.md) |

각자의 README에서 담당 범위·변경 시 협의 상대를 확인하고 TODO→SPEC→IMP-PLAN에 따라 진행한다. HANDOFF는 변경 요청·전달 기록이다.
일반 개발 담당자는 자기 폴더만 수정한다. 공통 문서와 상대 파일은 소유자에게 변경 요청한다.
공통 기준은 저장소 루트의 [AGENTS](../AGENTS.md), [API 계약](../docs/API-CONTRACT.md), [협업 절차](../docs/COORDINATION.md)다.

개인 폴더 이름 변경은 역할·웹훅·DB 설계를 바꾸지 않는다. 코드·워크플로우 구현은 아직 준비 단계다.

## 공통 참조 문서 (저장소 내부 기준)

모든 개발·검증·제출 기준은 외부 링크가 아닌 아래 저장소 내부 문서를 기준으로 한다.

- [전체 시스템 아키텍처](../docs/ARCHITECTURE.md)
- [의사결정 기록 (ADR-001)](../docs/adr/ADR-001-project-decisions.md)
- [팀 헌장 · 역할 · 중간 목표](../docs/TEAM-CHARTER.md)
- [공통 API · 웹훅 · 실행 환경 계약](../docs/API-CONTRACT.md)
- [데이터 · PostgreSQL · pgvector 구조](../docs/DATA-AND-DB.md)
- [제공 데이터 · 공통 14종 시나리오 · 평가/검증 기준](../docs/EVALUATION-GUIDE.md)
- [협업 · 변경 검토 · PR 절차](../docs/COORDINATION.md)

제출 파일과 취합 방법은 [오현님 제출 안내](ohyun/SUBMISSION.md)를 따른다. 설치·실행 명령은 각 역할의 P0에서 검증 후 자기 README에 적는다.
