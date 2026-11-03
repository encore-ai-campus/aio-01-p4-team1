# 다혁님 · 문의 처리 자동화

## 담당 범위

workflows/oke-support.json·본체 전용 보조 파일/로컬 시험 입력·Doc. 검색·이관 JSON과 다른 폴더는 수정하지 않는다.

**수정·생성·삭제·이동은 `develop/dahyeok/` 안에서만 한다.** 루트 docs·README·AGENTS·.env.example·다른 이름 폴더는 읽기만 한다. 상대의 코드를 복사해서 중복 구현하지 않는다. DB 접속·API 호출은 파일 수정 권한과 별개이며 합의한 계약과 자격증명으로 수행한다.

## 개발 시작

저장소 전체를 clone한 뒤 루트에서 `cd develop/dahyeok`으로 이동한다. 현재는 개발 준비 문서 단계다. 코드·설치·실행 명령은 P0에서 실제 확인 후 이 README에 추가한다.

1. [TODO](Doc/TODO.md)에서 목적과 필수 범위를 확인한다.
2. [SPEC](Doc/SPEC.md)에서 입력·출력·오류·통과 기준을 확인한다.
3. [IMP-PLAN](Doc/IMP-PLAN.md)의 첫 단계부터 구현·확인·커밋한다.
4. [공통 API](../../docs/API-CONTRACT.md)와 [데이터·DB](../../docs/DATA-AND-DB.md)를 그대로 적용한다. 상대 구현이 없으면 같은 계약의 Mock을 사용한다.

기준대로 개발할 때 사전 협의는 필요 없다. 자기 폴더만 수정하고 공통/상대 파일 변경은 소유자에게 요청한다.

## 변경 시 협의 상대

| 연결 | 변경 검토 상대 | 변경 요청에 담을 내용 |
| --- | --- | --- |
| C02 | 지혜님 | 본체 웹훅 입력/출력·인증·route·오류·로컬 실행 정보를 제공한다. / 웹 문의가 전달할 신원·attempt/context·서버 시간 제한 |
| C03 | 유빈님 | 검색에 필요한 query·type·권한 문맥·티켓 문맥안을 보낸다. / search 근거 목록 형식·빈 목록/실패 구분·시간 제한·인증 |
| C04 | 원민님 | 이관의 request_id·requester·요약·유형·긴급도·사유를 보낸다. / handoff ticket·duplicate·실패 사유·부분 실패 응답 |
| C08 | 원민님 | Agent·분기·루프·차단·권한·중복 기대와 관련 사례를 제공한다. / 공통/팀 테스트 기대와 실제 실패 보고서 |

위 표는 변경할 때의 연락망이다. 요청·검토 기록은 [내 HANDOFF](Doc/HANDOFF.md)에 작성하고 상대는 자기 기록에 확인한다.
공통 기준 변경은 오현님이 반영한다. PR·팀 VM 배포·회귀 규칙은 [COORDINATION](../../docs/COORDINATION.md)을 따른다.

## 제공할 결과물

본체 JSON·노드/Agent 역할 카드·분기/병렬/루프 설명·연결선별 실제 페이로드·개별 check 결과. 설계서 반영 자료는 develop/dahyeok/Doc/SUBMISSION-NOTES.md로 제공한다.

루트 제출 문서는 직접 수정하지 않고 자기 Doc/SUBMISSION-NOTES.md에 **반영할 문서·절 / 실제 설계 / 측정·보고서 경로 / 남은 문제**를 정리해 오현님에게 넘긴다.
코드·JSON은 담당자가 구현한 뒤 생성한다. 확인하지 않은 노드·수치·PASS를 채우지 않는다.
기능을 완성하면 자기 README에 설치·실행·확인 명령과 상대 서비스가 필요한 조건을 적는다.

## 에이전트 요청 예시

```text
현재 작업 폴더는 develop/dahyeok/이고 내 역할은 문의 처리 자동화이야.
루트 AGENTS.md와 docs/TOPIC.md·API-CONTRACT.md·COORDINATION.md,
이 폴더 AGENTS.md·README.md·Doc/SPEC.md·Doc/IMP-PLAN.md·Doc/HANDOFF.md를 읽어.
내가 지정한 요구 ID와 단계만 진행해. develop/dahyeok/ 안에서만 파일을 수정·생성·삭제해.
상대/공통 파일 변경이 필요하면 내 Doc/HANDOFF.md에 요청안만 적고 상대 파일은 고치지 마.
이번 수정 파일·입출력·통과 기준을 먼저 정리하고, 완료 후 실제 검사와 미실행을 구분해 보고해.
```

## 공통 문서

[주제](../../docs/TOPIC.md) · [팀 헌장·역할](../../docs/TEAM-CHARTER.md) · [협업](../../docs/COORDINATION.md) · [제출 취합](../ohyun/SUBMISSION.md).
역할별 수업자료 링크는 Doc/IMP-PLAN.md의 공통 자료 절에 있다.
