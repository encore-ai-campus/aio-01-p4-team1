# 직원·관리자 화면 · SPEC

작업 기준: [내 작업·협의 안내](WORK-GUIDE.md) · [내 협의 기록](HANDOFF.md). 공통 파일과 상대 폴더는 직접 고치지 않고 소유자에게 요청한다.

주 담당: **이수언**. 지원 담당은 추가 배정.

> 상태: 검토용 요구 초안. 아래 확인 기준을 담당자가 실제 입력·출력·오류 예시와 확인 방법으로 구체화한다. 테스트 통과 기록은 아니다.

## 요구와 확인 기준

| ID | 요구 | 기대 결과·확인할 것 |
| --- | --- | --- |
| FE-01 | 로그인·세션 상태 | 정상 로그인 뒤 직원 이름 표시, 로그아웃 뒤 보호 화면 접근 제한. 임시 비밀번호 변경 화면 포함. |
| FE-02 | 질문과 결과 표시 | 자동 답변·보완 질문·이관·권한 없음·차단을 각 상태로 표시하고 sources와 ticket을 계약에 맞게 렌더링. |
| FE-03 | 본인 문의 | 본인 기록을 표시하고 다른 직원의 데이터를 브라우저에서 숨기는 방식으로 권한을 대신하지 않음. |
| FE-04 | 관리자 기능 | 계정 발급·티켓 조회·담당자/상태/답변 변경·긴급 알림 화면. 직원 계정으로 관리자 API 호출 시 403을 안내. |
| FE-05 | 연결 실패 | 중복 제출 방지, 응답 지연·API 오류·세션 만료 안내. 키·n8n URL·DB 접속 정보가 브라우저에 노출되지 않음. |

## 구현 전에 담당자가 정할 것

- [ ] 웹 API별 실제 JSON·오류 형식: 백엔드와 공동 작성
- [ ] 화면 경로·레이아웃·모바일 범위·페이지별 필수 요소
- [ ] 비활성화·관리자 비밀번호 초기화 화면의 API 누락 여부 확인

## 각 요구에 추가할 실행 예시

- 요구 ID / 필수·나중:
- 입력·사전 조건:
- 예상 HTTP 상태·출력 JSON 또는 화면 상태:
- 실패·권한·경계 사례:
- 확인 명령·시나리오 ID:
- 연결 담당자와 합의한 날짜:

공통 계약과 중복되는 스키마는 [API-CONTRACT.md](../../docs/API-CONTRACT.md)를 참조한다. 바꿀 내용은 내 HANDOFF에 제안한다. 오현이 공통 문서를 반영한 뒤 각 담당자는 자기 SPEC만 갱신한다. 기준을 바꾸지 않고 구현을 고쳐야 하는 실패와, 요구 변경을 구분한다.

## 공통 자료

- [주제](../../docs/TOPIC.md) · [공통 API 계약](../../docs/API-CONTRACT.md) · [역할표](../../docs/ROLE-PLAN.md)
- [수업 방식과 연결 규칙](../../docs/DEVELOPMENT-FLOW.md)
- 수업 원문: [11-TOPIC-GUIDE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/11-TOPIC-GUIDE.md) · [02-ENVIRONMENT-AND-SERVICES.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/02-ENVIRONMENT-AND-SERVICES.md)
