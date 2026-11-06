# P1-4 갱신·중단 복구 준비 · 2026-11-05

상태: **PREPARED / VERIFIED_FAKE**. 실제 PostgreSQL·n8n·팀 VM 재시작, 백업 복원, OpenAI 호출은 수행하지 않았다. 아래 Fake 기록은 영속성·실제 DB 트랜잭션 원자성의 증거가 아니다.

## 구현과 Fake 시나리오

기존 `rag_index.index_snapshot`·`MockStore`·`PostgresStore`의 중복 건너뜀, 문서 단위 청크 교체, 임베딩 전량 준비, 실패 롤백 경로를 재사용했다. `tests/test_recovery.py`에서 두 합성 문서를 사용하여 다음을 검증한다.

| 시나리오 | Fake 검증 결과 |
| --- | --- |
| 동일 입력 재색인 | 두 문서 모두 skipped, 불필요한 임베딩·교체 없음 |
| 본문 변경, 한 문서만 변경 | 변경 문서 indexed 1, 다른 문서 skipped 1; 다른 문서 저장 상태 불변 |
| 청크 증가 2→3, 감소 3→1 | chunk_no 연속, content_hash와 실제 content 일치, 이전 잔여 청크 없음 |
| 첫 임베딩 및 두 번째 청크 임베딩 실패 | 실패 문서 failed, 다른 문서 skipped; 이전 저장 상태 불변 |
| Mock 저장소의 이전 청크 삭제 직후 실패 | 실패 문서 failed, 이전 문서/청크 상태로 롤백; 정상 재실행 indexed |
| 중복 원본 목록 후 정상 재시도 | 중복 입력 rejected, 기존 데이터 불변; 정상 재실행 skipped, 중복 청크 없음 |
| before/after 기록 | 실행 ID별 Fake inventory 비교, 기존 before 보존, 같은 단계 중복 기록 거절 |

기존 `tests/test_indexing.py`에는 PostgresStore의 DB-API Fake cursor 오류·rollback 호출, rollback 실패, 불명확한 commit 처리, 권한 축소 중지 검사가 있다. 이는 실제 PostgreSQL INSERT·트랜잭션 중간 실패의 검증이 아니다. 장애 이유는 외부 상세 정보 대신 고정 코드로 보고하며 재시도 결과와 분리한다.

## 복구 기록 도구

`develop/yubeen`에서 실행:

```bash
python3 tools/rag_verify.py recovery --phase before --run-id mock-local --output Doc/RECOVERY-RESULT.md
python3 tools/rag_verify.py recovery --phase after --run-id mock-local --output Doc/RECOVERY-RESULT.md
```

각 기록에는 UTC 검증 시각, run_id, `mode=fake`, 문서 키(`doc_key`), 청크 수·순서·content_hash, 원본 해시, 접근 권한, 중복/누락 번호, 실제 재시작·복원 여부(false)가 포함된다. after는 동일 run_id의 before가 필요하고 비교 결과를 추가한다. 같은 run_id·phase 중복 실행은 거절하며 기존 기록은 덮어쓰지 않는다. 출력은 담당 폴더 안에서만 허용한다. 별도 실행은 같은 합성 입력에서 새 MockStore를 만들므로 비교 성공이 프로세스·DB 재시작 유지 성공을 뜻하지 않는다.

## 실제 DB 연결 후 검증 순서

1. 지혜님이 제공한 **격리 DB**와 0004 DDL/역할을 읽기 전용으로 확인하고 오현님에게 8개 원본·권한·쓰기 범위를 확인받는다.
2. 기준 문서별 doc_key·chunk_no·content_hash·source_hash·권한, 고정 질문 top3, 환경·마이그레이션·볼륨 식별자를 기록한다.
3. 한 문서의 본문을 변경하고 청크 증가·감소를 각각 재색인한다. 변경하지 않은 문서·오래된 청크·중복 여부를 SQL로 확인한다.
4. 임베딩 실패와 DB INSERT/트랜잭션 중간 실패를 격리 환경에서 각각 주입해 이전 성공본 보존·rollback·정상 재시도를 확인한다. 권한 축소·삭제·동시 갱신은 H-Y03 운영정책 확정 전 별도 보류한다.
5. 담당자가 n8n을 재시작한 뒤 재색인 없이 검색을 비교한다. 지혜님·오현님이 같은 named volume으로 PostgreSQL을 재시작한 뒤 건수·해시·권한·검색을 다시 비교한다. 운영 볼륨은 삭제하지 않는다.
6. 지혜님이 **새 DB**에 마이그레이션한 뒤 동일 원본/설정으로 재색인하고 doc_key·chunk_no·content_hash, 권한, 중복/누락, 검색 결과 및 실제 소요시간을 비교한다.
7. 백업이 제공되면 지혜님이 별도 환경에 복원한 뒤 동일 비교를 한다. 백업 미제공이면 복원은 미실행으로 남긴다.

