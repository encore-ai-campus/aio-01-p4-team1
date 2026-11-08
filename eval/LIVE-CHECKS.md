# 팀 VM 통합 시험 재실행

이 저장소의 코드로 실제 FastAPI·n8n·DB를 확인한다. 별도 강의 저장소나 삭제된 `develop/`, `tools/` 폴더는 필요하지 않다. 실제 질문 전송에는 LLM·임베딩 API 비용과 시험용 문의·티켓·알림 저장이 발생한다.

## 비공개 설정

저장소 밖의 비공개 환경 파일을 준비한다. 파일 권한은 `0600`으로 제한하며 실제 값은 Git·출력·보고서에 넣지 않는다.

```text
OKE_EMP_USER=<현재 직원 로그인 ID>
OKE_EMP_PASS=<현재 직원 비밀번호>
OKE_ADMIN_USER=<현재 관리자 로그인 ID>
OKE_ADMIN_PASS=<현재 관리자 비밀번호>
OKE_TEAM_KEY=<현재 n8n 문의 웹훅 키>
VM_WEB_URL=https://aio-t1.isitsoft.kr/ssh/
VM_USER=toor
VM_PASSWORD=<웹 SSH 비밀번호>
```

API 시험은 첫 비밀번호 변경이 완료된 기존 계정을 사용한다. 도구가 계정을 생성하거나 비밀번호를 초기화하지 않는다. 2026-11-08 조회 당시 직원 ID는 `user1`~`user4`, IT 관리자 ID는 `user5`·`admin`이었다. 이전 인계의 `teamtest.employee1`·`minji.admin`은 현재 VM에 없어 그대로 사용할 수 없다. 현재 값은 관리자의 인계 정보를 따른다.

## 1. 문의·티켓·알림 전체 연결과 중복 방지

저장소 루트에서 실행한다. Python 3.10 이상과 `uv`가 필요하다. `websockets`는 실행하는 PC에 설치되며 VM에는 패키지를 설치하지 않는다.

```sh
uv run --with websockets python eval/live_check.py \
  --env-file /path/to/private.env --vm-db \
  --output runs/live-smoke-new.json
```

실제 검사 내용:

1. 직원 로그인 후 비밀번호 규정 질문을 새 요청 ID로 3회 전송한다. 매회 자동 답변·`password-policy` 근거·티켓 없음·8초 이내를 확인한다. 첫 측정도 판정에 포함한다.
2. 정보 부족 질문을 `attempt=3`으로 전송해 실제 이관 티켓을 만든다.
3. VM PostgreSQL을 **읽기 전용 트랜잭션**으로 조회해 요청 ID, 문의·티켓 연결키, 직원 소유권, 응답의 티켓 번호, 알림 1건을 대조한다.
4. 같은 요청을 재전송한다. 티켓 번호 유지·`duplicate=true`와 두 번째 DB 조회의 문의·티켓·알림 각 1건을 확인한다.
5. 직원의 내 문의 조회, 직원의 관리자 접근 403, 관리자의 해당 티켓·알림 조회를 확인하고 로그아웃한다.

`--vm-db`를 생략하면 API 검사만 수행하고 결과를 `PARTIAL_NO_DB_RECEIPT`로 기록한다. DB 확인 없이 전체 PASS를 기록하지 않는다. 이 시험은 관리자 답변 수정·화면 클릭·장애 주입을 수행하지 않는다.

## 2. 기존 요청의 DB 연결만 확인

새 문의를 만들지 않고 기존 실요청의 저장 관계를 확인한다. 이 모드에는 `VM_PASSWORD`만 필요하며 로그인·API 재전송 시험으로 집계하지 않는다.

```sh
uv run --with websockets python eval/live_check.py \
  --env-file /path/to/private.env --receipt-only \
  --request-id qa-idempotency-93f0e5f3de6549109a17245cd1e84121 \
  --expected-ticket-id T-2030 \
  --output runs/db-link-new.json
```

2026-11-08 이 방법으로 확인한 결과는 [DB 연결 추가 확인](../runs/db-link-followup-20261108.json)에 있다. 문의·티켓·알림 각 1건, 완료 문의, 직원·연결키·응답 티켓 일치, 해당 요청 DLQ 0건을 확인했다.

## 3. 유휴 시간 후 정상 답변 응답 속도

`OKE_TEAM_KEY`로 인증하고 비밀번호 규정 질문을 3회 전송한다. 요청 사이에 20초를 기다려 이전 실행기 자동 종료 기준 15초보다 긴 유휴 구간을 포함한다. 숨은 예열 호출은 없다.

```sh
python3 eval/webhook_latency.py \
  --env-file /path/to/private.env --idle-seconds 20 \
  --output runs/workflow-latency-new.json
```

모든 요청의 HTTP 200, 자동 답변, 규정 출처, 티켓 없음, 8초 이내를 각각 검사한다. FastAPI·화면 경유 시험이나 전체 서비스 재시작 직후의 성능 시험은 아니다.

변경 전후 결과: [변경 전](../runs/workflow-latency-before-20261108.json) · [변경 후](../runs/workflow-latency-after-20261108.json).

## 4. n8n 노드별 시간 확인

위 결과의 요청 ID에 해당하는 n8n 실행 시간만 읽는다. 현재 팀 VM의 Node.js 내장 SQLite와 기존 `okeSupportFlow01` 실행 데이터를 사용한다. 원문 입력·답변·Credential은 내보내지 않는다.

```sh
uv run --with websockets python eval/execution_profile.py \
  --env-file /path/to/private.env \
  --input runs/workflow-latency-before-20261108.json \
  --input runs/workflow-latency-after-20261108.json \
  --output runs/workflow-node-timings-new.json
```

## 판정과 공식 도구와의 차이

이 도구는 위에 명시한 범위를 검사하는 팀 전용 검사기다. 공식 `flow.py test cases/common.json`의 공통 14종이나 `cases/team.json` 전체를 실행한 결과로 집계하지 않는다. 원본 기대값을 완화하거나 공식 러너의 통과 기록을 대신 만들지 않는다.

기존 공식 도구는 `X-Team-Key` 전송을 지원하지 않고, 팀 사례의 일부 추가 판정 필드도 해석하지 않는다. 따라서 단순 HTTP 성공만으로 공식 전체 시험 통과를 기록할 수 없다. 원본 도구·판정의 호환성은 별도 확인 사항이다.

보고서는 새 파일에만 쓰며 기존 증거를 덮어쓰지 않는다. 응답 원문·계정·비밀번호·세션·DB URL을 저장하지 않는다. 실패한 검사나 예외가 있으면 실패로 종료하며, DB 생략은 부분 확인으로 종료한다.

도구 자체 회귀 검사:

```sh
python3 -m unittest discover -s eval -p 'test_live_check.py'
```

이 회귀 검사는 합성 HTTP 서버를 사용한다. 위 실제 VM 시험과 구분한다.

## 5. 배포된 서비스의 요청 한 건에만 티켓 저장 장애 적용

`SERVICE_MODE=app`을 유지한 채 실제 티켓 API 실패와 알림·DLQ 저장, 동일 ID 재접수를 확인하려면 [티켓 저장 실패 시험](TICKET-FAULT.md)을 따른다. 운영자 전용 파일과 읽기 전용 연결이 배포되어 있어야 하며, data-api의 연습 모드 장애 스위치를 사용하지 않는다.
