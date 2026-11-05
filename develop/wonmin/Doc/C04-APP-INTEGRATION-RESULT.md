# 본체 C04 → handoff → C05 app 연결 시험 · 2026-11-05

**직원 fixture를 쓰는 전용 app 경로에서 13개 시험 그룹을 통과했다.** 다혁 `bb2fa1f` 본체 → 실제 C04 HTTP → 원민 handoff → 지혜 `ec6a735` FastAPI → 실제 PostgreSQL 저장을 확인했다. 분류는 실제 로컬 `qwen2.5-coder:latest`를 사용했다. 실제 data-api 신원 연동·실제 규정 검색·팀 VM 검증 완료를 뜻하지 않는다.

## 먼저 발견한 차단과 오류

1. 기존 본체에 정상 형식 질문을 실제 호출했다. HTTP 200이지만 `reason=identity_unavailable, ticket=null`이었다. 현재 lab에는 실제 `LAB_DATA_API_URL`·`LAB_DATA_API_KEY`가 없다. [원래 환경의 차단 결과](../runs/c04-app-preflight-20261105.json). 직원 검증을 임의로 통과시키거나 기존 업무 workflow를 Mock 모드로 바꾸지 않았다.
2. 전용 DB에 이미 있는 계약 직원 6명(name/dept만)을 읽어, 인증이 필요한 읽기 전용 HTTP fixture로 제공했다. 본체의 실제 직원 HTTP 노드와 검증 Code를 그대로 실행했다. 이 fixture는 실제 data-api 제공/인증·관리자 계정·세션 권한의 증거가 아니다.
3. 최초 연결 시험에서 정상/중복은 성공했지만 긴급 문의는 실패했다. 실행 103의 로컬 모델이 유효한 분류 JSON을 마크다운 코드 블록으로 감싸 반환했고, 본체의 엄격한 JSON.parse가 `triage_invalid`로 판정했다. 결과적으로 실행 104에서 `T-2010`이 normal로 저장됐다. [최초 실패 보고서](../runs/c04-app-integration-20261105T103935Z.json)를 보존했다. 이 티켓은 시험 데이터이며 실패를 통과 처리하지 않는다.
4. 설치된 n8n OpenAI Chat Model 구현의 `options.responseFormat` → `response_format` 전달을 확인하고, **전용 시험 사본의 triage 모델에만 `json_object`를 설정**했다. 모델·Credential은 기존 로컬 구성을 사용했다. 다혁 분류 프롬프트/파서·정본 workflow는 수정하지 않았다. 같은 긴급 질문의 재시험은 실제 high 저장으로 성공했다. [원인·보완 설정·최종 상태](../runs/c04-app-final-state-20261105.json).

## 변경 파일과 배포 범위

- `tools/test-c04-app-integration.py`: Git 원본 출처 확인, 전용 support/handoff 게시, 실제 질문 호출·n8n 실행·SQL 대조, 장애 주입 및 종료 복구.
- `tools/c04-identity-fixture.py`, `deploy/compose.c04.yaml`, `tests/test_c04_identity_fixture.py`: 계약 직원 6명만 GET으로 제공. 인증 누락/오류 거절, POST 405, 다른 경로·query string 거절, 추가 민감 필드/불일치 fixture 시작 거절.
- 이번에 fetch한 `origin/feat/dahyeok-p0=bb2fa1fcc43ead160bda6330e3fdc11207492eee`는 이미 원민 HEAD에 포함돼 있었다. 해당 커밋의 `oke-support-13.json` Git blob을 직접 읽었고 해시를 남겼다. 지혜 app backend는 ec6a735/DB0005다.
- support 사본에서 바꾼 것은 전용 ID/웹훅, 실제 Credential 연결, app 모드, 직원 fixture·전용 C04 주소, 로컬 모델/triage JSON 출력 설정 및 진단 실행 저장이다. N20 요청 생성·C04 HTTP·캡처/매핑·최종 안내 코드는 그대로다.
- handoff 사본은 정본 30개 노드를 사용하며 app 모드·실제 저장 프록시 주소·Credential·전용 경로·진단 설정만 연결했다. 프록시의 정상 호출은 실제 FastAPI로 전달하며 저장 Mock은 없다.

## 확인 방법과 실제 결과

[최종 13개 그룹의 HTTP·n8n·SQL 근거](../runs/c04-app-integration-20261105T104124Z.json). 본체 응답뿐 아니라 N20의 실제 C04 HTTP 200·`handoff_mock=false`, handoff 실행 결과, 같은 request_key/event_key의 실제 행을 대조했다. 모든 저장 조건에서 실제 triage 실행과 유효한 분류 결과를 확인했다.