지혜님: 실제 트랜잭션·권한·별도 DB/백업·재시작 실행 환경을 제공해야 한다. 원민님: 실패·재시도·권한 누출 사례를 함께 확인해야 한다. 오현님: 재시작과 운영 정책, 원본/권한 확정 및 공통 문서 반영을 맡는다. 현재 RTO/RPO·자동 백업 주기는 확정되지 않았다.

수정·생성: `tools/rag_verify.py`, `tests/test_recovery.py`, `Doc/RECOVERY-RESULT.md`. 전체 Python 179개(기존 172개 + P1-4 Fake 7개), JavaScript 16개 통과. `git diff --check` 통과. 아래 CLI 기록은 합성 문서 4개에 대한 Fake before/after 2건이며 `same_inventory=true`; 같은 after 재실행은 `invalid_recovery_record`로 거절되어 기존 기록을 보존했다.


<!-- rag-recovery-record -->
```json
{
  "phase": "before",
  "run_id": "mock-local",
  "mode": "fake",
  "verified_at": "2026-11-05T05:23:15.285038+00:00",
  "indexed_counts": {
    "indexed": 4,
    "skipped": 0,
    "rejected": 1,
    "failed": 0
  },
  "documents": [
    {
      "doc_key": "mock-it",
      "chunk_count": 1,
      "chunk_nos": [
        0
      ],
      "content_hashes": [
        "ec810bae4ddcab2b24fce40f01823356c208c2bd6742eda19aac20d21d9c1c77"
      ],
      "source_hash": "5031d17d681f27e46799fa79cf561d542a6ec7d978dde34acab3726e809e76d8",
      "access_level": "it",
      "duplicate_chunk_nos": false,
      "missing_chunk_nos": false
    },
    {
      "doc_key": "mock-plain",
      "chunk_count": 1,
      "chunk_nos": [
        0
      ],
      "content_hashes": [
        "85c52a2b532aa3598325372faafa42e4b3a86f1663c7952c520b90e65c2f206c"
      ],
      "source_hash": "6f79e0cbd44008f0eafa70d1ff76496d0d6b6df3f28a0115e23eeb9df4a90e6e",
      "access_level": "all",
      "duplicate_chunk_nos": false,
      "missing_chunk_nos": false
    },
    {
      "doc_key": "mock-structure",
      "chunk_count": 3,
      "chunk_nos": [
        0,
        1,
        2
      ],
      "content_hashes": [
        "c4494c8cef0eec81efd3c2aa3c9b6b11c6df475c54978865e6ebc38f6df7f236",
        "9b8a969586d9700ca172abe2e91c26855f8a9752b6eb7671ae62af535e406d19",
        "6ddb0837e7c4e935ee49ee0481486f31459573cebf8d6ee55e521bdbf7ff7dd2"
      ],
      "source_hash": "714636dd0cb292851fdb9c09e400a3c5adb70b792e80d2cb0920f29f32c40c0b",
      "access_level": "all",
      "duplicate_chunk_nos": false,
      "missing_chunk_nos": false
    },
    {
      "doc_key": "mock-unicode",
      "chunk_count": 2,
      "chunk_nos": [
        0,
        1
      ],
      "content_hashes": [
        "1b9ab34293121c30f0aa6d6b6de1395ff584f04583707796b8b1a50c7af147c5",
        "573570ba67e9ad7b9f24c415ed08171048607f102d62fb1f8dd652cbaecba515"
      ],
      "source_hash": "05249d4c146570856ad4179fbfa1272dabf7802a1d4705eb25a265f3179bd12f",
      "access_level": "all",
      "duplicate_chunk_nos": false,
      "missing_chunk_nos": false
    }
  ],
  "actual_restart_or_restore": false
}
```


