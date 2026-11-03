# 업무 API·DB·공통 실행 설정 · TODO

> 운영 기준: 팀장 배포 기본안으로 바로 구현한다. 이 문서의 기존 "합의·협의" 항목은 기준 적용 여부 확인이며, 기본안을 바꿀 때만 상대와 협의한다. 기준은 저장소 루트 docs/API-CONTRACT.md와 docs/DATA-AND-DB.md를 따른다.
작업 기준: [내 작업·협의 안내](../README.md) · [내 협의 기록](HANDOFF.md). 공통 파일과 상대 폴더는 직접 고치지 않고 소유자에게 요청한다.

주 담당: **지혜님**. 지원 담당은 추가 배정.

> 상태: 팀 합의 내용을 옮긴 참고 초안. 담당자가 자기 말로 고치고 필수·나중을 구분한 뒤 SPEC을 작성한다. 체크는 구현 완료가 아니라 요구 이해·검토 완료 표시다.

## 먼저 이해할 일

- [ ] 제공 직원 6명을 대상으로 관리자 발급 계정과 실제 로그인을 지원한다.
- [ ] 세션으로 신원을 확인하고 본인·IT팀 권한을 서버에서 검사한다.
- [ ] 질문을 공통 계약으로 변환해 n8n에 보내고 문의·티켓·알림을 PostgreSQL에 저장한다.
- [ ] 새 환경의 DB 생성과 웹·서버·DB 실행을 재현할 수 있게 한다.

## 담당 경로 · 저장소 루트 기준

`develop/jihye/`, `develop/jihye/migrations/`, `develop/jihye/deploy/`의 실행 설정. 팀 VM의 실제 배포·환경값 등록은 리드가 관리한다.

## 담당자가 채울 것

- 내가 이해한 목적·사용자: 작성 필요
- 이번 일정에서 반드시 할 것 / 나중에 할 것: 작성 필요
- 의문·필요한 자료·다른 역할의 도움이 필요한 것: 작성 필요
- 요구 검토자·검토일: 미정

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [팀 헌장·역할](../../../docs/TEAM-CHARTER.md)
- [수업 방식과 연결 규칙](../../../docs/COORDINATION.md)
- 수업 원문: [02-ENVIRONMENT-AND-SERVICES.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/02-ENVIRONMENT-AND-SERVICES.md) · [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md)
