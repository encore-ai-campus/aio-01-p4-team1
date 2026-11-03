# 오케퐁 사내 IT 헬프데스크

직원 6명의 사내 IT 문의에 규정의 근거로 답하고, 근거가 없거나 긴급한 문의는 IT팀 티켓·알림으로 이관한다.
웹 화면(Next.js) → FastAPI → n8n의 같은 문의 본체 → FastAPI·PostgreSQL 저장 구조다.
규정·FAQ·직원·기존 티켓은 수업 data-api를 활용하고, 실제 로그인 계정은 관리자가 발급한다.

## 각자 여기서 시작하기

저장소 전체를 clone하고 자기 이름 폴더로 이동한다. 각 README에서 TODO → SPEC → IMP-PLAN → 지정 단계 개발 → 직접 확인 → 커밋 순서로 진행한다.

| 담당자 | 역할 | 시작 문서 |
| --- | --- | --- |
| 오현 | 팀장·통합·PR·배포·제출 | [hyun/README](hyun/README.md) |
| 이수언 | 프론트엔드 | [sueon/README](sueon/README.md) |
| 박지혜 | 백엔드·DB·공통 실행 설정 | [jihye/README](jihye/README.md) |
| 임다혁 | 문의 처리 자동화 | [dahyeok/README](dahyeok/README.md) |
| 신유빈 | RAG·지식 검색 | [yubin/README](yubin/README.md) |
| 이원민 | 안정성·이관·시험 | [wonmin/README](wonmin/README.md) |

```text
Aio-4pj-1team/
├── README.md · AGENTS.md · .env.example
├── docs/                     공통 기획·API 계약·필수 제출 문서
├── hyun/                     통합·마일스톤·배포·제출 취합
│   └── Doc/                  TODO · SPEC · IMP-PLAN
├── sueon/                   Next.js 프로젝트 루트 (코드 구현 예정)
│   └── Doc/
├── jihye/                   FastAPI 프로젝트 루트 (코드 구현 예정)
│   ├── Doc/
│   ├── migrations/
│   └── deploy/
├── dahyeok/
│   ├── Doc/
│   └── workflows/            oke-support.json 구현 예정
├── yubin/
│   ├── Doc/
│   └── workflows/            oke-index.json · oke-search.json 구현 예정
└── wonmin/
    ├── Doc/
    ├── workflows/            oke-handoff.json · oke-errors.json 구현 예정
    ├── cases/
    ├── requests/
    └── runs/
```

폴더 이름은 성을 뺀 이름의 영문 표기다. 각 이름 폴더에는 README와 역할별 AGENTS 규칙이 있다. 지금은 개발 문서·안내·제출 양식 단계이며 실행 코드·패키지·워크플로우·시험 보고서는 없다.
P0에서 담당자가 실행 뼈대를 만들고 설치·실행 명령을 자기 README에 적는다. 개발 문서 초안도 담당자가 검토·구체화한다.

## 팀 공통 기준

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
개인 폴더의 개발 원본을 기준으로 삼고, 제출 직전 [hyun/제출 안내](hyun/SUBMISSION.md)에 따라 루트 workflows·cases·requests·runs로 취합한다.
