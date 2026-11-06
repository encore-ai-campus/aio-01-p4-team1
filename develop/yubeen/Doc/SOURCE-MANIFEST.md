# P0-1 원본 대장

모드: mock. 실제 API 응답 구조·권한 및 관리자 문서 제공 여부 미검증.
입력 스냅샷 SHA-256 (안전한 대장 투영): 5941e1a7c8d985134e736d010404f70a34c101ff01c654563acab9b7d8e709d6

어댑터 지원 형태(실측 전): /docs → {docs:[{name,access_level?}]}, /docs/{name} → {name,title,text,access_level?}. 다른 구조는 거절하며 추측 변환하지 않는다.
인증 헤더 X-Api-Key는 구현 가정이며 실제 data-api 확인 필요.
해시: 전체 본문 CRLF/CR→LF, 나머지 공백 보존, UTF-8 SHA-256. 절은 원문 순서이며 길이 0인 절도 보존한다. 청크 생성/빈 절 색인 판단은 하지 않는다.
권한: 명시 메타데이터 우선, 충돌/미지 값 거절. 없으면 공통 확정 규정 8종의 정확한 키만 all 매핑. 관리자 키 미확정은 거절한다. H-Y02의 별도 매핑표 제안은 확정 출처로 사용하지 않는다.

조사 6항목 / 후속 준비 가능 2항목 / 거절 4항목. 색인 성공 건수 아님.
입력 목록 기준 누락 규정: device-issue-return, email-and-documents, meeting-room, password-policy, privacy, remote-work-vpn, security-incident, software-usage. 실제 규정 8종·관리자 문서 확보: 미확인.

```json
[
  {
    "doc_key": "mock-public",
    "source_url": "/docs/mock-public",
    "title": "합성 공개 문서",
    "retrieved_at": "2026-11-04T07:11:45.389783+00:00",
    "access_level": "all",
    "permission_evidence": [
      {
        "source": "list_response",
        "field": "docs[0].access_level",
        "value": "all"
      }
    ],
    "source_hash": "972c0b7ff3487a635c114f1bb3b0b6e5f974178e21d6b3733c8e64e3970e4c28",
    "body_length": 35,
    "sections": [
      [
        "서문",
        3
      ],
      [
        "점검",
        26
      ]
    ],
    "reasons": []
  },
  {
    "doc_key": "mock-empty",
    "source_url": "/docs/mock-empty",
    "title": "빈 문서",
    "retrieved_at": "2026-11-04T07:11:45.389783+00:00",
    "access_level": "all",
    "permission_evidence": [
      {
        "source": "list_response",
        "field": "docs[1].access_level",
        "value": "all"
      }
    ],
    "source_hash": "36a9e7f1c95b82ffb99743e0c5c4ce95d83c9a430aac59f84ef3cbfab6145068",
    "body_length": 1,
    "sections": [
      [
        "본문",
        1
      ]
    ],
    "reasons": [
      "empty_document"
    ]
  },
  {
    "doc_key": "mock-duplicate",
    "source_url": "/docs/mock-duplicate",
    "title": "중복 문서",
    "retrieved_at": "2026-11-04T07:11:45.389783+00:00",
    "access_level": "all",
    "permission_evidence": [
      {
        "source": "list_response",
        "field": "docs[2].access_level",
        "value": "all"
      }
    ],
    "source_hash": "83f0a88bc5e206146603d7183941a08b4661bd4611748132dee6cec1de7f9456",
    "body_length": 5,
    "sections": [
      [
        "본문",
        5
      ]
    ],
    "reasons": [
      "duplicate_doc_key"
    ]
  },
  {
    "doc_key": "mock-duplicate",
    "source_url": "/docs/mock-duplicate",
    "title": "중복 문서",
    "retrieved_at": "2026-11-04T07:11:45.389783+00:00",
    "access_level": "all",
    "permission_evidence": [
      {
        "source": "list_response",
        "field": "docs[3].access_level",
        "value": "all"
      }
    ],
    "source_hash": "83f0a88bc5e206146603d7183941a08b4661bd4611748132dee6cec1de7f9456",
    "body_length": 5,
    "sections": [
      [
        "본문",
        5
      ]
    ],
    "reasons": [
      "duplicate_doc_key"
    ]
  },
  {
    "doc_key": "mock-unknown",
    "source_url": "/docs/mock-unknown",
    "title": "[非공개]",
    "retrieved_at": "2026-11-04T07:11:45.389783+00:00",
    "access_level": null,
    "permission_evidence": [],
    "source_hash": "eaba55ad20193f6c963c67801e473051fe1a216ce4cb27d680339661a4c9b575",
    "body_length": 11,
    "sections": [
      [
        "[非공개]",
        11
      ]
    ],
    "reasons": [
      "permission_unconfirmed"
    ]
  },
  {
    "doc_key": "mock-it",
    "source_url": "/docs/mock-it",
    "title": "[非공개]",
    "retrieved_at": "2026-11-04T07:11:45.389783+00:00",
    "access_level": "it",
    "permission_evidence": [
      {
        "source": "list_response",
        "field": "docs[5].access_level",
        "value": "it"
      }
    ],
    "source_hash": "aa920884b7eb730ba186c021ce9474eae91c30516eec381baee02b1e0e13cc94",
    "body_length": 19,
    "sections": [
      [
        "[非공개]",
        8
      ]
    ],
    "reasons": []
  }
]
```
