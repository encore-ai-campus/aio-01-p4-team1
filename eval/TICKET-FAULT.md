# 배포된 서비스의 티켓 저장 실패 시험

실제 직원 로그인 → FastAPI → n8n → 업무 PostgreSQL 경로에서 **지정한 요청의 티켓 저장만** 실패시킨다. `SERVICE_MODE=app`을 유지하며 별도 연습 환경이나 data-api 장애 스위치를 사용하지 않는다.

## 적용 범위와 접근 제한

- 운영자만 서버의 `/home/toor/.config/oke/ticket-fault/active.json`을 만든다. HTTP로 장애를 설정하는 API는 없다.
- 백엔드는 이 폴더를 `/run/oke-ticket-fault`에 **읽기 전용**으로 연결한다. 애플리케이션 사용자는 설정을 쓸 수 없다.
- `audit-fault-`와 임의의 32자리 16진수로 구성한 요청 ID가 정확히 일치할 때만 `/tickets`에 503을 반환한다. 기존 내부 API 인증은 그대로 필요하다.
- 설정은 최대 300초만 유효하다. 파일 삭제·만료·잘못된 내용은 모두 장애를 비활성화한다.
- 문의 저장, 다른 요청의 티켓 저장, 알림, DLQ 저장은 장애 대상으로 삼지 않는다.

이 시험은 티켓 API가 실패했지만 DB는 사용할 수 있는 상황을 확인한다. DB 전체가 중단된 상황이나 브라우저 클릭을 확인한 시험은 아니다.

## 자동 실행

[실서버 검사 안내](LIVE-CHECKS.md)의 비공개 환경 파일에서 현재 `VM_PASSWORD`, `OKE_EMP_USER`, `OKE_EMP_PASS`를 읽는다. 값은 명령 인자·보고서·Git에 기록하지 않는다.

```sh
uv run --with websockets python eval/ticket_fault_check.py \
  --env-file /path/to/private.env \
  --output runs/app-ticket-fault-new.json
```

도구는 다음 순서로 실행하며, 실제 시험용 문의·티켓·알림·DLQ 기록이 생성된다.

1. 직원 로그인 후 고유 요청 ID 하나에만 티켓 저장 장애를 설정한다.
2. “사내 식당 앱이 열리지 않아요. 담당자 점검을 요청합니다”를 전송한다.
3. HTTP 200의 안전 응답, `reason=tickets_down`, 티켓 없음, 문의 1건·실패 알림 1건·DLQ 1건을 확인한다.
4. 장애 설정을 유지한 상태에서 별도 비밀번호 규정 문의가 정상 자동 답변되는지 확인한다.
5. 설정을 해제하고 **같은 요청 ID와 입력**으로 다시 전송한다. 문의는 1건을 유지하고 연결된 티켓 1건·접수 알림 1건이 생성되는지 확인한다.
6. 직원의 ‘내 문의’에서 복구된 티켓을 조회하고 로그아웃한다.

오류가 발생해도 자신이 만든 장애 설정은 `finally`에서 해제한다. 연결이 끊겨 해제하지 못한 경우에도 300초 후 효력이 사라진다. 다른 운영자가 이미 설정한 파일은 덮어쓰거나 삭제하지 않는다.

기존 DLQ는 시험 후에도 `pending` 상태로 보존된다. 이 시험의 복구는 명시적인 동일 ID 재요청이며, DLQ가 자동으로 재처리되거나 삭제된다는 뜻은 아니다.

## 배포와 원복

현재 main의 `deploy/compose.vm.yaml`은 `TICKET_FAULT_DIR` 폴더를 백엔드에 읽기 전용으로 연결한다. 지정하지 않으면 `deploy/local/.private/ticket-fault`를 사용한다. VM에서는 `TICKET_FAULT_DIR=/home/toor/.config/oke/ticket-fault`로 운영자 폴더를 선택한다. 폴더에 `active.json`이 없으면 비활성 상태다.

기존 VM에는 현재 실행 이미지에서 백엔드의 설정·티켓 서비스·장애 제어 모듈 3개만 교체한 이미지를 적용했다. `/home/toor/.config/oke/ticket-fault.yaml`은 이미지·읽기 전용 폴더 연결과 `SERVICE_MODE=app`을 명시한다. VM checkout 전체나 n8n 워크플로우를 최신 main으로 바꾼 배포가 아니다.

기존 VM에서 백엔드를 다시 생성할 때는 기존 Compose와 비공개 설정에 이 overlay를 추가한다.

```sh
docker compose \
  --env-file /home/toor/n8n/day65-n8n/.env \
  --env-file /home/toor/Aio-4pj-1team/deploy/.env.vm \
  -f /home/toor/Aio-4pj-1team/deploy/compose.vm.yaml \
  -f /home/toor/.config/oke/ticket-fault.yaml -p oke \
  up -d --no-deps --no-build backend
```

장애 설정만 해제할 때는 자신이 설정한 요청 ID와 일치하는 `active.json`을 삭제한다. 코드 원복이 필요하면 [최종 배포 근거](../runs/ticket-fault-deploy-final-20261108.json)의 `rollback_image_tag`를 overlay 이미지로 지정하고 **`SERVICE_MODE=app`을 유지한 채** 위 명령으로 백엔드만 재생성한다. 기존 VM Compose의 기본 모드를 그대로 상속하면 `practice`로 바뀔 수 있으므로, 검사 도구도 `app` 모드가 아니면 시험을 시작하지 않는다.

## 확인 결과

[실제 app 모드 시험](../runs/app-ticket-fault-20261108T110410Z.json)의 16개 항목이 통과했다. 장애 요청은 3.156초에 HTTP 200·`tickets_down`·티켓 없음으로 응답했고, 문의 1건·실패 알림 1건·DLQ 1건이 저장됐다. 설정이 켜진 동안 다른 비밀번호 문의는 4.782초에 자동 답변됐다. 설정 해제 후 같은 요청 ID로 1.827초에 `T-2040`이 생성됐으며 문의·티켓 소유권과 응답 번호가 일치했다.

시험 후 장애 파일은 삭제됐고 backend는 `app` 모드다. [최종 배포 확인](../runs/ticket-fault-deploy-final-20261108.json)에서 다른 8개 컨테이너의 ID·기동 시각과 배포 소스 해시를 대조했다. 앞선 배포·집계 실패와 `practice` 모드의 불완전 시험은 [실행 결과서](../docs/EXECUTION-RESULT.md)에 구분해 남긴다.
