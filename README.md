# 오케퐁 · 사내 IT 헬프데스크

직원이 질문하면 사내 규정 근거로 안내하고, 자동 답변이 어려운 문의는 IT팀 티켓으로 접수해 처리 결과까지 확인하는 서비스다.

엔코아 4차 단위 프로젝트 **1팀 · 오케퐁**의 결과물이다. 제공된 가상 직원 6명·규정 8종·FAQ 6종·기존 티켓 4건을 바탕으로 직원 문의부터 관리자 처리 결과 확인까지 연결한다.

## 주요 기능과 화면

| 사용자 | 주요 기능 |
| --- | --- |
| 직원 | 로그인, IT 문의, 규정 근거 확인, 보완 질문 응답, 내 문의·티켓 처리 결과 조회 |
| IT팀 관리자 | 이관 티켓·긴급 알림 확인, 담당자·처리 상태·답변 변경, 직원 계정 발급·관리 |

공개 회원가입은 없으며 관리자가 계정을 발급한다. 화면은 FastAPI만 호출하고, 신원과 권한은 서버 세션으로 확인한다.

**실제 화면 캡처: 준비 예정.** 직원의 질문·답변·근거 화면과 관리자의 티켓·처리 화면을 촬영해 `docs/images/`에 추가한 뒤 이 절에 연결한다. 직원이 처리 결과를 다시 확인하는 화면도 가능하면 포함한다. 개인정보·키·연락처를 가리고, 관련 실행 기록과 같은 결과인지 확인한다. 현재 [예상 화면](docs/PREVIEW.md)과 `docs/images/planned/`는 설계 자료이며 실제 실행 증거가 아니다.

## 시스템 구성

```text
직원·관리자 브라우저
  → Next.js 화면 및 /api 프록시
  → FastAPI: 세션 인증·권한 검사·문의 및 업무 데이터 저장
  → n8n oke-support: 분류 → 검색 → 답변 생성·검증 → 응답 또는 이관
      ├─ oke-search → RAG 검색 서비스 → PostgreSQL + pgvector
      ├─ oke-handoff → FastAPI 내부 API → 티켓·알림·DLQ 저장
      └─ oke-errors → 예상 밖 실행 오류 처리

규정 원문 → 수동 색인(oke-index / RAG 색인 서비스) → PostgreSQL + pgvector
관리자 처리 → 업무 DB 저장 → 직원이 내 문의에서 재조회
```

LLM은 분류(triage)·답변 작성(writer)·검증(verifier)을 맡는다. 문서 권한은 검색 전에 적용하며, 업무 기록과 RAG 문서·벡터는 PostgreSQL의 별도 스키마에 저장한다. 상세 구성은 [아키텍처](docs/ARCHITECTURE.md), [워크플로우 설계](docs/WORKFLOW-DESIGN.md), [RAG 설계](docs/RAG-ARCHITECTURE.md)를 따른다.

## 팀원과 역할

| 팀원 | 담당 | 주요 구현 경로 |
| --- | --- | --- |
| 권오현 · 팀장 | 기획·공통 계약·통합·배포·제출 관리 | `deploy/`, 공통 문서 |
| 이수언 | 직원·관리자 프론트엔드·발표자료 준비 | `frontend/` |
| 박지혜 | FastAPI·인증·권한·업무 DB | `backend/` |
| 임다혁 | 문의 분류·보완 질문·답변 생성·검증·발표 | `workflows/oke-support.json` |
| 신유빈 | 규정 색인·임베딩·권한별 검색 | `rag/`, `workflows/oke-index.json`, `workflows/oke-search.json` |
| 이원민 | 이관·오류 처리·멱등성·시험 및 결과 집계 | `workflows/oke-handoff.json`, `workflows/oke-errors.json`, `cases/`, `requests/`, `runs/` |

협업 기준과 문서 책임은 [팀 헌장](docs/TEAM-CHARTER.md)을 따른다.

## 실행 방법

### 기존 팀 VM 이용

직원·관리자 화면은 <https://aio-t1.isitsoft.kr/login>, API 문서는 <https://aio-t1.isitsoft.kr/docs>다. 계정과 비밀번호는 팀장이 비공개로 인계한다. 직원과 관리자 세션을 별도 브라우저 창으로 구분해 로그인하고, 직원 문의 → 관리자 처리 → 직원 재조회 순서로 확인한다.

