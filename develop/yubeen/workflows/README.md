# 유빈님 n8n 개발 결과물

이 폴더의 `oke-index.json`과 `oke-search.json`은 비활성 배포 준비본이다. 색인은 내부 Python 색인 HTTP 서비스, 검색은 내부 Python 검색 HTTP 서비스를 호출한다. n8n Credential과 서비스 URL은 실행 환경에서 연결한다. 로컬 Mock 색인 워크플로우는 `../tests/fixtures/oke-index-mock.json`에 보존한다. 실제 n8n import·push·test와 DB/VM 검증은 아직 수행하지 않았다.

개인 n8n에서 외부 서비스 없이 실행 계약을 확인할 때는 `../Doc/N8N-FAKE-HTTP-GUIDE.md`의 Fake HTTP 서버와 URL을 사용한다.
[자기 개발 계획](../Doc/IMP-PLAN.md) → [공통 계약](../../../docs/API-CONTRACT.md) → 한 단계 구현·check → 사람이 push·test 순서로 진행한다.
전체 경로·작업 디렉터리를 명령에 명시하고, 키는 Credential에만 둔다. 제출은 [리드의 취합 안내](../../ohyun/SUBMISSION.md)를 따른다.
