# P0-2 청킹 비교

모드: mock. 실제 API·인증·원본 미검증.
동일 스냅샷의 안전한 비교 투영 SHA-256: 0be2663af51990671ee31f01c8c581b9639e0eaa5ce4aa3ae9c9abf0285763df

기본 section / 비교 본문 300 유니코드 문자, overlap=0. 본문은 LF 정규화 전체 text이며 원본 ## 제목 행도 보존한다. 두 방식의 접두어는 문서 제목 + LF + 포함 절 제목(여럿이면 / 연결) + LF. content는 접두어+원문 범위이며 향후 임베딩 입력과 동일하다. 범위는 0부터 시작하는 반열린 문자 범위다. 빈 절은 분석에 남기고 기본 청크에서 제외한다.
한도 검토: content UTF-8 8000바이트 초과는 별도 거절. 토큰 한도 실측이나 최종 운영 한도가 아닌 보수적 개인 검토 기준이다. coverage_with_exclusions는 제외/거절까지 합친 범위 대장 검사다. 실제 청크 보존은 chunk_coverage로 별도 확인한다. 본문·제목 원문은 출력하지 않고 비공개 표제도 가린다.
실제 문서 길이·검색 품질·토큰·비용·시간: 미측정. 아래는 Mock 로컬 분석값이며 색인/검색 결과가 아니다.