접속 주소는 [팀 VM 안내](docs/VM-TEAM-TESTING.md)에 기록된 값이며, 이 README 수정에서 현재 가용성을 재확인하지 않았다. 기존 VM 재배포는 [VM 배포 안내](deploy/README.md)를 따르며 새 로컬 환경 초기화와 구분한다.

### 새 로컬 환경 실행

준비물은 Git 체크아웃, Python 3, 실행 중인 Docker Engine/Desktop과 Docker Compose, 실제 LLM·임베딩 호출에 사용할 OpenAI API 키다. 로컬 절차의 기존 검증 환경은 Apple Silicon Mac이다. 비공개 설정은 로컬에서 생성하며 저장소에 커밋하지 않는다.

1. 저장소 루트에서 다음 초기화 명령을 실행한다.

   ```sh
   cd deploy
   python3 local/setup.py init
   ```

2. [로컬 실행 안내의 Fresh setup](deploy/LOCAL-MAC.md#fresh-setup)에 따라 OpenAI 키 설정, Compose 검증, TLS 초기화, 이미지 빌드, DB 마이그레이션·권한·직원 초기 적재·첫 관리자 생성을 순서대로 수행한다.
3. 같은 안내에 따라 서비스를 기동하고 `python3 local/bootstrap_n8n.py`로 로컬 Credential을 연결해 워크플로우를 등록한다. 초기화 명령만으로 서비스가 기동되지는 않는다.
4. [실제 색인 절차](deploy/LOCAL-MAC.md#start-stop-and-recover)에 따라 승인 규정 8종을 로컬 DB에 색인한다. 실제 임베딩·답변 생성에는 API 비용이 발생한다.
5. <http://localhost:3001/login>에 접속한다. 생성된 관리자 비밀번호는 로컬 비공개 인계 파일에서 확인하고 첫 로그인 시 변경한 뒤 직원 계정을 발급한다. 기존 로컬 검증은 첫 비밀번호 변경 후 전체 화면 흐름까지 확인한 결과가 아니다.

서비스 기동·중지·로그 확인 명령과 환경 파일 위치는 위 로컬 안내를 따른다. 구현·입력 데이터는 루트 폴더를 사용하며, 패키지·이미지 설치 및 비공개 인증 설정은 별도로 필요하다. 폴더 정리는 새 환경의 전체 동작이나 VM 재배포 완료를 뜻하지 않는다.

## 웹훅과 요청 계약

n8n 웹훅 origin은 팀 VM 안내 기준 `https://aio-t1.isitsoft.kr:5678`, 격리 Mac 로컬은 `http://localhost:15679`다. 아래 경로는 이 origin에 붙인다. 브라우저 화면은 웹훅을 직접 호출하지 않고 FastAPI의 `POST /api/ask`를 사용한다.

| 메서드·경로 | 용도 | 입력 핵심 필드 |
| --- | --- | --- |
| `POST /webhook/oke-support` | 문의 분류·답변·보완·이관 | `request_id`, `user`, `question`; 선택 `attempt`, `context`, `channel` |
| `POST /webhook/oke-search` | 내부 권한별 근거 검색 | `request_id`, `query`, `type`, `access_levels`, `top_k` |
| `POST /webhook/oke-handoff` | 내부 티켓·알림 이관 | `request_id`, `requester`, `title`, `category`, `priority`, `reason` |

웹훅은 `X-Team-Key` 헤더로 인증하며 각 용도의 키는 비공개로 인계한다. 실제 값은 요청 파일·README·로그에 넣지 않는다. `oke-index`는 수동 색인용이고 `oke-errors`는 Error Trigger용이므로 공개 문의 웹훅이 아니다.

문의 요청 예시([원본](requests/demo-normal.json)):

```json
{
  "request_id": "wm-demo-normal",
  "user": "박서연",
  "question": "Windows VPN 연결 오류 809가 나요. 점검 절차를 알려주세요.",
  "attempt": 1
}
```

응답에서 `route`, `answer`, `sources`, `ticket`을 확인한다. 독립 시험마다 새 `request_id`를 사용하고 멱등성 시험에서만 같은 ID를 재사용한다. 요청·응답의 전체 필드와 신원·권한 기준은 [API 계약](docs/API-CONTRACT.md)을 따른다.

## 팀 VM 시연 순서

시연 시작 전 공식 키트의 `doctor`에서 `ready` 상태를 확인하고, `fault all ok`·`llm up`으로 기본 상태를 준비한다. 이 표현은 공식 제출 안내의 점검 항목이며, 실행 도구의 실제 호출법과 시험 대상은 발표 전 확인해야 한다.

| 순서 | 입력·조건 | 확인할 결과 |
| --- | --- | --- |
| 1. 정상 | [VPN 정상 질문](requests/demo-normal.json), 검색·LLM 정상 | 자동 답변, 규정 출처, 응답 시간 |
| 2. 보완 질문 | [모호한 질문](requests/demo-clarify.json) | 보완 질문 반환; [attempt=3 입력](requests/clarify-3.json)에서는 한도 도달 이관 |
| 3. 장애 | 격리된 연습 모드에서 티켓 장애 조건을 설정하고 [이관 요청](requests/demo-handoff.json) 전송 | WF-04 기준 안전 이관 응답, `ticket=null`, `reason=tickets_down`, DLQ·알림 저장 및 정상 복구 |
| 4. 이관·로그 | 장애 복구 후 새 ID로 [이관 요청](requests/demo-handoff.json) 전송 | 티켓 발급·실행 기록 확인 → 관리자 상태·답변 저장 → 직원 내 문의에서 재조회 |

장애 조건과 관측·복구 대상은 [평가 가이드](docs/EVALUATION-GUIDE.md)의 WF-04를 따른다. `practice`의 data-api 장애 설정을 `app`의 업무 DB 장애로 해석하지 않는다. 장애용 요청 JSON 자체가 장애를 발생시키지는 않는다. 특히 `demo-failure.json`은 식당 앱 문의일 뿐이므로 그 파일 호출만으로 장애 시험을 수행했다고 기록하지 않는다. 격리된 장애 시험 구성과 위 시연 전체의 재현은 발표 전 확인할 항목이다.

## 검증 결과와 공식 시험 재현 상태

기존 실서버 기록은 2026-11-07 당시의 버전과 환경에 대한 증거다. 이번 README 수정은 서비스 재시험이 아니다.

| 검증 범위 | 기존 기록 위치 |
| --- | --- |
| 세션 인증·직원/관리자 권한·문의 DB 저장 | [백엔드·DB 기록](runs/be-db-integration-20261107.json) |
| RAG 색인·차원·권한별 검색 | [RAG 기록](runs/rag-search-eval-20261107.json) |
| 정상·보완·한도 이관·무근거 문의 처리 | [support v18 기록](runs/support-v18-integration-20261107.json) |
| 이관 복구 후 티켓·알림 중복 방지 | [멱등성 재시험 기록](runs/live-integration-qa-20261107T113546Z.json) |

판정·측정값·실패 원인·남은 위험은 [실행 결과서](docs/EXECUTION-RESULT.md), 전체 기록은 [runs 인덱스](runs/README.md)를 따른다. 실행 결과서에 기록된 정상 답변 첫 호출의 8초 초과와 이후 재측정은 함께 평가해야 한다. Mock·합성 fixture 검사는 실제 검색 품질이나 공식 시험 통과로 집계하지 않는다.

공식 `08-SUBMISSION.md`는 강사가 README를 따라 아래 순서로 실행해 같은 결과를 얻을 것을 요구한다.

```sh
flow.py push workflows/*.json
flow.py test cases/team.json
```

**현재 이 공식 재현 요구의 충족은 확인되지 않았다.** 기존 기록에는 공식 러너의 `X-Team-Key` 헤더 지원 제약이 있으며, `cases/team.json`도 원본 러너 형식 대조가 필요하다고 명시한다. 위 명령은 공식 요구 절차를 제시한 것으로, 현재 저장소에서 실행 성공을 검증한 명령이 아니다. 게시 전에는 [워크플로우 안내](workflows/README.md)에 따라 실행 환경 Credential 매핑도 필요하다. 인증 지원·suite 형식·등록 절차를 확인하고 실제 실행 보고서를 `runs/`에 남겨야 하며, 직접 HTTP 시험을 공식 러너 통과로 대체하지 않는다.

저장소에서 실행하는 정적·단위·Mock 검사는 [SUBMISSION.md](SUBMISSION.md)에 별도로 정리돼 있다.

## 제출·발표 준비 일정

아래는 2026-11-08 기준 준비 계획이며 완료 기록이 아니다. 공식 마감은 **82일차 2026-11-09(월) 14:50, 기본 브랜치의 마지막 커밋 시각**이다. 마감 후에는 수정하지 않고 마감 시점 저장소로 발표한다.

| 항목 | 11/08(일) · 사전 준비 | 11/09(월) · 82일차 |
| --- | --- | --- |
| README·산출물 | 내용 보완, 구현·증거와 대조 | 최종 확인 후 14:50 전 제출 확정 |
| 공식 시험 재현 | 러너 인증·suite 형식 제약 확인·해결 및 재현 시험 | 필요 시 최종 회귀 확인, 미해결 사항은 그대로 명시 |
| 실제 화면 | 직원·관리자 화면 촬영·마스킹·반영 | 변경 화면이 있을 때 갱신 |
| 보안 검사 | `tscan scan .` 사전 실행·발견 사항 수정 | 최종 변경 반영 후 제출 직전 재검사 |
| 시연 | 입력·장애 격리·복구 절차 확인, 대본·자료 준비 | 시작 전 `doctor`의 `ready`·`fault all ok`·`llm up` 확인 |
| 리허설·발표 | 순서대로 사전 연습 | 1팀 리허설 3교시, 최종 발표 6교시: 발표·시연 20분 + 질의 5분 |

제출 전 `tscan scan .`의 기준은 키·실제 연락처 0건이다. 가상 데이터 연락처도 문서·로그에서는 가린다. 저장소는 비공개로 운영하고 강사를 초대해야 하며, 실제 설정 확인은 별도 필요하다. 필수 세 산출물·헌장·데일리 3장·워크플로우·팀 시나리오·실행 기록을 최종 확인한다. 공식 KSM-REQ §6의 15항목 체크리스트 위치는 [실행 결과서 §18](docs/EXECUTION-RESULT.md#18-ksm-req-6-제출-전-체크리스트-원문-15항목)이며 체크 상태는 실제 근거와 대조해야 한다.

## 저장소와 상세 문서

| 경로 | 내용 |
| --- | --- |
| [frontend/](frontend/README.md) | Next.js 직원·관리자 웹 화면 |
| [backend/](backend/README.md) | FastAPI 인증·업무 API, DB 마이그레이션·검사 |
| [rag/](rag/README.md) | 색인·검색 HTTP 서비스, 권한 매핑·설정 |
| [data-api/](data-api/server.py), [data/](data/README.md) | 제공 API와 가상 초기 데이터·스키마 |
| [knowledge/](knowledge/README.md), [prompts/](prompts/README.md) | 규정 8종과 프롬프트 3종 |
| [workflows/](workflows/README.md) | n8n 워크플로우 5종 |
| [cases/](cases/README.md), [requests/](requests/README.md), [eval/](eval/README.md) | 시나리오·요청·오프라인 평가 |
| [runs/](runs/README.md) | 기존 시험·측정 영수증 |
| [deploy/](deploy/README.md) | VM Compose와 격리 로컬 환경 |
| [docs/](docs/README.md), [daily/](daily/README.md) | 계약·설계·실행 결과·일일 기록 |

필수 산출물: [워크플로우 설계](docs/WORKFLOW-DESIGN.md) · [RAG 설계](docs/RAG-ARCHITECTURE.md) · [실행 결과](docs/EXECUTION-RESULT.md). [주제](docs/TOPIC.md) · [팀 헌장](docs/TEAM-CHARTER.md) · [API 계약](docs/API-CONTRACT.md) · [DB 기준](docs/DATA-AND-DB.md)도 함께 참고한다.

개발 당시 경로가 나오는 과거 일일 기록·실행 기록은 당시 이력이다. 현재 실행은 위 루트 폴더와 각 실행 안내를 따른다.
