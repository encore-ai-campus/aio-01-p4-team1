# 오케퐁 사내 IT 헬프데스크

직원 6명의 사내 IT 문의에 규정의 근거로 답하고, 근거가 없거나 긴급한 문의는 IT팀 티켓·알림으로 이관한다.
웹 화면(Next.js) → FastAPI → n8n의 같은 문의 본체 → FastAPI·PostgreSQL 저장 구조다.
규정·FAQ·직원·기존 티켓은 수업 data-api를 활용하고, 실제 로그인 계정은 관리자가 발급한다.
업무 데이터는 PostgreSQL, RAG 문서 청크·임베딩은 같은 PostgreSQL의 pgvector에 저장하며 테이블을 분리한다. DB·검색 구현은 아직 준비 단계다.

## 각자 여기서 시작하기

저장소 전체를 clone하고 develop/ 아래 자기 이름 폴더로 이동한다. [개발 폴더 안내](develop/README.md)를 따른다. 각 README에서 TODO → SPEC → IMP-PLAN → 지정 단계 개발 → 직접 확인 → 커밋 순서로 진행한다.

| 담당자 | 역할 | 시작 문서 |
| --- | --- | --- |
| 오현님 | 팀장·통합·PR·배포·제출 | [develop/ohyun/README](develop/ohyun/README.md) |
| 수언님 | 프론트엔드 | [develop/sueon/README](develop/sueon/README.md) |
| 지혜님 | 백엔드·DB·공통 실행 설정 | [develop/jihye/README](develop/jihye/README.md) |
| 다혁님 | 문의 처리 자동화 | [develop/dahyeok/README](develop/dahyeok/README.md) |
| 유빈님 | RAG·지식 검색 | [develop/yubeen/README](develop/yubeen/README.md) |
| 원민님 | 안정성·이관·시험 | [develop/wonmin/README](develop/wonmin/README.md) |

```text
Aio-4pj-1team/
├── README.md · AGENTS.md · .env.example
├── docs/                       공통 기획·계약·필수 제출 문서
└── develop/
    ├── README.md               담당자별 시작 안내
    ├── ohyun/                  오현님 · 통합·배포·제출
    │   └── Doc/
    ├── sueon/                  수언님 · 프론트엔드
    │   └── Doc/
    ├── jihye/                  지혜님 · 백엔드·DB
    │   ├── Doc/
    │   ├── migrations/
    │   └── deploy/
    ├── dahyeok/                다혁님 · 문의 처리
    │   ├── Doc/
    │   └── workflows/
    ├── yubeen/                 유빈님 · RAG
    │   ├── Doc/
    │   └── workflows/
    └── wonmin/                 원민님 · 안정성·시험
        ├── Doc/
        ├── workflows/
        ├── cases/
        ├── requests/
        └── runs/
```

영문 폴더명은 ohyun·sueon·jihye·dahyeok·yubeen·wonmin이다. 각 이름 폴더에는 README와 역할별 AGENTS 규칙이 있다. 지금은 개발 문서·안내·제출 양식 단계이며 실행 코드·패키지·워크플로우·시험 보고서는 없다.
P0에서 담당자가 실행 뼈대를 만들고 설치·실행 명령을 자기 README에 적는다. 개발 문서 초안도 담당자가 검토·구체화한다.

## 협의·파일 수정 규칙

각 담당자는 자기 이름 폴더만 수정한다. 상대 파일은 해당 소유자에게, 공통 계약·제출 문서는 오현님에게 변경 요청한다. 자기 폴더의 Doc/WORK-GUIDE.md에 협의 상대·입출력·개발 순서가 있고 Doc/HANDOFF.md에 전달·검토 기록을 남긴다.

전체 연결 책임은 [COORDINATION](docs/COORDINATION.md)을 따른다. 아직 협의·코드 구현이 완료됐다는 뜻은 아니다.

## 팀 공통 기준

- [팀장 연결 기본안 v0](docs/BASELINE-v0.md): 개발에 적용할 JSON·서비스 기본값
- [제공 데이터와 DB 기본안](docs/DATA-AND-DB.md): 사용 데이터·PostgreSQL·pgvector 테이블 기준

- [주제·기능 범위](docs/TOPIC.md)
- [사람별 역할·파일 소유권](docs/ROLE-PLAN.md)
- [팀 헌장](docs/TEAM-CHARTER.md)
- [공통 API 계약](docs/API-CONTRACT.md)
- [개발 순서·담당자가 정할 것](docs/DEVELOPMENT-FLOW.md)
- [폴더별 안내·강사 자료](docs/WORKSPACE-GUIDE.md)
- [n8n 워크플로우 역할](docs/WORKFLOWS.md)

공통 계약을 기준으로 연결하고, 상대의 이름 폴더를 통째로 복사해 개발하지 않는다. 한 서비스의 구성요소이므로 통합 실행에는 다른 담당자의 서비스도 필요하다.
비밀값은 실제 .env·n8n Credential로 관리한다. 공개 회원가입은 없다. 텔레그램은 필수 기능·시험 완료 후 검토한다.

## 필수 제출물

[워크플로우 설계서](docs/WORKFLOW-DESIGN.md), [RAG 설계서](docs/RAG-ARCHITECTURE.md), [실행 결과서](docs/EXECUTION-RESULT.md)는 강사 양식에서 준비한 작성 틀이다.
주제·헌장·데일리 3장·n8n JSON·팀 시나리오·실제 시험 보고서도 필요하다.
개인 폴더의 개발 원본을 기준으로 삼고, 제출 직전 [develop/ohyun/제출 안내](develop/ohyun/SUBMISSION.md)에 따라 루트 workflows·cases·requests·runs로 취합한다.
