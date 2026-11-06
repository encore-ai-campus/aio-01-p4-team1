# 팀 서비스 배포 구조와 반영 상태

작성 기준: 2026-11-06에 저장소 문서와 Git 이력에서 확인한 내용
기준 저장소: `origin/main` `5b7d597`, 작업 브랜치 병합 `8b18ff1`
VM 배포 기록: 공통 EXECUTION-RESULT 12·13절 및 DAY81 7교시 보고. 문서의 VM repo·서비스별 코드·workflow 버전과 현재 작업 브랜치를 구분한다.

## 팀 VM 접속 주소

| 대상 | 주소 | 확인 범위 |
| --- | --- | --- |
| 웹 로그인 | <https://aio-t1.isitsoft.kr/login> | 공개 응답과 사용자 제공 이준호 로그인·문의 화면 표본 확인. 전체 관리자 화면 흐름은 미완료 |
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
| 지혜님 FastAPI·DB | 인증·문의·C05·마이그레이션 구현이 main에 있다. 개인 seed/백업 도구와 후속 계획은 본인 브랜치에서 보존됐다. | 이전 FE/BE API 통합·WF-02b 결과가 보고됐다. 7교시 배포에서 backend/DB/RAG는 재배포하지 않았다. 본인 브랜치 최신 커밋의 VM 적용은 별도다. |
| 수언님 웹 | 시각 디자인 `840c5e6` 및 내 문의 변경이 main에 반영됐다. | 7교시 frontend image-code `bb3ef06` 배포·healthy 보고. 사용자 제공 문의 화면은 한 사례이며 전체 브라우저 회귀 완료는 아니다. |
| 다혁님 본체 | main에 `oke-support-15.json`과 제출본 `workflows/oke-support.json`, 오류 workflow 연결이 반영됐다. | VM repo `17007f1`, 본체 15번 published version `d0d6396d-08f4-4b8a-8514-4e8473a6203d`가 공통 보고에 명시됐다. 과거 13/14번 미확인 안내보다 최신 근거다. |
| 유빈님 검색·색인 | 검색·색인 workflow와 RAG 코드가 main에 있다. | 기존 8문서/33청크 유지 및 과거 직접 C03 검색 근거가 있다. 7교시 재색인·threshold 변경은 없었고 정상 본체 답변은 실패했다. index는 수동 대상이다. |
| 원민님 handoff·errors | 두 workflow 및 7교시 QA 원자료·도구가 main에 있다. | handoff/errors 활성 및 support의 Error Workflow 설정 연결이 보고됐다. 실제 Error Trigger 발화와 alert/DLQ 행 대조는 여전히 미확인이다. |

위 상태는 공통 문서에 기록된 실행 시점의 보고이며 이번 문서 정리에서 VM을 직접 조회하지 않았다. Git main `5b7d597`, VM repo `17007f1`, frontend image-code `bb3ef06`, n8n published version은 서로 다른 기준이다.

## 실제 통합 시험 범위와 한계

11월 6일 기록된 실제 웹/API QA에서 로그인·세션 흐름 일부, 직원 문의 저장과 재조회, 관리자 상태/답변 조회, 직원의 관리자 API 접근 거절(403)을 확인했다. 해당 요청은 FastAPI와 PostgreSQL 저장까지 이어졌다.

이전 API QA의 응답은 담당자 이관·sources=[]였다. 후속 WF-02b는 API 기반 관리자 처리·직원 재조회까지 통과했다고 보고됐다. 7교시 QA는 n8n 직접 호출 22회/21개 ID의 부분 결과이며 정상 WF-01 자동답변은 3회 모두 실패했다. 14개 티켓 응답 ID가 DB 각 1행과 일치했고 7개 무티켓 ID는 0행으로 대조됐다. 이 결과는 FE→FastAPI 문의 저장의 재시험이나 공식 common-14 전체 통과가 아니다.

사용자 제공 실제 화면/API 표본은 이준호/영업팀의 VPN 문의, T-2012 접수, route=담당자 이관, sources=[], agents=[triage], reason=low_confidence다. 이 요청의 활성 본체 버전과 C03 실행 여부를 7교시 보고로 추정하지 않는다. 관리자 화면 처리·직원 재조회는 이번 사용자 시험에서 아직 확인되지 않았다.

남은 범위는 정상 근거 자동답변·8초 기준, 전체 화면 회귀, C02/C03/C04/C05의 미확인 trace·장애복구·alert/DLQ, 실제 RAG 데이터 격리 복원 후 검색/권한·품질 측정과 공식 공통 평가다. 기존 확인 자료의 실행 시점과 직접 실행/보고 수신을 구분한다.

## 문서 상태 참고

최신 main에서 [WORKFLOW-DESIGN.md](../../../docs/WORKFLOW-DESIGN.md)의 배포 상태 설명이 갱신됐다. 이전 본 문서의 ‘구현 예정 표가 남아 있음’ 안내는 과거 대조 결과다. 실제 판정은 [VM-TEAM-TESTING.md](../../../docs/VM-TEAM-TESTING.md), [EXECUTION-RESULT.md](../../../docs/EXECUTION-RESULT.md), [DAY81](../../../daily/DAY81.md)의 날짜별 근거를 따른다. 계획·요약의 완료 문구보다 개별 실행 자료와 명시된 미검증 범위를 확인한다.

이 요약은 팀 공유를 위한 현황 정리다. VM에 배포하거나 n8n 워크플로우를 수정·활성화하는 작업은 수행하지 않았다.
