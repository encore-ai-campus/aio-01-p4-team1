# P1-4 독립 반복·bench·증거 대조 · 2026-11-05

**P1-4 일부를 실행했고 실제 기대 불일치 1개를 발견했다. 전체 완료가 아니다.** 본체 app 시험 사본의 계약 직원 HTTP fixture, 실제 로컬 qwen triage, 실제 C04/C05·PostgreSQL을 사용했다. 기존 업무 workflow와 기본 DB 설정은 바꾸지 않았다.

## 실제 신원 제공자·공식 키트 준비 상태

- 루트 `.env` 및 lab의 비공개 설정에서 실제 data-api 주소/키를 찾지 못했다. 기존 본체를 다시 호출한 실제 응답도 HTTP200/identity_unavailable·ticket=null이다.
- 로컬 Ubuntu Docker에는 실제 data-api 컨테이너가 없다. 등록된 원격 Ubuntu 연결도 연결/인증 오류로 접근하지 못했다. 팀 VM 접속·배포 성공으로 기록하지 않는다.
- 저장소와 관련 로컬 수업 자료를 검색했다. 로컬 자료는78일차까지이며80일차 공식 flow.py/common.json은 찾지 못했다. 이전 일차 flow.py나 다혁님의 독자 도구를 공식 도구로 복사하지 않았다.
- 실제 data-api의 비공개 설정 경로/접속 환경 및 공식 키트 배포 경로를 사용자에게 요청했다. 키 값을 채팅/문서에 적도록 요구하지 않았다.
- fetch로 유빈3276817의 추가 구현 인계를 확인했지만 병합·재배포·실제 RAG 검증을 한 것은 아니다. 새 코드 존재만으로 C03/원본/권한/임베딩 준비를 완료 처리하지 않는다.

[준비 상태·기존 본체 실제 응답·건강 확인](../runs/p1-4-readiness-20261105.json).

## 변경 파일

- `cases/team-llm.json`: 원민 team.json의 TM-02·03·06 입력/기대/부작용을 그대로 추출했다. 원본 SHA-256 및 app 변형의 조건 차이를 명시했다. 원본 team.json/common 기대를 수정하지 않았다. 내부 not_run 표기는 원본 복사이며 원래 practice 조건 완료 표시가 아니다.
- `tools/run-fresh.py`: 회차별 새 request_id, 같은 회차의 중복 요청만 동일 key, 실제 HTTP 응답시간·n8n 실행·SQL을 기록한다. 재사용 key는 실행 전에 거절하고, 보고서 덮어쓰기/비밀값 저장을 막는다.
- `tools/check-evidence.py`: 독립 반복 보고서의 요청/실행 ID·실제 모델 노드 기록·판정·지연 집계를 대조한다. 실패 보고서가 정합하더라도 기능 성공으로 바꾸지 않는다. 공식 평가나 독립적인 실환경 인증 도구가 아니다.
- 관련 Python 시험을 추가했다. 구현 전 도구 부재 실패와 모델 노드 기록 검증 실패를 확인한 뒤 구현했고 전체20개 통과했다. [회귀 근거](../runs/p1-4-regression-20261105.json).

## 독립 3회 결과

[원 실행 보고서](../runs/llm-fresh-app-20261105.json)의 판정은 **FAIL_SCOPED_APP_VARIANTS**이다. 고유 시나리오3개 × 새 ID3회 =9개 회차다. TM-06은 각 회차에 동일 key2회이므로 총HTTP12회·서로 다른 실제 LLM 실행12회다. 반복 횟수를 고유 시나리오 수로 세지 않았다.

| 원본 대응 app 변형 | 3회 결과 | 실제 결과 |
| --- | --- | --- |
| TM-02 정보 부족 | 0/3 통과 | route=보완 질문·ticket=null이지만 접속 대상만 질문. 오류·발생 시점 질문 누락 |
| TM-03 보완 한도 | 3/3 통과 | attempt3에서 실제 normal 티켓·알림 저장 |
| TM-06 순차 중복 | 3/3 통과 | 회차별 티켓/알림 각1건, 동일 key 두 번째 응답 duplicate=true |

TM-02의 실제 missing은 세 번 모두 `["접속 대상"]`이었다. 원민 TM-02와 공통 EVALUATION-GUIDE WF-02는 대상·오류·발생 시점을 확인하는 질문을 요구한다. 기대를 줄이거나 모델 출력을 시험 도구에서 보정하지 않았다. 본체 프롬프트/파서 소유자인 다혁님께 재현과 보완 제안을 HANDOFF로 인계한다. 상대 수정·같은 조건 재시험은 아직 미실행이다.

