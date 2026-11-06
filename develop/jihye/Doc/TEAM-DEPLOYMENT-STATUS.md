# 팀 서비스 배포 구조와 반영 상태

작성 기준: 2026-11-06에 저장소 문서와 Git 이력에서 확인한 내용  
기준 저장소: `origin/main` `deb9c6b`  
VM 배포 기록: `docs/VM-TEAM-TESTING.md`의 2026-11-06 11:55 KST 기록

## 팀 VM 접속 주소

| 대상 | 주소 | 확인 범위 |
| --- | --- | --- |
| 웹 로그인 | <https://aio-t1.isitsoft.kr/login> | 로그인 페이지 응답 확인. 화면의 브라우저 시각·클릭 검증은 별도 미실행 |
| FastAPI Swagger | <https://aio-t1.isitsoft.kr/docs> | Swagger UI 응답 확인. 공개 UI가 열린다는 사실과 인증이 필요한 API 실행은 구분 |
| FastAPI OpenAPI | <https://aio-t1.isitsoft.kr/openapi.json> | OpenAPI JSON 응답 확인 |
| n8n | <https://aio-t1.isitsoft.kr:5678/> | 기존 VM n8n UI. Owner: `team1@test.com` |

비밀번호, API 키, n8n credential 값은 이 문서에 포함하지 않는다.

## 배포 단위와 요청 흐름

```text
직원 브라우저
  → Next.js 웹 컨테이너
  → FastAPI backend 컨테이너
  → n8n의 oke-support 워크플로우
       ├→ oke-search 워크플로우 → rag-search Python 컨테이너 → PostgreSQL
       └→ oke-handoff 워크플로우 → FastAPI 저장 API → PostgreSQL

n8n 오류 발생 → oke-errors 워크플로우
수동 색인 요청 → oke-index 워크플로우 / rag-index 작업 컨테이너
```

- **웹과 FastAPI**는 별도 컨테이너로 배포한다. 웹의 `/api` 요청은 FastAPI로 전달된다. FastAPI는 인증·세션과 문의·티켓 저장 API를 제공한다.
- **oke-support, oke-search, oke-handoff, oke-errors**는 각각 독립된 n8n 워크플로우다. 별도 애플리케이션 컨테이너가 아니라 같은 n8n 인스턴스 안에서 webhook 또는 오류 트리거로 실행된다.
- **rag-search**는 n8n 워크플로우와 별개인 Python HTTP 서비스 컨테이너다. n8n의 `oke-search`가 내부 네트워크로 이 서비스를 호출한다.
- **PostgreSQL**은 별도 컨테이너다. `rag-index`는 상시 기동 서비스가 아니라 `indexing` profile의 수동 작업 대상이다.
- **oke-errors**는 오류 처리 워크플로우다. 일반 요청 처리 경로와 별도이며, 모든 요청이 이를 거치는 것은 아니다.

## 개인 구현의 main 반영 및 VM 상태

`main` 반영, VM 배포, 실제 기능 확인은 서로 다른 상태다.

| 담당 영역 | main 반영 상태 | VM에서 확인된 상태 |
| --- | --- | --- |
| 지혜님 FastAPI·DB | 백엔드 API, 인증·세션, C02/C05 저장 구현과 DB 마이그레이션이 `main`에 반영되어 있다. | VM은 backend/frontend 코드 기준 `3ff836a`로 배포되어 둘 다 healthy로 기록됐다. 최신 `origin/main`은 `deb9c6b`이며, `3ff836a` 이후 커밋은 QA 문서 기록이다. |
| 수언님 웹 | 웹 구현과 FastAPI 연결이 `main`에 반영되어 있다. | 같은 VM 배포에서 frontend healthy 및 API 기반의 로그인·문의·관리자 권한 흐름 일부가 확인됐다. 브라우저 화면의 시각·클릭 검증은 미실행이다. |
| 다혁님 본체 | `develop/dahyeok/workflows/oke-support-13.json`과 `oke-support.json`이 `main`에 있다. `oke-support-14.json`은 `main`에 없다. | VM snapshot에는 `oke-support`가 active로 기록됐지만, active workflow의 JSON 개정판이 13인지 14인지는 해당 snapshot에서 확인되지 않는다. 따라서 14가 VM에 배포됐다고 단정하지 않는다. |
| 유빈님 검색·색인 | `oke-search.json`, `oke-index.json` 및 RAG 구현이 `main`에 있다. | VM snapshot에서 `oke-search` active, `rag-search` healthy, `oke-index` inactive/manual로 기록됐다. 이전 실행에서 C03 evidence 3개 응답을 확인했으나, 11월 6일 최신 웹 QA는 `sources=[]`로 끝나 정상 RAG 자동답변 성공을 확인한 것은 아니다. |
| 원민님 handoff·errors | `oke-handoff.json`, `oke-errors.json`이 `main`에 있다. | VM snapshot에서 두 워크플로우가 active로 기록됐다. 이전 VM 실행에서 handoff 신규 저장과 동일 요청 중복 응답을 확인했다. 11월 6일 최신 웹 QA는 alert/DLQ 관계와 errors 복구 경로를 재검증하지 않았다. |

VM 상태 근거는 2026-11-06 11:55 KST 기록이다. n8n의 active 상태는 워크플로우가 활성화됐다는 뜻이며, Git의 특정 커밋이나 파일 버전과 일치한다는 뜻은 아니다.

## 실제 통합 시험 범위와 한계

11월 6일 기록된 실제 웹/API QA에서 로그인·세션 흐름 일부, 직원 문의 저장과 재조회, 관리자 상태/답변 조회, 직원의 관리자 API 접근 거절(403)을 확인했다. 해당 요청은 FastAPI와 PostgreSQL 저장까지 이어졌다.

같은 QA의 본체 응답은 `담당자 이관`이었고 `sources=[]`였다. 따라서 이 결과를 C03 검색 근거가 붙은 정상 자동답변 성공으로 해석하지 않는다. 다음 항목도 그 QA에서 확인되지 않았다.

- 브라우저 화면의 시각·클릭 검증
- 정상 자동답변 및 8초 기준
- 최신 요청에서의 RAG evidence 검색
- 같은 request ID 중복 요청
- alert/DLQ 관계와 오류 복구 경로
- 공식 common-14 전체 시나리오

이전 실행에서 확인된 C03 검색 및 C04 중복 저장 결과는 해당 실행 시점의 결과다. 최신 전체 통합 검증 결과로 합산하지 않는다.

## 문서 상태 참고

공통 [WORKFLOW-DESIGN.md](../../../docs/WORKFLOW-DESIGN.md)는 상단에서 워크플로우 구현·게시 및 일부 확인을 설명하지만, 아래 담당별 파일 표에는 같은 워크플로우가 `구현 예정`으로 남아 있다. 문서 내용이 서로 일치하지 않으므로 VM 실행 상태는 [VM-TEAM-TESTING.md](../../../docs/VM-TEAM-TESTING.md)와 시점별 [EXECUTION-RESULT.md](../../../docs/EXECUTION-RESULT.md)를 기준으로 구분해 읽는다.

이 요약은 팀 공유를 위한 현황 정리다. VM에 배포하거나 n8n 워크플로우를 수정·활성화하는 작업은 수행하지 않았다.
