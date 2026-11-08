# rag · RAG 색인·검색

색인·검색 HTTP 서비스, 공통 엔진·평가 도구, `config/rag-settings.json`, `rag-permissions.json`, `requirements-runtime.txt`를 포함한다. Docker 작업 경로는 `/app/rag`이며 설정 로더도 이 폴더의 `config/`를 사용한다.

저장소 루트에서 외부 호출 없이 합성 색인·멱등성 검사를 실행한다.

```sh
python3 apps/rag/rag_verify.py index --scenario initial-and-repeat --json
python3 apps/rag/rag_load.py --docs-dir knowledge --permissions apps/rag/rag-permissions.json --mode fake
```

실제 색인은 `knowledge/`의 승인된 규정 8종과 해시·`all`/`it` 권한 매핑을 확인한다. 폴더 안내용 `README.md`는 규정에서 제외하며 다른 추가 파일·해시 불일치는 거절한다. Mock fixture는 [cases/](../../cases/README.md)에 포함한다.

실제 서비스는 [배포 안내](../../deploy/README.md)·[로컬 안내](../../deploy/LOCAL-MAC.md)를 따른다. PostgreSQL과 비공개 `DATABASE_URL`, `OPENAI_API_KEY`, 검색·색인 인증 설정이 필요하다. 실제 임베딩·DB 접근은 명시된 실행 모드에서만 수행한다. 설계·측정 근거는 [RAG 설계](../../docs/RAG-ARCHITECTURE.md), 평가 재현은 [eval/](../../eval/README.md)를 따른다.
