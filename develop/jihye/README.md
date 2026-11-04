# 지혜님 · 백엔드·DB·실행 환경

FastAPI에서 직원 신원·권한을 확인하고, 동일한 `oke-support`에 질문을 전달하며, 새 업무 기록과 RAG 저장 기반을 PostgreSQL에 준비한다. 팀장이 배포한 기준대로 바로 시작한다. 기준 적용에 상대의 재승인은 필요 없다.

현재 결과물은 **개발 작업 지시 문서**다. 아래 코드·설정·시험 파일은 구현 예정이며 설치·서버 실행·DB 적용·시험·배포를 완료한 상태가 아니다.

## 범위와 읽는 순서

편집 경계는 `develop/jihye/`다. FastAPI·Pydantic/OpenAPI·업무 저장·마이그레이션·배포 설정·본인 시험을 소유한다. DB 확장과 업무/RAG 스키마의 마이그레이션 파일은 지혜님만 수정한다. 다른 사람 소스·공통 docs·루트 설정은 읽고, 변경은 소유자에게 요청한다.

1. [TODO](Doc/TODO.md): 직원 6명에게 필요한 목적과 필수/후순위 범위를 읽는다.
2. [SPEC](Doc/SPEC.md): BE 요구 ID, 입력·응답 모델, API별 정상/실패 예시와 통과 기준을 읽는다.
3. [IMP-PLAN](Doc/IMP-PLAN.md): **P0-1부터** 한 단계씩 파일을 만들고 해당 확인을 수행한다.
4. 기준 변경이 필요할 때만 [HANDOFF](Doc/HANDOFF.md)에 기존/제안/영향/검토 상대를 기록한다. 제안은 확정 기준이 아니다.

명령은 본인 폴더 `develop/jihye`를 작업 디렉터리로 실행한다. 상대 서비스가 아직 없으면 같은 계약의 HTTP Mock으로 진행하고 실제 연결은 별도로 기록한다.

## 바로 시작할 첫 단계

IMP-PLAN P0-1에서 `pyproject.toml`, `app/main.py`, `app/core/config.py`, `app/api/errors.py`, `app/schemas/common.py`, `tests/test_contract_basics.py`를 만들 예정이다. 공통 환경변수 읽기, `/health/live`, 웹 오류 모델과 Pydantic 입력 오류의 HTTP 400 변환까지 작은 단위로 만든다. 외부 서비스를 호출하지 않는 시험으로 빈 질문·501자·정상 500자·잘못된 attempt를 먼저 확인한다. 다음 P0-2에서 요청/응답 모델 전체와 OpenAPI를 붙인다. 구체 명령과 기대값은 IMP-PLAN에 있다.

## 적용할 공통 기준

| 항목 | 기준 |
| --- | --- |
| 사용자·기능 | [TOPIC](../../docs/TOPIC.md): 공개 회원가입 없음, 첫 관리자 후 관리자 발급, 첫 비밀번호 변경 |
| API·인증·서비스 | [API-CONTRACT](../../docs/API-CONTRACT.md): C01/C02/C05/C06/C07, 세션·X-Team-Key·X-Api-Key 분리 |
| 업무·RAG DB | [DATA-AND-DB](../../docs/DATA-AND-DB.md): app/rag, bigint identity, pgvector 3072차원, 정확 cosine 검색 |
| 소유권·통합 | [TEAM-CHARTER](../../docs/TEAM-CHARTER.md) · [COORDINATION](../../docs/COORDINATION.md) · [루트 AGENTS](../../AGENTS.md) · [본인 AGENTS](AGENTS.md) |

포트·테이블·모델·차원을 다시 선정하지 않는다. 전체 배포·환경값 등록·기본 브랜치 반영은 오현님이 맡는다.

## 변경할 때의 검토 상대

| 연결 | 상대 | 변경 검토 내용 |
| --- | --- | --- |
| C01 | 수언님, 공통 반영 오현님 | 요청/응답 필드, 쿠키·만료·첫 변경 제한·관리자 화면 영향 |
| C02 | 다혁님, 공통 반영 오현님 | 신원 변환·support 응답 보존·시간 제한·장애 응답 |
| C05 | 원민님, 공통 반영 오현님 | 내부 저장 API·멱등·DLQ·practice/app 관측 대상 |
| C06 | 유빈님, 공통 반영 오현님 | 확장·테이블·권한·색인/검색 접속·모델 변경 |
| C07 | 오현님, 영향받는 담당자 | 서비스명·포트·build context·볼륨·healthcheck·실행 명령 |

이 표는 개발 전 승인 목록이 아니다. 기존 기준에 없는 정책 제안은 HANDOFF JH-H01~H06에 있으며 상대 확인·공통 반영·실제 연결은 모두 미확인이다. 다른 담당자에게 메시지를 보낸 상태도 아니다.

## 넘길 결과와 기록

수언님에게 OpenAPI·API별 예시·쿠키 조건을, 다혁님에게 세션→직원 이름 변환과 support 호출 예시를, 원민님에게 저장 API·동시 중복/장애 증거를, 유빈님에게 마이그레이션 head·테이블/접속 권한·벡터 차원 확인 결과를 넘긴다. 오현님에게 실행 설정과 새 환경 생성·재시작·복구 절차를 넘긴다.

[마이그레이션 안내](migrations/README.md)와 [배포 안내](deploy/README.md)는 해당 작업의 상세 절차다. 기본 시작 안내를 복제한 파일은 만들지 않는다. 실제 결과는 구현 뒤 `Doc/SUBMISSION-NOTES.md`에 요구/계약 ID·실행 위치·명령·종료 상태·Mock/실연결·보고서 경로·남은 문제를 적어 [제출 취합](../ohyun/SUBMISSION.md)으로 전달한다. 지금 그 결과 파일을 만들거나 PASS를 채우지 않는다.

## 참고

[전체 아키텍처](../../docs/ARCHITECTURE.md) · [공통 API](../../docs/API-CONTRACT.md) · [데이터·DB 기준](../../docs/DATA-AND-DB.md) · [평가·시나리오 가이드](../../docs/EVALUATION-GUIDE.md).
