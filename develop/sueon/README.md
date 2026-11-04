# 수언님 · 직원·관리자 화면

**목표:** 직원 질문부터 IT팀 처리 결과 확인까지 화면으로 연결한다. 작업 폴더는 develop/sueon. 현재 구현 전이며 아래 그림은 예상 화면이다.

<img src="../../docs/images/planned/ui-employee.png" width="680" alt="직원 예상 화면">

[관리자·계정·로그인 화면과 기능표](../../docs/PREVIEW.md) · [참고 예제](../../docs/references/README.md)

## 내가 만들 것

- FE-01 로그인·첫 비밀번호 변경·로그아웃.
- FE-02 질문·근거·보완 답변·이관/실패 안내, FE-03 내 문의·상태 재조회.
- FE-04T 티켓 처리, FE-04U 계정 발급/초기화, FE-04A 알림.
- 같은 출처 /api 프록시·Mock·실제 API 연결. 서버·DB·n8n 파일은 지혜님/다혁님 소유다.

## 지금 첫 작업 · P0-1

저장소 루트에서 cd develop/sueon 후 [IMP-PLAN P0-1](Doc/IMP-PLAN.md)의 Next.js 골격만 만든다. package.json·설치한 버전의 잠금 파일·src/app/layout.tsx·page.tsx가 첫 결과다. 서버를 기다리지 말고 먼저 기본 화면의 typecheck·build를 확인한다. 실제 API 연결은 뒤 단계다.

## 정해진 것과 내가 정할 것

| 구분 | 적용·결정 |
| --- | --- |
| 확정 | Next.js/TS, 제공 직원6명, 관리자 발급·세션 쿠키, 화면은 /api만 호출 |
| 담당자 결정 | 화면 배치·색·컴포넌트·상태 표현은 이 예상안을 바탕으로 설계. API 상세 필드/처리 중 응답 변경은 지혜님과 C01 확인 후 오현님 반영 |
| 선택 고도화 | 다크모드·추가 통계 등은 필수 실제 연결·시험 이후 |

P0/P1/P2는 구현 단계다. ‘담당자 결정’이라고 모두 개발을 멈추는 것이 아니며 디자인 선택에는 새 승인이 필요 없다.

## 바로 볼 예제

[로그인](../../docs/references/qnaweb/src-fe/src/app/login/page.tsx.example) · [질문](../../docs/references/qnaweb/src-fe/src/app/qna/new/page.tsx.example) · [내 문의](../../docs/references/qnaweb/src-fe/src/app/qna/my/page.tsx.example) · [티켓 편집](../../docs/references/qnaweb/src-fe/src/app/admin/tickets/page.tsx.example)

폼·목록·상태 표현을 참고한다. 예제의 샘플 빠른 로그인·JWT 브라우저 저장을 가져오지 말고 우리 세션 쿠키·첫 변경·공통 API에 맞춘다. 자세한 적용표는 참고 예제 안내에 있다.

## 누구에게 받고 무엇을 넘기나

- 지혜님에게 API 명세·응답 예시·실행법을 받고 Mock을 실제 호출로 연결한다(C01/C07). 오류·권한 시험은 원민님과 확인한다.
- 오현님에게 화면 소스·검증된 실행법·기능별 실제 결과·가린 캡처를 넘긴다. 직원 질문→이관→관리자 변경→직원 재조회가 완료 기준이다.
- 매 단계 보고는 변경 파일 / 확인 명령·입력 / 기대와 실제 / Mock·남은 문제·다음 상대 네 묶음으로 한다. 결과는 자기 Doc/SUBMISSION-NOTES.md에 취합한다.

## 내 CLI 첫 요청

    내 README와 AGENTS, 공통 API를 읽고 IMP-PLAN P0-1만 구현해.
    참고 예제에서 재사용할 구조와 바꿀 부분을 먼저 말해.
    develop/sueon 밖은 수정하지 말고 실제 확인 결과와 다음 작업을 보고해.

상세: [TODO](Doc/TODO.md) · [SPEC](Doc/SPEC.md) · [IMP-PLAN](Doc/IMP-PLAN.md) · [변경 요청 HANDOFF](Doc/HANDOFF.md).
