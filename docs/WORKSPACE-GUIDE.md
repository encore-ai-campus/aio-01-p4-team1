# 이름 폴더별 작업 안내

현재 합의한 주제·역할·기술은 유지하고 개발 시작 위치를 사람 이름으로 바꿨다. 프로젝트는 실행 코드 구현 전이다.

| 위치 | 의미·작성 내용 | 규칙·나와야 할 결과 |
| --- | --- | --- |
| [오현](../hyun/README.md) | 공통 계약·통합 단계·PR·마일스톤·배포·제출 | 상대 담당자 계약 검토, 기본 브랜치·VM 버전과 실제 회귀 결과 관리 |
| [이수언](../sueon/README.md) | Next.js 직원·관리자 화면 | FastAPI만 호출. 로그인→질문→근거/이관→내 문의, 관리자 티켓 처리 시연 |
| [박지혜](../jihye/README.md) | FastAPI·Pydantic·계정·권한·DB·배포 설정 | 서버 권한 검사·중복 방지·비밀번호 해시·재시작 뒤 기록 유지 |
| [임다혁](../dahyeok/README.md) | 문의 본체·분류·답변·검증·분기·루프 | 공통 계약 유지, 검색·이관 하위 호출과 정상·예외 응답 |
| [신유빈](../yubin/README.md) | 문서 청킹·임베딩·색인·검색 | 검색 전 권한 필터, 출처 반환, 품질 측정·재색인·복구 |
| [이원민](../wonmin/README.md) | 티켓·알림·DLQ·Error Workflow·시험 | 공통 14유형·팀 5개 이상·LLM 3회 반복·장애·재시험 보고서 |
| [docs](README.md) | 공통 기획·계약·필수 제출 문서 | 역할별 Doc을 대체하지 않음. 실제 구현·측정·로그와 일치하도록 취합 |

## 각자 작성할 세 문서

각 이름 폴더의 Doc/TODO.md는 무엇을 왜 할지, SPEC.md는 입력·출력·권한·오류·통과 기준, IMP-PLAN.md는 순서·수정 파일·확인 명령을 적는다.
현재 초안은 담당자가 자기 말로 검토한다. 연결 필드는 [API 계약](API-CONTRACT.md)에 공동 작성한다.
단계별 구현·직접 확인·커밋 후 다음 단계로 진행한다. 실행 뼈대와 실제 명령은 P0에서 각 담당자가 준비한다.

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

## 제출 준비

필수 3종은 docs/WORKFLOW-DESIGN.md·RAG-ARCHITECTURE.md·EXECUTION-RESULT.md다.
TOPIC·TEAM-CHARTER·daily/DAY80~82·images와 실제 JSON·시나리오·보고서도 준비한다.
개인 작업 폴더는 개발 원본이고 강사의 루트 제출 경로는 제출 전에 취합한다. [취합 규칙](../hyun/SUBMISSION.md)을 따른다.
