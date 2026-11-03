# 수언님 · 프론트엔드

## 담당 범위

이 폴더의 Next.js 코드·화면·API 클라이언트·테스트·Doc·README. 예: app/ 또는 src/ 구조는 본인이 선택해 계획에 기록한다.

**수정·생성·삭제·이동은 `develop/sueon/` 안에서만 한다.** 루트 docs·README·AGENTS·.env.example·다른 이름 폴더는 읽기만 한다. 상대의 코드를 복사해서 중복 구현하지 않는다. DB 접속·API 호출은 파일 수정 권한과 별개이며 합의한 계약과 자격증명으로 수행한다.

## 개발 시작

저장소 전체를 clone한 뒤 루트에서 `cd develop/sueon`으로 이동한다. 현재는 개발 준비 문서 단계다. 코드·설치·실행 명령은 P0에서 실제 확인 후 이 README에 추가한다.

1. [TODO](Doc/TODO.md)에서 목적과 필수 범위를 확인한다.
2. [SPEC](Doc/SPEC.md)에서 입력·출력·오류·통과 기준을 확인한다.
3. [IMP-PLAN](Doc/IMP-PLAN.md)의 첫 단계부터 구현·확인·커밋한다.
4. [공통 API](../../docs/API-CONTRACT.md)와 [데이터·DB](../../docs/DATA-AND-DB.md)를 그대로 적용한다. 상대 구현이 없으면 같은 계약의 Mock을 사용한다.

기준대로 개발할 때 사전 협의는 필요 없다. 자기 폴더만 수정하고 공통/상대 파일 변경은 소유자에게 요청한다.

## 변경 시 협의 상대

| 연결 | 변경 검토 상대 | 변경 요청에 담을 내용 |
| --- | --- | --- |
| C01 | 지혜님 | 필요한 화면과 API 요청 목록을 먼저 보낸다. 로그인·계정 발급·질문·내 문의·티켓 처리·알림별 화면 상태를 제안한다. / 지혜님의 OpenAPI/JSON 예시, HTTP 오류, 세션 쿠키·비밀번호 변경 조건 |
| C07 | 지혜님·오현님 | 프론트 실행 명령·포트·환경변수 이름·Dockerfile 경로를 제공한다. / 브라우저용 API 주소/프록시와 배포 방법 |

위 표는 변경할 때의 연락망이다. 요청·검토 기록은 [내 HANDOFF](Doc/HANDOFF.md)에 작성하고 상대는 자기 기록에 확인한다.
공통 기준 변경은 오현님이 반영한다. PR·팀 VM 배포·회귀 규칙은 [COORDINATION](../../docs/COORDINATION.md)을 따른다.

## 제공할 결과물

Doc/SPEC.md의 화면 목록·상태 표, Mock 응답·API 클라이언트, 실제 화면 코드, 실행 README, 단계별 확인 기록. 캡처 원본은 develop/sueon/evidence/에 두고 오현님이 공통 docs/images로 취합한다.

루트 제출 문서는 직접 수정하지 않고 자기 Doc/SUBMISSION-NOTES.md에 **반영할 문서·절 / 실제 설계 / 측정·보고서 경로 / 남은 문제**를 정리해 오현님에게 넘긴다.
코드·JSON은 담당자가 구현한 뒤 생성한다. 확인하지 않은 노드·수치·PASS를 채우지 않는다.
기능을 완성하면 자기 README에 설치·실행·확인 명령과 상대 서비스가 필요한 조건을 적는다.

## 에이전트 요청 예시

```text
현재 작업 폴더는 develop/sueon/이고 내 역할은 프론트엔드이야.
루트 AGENTS.md와 docs/TOPIC.md·API-CONTRACT.md·COORDINATION.md,
이 폴더 AGENTS.md·README.md·Doc/SPEC.md·Doc/IMP-PLAN.md·Doc/HANDOFF.md를 읽어.
내가 지정한 요구 ID와 단계만 진행해. develop/sueon/ 안에서만 파일을 수정·생성·삭제해.
상대/공통 파일 변경이 필요하면 내 Doc/HANDOFF.md에 요청안만 적고 상대 파일은 고치지 마.
이번 수정 파일·입출력·통과 기준을 먼저 정리하고, 완료 후 실제 검사와 미실행을 구분해 보고해.
```

## 공통 문서

[주제](../../docs/TOPIC.md) · [팀 헌장·역할](../../docs/TEAM-CHARTER.md) · [협업](../../docs/COORDINATION.md) · [제출 취합](../ohyun/SUBMISSION.md).
역할별 수업자료 링크는 Doc/IMP-PLAN.md의 공통 자료 절에 있다.
