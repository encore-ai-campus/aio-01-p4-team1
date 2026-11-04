# 바로 참고할 예제

내 역할의 예제만 읽고, 개인 SPEC·공통 계약에 맞춰 필요한 구조를 가져온다. 아래 사본은 읽기용 .example이며 설치·게시·공통 시험 도구가 아니다. 인증 참조·예제 비밀값은 치환했고 원본 실행 데이터는 제외했다.

## 역할별 읽을 곳

| 담당 | 바로 볼 예제 | 재사용할 부분 | 우리 기준으로 바꿀 부분 |
| --- | --- | --- | --- |
| 수언님 | [로그인](qnaweb/src-fe/src/app/login/page.tsx.example), [질문](qnaweb/src-fe/src/app/qna/new/page.tsx.example), [내 문의](qnaweb/src-fe/src/app/qna/my/page.tsx.example), [관리자 티켓](qnaweb/src-fe/src/app/admin/tickets/page.tsx.example) | Next.js 페이지·폼·상태·목록·편집 UI | 샘플 빠른 로그인 제거, JWT 저장 대신 세션 쿠키, 우리 /api 경로·6명·첫 변경·실제 AI 답변 |
| 지혜님 | [앱 구성](qnaweb/src-be/app/main.py.example), [모델](qnaweb/src-be/app/models.py.example), [Q&A API](qnaweb/src-be/app/routers/qna.py.example), [Compose](qnaweb/docker/compose/docker-compose.yml.example) | 라우터 등록·모델/스키마/저장 분리·서비스 연결 | create_all/자동 시드 대신 Alembic·명시적 bootstrap, 관리자 발급·HttpOnly 세션·app/rag, InfluxDB 제외 |
| 다혁님 | [도구 연결](workflows/tools.json.example), [작성·검토 파이프라인](workflows/pipeline.json.example), [모듈 호출](workflows/module.json.example) | 조회 노드·역할 분리·JSON 파싱·분기·하위 호출 경계 | Agent3역할·Header Auth·공통 입출력, 기본 재작성0회, 하위 HTTP 웹훅 계약 |
| 유빈님 | [색인](workflows/index.json.example), [검색](workflows/search.json.example) | 목록→문서→청크·임베딩→근거 반환 흐름 | In-Memory를 rag 테이블·pgvector로 교체, 권한 WHERE·3072차원·정확 cosine·재색인 거래 |
| 원민님 | [티켓 처리](workflows/intake.json.example), [오류 알림](workflows/errors.json.example), [재처리](workflows/replay.json.example) | 키·HTTP 상태 분기·Error Trigger·실패 건 선택·성공 건 해제 | 공통 C04/C05·모드 어댑터·중복·DLQ·마스킹, 오류 예제의 알림만 있는 부분에 독립 DLQ 경로 |
| 오현님 | 위 예제의 적용표와 각 담당자 실제 인계 | 구현 범위·소유권·연결·검증 근거 확인 | 예제 존재와 구현/시험 완료를 구별, 공통 파일은 오현님이 반영 |

원본 qnaweb은 10명·관리자1명·InfluxDB·자동답변 빈 영역의 실습이다. 우리 서비스는 6명·IT관리자2명·PostgreSQL+pgvector·n8n 실제 응답이 기준이다. 예제의 샘플 계정·인증·저장 스키마를 그대로 운영안으로 쓰지 않는다.

## 사용 순서

1. 개인 README의 첫 P0 작업을 고른다.
2. 표에서 관련 예제 1~2개와 개인 SPEC의 해당 요구만 읽는다.
3. AI에게 재사용할 구조와 바꿀 부분을 함께 주고 자기 폴더 안에서 한 단계만 구현한다.
4. 확인한 파일·명령·입력/기대/실제·다음 연결을 보고한다. n8n 게시·시험은 담당자가 직접 확인한다.

예제의 import 대상·모델·데이터 API·Credential은 이 사본에 모두 포함돼 있지 않다. 파일명에서 .example을 지우고 그대로 배포하기보다 구조를 읽어 개인 프로젝트로 구현한다.

## 참고 사본 관리

- qnaweb: 웹서비스 실습의 페이지·서버·Compose에서 필요한 파일 8개를 선별했다. 로그인 기본 암호와 Compose 비밀값은 REPLACE_LOCAL_SECRET로 바꿨다.
- workflows: 67/69/70/71/76일차 reference에서 구조별 8개를 선별했다. active=false, pinData 제거, Credential 참조는 로컬 교체용이다.
- 80일차 flow.py·common.json은 이 폴더에 없다. 실제 배포 키트의 원본·버전을 확인하고 원민님 계획대로 준비한다.
- 참고 사본은 공통 관리 자료다. 일반 담당자는 읽고 자기 폴더에서 구현하며 공통 사본 수정은 오현님에게 요청한다.
- 원본 위치·사본 변경 내용은 아래 기록으로 관리한다. 외부 저장소를 열지 않아도 예제 내용을 읽을 수 있다.

<details>
<summary>원본 파일 기록</summary>

| 사본 | 원본 논리 경로 |
| --- | --- |
| tools.json.example | 67/reference/lab02-example-two-tools.json |
| pipeline.json.example | 69/reference/lab02-example2-pipeline.json |
| module.json.example | 70/reference/lab02-example2-kit-module.json |
| index.json.example | 71/reference/lab01-example2-index.json |
| search.json.example | 71/reference/lab01-example2-search.json |
| intake.json.example | 76/reference/lab01-example2-intake.json |
| errors.json.example | 76/reference/lab02-example2-error-handler.json |
| replay.json.example | 76/reference/lab03-example1-replay.json |

qnaweb 사본은 각 링크의 qnaweb/ 이후 경로와 원본 내부 경로가 같다. 사본은 학습 패턴 재사용을 위한 편집본이며 원본과 동일한 실행물을 주장하지 않는다.

</details>
