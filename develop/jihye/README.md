# 지혜님 · 로그인·업무 API·DB·실행 환경

**목표:** 화면·워크플로우가 같은 신원·저장 규칙과 실행 환경을 사용하게 한다. 작업 폴더는 develop/jihye. 현재 구현 전 설계다.

<img src="../../docs/images/planned/flow-backend.svg" width="680" alt="백엔드와 저장 연결 설계">

## 내가 만들 것

- 로그인·세션·첫 변경·관리자 계정 발급과 직원/관리자 권한 검사.
- 문의 선저장·support 호출·내 문의·관리자 티켓/알림 API.
- /tickets·/alerts·/dlq, 멱등·부분 실패·소유권.
- app/rag 마이그레이션·직원 seed·첫 관리자·pgvector·Compose·API 명세와 실행법.

## 지금 첫 작업 · P0-1

저장소 루트에서 cd develop/jihye 후 [IMP-PLAN P0-1](Doc/IMP-PLAN.md)의 pyproject.toml·app/main.py·config·health·공통 검증 타입을 만든다. DB/n8n 없이 골격·입력/오류 형식을 확인한다. 이어 P0-2 계약 모델, P0-3~5 DB 기반을 먼저 공유해 유빈님·원민님이 실제 연결을 시작하게 한다.

## 정해진 것과 내가 정할 것

| 구분 | 적용·결정 |
| --- | --- |
| 확정 | FastAPI·Pydantic, PostgreSQL app/rag·pgvector3072, 관리자 발급·쿠키, assignee는 IT 직원 employees.id |
| 담당자 결정 | 내부 코드 구조·의존성 버전·물리 마이그레이션. 목록 DTO·처리 중/충돌 응답 세부는 수언님/다혁님과 계약 확인, DB 사용 변경은 유빈님, 저장 ACK는 원민님과 확인 |
| 선택 고도화 | 추가 모니터링·세밀한 인증 고도화·추가 성능 최적화는 필수 뒤 |

## 바로 볼 예제

[FastAPI 앱](../../docs/references/qnaweb/src-be/app/main.py.example) · [모델](../../docs/references/qnaweb/src-be/app/models.py.example) · [Q&A 라우터](../../docs/references/qnaweb/src-be/app/routers/qna.py.example) · [Compose](../../docs/references/qnaweb/docker/compose/docker-compose.yml.example)

라우터·저장·컨테이너 구성을 참고한다. create_all·자동 샘플 시드 대신 Alembic·명시적 bootstrap, 10명/InfluxDB/JWT 예제 대신 우리 6명·app/rag·세션 규칙을 적용한다. [적용표](../../docs/references/README.md).

## 누구에게 받고 무엇을 넘기나

- 수언님에게 요청/응답 명세·실행 주소·오류 예시, 유빈님에게 rag DDL·권한·접속법, 원민님에게 저장 API·관측법을 먼저 넘긴다.
- 다혁님과 공통 요청/응답·시간 예산을 확인한다. 오현님에게 Compose·마이그레이션·seed·기동·회귀 절차와 실제 결과를 넘긴다.
- 완료 기준: 빈 환경에서 재현 가능한 실행, 권한 거절·같은 키 티켓1건·재시작 유지, 화면과 워크플로우의 실제 연결. 비밀값을 문서에 넣지 않는다.
- 보고: 변경 파일 / 확인 명령·입력 / 기대와 실제 / 미해결·다음 상대. 실제 API 명세는 구현된 OpenAPI와 맞춰 제공한다.

## 내 CLI 첫 요청

    내 README·AGENTS·공통 API/DB를 읽고 IMP-PLAN P0-1만 구현해.
    예제에서 참고할 구조와 우리 기준의 차이를 먼저 말해.
    develop/jihye 밖은 수정하지 말고 실제 확인 결과·다음 연결을 보고해.

상세: [TODO](Doc/TODO.md) · [SPEC](Doc/SPEC.md) · [IMP-PLAN](Doc/IMP-PLAN.md) · [마이그레이션](migrations/README.md) · [배포](deploy/README.md) · [HANDOFF](Doc/HANDOFF.md).
