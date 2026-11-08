# rag · RAG 구현·런타임 자산 제출본

기준 커밋 `ca94191`의 `develop/yubeen/`에서 다음 13개 파일을 원문 그대로 복사했다.

- `tools/rag_*.py` 9개: 계약·DB·평가·색인·적재·측정·전처리·검색·검증
- `tools/index_http.py`, `tools/search_http.py`
- `rag-permissions.json`, `requirements-runtime.txt`

`__pycache__`와 환경 파일은 취합하지 않았다. 개발 원본과 VM 실행 경로는 그대로 유지한다. 설계·운영·측정 근거는 [RAG 설계서](../docs/RAG-ARCHITECTURE.md)와 [개발 원본](../develop/yubeen/README.md)을 따른다.

이 폴더는 제출용 소스 사본이다. 일부 도구의 `__file__` 기준 상대 경로는 원본의 `tools/`, `cases/`, 전처리 자료 배치를 전제로 하므로 실제 평가·색인·검색 재현은 개발 원본의 실행 안내를 따른다. 이번 이관에서는 Python 컴파일 검사를 통과했으며 실제 DB·임베딩·HTTP 서비스 실행은 재검증하지 않았다.
