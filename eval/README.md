# eval · 평가 스크립트·케이스 제출본

기준 커밋 `ca94191`에서 다음 4개 자산을 원문 그대로 복사했다.

- `develop/yubeen/tools/rag_evaluate.py`: RAG 평가 집계
- `develop/yubeen/tests/test_evaluation.py`: 평가 로직 회귀 검사
- `develop/dahyeok/tools/retrieval_check.py`: 검색·조회 Mock 검사
- `develop/dahyeok/cases/support-retrieval.json`: 검색 평가 케이스

원본의 `tools/`, `cases/`, `workflows/` 상대 경로 참조는 보존했다. 추가 자료가 필요한 평가·테스트 실행은 [유빈님 개발 안내](../develop/yubeen/README.md)와 [다혁님 개발 안내](../develop/dahyeok/README.md)의 원본 배치에서 수행한다. 이번 이관에서는 Python 컴파일과 JSON 구문 검사를 통과했으며 평가를 재실행하거나 새 품질 수치를 생성하지 않았다.

평가 기준은 [EVALUATION-GUIDE](../docs/EVALUATION-GUIDE.md), 기존 결과와 측정 근거는 [EXECUTION-RESULT](../docs/EXECUTION-RESULT.md) 및 [runs/](../runs/)를 따른다.
