# 다혁님 · 문의 처리 자동화

직원 문의를 검사하고 분류해, 허용된 근거로 답하거나 보완 질문·IT팀 이관으로 마무리하는 `oke-support` 본체를 담당한다. 검색·저장·이관을 직접 중복 구현하지 않는다.

## 범위와 현재 상태

- 구현 시 소유 파일: `workflows/oke-support.json`, 본체 전용 요청·Mock·시험 자료, `Doc/`.
- 지금은 **작업 지시 문서만 보완한 상태**다. 워크플로우·요청 JSON·패키지는 아직 생성하지 않았으며 설치·check·push·test·서비스 연결은 미실행이다.
- 편집은 `develop/dahyeok/` 안에서만 한다. 이번 문서 정비의 편집 범위는 그 안의 Markdown뿐이다. 공통 docs·루트·다른 담당자 폴더는 읽기 전용이다.
- `oke-search`·`oke-index`는 유빈님, `oke-handoff`·`oke-errors`는 원민님, 신원·문의/티켓 저장·DB는 지혜님 소유다.

## 바로 시작하는 순서

저장소 전체를 받은 뒤 작업 위치는 저장소 기준 `develop/dahyeok`으로 고정한다. 명령마다 이 위치 또는 저장소 루트를 workdir로 지정한다.

1. [TODO](Doc/TODO.md): 목적과 필수/후순위를 읽는다.
2. [SPEC](Doc/SPEC.md): `SUP-*` 요구, 노드 순서, 프롬프트, 계약 예시와 예상 route를 읽는다. `WF-*`는 공통 시험 ID다.
3. [IMP-PLAN](Doc/IMP-PLAN.md): **P0-1부터 한 단계씩** 구현한다. 첫 결과는 Webhook→입력 검사→직원 확인→규칙 차단→응답의 JSON 골격과 로컬 요청 예시다. 이 문서 정비에서는 생성하지 않는다.
4. 단계별 실제 확인 결과를 기록한 뒤 다음 단계로 간다. 하위 서비스가 없으면 SPEC의 같은 계약으로 Mock을 만들고, 실제 연결 결과와 구분한다.

[API-CONTRACT](../../docs/API-CONTRACT.md)·[DATA-AND-DB](../../docs/DATA-AND-DB.md)의 기본안을 적용하는 데 사전 동의는 필요 없다. 미정 정책은 [HANDOFF](Doc/HANDOFF.md)에 제안으로 분리했다. 해당 부분만 확정 상태를 확인하고 나머지 구현은 진행한다.

## 변경할 때의 검토 상대

| 연결 | 검토 상대 | 변경 요청 대상 |
| --- | --- | --- |
| C02 FastAPI↔support | 지혜님 | 공통 필드·오류 코드, 신원 변환, attempt/context, 결과 재사용 API |
| C03 support↔search | 유빈님 | query/type/access_levels/top_k·evidence·장애 응답, 검색 시간 예산 |
| C04 support↔handoff | 원민님 | 이관 입력·ticket·중복·부분 실패·시간 예산 |
| C08 기능↔시험 | 원민님 | 공통 판정과 구현의 불일치, 팀 사례·장애·측정 절차 |
| C09 통합·공통 기준 | 오현님 | 위 변경의 공통 문서 반영, 제출 자료 취합 |

표는 매번 협의할 목록이 아니다. 기준 변경이나 실제 계약 불일치가 있을 때만 내 HANDOFF에 기존/제안/영향/재현을 적는다. 상대 확인·공통 반영·실제 연결은 각각 증거가 있어야 기록한다.

## 넘길 결과

완성 시 본체 JSON, 노드·Agent 역할/연결선, 실제 페이로드, 보완/재검색 한도, check 결과, Mock/실연결 구분과 실패 기록을 제공한다. 제출 자료는 구현 뒤 생성할 `Doc/SUBMISSION-NOTES.md`에 **반영 문서·절 / 실제 설계 / 측정·보고서 경로 / 남은 문제**로 정리한다. 현재 존재하는 파일이나 완료 결과로 취급하지 않는다.

루트 설계서와 시험 파일은 소유자가 반영한다. 검토와 최종 GitHub 반영은 상위 담당자가 한다. 설치·실행 명령은 구현 후 검증한 것만 이 README에 추가한다. n8n push·test는 사람이 수행한다.

## 기준·참고

[루트 AGENTS](../../AGENTS.md) · [내 AGENTS](AGENTS.md) · [주제](../../docs/TOPIC.md) · [팀 헌장](../../docs/TEAM-CHARTER.md) · [협업 절차](../../docs/COORDINATION.md) · [리드 제출 안내](../ohyun/SUBMISSION.md). 역할별 참고 링크는 [IMP-PLAN](Doc/IMP-PLAN.md)의 공통 자료에 유지한다.