```json
[
  {
    "doc_key": "mock-structure",
    "access_level": "all",
    "source_hash": "714636dd0cb292851fdb9c09e400a3c5adb70b792e80d2cb0920f29f32c40c0b",
    "reasons": [],
    "status": "complete",
    "methods": {
      "section": {
        "chunk_count": 3,
        "status": "complete",
        "reasons": [],
        "chunk_coverage": {
          "ranges": [
            [
              0,
              3
            ],
            [
              3,
              89
            ],
            [
              96,
              105
            ]
          ],
          "characters": 98,
          "source_characters": 105,
          "ratio": 0.9333333333333333,
          "covers_entire_source": false
        },
        "coverage_accounting": {
          "source_characters": 105,
          "chunk_characters": 98,
          "excluded_characters": 7,
          "rejected_characters": 0,
          "all_ranges_accounted": true
        },
        "excluded_ranges": [
          {
            "start": 89,
            "end": 96,
            "reason": "empty_section"
          }
        ],
        "section_inventory": [
          {
            "section": "서문",
            "start": 0,
            "end": 3,
            "body_start": 0
          },
          {
            "section": "절 하나",
            "start": 3,
            "end": 89,
            "body_start": 11
          },
          {
            "section": "빈 절",
            "start": 89,
            "end": 96,
            "body_start": 96
          },
          {
            "section": "마지막",
            "start": 96,
            "end": 105,
            "body_start": 103
          }
        ],
        "body_lengths": {
          "min": 3,
          "median": 9,
          "max": 86
        },
        "content_lengths": {
          "min": 12,
          "median": 19,
          "max": 97
        },
        "prefix_lengths": {
          "min": 9,
          "median": 10,
          "max": 11
        },
        "coverage_with_exclusions": true,
        "order_and_ranges_valid": true,
        "empty_sections_excluded": 1,
        "rejected_ranges": [],
        "samples": [
          {
            "chunk_no": 0,
            "section": "서문",
            "content_hash": "c4494c8cef0eec81efd3c2aa3c9b6b11c6df475c54978865e6ebc38f6df7f236",
            "metadata": {
              "chunking": "section",
              "chunking_version": "p0-2-v1",
              "source_hash": "714636dd0cb292851fdb9c09e400a3c5adb70b792e80d2cb0920f29f32c40c0b",
              "section_order": 0,
              "part_no": 0,
              "source_range": [
                0,
                3
              ],
              "included_sections": [
                "서문"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          },
          {
            "chunk_no": 1,
            "section": "절 하나",
            "content_hash": "9b8a969586d9700ca172abe2e91c26855f8a9752b6eb7671ae62af535e406d19",
            "metadata": {
              "chunking": "section",
              "chunking_version": "p0-2-v1",
              "source_hash": "714636dd0cb292851fdb9c09e400a3c5adb70b792e80d2cb0920f29f32c40c0b",
              "section_order": 1,
              "part_no": 0,
              "source_range": [
                3,
                89
              ],
              "included_sections": [
                "절 하나"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          },
          {
            "chunk_no": 2,
            "section": "마지막",
            "content_hash": "6ddb0837e7c4e935ee49ee0481486f31459573cebf8d6ee55e521bdbf7ff7dd2",
            "metadata": {
              "chunking": "section",
              "chunking_version": "p0-2-v1",
              "source_hash": "714636dd0cb292851fdb9c09e400a3c5adb70b792e80d2cb0920f29f32c40c0b",
              "section_order": 3,
              "part_no": 0,
              "source_range": [
                96,
                105
              ],
              "included_sections": [
                "마지막"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          }
        ]
      },
      "300": {
        "chunk_count": 1,
        "status": "complete",
        "reasons": [],
        "chunk_coverage": {
          "ranges": [
            [
              0,
              105
            ]
          ],
          "characters": 105,
          "source_characters": 105,
          "ratio": 1.0,
          "covers_entire_source": true
        },
        "coverage_accounting": {
          "source_characters": 105,
          "chunk_characters": 105,
          "excluded_characters": 0,
          "rejected_characters": 0,
          "all_ranges_accounted": true
        },
        "excluded_ranges": [],
        "section_inventory": [
          {
            "section": "서문",
            "start": 0,
            "end": 3,
            "body_start": 0
          },
          {
            "section": "절 하나",
            "start": 3,
            "end": 89,
            "body_start": 11
          },
          {
            "section": "빈 절",
            "start": 89,
            "end": 96,
            "body_start": 96
          },
          {
            "section": "마지막",
            "start": 96,
            "end": 105,
            "body_start": 103
          }
        ],
        "body_lengths": {
          "min": 105,
          "median": 105,
          "max": 105
        },
        "content_lengths": {
          "min": 133,
          "median": 133,
          "max": 133
        },
        "prefix_lengths": {
          "min": 28,
          "median": 28,
          "max": 28
        },
        "coverage_with_exclusions": true,
        "order_and_ranges_valid": true,
        "empty_sections_excluded": 0,
        "rejected_ranges": [],
        "samples": [
          {
            "chunk_no": 0,
            "section": "서문 / 절 하나 / 빈 절 / 마지막",
            "content_hash": "0ae81de48c28744e5abcfe3d5ae01198c389aa7e4f1ff9cc12c7bff7e17e1c02",
            "metadata": {
              "chunking": "300",
              "chunking_version": "p0-2-v1",
              "source_hash": "714636dd0cb292851fdb9c09e400a3c5adb70b792e80d2cb0920f29f32c40c0b",
              "section_order": 0,
              "part_no": 0,
              "source_range": [
                0,
                105
              ],
              "included_sections": [
                "서문",
                "절 하나",
                "빈 절",
                "마지막"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          }
        ]
      }
    }
  },
  {
    "doc_key": "mock-unicode",
    "access_level": "all",
    "source_hash": "05249d4c146570856ad4179fbfa1272dabf7802a1d4705eb25a265f3179bd12f",
    "reasons": [],
    "status": "complete",
    "methods": {
      "section": {
        "chunk_count": 2,
        "status": "complete",
        "reasons": [],
        "chunk_coverage": {
          "ranges": [
            [
              0,
              406
            ],
            [
              406,
              511
            ]
          ],
          "characters": 511,
          "source_characters": 511,
          "ratio": 1.0,
          "covers_entire_source": true
        },
        "coverage_accounting": {
          "source_characters": 511,
          "chunk_characters": 511,
          "excluded_characters": 0,
          "rejected_characters": 0,
          "all_ranges_accounted": true
        },
        "excluded_ranges": [],
        "section_inventory": [
          {
            "section": "앞",
            "start": 0,
            "end": 406,
            "body_start": 5
          },
          {
            "section": "뒤",
            "start": 406,
            "end": 511,
            "body_start": 411
          }
        ],
        "body_lengths": {
          "min": 105,
          "median": 255.5,
          "max": 406
        },
        "content_lengths": {
          "min": 113,
          "median": 263.5,
          "max": 414
        },
        "prefix_lengths": {
          "min": 8,
          "median": 8.0,
          "max": 8
        },
        "coverage_with_exclusions": true,
        "order_and_ranges_valid": true,
        "empty_sections_excluded": 0,
        "rejected_ranges": [],
        "samples": [
          {
            "chunk_no": 0,
            "section": "앞",
            "content_hash": "1b9ab34293121c30f0aa6d6b6de1395ff584f04583707796b8b1a50c7af147c5",
            "metadata": {
              "chunking": "section",
              "chunking_version": "p0-2-v1",
              "source_hash": "05249d4c146570856ad4179fbfa1272dabf7802a1d4705eb25a265f3179bd12f",
              "section_order": 0,
              "part_no": 0,
              "source_range": [
                0,
                406
              ],
              "included_sections": [
                "앞"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          },
          {
            "chunk_no": 1,
            "section": "뒤",
            "content_hash": "573570ba67e9ad7b9f24c415ed08171048607f102d62fb1f8dd652cbaecba515",
            "metadata": {
              "chunking": "section",
              "chunking_version": "p0-2-v1",
              "source_hash": "05249d4c146570856ad4179fbfa1272dabf7802a1d4705eb25a265f3179bd12f",
              "section_order": 1,
              "part_no": 0,
              "source_range": [
                406,
                511
              ],
              "included_sections": [
                "뒤"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          }
        ]
      },
      "300": {
        "chunk_count": 2,
        "status": "complete",
        "reasons": [],
        "chunk_coverage": {
          "ranges": [
            [
              0,
              300
            ],
            [
              300,
              511
            ]
          ],
          "characters": 511,
          "source_characters": 511,
          "ratio": 1.0,
          "covers_entire_source": true
        },
        "coverage_accounting": {
          "source_characters": 511,
          "chunk_characters": 511,
          "excluded_characters": 0,
          "rejected_characters": 0,
          "all_ranges_accounted": true
        },
        "excluded_ranges": [],
        "section_inventory": [
          {
            "section": "앞",
            "start": 0,
            "end": 406,
            "body_start": 5
          },
          {
            "section": "뒤",
            "start": 406,
            "end": 511,
            "body_start": 411
          }
        ],
        "body_lengths": {
          "min": 211,
          "median": 255.5,
          "max": 300
        },
        "content_lengths": {
          "min": 223,
          "median": 265.5,
          "max": 308
        },
        "prefix_lengths": {
          "min": 8,
          "median": 10.0,
          "max": 12
        },
        "coverage_with_exclusions": true,
        "order_and_ranges_valid": true,
        "empty_sections_excluded": 0,
        "rejected_ranges": [],
        "samples": [
          {
            "chunk_no": 0,
            "section": "앞",
            "content_hash": "631d5ded6f53b607f051b34ee2eafb73f94ba084dbb9ac66e11487735485b232",
            "metadata": {
              "chunking": "300",
              "chunking_version": "p0-2-v1",
              "source_hash": "05249d4c146570856ad4179fbfa1272dabf7802a1d4705eb25a265f3179bd12f",
              "section_order": 0,
              "part_no": 0,
              "source_range": [
                0,
                300
              ],
              "included_sections": [
                "앞"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          },
          {
            "chunk_no": 1,
            "section": "앞 / 뒤",
            "content_hash": "136630bbc49e8a837f1d8d15244ebb1330515558dc481b6ebafde6d9ed2add64",
            "metadata": {
              "chunking": "300",
              "chunking_version": "p0-2-v1",
              "source_hash": "05249d4c146570856ad4179fbfa1272dabf7802a1d4705eb25a265f3179bd12f",
              "section_order": 0,
              "part_no": 1,
              "source_range": [
                300,
                511
              ],
              "included_sections": [
                "앞",
                "뒤"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          }
        ]
      }
    }
  },
  {
    "doc_key": "mock-plain",
    "access_level": "all",
    "source_hash": "6f79e0cbd44008f0eafa70d1ff76496d0d6b6df3f28a0115e23eeb9df4a90e6e",
    "reasons": [],
    "status": "complete",
    "methods": {
      "section": {
        "chunk_count": 1,
        "status": "complete",
        "reasons": [],
        "chunk_coverage": {
          "ranges": [
            [
              0,
              12
            ]
          ],
          "characters": 12,
          "source_characters": 12,
          "ratio": 1.0,
          "covers_entire_source": true
        },
        "coverage_accounting": {
          "source_characters": 12,
          "chunk_characters": 12,
          "excluded_characters": 0,
          "rejected_characters": 0,
          "all_ranges_accounted": true
        },
        "excluded_ranges": [],
        "section_inventory": [
          {
            "section": "본문",
            "start": 0,
            "end": 12,
            "body_start": 0
          }
        ],
        "body_lengths": {
          "min": 12,
          "median": 12,
          "max": 12
        },
        "content_lengths": {
          "min": 21,
          "median": 21,
          "max": 21
        },
        "prefix_lengths": {
          "min": 9,
          "median": 9,
          "max": 9
        },
        "coverage_with_exclusions": true,
        "order_and_ranges_valid": true,
        "empty_sections_excluded": 0,
        "rejected_ranges": [],
        "samples": [
          {
            "chunk_no": 0,
            "section": "본문",
            "content_hash": "85c52a2b532aa3598325372faafa42e4b3a86f1663c7952c520b90e65c2f206c",
            "metadata": {
              "chunking": "section",
              "chunking_version": "p0-2-v1",
              "source_hash": "6f79e0cbd44008f0eafa70d1ff76496d0d6b6df3f28a0115e23eeb9df4a90e6e",
              "section_order": 0,
              "part_no": 0,
              "source_range": [
                0,
                12
              ],
              "included_sections": [
                "본문"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          }
        ]
      },
      "300": {
        "chunk_count": 1,
        "status": "complete",
        "reasons": [],
        "chunk_coverage": {
          "ranges": [
            [
              0,
              12
            ]
          ],
          "characters": 12,
          "source_characters": 12,
          "ratio": 1.0,
          "covers_entire_source": true
        },
        "coverage_accounting": {
          "source_characters": 12,
          "chunk_characters": 12,
          "excluded_characters": 0,
          "rejected_characters": 0,
          "all_ranges_accounted": true
        },
        "excluded_ranges": [],
        "section_inventory": [
          {
            "section": "본문",
            "start": 0,
            "end": 12,
            "body_start": 0
          }
        ],
        "body_lengths": {
          "min": 12,
          "median": 12,
          "max": 12
        },
        "content_lengths": {
          "min": 21,
          "median": 21,
          "max": 21
        },
        "prefix_lengths": {
          "min": 9,
          "median": 9,
          "max": 9
        },
        "coverage_with_exclusions": true,
        "order_and_ranges_valid": true,
        "empty_sections_excluded": 0,
        "rejected_ranges": [],
        "samples": [
          {
            "chunk_no": 0,
            "section": "본문",
            "content_hash": "85c52a2b532aa3598325372faafa42e4b3a86f1663c7952c520b90e65c2f206c",
            "metadata": {
              "chunking": "300",
              "chunking_version": "p0-2-v1",
              "source_hash": "6f79e0cbd44008f0eafa70d1ff76496d0d6b6df3f28a0115e23eeb9df4a90e6e",
              "section_order": 0,
              "part_no": 0,
              "source_range": [
                0,
                12
              ],
              "included_sections": [
                "본문"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          }
        ]
      }
    }
  },
  {
    "doc_key": "mock-it",
    "access_level": "it",
    "source_hash": "5031d17d681f27e46799fa79cf561d542a6ec7d978dde34acab3726e809e76d8",
    "reasons": [],
    "status": "complete",
    "methods": {
      "section": {
        "chunk_count": 1,
        "status": "complete",
        "reasons": [],
        "chunk_coverage": {
          "ranges": [
            [
              0,
              17
            ]
          ],
          "characters": 17,
          "source_characters": 17,
          "ratio": 1.0,
          "covers_entire_source": true
        },
        "coverage_accounting": {
          "source_characters": 17,
          "chunk_characters": 17,
          "excluded_characters": 0,
          "rejected_characters": 0,
          "all_ranges_accounted": true
        },
        "excluded_ranges": [],
        "section_inventory": [
          {
            "section": "[非공개]",
            "start": 0,
            "end": 17,
            "body_start": 8
          }
        ],
        "body_lengths": {
          "min": 17,
          "median": 17,
          "max": 17
        },
        "content_lengths": {
          "min": 28,
          "median": 28,
          "max": 28
        },
        "prefix_lengths": {
          "min": 11,
          "median": 11,
          "max": 11
        },
        "coverage_with_exclusions": true,
        "order_and_ranges_valid": true,
        "empty_sections_excluded": 0,
        "rejected_ranges": [],
        "samples": [
          {
            "chunk_no": 0,
            "section": "[非공개]",
            "content_hash": "ec810bae4ddcab2b24fce40f01823356c208c2bd6742eda19aac20d21d9c1c77",
            "metadata": {
              "chunking": "section",
              "chunking_version": "p0-2-v1",
              "source_hash": "5031d17d681f27e46799fa79cf561d542a6ec7d978dde34acab3726e809e76d8",
              "section_order": 0,
              "part_no": 0,
              "source_range": [
                0,
                17
              ],
              "included_sections": [
                "[非공개]"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          }
        ]
      },
      "300": {
        "chunk_count": 1,
        "status": "complete",
        "reasons": [],
        "chunk_coverage": {
          "ranges": [
            [
              0,
              17
            ]
          ],
          "characters": 17,
          "source_characters": 17,
          "ratio": 1.0,
          "covers_entire_source": true
        },
        "coverage_accounting": {
          "source_characters": 17,
          "chunk_characters": 17,
          "excluded_characters": 0,
          "rejected_characters": 0,
          "all_ranges_accounted": true
        },
        "excluded_ranges": [],
        "section_inventory": [
          {
            "section": "[非공개]",
            "start": 0,
            "end": 17,
            "body_start": 8
          }
        ],
        "body_lengths": {
          "min": 17,
          "median": 17,
          "max": 17
        },
        "content_lengths": {
          "min": 28,
          "median": 28,
          "max": 28
        },
        "prefix_lengths": {
          "min": 11,
          "median": 11,
          "max": 11
        },
        "coverage_with_exclusions": true,
        "order_and_ranges_valid": true,
        "empty_sections_excluded": 0,
        "rejected_ranges": [],
        "samples": [
          {
            "chunk_no": 0,
            "section": "[非공개]",
            "content_hash": "ec810bae4ddcab2b24fce40f01823356c208c2bd6742eda19aac20d21d9c1c77",
            "metadata": {
              "chunking": "300",
              "chunking_version": "p0-2-v1",
              "source_hash": "5031d17d681f27e46799fa79cf561d542a6ec7d978dde34acab3726e809e76d8",
              "section_order": 0,
              "part_no": 0,
              "source_range": [
                0,
                17
              ],
              "included_sections": [
                "[非공개]"
              ]
            },
            "content": "[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]"
          }
        ]
      }
    }
  },
  {
    "doc_key": "mock-unknown",
    "access_level": null,
    "source_hash": "e850d64613864958ecb0e2ba9aaf6137d5d16a8db315edea0c5f4cc747b9be67",
    "reasons": [
      "permission_unconfirmed"
    ],
    "status": "rejected",
    "methods": {}
  }
]
```

