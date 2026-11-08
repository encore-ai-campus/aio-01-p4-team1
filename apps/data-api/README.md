# 제공 데이터 API

`server.py`가 루트 `data/`의 가상 직원·FAQ·기존 티켓·스키마, `knowledge/`의 규정, `prompts/`의 제공 프롬프트를 읽는다. 코드와 데이터 원본을 분리하며 사본을 이 폴더에 두지 않는다.

통합 실행은 [배포 안내](../../deploy/README.md)를 따른다. `compose.yml`은 이 서비스만 실행하는 구성이다. 연습 모드의 생성 티켓·장애 설정 등은 메모리에 저장되며 실제 업무 기록은 FastAPI와 PostgreSQL이 담당한다.
