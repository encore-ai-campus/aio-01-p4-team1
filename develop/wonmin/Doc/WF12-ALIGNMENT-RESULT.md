# 다혁 요청 WF-12·배포 출처 정합성 보완 · 2026-11-05

사용자가 전달한 팀장 WF-12 결정과 다혁님 `b9752869ae62d8a12b1395110d21ff68a4388181`을 기준으로 확인·보완했다. 다혁 최신 커밋은 원민 브랜치에 충돌 없이 병합했다(132533b). **공통 cases/team.json은 이번 사용자 요청에 명시된 수정 대상으로만 변경했다.** 다른 루트·공통 문서나 팀원 소스는 직접 수정하지 않았다.

## 원인과 수정 파일

1. **TM-05 기대/조건이 이전 결정에 남아 있었다.** 공통 `cases/team.json`과 원민 `develop/wonmin/cases/team.json` 모두 일반 직원에게 security-incident 근거를 요구하고 보안 규정 색인을 선행조건으로 뒀다. 최신 본체의 올바른 빈 sources 응답을 실패시키면서 IT 문서가 섞인 응답을 허용할 수 있었다.
   - 두 사본의 TM-05만 `equals.sources=[]`로 바꾸고 source_docs_include를 제거했다. 조건은 긴급 티켓·알림 저장과 본인 T-1002 조회 준비로 정리했다.
   - answer의 신규 긴급 티켓 ID·사내망 분리·본인 상태와 알림 ACK는 계속 요구한다. 입력·ID·priority=high·부작용·실행 상태는 변경하지 않았다. 실제 접수 ID를 시험 기대값으로 고정하지 않는다.
   - 같은 오래된 기대가 있던 원민 `Doc/SPEC.md`와 시연 설명 `Doc/IMP-PLAN.md`도 갱신했다. 제공 common.json의 기대를 변경한 작업이 아니다.
2. **배포 출처와 실제 읽는 파일이 분리돼 있었다.** `tools/prepare-team-deploy.py`는 다혁 SOURCES를859e3af로 기록하면서 workflow는 작업 폴더에서 읽었다. 최신/미커밋 파일이 섞여도 과거 커밋의 배포물처럼 보일 수 있었고, 다혁 커밋에는 병합 여부 확인도 없었다.
   - 다혁 pin을 승인된 b975286으로 갱신했다. 팀 workflow는 해당 커밋의 Git blob을 직접 읽고 source_commit/source_sha256/source_kind를 함께 기록한다.
   - 모든 팀 소스가 현재 브랜치에 병합돼 있는지 파일 생성 전에 확인한다. 원민 소스는 작업 폴더에서 읽는다는 점을 source_kind=working_tree, source_commit=null로 명시한다. pin은 검증한 버전을 명시적으로 갱신하는 방식이며 네트워크의 최신 HEAD를 자동 배포하지 않는다.

## 확인 방법과 실제 결과

- 수정 전 실패 재현: 새 WF-12 시험8개 중4개 실패(정상 응답 거절·IT 문서 누출 허용), 실제 임시 Git 저장소를 사용하는 배포 시험3개 모두 실패했다.
- 수정 후 원민 Node 전체 **97 passed**, Python 배포 시험 **3 passed**. WF-12 시험은 배포 설정의 실제 pin을 읽어 해당 Git blob의 N22 Code를 실행하므로, 예전 pin으로 되돌려 사내망 안내·본인 상태가 사라지는 회귀도 잡는다.
- WF-12는 이관/high·sources=[]·긴급 티켓 ID·사내망 분리·본인 T-1002 상태, 타인 상태 미노출, alerts_down의 티켓 보존, tickets_down의 확인 불가 문구를 검사했다. 비보안 tickets_down에도 B안 문구가 적용되는 것을 확인했다.
- Python은 실제 Git/파일 I/O로 pin과 다른 미커밋 파일의 혼입 방지, pin 갱신 시 새 코드 반영, 미병합 다혁 커밋 거절을 확인했다.
- 다혁 기존 HTTP adapter **12/12**, retrieval Mock **9/9** 통과. 두 도구는 실제 n8n/HTTP 시험이 아니다.
- 실제 준비 도구를 실행해 support source_commit=b975286, 원본 SHA-256=38e4d615a37e0d7bb0c3f66e0000d36286a6b6ef2001f2568f08152e6f1497b3을 확인했다.

근거: [합성 Code 결과·회귀 집계](../runs/wf12-alignment-20261105T074522Z.json), [실제 n8n 변경·보존 대조](../runs/wf12-n8n-update-20261105T074133Z.json). 합성 예시 티켓 T-2999는 실제 발급/저장 증거가 아니다. 공식 flow.py 검사는 별도 미실행이다.

## 현재 n8n 반영

로컬 Ubuntu lab의 [oke-support](http://127.0.0.1:15678/workflow/wmsup6dde10727e)를 먼저 private 백업했다. 기존 N22가 알려진859e3af/b975286 코드인지 확인한 뒤, 최신 커밋에서 달라진 노드가 N22 하나뿐인 것을 대조하고 그 Code만 교체했다. 다른 노드·Credential·모델·연결·Settings·게시 상태는 보존했으며 재가져오기/게시/재시작 후 실제 저장된 코드 해시까지 확인했다. 키 없는 support 요청은 HTTP403이었다. 공용 원격 팀 VM 배포 결과가 아니다.

전체 WF-12 HTTP와 실제 긴급 티켓/알림 ACK는 아직 직원·기존 티켓 data-api가 연결되지 않아 미실행이다. 일반 직원의 이 사례에는 보안 문서 색인이나 실제 검색 근거가 선행조건이 아니다. 기존 C05 실제 저장 미구현 상태도 이번 수정으로 해결됐다고 표시하지 않는다.

## 다음 연결 상대

- 다혁님: 두 TM-05 기대와 배포 출처를 최신 결정에 맞췄고 B안/WF-12 코드를 로컬 n8n에 반영했다. Code 검증과 전체 업무 HTTP 결과를 구분해 전달한다.
- 오현님: docs/EVALUATION-GUIDE.md의 WF-12에는 이전 security-incident 근거 설명이 남아 있다. 공통 문서 소유자가 사용자 전달 팀장 결정에 맞춰 정리할 항목으로 인계한다. 루트 공식 workflow snapshot도 최신 개발본과 별도 관리하므로 최종 평가 대상 버전을 대조한다.
- 직원·티켓 data-api와 저장 API가 준비되면 같은 TM-05 입력으로 실제 티켓1건·알림 ACK·본인 상태·sources=[]를 다시 확인한다. 다른 팀 기대나 common 원본을 시험 통과 목적으로 완화하지 않는다.
