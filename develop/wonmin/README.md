# 원민님 · 안정성·이관·시험

직원이 자동 답변을 받지 못해도 문의가 유실되지 않도록 티켓·알림·실패 대기열(DLQ)을 연결하고, 팀 전체의 정상·권한·장애 결과를 재현 가능한 증거로 남긴다.

> 현재 상태: 작업 지시 문서 준비. 워크플로우·시험 도구·JSON 요청·설치·서비스 연결·시험·측정은 미실행이다. 문서의 파일명과 실행 명령은 **구현 예정**이며 존재·성공을 뜻하지 않는다.

## 범위와 읽는 순서

**편집은 `develop/wonmin/` 안에서만 한다.** 루트·공통 docs·상대 폴더는 읽기 전용이다. 상대 코드를 복제하거나 본체·검색·백엔드를 대신 구현하지 않는다.

1. [TODO](Doc/TODO.md): 목적, 필수와 후순위를 읽는다.
2. [SPEC](Doc/SPEC.md): REL 요구, 노드 책임, 입출력, 처리표, 팀 시나리오의 기대를 읽는다.
3. [IMP-PLAN](Doc/IMP-PLAN.md): **P0의 파일 준비부터** 한 단계씩 구현하고 확인한다.
4. 기준 변경이 필요한 경우에만 [HANDOFF](Doc/HANDOFF.md)의 해당 제안을 검토 상대에게 전달한다. 기본안대로 하는 작업에는 새 협의가 필요 없다.

공통 기준은 [API 계약](../../docs/API-CONTRACT.md) C04·C05·C07, [데이터·DB](../../docs/DATA-AND-DB.md), [협업](../../docs/COORDINATION.md)이다. 상대 서비스가 없으면 같은 입출력의 Mock으로 진행하고 실제 연결 결과와 구별한다.

## 첫 작업과 제공할 결과

첫 작업은 SPEC의 TM-01~TM-10을 시나리오 파일로 옮길 준비다. [IMP-PLAN P0](Doc/IMP-PLAN.md#p0--계약과시험입력준비)의 예정 파일·순서를 따른다. 공통 14유형 원본은 기대값을 바꾸지 않고 보존한다. 키트가 준비되지 않았으면 팀 입력·기대 작성부터 진행하고 공통 시험은 미실행으로 남긴다.

| 담당 산출물 · 모두 구현 예정 | 목적 |
| --- | --- |
| `workflows/oke-handoff.json` | 티켓 생성·중복·알림·DLQ와 C04 응답 |
| `workflows/oke-errors.json` | Error Trigger 기반 예상 밖 실행 실패 수습 |
| `cases/common.json`, `cases/team.json`, `cases/handoff.json` | 공통 원본 보존, 팀 사례, 하위 연결 단독 시험 |
| `requests/demo-*.json`, `requests/bench-normal.json` | 시연·측정 입력 |
| `tools/flow.py`, `tools/check-evidence.py`, `tools/run-fresh.py` | 제공 키트 도구, 증거 대조, 새로운 요청의 반복 측정 |
| `runs/` 실제 보고서, `Doc/SUBMISSION-NOTES.md` | 실패·재시험·배포 커밋·측정과 제출 반영 자료 |

하위 폴더 안내: [workflows](workflows/README.md) · [cases](cases/README.md) · [requests](requests/README.md) · [runs](runs/README.md). 상세 절차는 IMP-PLAN 한 곳에서 관리한다.

## 실행 모드와 확인 책임

| 모드 | 티켓·알림·DLQ 대상 | 관측·주의 |
| --- | --- | --- |
| `SERVICE_MODE=practice` | data-api:8800의 공통 호환 API | fault/reset/ops가 **같은 data-api 인스턴스**를 보도록 확인한 뒤 공통 고장 시험 |
| `SERVICE_MODE=app` | backend:8000 내부 API → PostgreSQL app 테이블 | FastAPI 인증·저장·권한·중복·재시작 유지 별도 통합 시험. data-api ops 수치를 앱 결과로 쓰지 않음 |

직원·규정·FAQ·기존 티켓 조회는 공통 기준대로 data-api를 사용한다. 모드는 새 업무 저장 대상을 선택하며 같은 티켓을 두 저장소에 동시 생성하지 않는다. Docker 안 주소와 호스트 주소는 달라도 같은 인스턴스임을 확인한다. 자세한 대조 절차는 [SPEC REL-05](Doc/SPEC.md#rel-05--실행대상과관측일치)를 따른다.

명령은 모두 본인 절대경로에서 실행하도록 IMP-PLAN에 준비한다. 도구·파일이 생기기 전에는 실행하지 않는다. n8n JSON은 담당 에이전트가 check하고 게시·push·test·고장 주입·시연은 사람이 수행한다. VM 배포와 최종 GitHub 반영은 오현님이 맡는다.

## 변경이 필요할 때만 검토할 상대

| 연결 | 검토 상대 | 전달할 것 |
| --- | --- | --- |
| C04 | 다혁님 | handoff 입력·응답 변경, 본체 timeout·ticket/reason 매핑, errors 워크플로우 ID |
| C05 | 지혜님 | 내부 저장 API·인증·멱등성·DLQ·알림 중복·관측 변경 |
| C07 | 지혜님·오현님 | 모드·서비스 주소·포트·배포 설정 변경 |
| C08 | 해당 기능 담당 | 재현 입력, 기대/실제 JSON, 마스킹한 실행 근거, 재시험 조건 |
| C09 | 오현님 | 공통 변경 제안, 실제 보고서·통과/실패 수, 제출·시연 자료 |

HANDOFF의 WM-01~WM-04는 **미검토 제안**이다. 상대 응답·공통 반영·실제 연결은 각각 구분한다. 해당 미정 경계만 Mock/미판정으로 두고 입력 준비·기본 API 매핑·정상/중복 시험 개발을 계속한다.

## 참고

[주제](../../docs/TOPIC.md) · [팀 헌장](../../docs/TEAM-CHARTER.md) · [루트 규칙](../../AGENTS.md) · [본인 규칙](AGENTS.md) · [제출 취합](../ohyun/SUBMISSION.md). 공통 참고 링크는 [IMP-PLAN 공통 자료](Doc/IMP-PLAN.md#공통-자료)에 유지한다.