<!-- rag-recovery-record -->
```json
{
  "phase": "after",
  "run_id": "mock-local",
  "mode": "fake",
  "verified_at": "2026-11-05T05:23:23.417249+00:00",
  "indexed_counts": {
    "indexed": 4,
    "skipped": 0,
    "rejected": 1,
    "failed": 0
  },
  "documents": [
    {
      "doc_key": "mock-it",
      "chunk_count": 1,
      "chunk_nos": [
        0
      ],
      "content_hashes": [
        "ec810bae4ddcab2b24fce40f01823356c208c2bd6742eda19aac20d21d9c1c77"
      ],
      "source_hash": "5031d17d681f27e46799fa79cf561d542a6ec7d978dde34acab3726e809e76d8",
      "access_level": "it",
      "duplicate_chunk_nos": false,
      "missing_chunk_nos": false
    },
    {
      "doc_key": "mock-plain",
      "chunk_count": 1,
      "chunk_nos": [
        0
      ],
      "content_hashes": [
        "85c52a2b532aa3598325372faafa42e4b3a86f1663c7952c520b90e65c2f206c"
      ],
      "source_hash": "6f79e0cbd44008f0eafa70d1ff76496d0d6b6df3f28a0115e23eeb9df4a90e6e",
      "access_level": "all",
      "duplicate_chunk_nos": false,
      "missing_chunk_nos": false
    },
    {
      "doc_key": "mock-structure",
      "chunk_count": 3,
      "chunk_nos": [
        0,
        1,
        2
      ],
      "content_hashes": [
        "c4494c8cef0eec81efd3c2aa3c9b6b11c6df475c54978865e6ebc38f6df7f236",
        "9b8a969586d9700ca172abe2e91c26855f8a9752b6eb7671ae62af535e406d19",
        "6ddb0837e7c4e935ee49ee0481486f31459573cebf8d6ee55e521bdbf7ff7dd2"
      ],
      "source_hash": "714636dd0cb292851fdb9c09e400a3c5adb70b792e80d2cb0920f29f32c40c0b",
      "access_level": "all",
      "duplicate_chunk_nos": false,
      "missing_chunk_nos": false
    },
    {
      "doc_key": "mock-unicode",
      "chunk_count": 2,
      "chunk_nos": [
        0,
        1
      ],
      "content_hashes": [
        "1b9ab34293121c30f0aa6d6b6de1395ff584f04583707796b8b1a50c7af147c5",
        "573570ba67e9ad7b9f24c415ed08171048607f102d62fb1f8dd652cbaecba515"
      ],
      "source_hash": "05249d4c146570856ad4179fbfa1272dabf7802a1d4705eb25a265f3179bd12f",
      "access_level": "all",
      "duplicate_chunk_nos": false,
      "missing_chunk_nos": false
    }
  ],
  "actual_restart_or_restore": false,
  "comparison": {
    "same_inventory": true,
    "baseline_verified_at": "2026-11-05T05:23:15.285038+00:00"
  }
}
```


## 실제 DB 검증 경로 구현 갱신 · 2026-11-05

기존 rag_verify recovery의 Fake 모드는 유지한다. 새 rag_db snapshot --allow-db는 실제 PostgreSQL의 읽기 전용 REPEATABLE READ에서 문서·청크·본문/벡터 해시·모델/차원을 기록하고 compare로 전후 차이를 확인한다. DB PK와 시각은 상태 비교에서 제외한다. 재시작을 도구가 실행하거나 관측했다고 표시하지 않으며 리드 실행 증거와 함께 확인한다. 새 DB 재적재 및 백업 복원 뒤 같은 도구를 사용한다. 실제 DB/VM 검증은 여전히 미실행이다. 상세 명령은 SUBMISSION-NOTES.md 참조.
