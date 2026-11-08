# 구현한 서비스

- [frontend/](frontend/) — 직원·관리자가 사용하는 Next.js 화면
- [backend/](backend/) — FastAPI 인증·권한·업무 API와 DB 마이그레이션
- [rag/](rag/) — 규정 색인·임베딩·권한별 검색 서비스
- [data-api/](data-api/) — 가상 직원·FAQ·기존 티켓·규정 조회 API

전체 서비스의 Compose와 배포 안내는 루트 [deploy/](../deploy/)에 있다. n8n 워크플로우는 [workflows/](../workflows/), 데이터 원본은 [data/](../data/)와 [knowledge/](../knowledge/), 검사는 [eval/](../eval/)을 사용한다.
