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

각자의 Doc/WORK-GUIDE와 HANDOFF에서 협의 상대·순서·기록 방법을 확인하고 TODO→SPEC→IMP-PLAN에 따라 진행한다.
일반 개발 담당자는 자기 폴더만 수정한다. 공통 문서와 상대 파일은 소유자에게 변경 요청한다.
공통 기준은 저장소 루트의 [AGENTS](../AGENTS.md), [API 계약](../docs/API-CONTRACT.md), [협업 절차](../docs/COORDINATION.md)다.

개인 폴더 이름 변경은 역할·웹훅·DB 설계를 바꾸지 않는다. 코드·워크플로우 구현은 아직 준비 단계다.