12회 전체 응답시간은 p50=0.729253초, p95/max=1.412597초이며 실패3회도 분모에 포함했다. 이 값이 기능 합격이나 정상 근거 답변의 SLA 충족을 의미하지 않는다.

실행 중 DB는 티켓16→22·알림26→32·DLQ11→11이다. 보완 질문에는 티켓/알림이 없었고, 나머지6개 fresh key에 각1건씩 실제 저장됐다. 기본 DB는 전후0→0이다. 모든 회차에서 실제 triage 모델/Agent 노드 기록과 유효 분류를 확인했으며 같은 실행 ID를 재사용하지 않았다.

## 이관 경로 fresh bench 5회

[bench 보고서](../runs/bench-fresh-app-20261105.json)는 TM-03의 동일 질문에 새 ID를 매회 사용했다. **5/5 통과·실제 LLM 실행5회**, 티켓22→27·알림32→37·DLQ11 유지다.

| 분모 | p50 | p95 | 최대 | 실패 |
| --- | --- | --- | --- | --- |
| HTTP5회 | 0.771119초 | 0.849413초 | 0.849413초 | 0 |

nearest-rank로 집계했으므로 n=5의 p95는 최대값이다. HTTP 왕복만 측정하고 이후 SQL/증거 조회 시간은 포함하지 않는다. 모델/서비스 warm 상태 및 직원 fixture·로컬 Ubuntu 조건의 표본이며 CPU/GPU 초기 기동·공용 VM 수치가 아니다. VPN 근거 답변인 `requests/bench-normal.json`의 공식 bench는 실제 검색 미준비로 실행하지 않았다. writer/verifier의3회 검증 결과도 아니다.

## 증거 대조와 종료 상태

[보고서 정합성 대조](../runs/p1-4-evidence-audit-20261105.json)는 두 보고서의 해시·원본 기대 출처·회차별 ID·모델 노드 실행·분모·실패수·분위수·색인 링크를 확인한다. 정합성 통과와 **all_functional_passed=false**를 함께 기록한다. TM-02 실패는 그대로 남아 있다.

n8n·두 backend 건강 확인 HTTP200, 프록시 장애 계획 `{}`를 확인했다. 이번 반복/bench 도구는 workflow나 fault 설정을 변경하지 않았다. 보고서의 workflow 전후 메타데이터와 기본 DB도 동일하다. 시험 행은 보존했고 reset/볼륨 삭제는 하지 않았다.

## 재현

현재 전용 C04 app 사본·JSON 출력 모델·fixture·실제 C05 DB가 준비된 Ubuntu의 `develop/wonmin`에서 실행한다. output은 기존 파일과 다른 이름을 사용한다.

```bash
python3 tools/run-fresh.py --suite cases/team-llm.json --repeat 3 --output runs/llm-fresh-new.json
python3 tools/run-fresh.py --case TM-03 --repeat 5 --bench --output runs/bench-fresh-new.json
python3 tools/check-evidence.py --index runs/INDEX.md --report runs/llm-fresh-app-20261105.json --report runs/bench-fresh-app-20261105.json --output runs/evidence-audit-new.json
```

첫 명령은 TM-02 불일치가 남아 있으면 비정상 종료하며 실패 JSON을 보존한다. 감사 도구의 종료0은 기록의 정합성만 뜻하고 기능 판정은 별도 필드다. 새 보고서는 실행 후 INDEX에 링크해야 감사의 색인 검사를 통과한다. `--parallel` 및 공식 suite 전체 판정은 이 도구에서 지원하지 않는다. 동시 요청은 기존 C04/C05 실제 통합 보고서에 있다.

## 다음 연결

1. 다혁님: bare 접속 불가 문의에서 미확인3항목을 모두 질문하도록 분류 프롬프트/정규화 정책을 보완하고, 같은 TM-02 입력을 JSON 모드·새 ID로3회 재시험한다. 한 항목씩 묻는 것이 의도라면 현재 공통 WF-02/팀 기대와 먼저 정리해야 하며 원민이 임의로 기대를 변경하지 않는다.
2. 지혜님/오현님: 실제 data-api 설정 및 공식80일차 키트·접속 환경 제공 후 기존 본체의 신원·본인/타인 티켓·WF-12를 재시험한다. 공통 C05 문서 반영도 별도 확인한다.
3. 원민: TM-02 수정 재시험, 공식 공통14유형·팀5개 이상·실제 RAG/writer/verifier3회·정상 근거 답변 bench·팀 VM 회귀를 이어간다. 이번 세 app 변형과 부분 bench로 P1-4 전체 완료 체크를 하지 않는다.