| 시험 그룹 | 실제 결과 |
| --- | --- |
| 인증 | support/handoff 키 없음 403, 직원 fixture 키 없음 401 |
| 미등록 직원 | 400/unknown_user, 티켓 생성 호출 없음 |
| 주입 요청 | route=차단, 티켓 생성 호출 없음 |
| 정상·중복 | 본체107→handoff108, 재요청109→110. 동일 T-2011, duplicate false→true, 티켓/알림 각1건 |
| 긴급 보안 | 본체111→handoff112. T-2012/high, 사내망 분리 안내·sources=[] |
| 알림 실패 | 114→115. T-2013 유지, 본체 alerts_down 안내, C04 alerted=false·dlq=true |
| 알림 복구 | 116→117. 같은 T-2013/duplicate=true, 알림1건, 정상 접수 안내로 복구 |
| 티켓 실패 | 118→119. 티켓0건, C04 alerted=true·dlq=true. 본체는 접수 실패를 단정하지 않고 같은 ID로 재확인 안내 |
| 티켓+DLQ 실패 | 120→121. 티켓0건, alerted=true·dlq=false |
| 알림+DLQ 실패 | 122→123. T-2014 유지, alerted=false·dlq=false |
| 전체 실패 | 124→125. 티켓0건, alerted=false·dlq=false, 유한 종료 |
| 일시 티켓 실패 | 126→127. 첫503 후 2차 실제 저장, T-2015 1건 |
| 동일 요청 동시2회 | 본체128/129→handoff130/131. 동일 T-2016·신규1/중복1, 티켓/알림 각1건 |

프록시 장애는 통제된 HTTP 503 주입이며 실제 PostgreSQL 고장 시험과 구별한다. 최종 실행의 시험 DB는 티켓10→16, 알림19→26, DLQ9→11이며 기존 기본 DB는 세 테이블 모두0→0이다. 최초 실패 실행의 티켓2건/알림2건도 보존됐으므로 최종 실행의 증가량과 합산하지 않는다.

긴급 문의는 먼저 이관·저장된 뒤 실제 검색 경로도 호출했으나 C03은 현재503이다. 이번에 규정 근거나 writer/verifier 품질을 검증하지 않았다. 긴급 질문에는 기존 T-1002를 포함하지 않았으므로 **WF-12의 본인 기존 티켓 상태 조합까지 검증한 결과는 아니다.** 본체의 `N05 Replay MOCK`은 원본의 miss adapter 그대로이며, 검증한 멱등성은 handoff/C05 저장 경계다. 영속 응답 캐시 API 검증과 구별한다.

## 회귀·종료 상태와 재실행

- fixture 시험은 도구가 없는 상태에서 3개 실패를 확인한 뒤 구현했다. 최종 Python 전체11개, 저장소 루트 Node113개(원민97+유빈16)가 통과했다. [실제 출력 집계](../runs/c04-app-regression-20261105.json). 공식 flow.py 검사는 아니다.
- 기존 workflow의 게시 상태·설정·버전은 전후 동일하다. 기본 practice 모드, 기존 사용자/모델 Credential, main/submission 및 상대 소스는 바꾸지 않았다. Git push는 하지 않았다.
- 프록시 장애 계획은 `{}`로 복구했으며 n8n·두 backend 건강 확인 HTTP200이다. 시험용 두 workflow는 검토할 수 있도록 게시 상태로 남겼다. 직원 fixture는 읽기 전용이다. 시험용 사본만 합성 실행 데이터를 저장하며, 실제 사용자 정보를 넣는 운영 환경으로 사용하지 않는다.
- [시험용 본체 열기](http://127.0.0.1:15678/workflow/wmc0417676ce1ea), [실제 app handoff 사본 열기](http://127.0.0.1:15678/workflow/wmc0426f3465344). 기존 Credential로 인증하며 키를 보고서/명령에 직접 적지 않는다.

기존 C05 lab·전용 DB0005·직원6명·n8n Credential/ID가 준비된 Ubuntu에서 `develop/wonmin`으로 이동해 실행한다.

```bash
python3 tools/test-c04-app-integration.py
```

n8n/프록시 재시작을 포함하므로 다른 시험과 동시에 실행하지 않는다. 매번 새 요청 접두사와 새 보고서를 사용하며 기존 행을 삭제하지 않는다. 실패 시 전용 두 workflow를 게시 해제하고, 성공 시 게시 상태로 유지한다. 기존 workflow는 재가져오기하지 않는다.

## 다음 연결 상대와 남은 일

- 다혁님: bb2fa1f의 C04 발신/매핑/B안 안내와 원민 C05 실저장 연결은 위 조건에서 적합했다. 로컬 qwen의 코드 블록 출력으로 긴급이 normal로 내려간 최초 실패를 공유한다. 실제 운영/팀 VM의 triage 모델에서 JSON 출력 설정을 검토하고 동일 긴급 질문을 재시험해야 한다. 원민은 상대 정본/기존 업무 workflow를 직접 수정하지 않았다.
- 지혜님·오현님: 실제 data-api 주소/키·직원/기존 티켓 권한 근거를 준비한 뒤 기존 본체의 identity_unavailable을 해소해야 한다. fixture를 실제 신원 검증 완료로 처리하지 않는다. 공통 C05 알림 duplicate·DLQ200 문서 반영 확인도 남아 있다.
- 유빈님: 실제 C03 검색의503 해소 후 근거·권한·writer/verifier 및 WF-12 본인 티켓 조합을 이어서 확인해야 한다.
- 원민: 실제 신원 제공자 연결 후 같은 suite를 기존 업무 환경에 맞춰 재시험하고, 공식 키트/공통14유형·팀사례·LLM3회·bench·팀 VM 회귀 근거를 완성한다.
