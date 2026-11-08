# eval · 평가·회귀·실서버 검사

실제 팀 VM의 API·웹훅·DB 연결 재검사는 [실서버 검사 안내](LIVE-CHECKS.md)를 따른다. 아래는 오프라인 검사다.

저장소 루트에서 실행한다.

```sh
python3 -m unittest discover -s eval -p 'test_evaluation.py'
python3 eval/retrieval_check.py
```

첫 명령은 평가 집계 로직과 CLI의 30개 회귀 검사를 실행한다. RAG CLI·설정은 `apps/rag/`, 평가 후보는 `cases/rag-search.json`을 사용한다. 두 번째 명령은 Node.js로 `workflows/oke-support-mock.json`과 `fixtures/`를 사용해 `support-retrieval.json`의 21개 합성 검색·조회·이관 사례를 실행한다. 여기의 상대 경로는 `eval/` 기준 자산이며 `request_file`은 저장소 루트 `requests/`를 가리킨다.

이 검사는 실제 n8n·검색·티켓 API를 호출하지 않는다. 실제 실행 자료는 [runs/](../runs/README.md), 기준과 한계는 [평가 가이드](../docs/EVALUATION-GUIDE.md)·[실행 결과](../docs/EXECUTION-RESULT.md)를 따른다. 관측 결과 집계는 공통 구현인 [apps/rag/rag_evaluate.py](../apps/rag/rag_evaluate.py)를 사용하며 단독 네트워크 호출을 만들지 않는다.
