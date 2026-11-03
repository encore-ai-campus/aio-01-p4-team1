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

## 참고할 강사 자료

아래 링크는 지정한 커밋의 수업자료다. 개인 Doc에도 역할별 직접 링크를 보존했다.

- [요구→TODO→SPEC→IMP-PLAN 수업](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/78/VIBE-Q-TCHECK.md)
- [일정·팀 역할·동결](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/01-SCHEDULE-AND-TEAMS.md)
- [환경·FastAPI 어댑터·팀 VM](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/02-ENVIRONMENT-AND-SERVICES.md)
- [흐름·공통 계약·하위 워크플로우](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md)
- [RAG](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/05-RAG-DESIGN-GUIDE.md)
- [보안·안정성](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/06-RELIABILITY-AND-SECURITY.md)
- [시험·실제 보고서](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/07-TESTING-GUIDE.md)
- [필수 제출 경로·발표](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/08-SUBMISSION.md)

제출 파일과 취합 방법은 [오현님 제출 안내](ohyun/SUBMISSION.md)를 따른다. 설치·실행 명령은 각 역할의 P0에서 검증 후 자기 README에 적는다.