## 상태별 분리 통계

완전 성공·부분 생성·거절을 분리한다. 부분 생성 청크를 완전 성공 건수에 더하지 않는다.

```json
{
  "section": {
    "complete": {
      "document_count": 4,
      "chunk_count": 7,
      "body_lengths": {
        "min": 3,
        "median": 17,
        "max": 406
      },
      "content_lengths": {
        "min": 12,
        "median": 28,
        "max": 414
      }
    },
    "partial": {
      "document_count": 0,
      "chunk_count": 0,
      "body_lengths": "미측정",
      "content_lengths": "미측정"
    },
    "rejected": {
      "document_count": 1,
      "chunk_count": 0,
      "body_lengths": "미측정",
      "content_lengths": "미측정"
    }
  },
  "300": {
    "complete": {
      "document_count": 4,
      "chunk_count": 5,
      "body_lengths": {
        "min": 12,
        "median": 105,
        "max": 300
      },
      "content_lengths": {
        "min": 21,
        "median": 133,
        "max": 308
      }
    },
    "partial": {
      "document_count": 0,
      "chunk_count": 0,
      "body_lengths": "미측정",
      "content_lengths": "미측정"
    },
    "rejected": {
      "document_count": 1,
      "chunk_count": 0,
      "body_lengths": "미측정",
      "content_lengths": "미측정"
    }
  }
}
```
