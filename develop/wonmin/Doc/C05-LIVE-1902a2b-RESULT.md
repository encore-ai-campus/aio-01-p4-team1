# C05 후속 검증 · 지혜1902a2b · 2026-11-05

지혜님 `feat/jihye-p0` 최신 `1902a2b14d6d3a21f80519ffe4a91565b26abb4c`를 가져와 원민 브랜치에 충돌 없이 병합했다(병합 커밋5928b77). 원격 브랜치도 재조회해 이 HEAD가 최신임을 확인했다. **새 완료 범위는 P0-6 직원 seed·첫 관리자 CLI이며 C05 실제 저장 검증은 계속 미구현으로 차단된다.**

## 변경 파일·실제 배포

- `deploy/compose.lab.yaml`, `tools/prepare-team-deploy.py`: backend 실행 snapshot을 4fdc313에서1902a2b로 갱신했다. 새 소스를 Git archive로 private `.runtime/peer-jihye-1902a2b`에 준비하고 잠금 의존성으로 이미지를 재빌드했다.
- 교체 전에 private PostgreSQL pg_dump와 이전 backend 이미지 ID를 보존했고 backend만 교체했다. 기존 볼륨·DB revision0004·로그인·Assistant 설정은 유지했다. 상대 소스·main·submission은 수정하지 않았고 push도 하지 않았다.
- `tools/verify-c05-live.py`: 실행 컨테이너의 snapshot commit과 C05 관련4개 파일뿐 아니라 신규 cli/bootstrap2개 파일 해시까지 병합 소스와 대조했다. 이전 백엔드로 시험한 결과가 아니다.

## 실제 결과

| 확인 | 결과 |
| --- | --- |
| 배포 source commit | **1902a2b** |
| backend 전체 시험 | **180 passed, 경고1건**. 단위/Mock 및 실제 PostgreSQL 시험 포함 |
| 원민 회귀 | **89 passed** |
| C05 HTTP33회 | 키 누락3회401, 나머지30회501 |
| 티켓 순차2·동시8·high | 모두501, 신규/중복 저장 검증 불가 |
| 알림 순차2·동시8·키 없음/null | 모두501, ACK 검증 불가 |
| DLQ 문자열/null request_id | 모두501, HTTP200 stored ACK 미확인 |
| 시험 DB 전후 | 티켓0→0, 알림0→0, DLQ0→0 |
| 별도 n8n app 경로 | HTTP200이지만 ok=false, ticket=null, reason=tickets_down, alerted=false, dlq=false |
| 시험 정리 | app 시험 사본 게시 해제. 일반 lab은 practice 모드 유지 |

새 bootstrap의 직원/관리자 시험 데이터는 테스트 자체의 거래 rollback으로 정리됐다. 실제 직원 원본/API 인증 확인과 영구 seed·첫 관리자 생성은 실행하지 않았다. employees도 시험 후0건이다. 전체180개 통과를 실제 업무 저장 성공이나 실제 관리자 발급 완료로 해석하지 않는다.

근거: [백엔드 전체180개](../runs/jihye-1902a2b-full-20261105T055426Z.json), [최신 배포의 C05 실제 HTTP·DB·n8n](../runs/c05-live-20261105T055450Z.json).

## 차단 원인과 지혜님 확인 요청

[지혜님 최신 README](https://github.com/hyunport/Aio-4pj-1team/blob/1902a2b/develop/jihye/README.md)의 현재 상태에도 내부키 검증·DB 저장은 미구현/미검증으로 기록돼 있다. `app/api/deps.py`의 require_internal_key는 키가 있으면501, get_backend는 UnavailableBackend를 반환하며 execute도501이다. `StoredResponse`도 여전히 stored/count만 있어 duplicate=true가 제거된다.

다음 반영 대상으로 실제 내부키 대조, 티켓/알림/DLQ 저장 서비스, duplicate 응답 필드, 직원 원본 seed 연결이 필요하다. **C05 저장 구현이 반영된 별도 커밋/브랜치가 있다면 해당 식별자로 배포 대상을 맞춘 뒤 재시험해야 한다.** 원민은 상대 구현을 대신 수정하지 않았다. 티켓1건·알림 실패 시 티켓 유지·실제 동시성/재시작 영속성은 아직 성공 전제에 도달하지 못했으므로 미검증으로 유지한다.
