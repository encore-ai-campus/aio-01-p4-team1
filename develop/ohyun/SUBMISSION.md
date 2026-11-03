# 제출·배포 취합 · 오현님

개발 원본은 각자 이름 폴더에 둔다. 강사 안내의 루트 제출 경로는 제출 전 취합 단계에서 만든다.
현재는 아직 구현물이 없으므로 빈 JSON·가짜 결과서를 생성하지 않는다. 이 단계가 끝나기 전에는 제출 준비 완료로 표시하지 않는다.

## 취합 대상 · 저장소 루트 기준

| 개발 원본 | 제출 사본 |
| --- | --- |
| develop/dahyeok/workflows/oke-support.json | workflows/oke-support.json |
| develop/yubeen/workflows/oke-index.json · oke-search.json | workflows/의 같은 파일명 |
| develop/wonmin/workflows/oke-handoff.json · oke-errors.json | workflows/의 같은 파일명 |
| develop/wonmin/cases/team.json | cases/team.json |
| develop/wonmin/requests/의 실제 시연 JSON | requests/의 같은 파일명 |
| develop/wonmin/runs/의 실제 보고서 JSON | runs/의 같은 파일명 |
| docs/ 필수 문서·헌장·데일리·캡처 | 현재 루트 docs/에서 직접 관리 |

공통 기본 시나리오는 수업 키트 원본을 사용한다. 개인 원본과 제출 사본을 동시에 개발하지 않는다.
파일 수정은 개인 원본에서 하고, 리드가 승인한 기본 브랜치 커밋에서 최종 사본을 다시 취합한다.
제출 사본을 만든 뒤 경로를 고칠 때는 JSON에 하드코딩한 파일 경로·팀 시나리오의 before/after·README 명령도 확인한다.

## 완료 기준

- [ ] 역할별 PR을 검토·병합하고 소스 커밋을 기록했다.
- [ ] 위 표의 실제 파일을 누락 없이 취합했다. 빈 파일은 결과물로 인정하지 않는다.
- [ ] 수업 flow.py로 JSON을 검사하고 사람이 push·공통/팀 시험을 수행했다.
- [ ] 팀 VM에서 develop/jihye/deploy 설정으로 수언님·지혜님 서비스를 실행했다. Compose build context는 deploy 위치를 기준으로 지혜님 프로젝트는 .., 수언님 프로젝트는 ../../sueon 경로를 검토한다.
- [ ] 문서의 노드·측정값·보고서 링크·캡처가 실제 구현과 같다.
- [ ] 루트 README에 실제 설치·실행·push·test·시연 명령을 적었다.
- [ ] 비밀값·개인정보를 검사하고 82일차 마감 커밋을 확정했다.

위 명령·배포 설정은 아직 구현 전이다. 실행한 것처럼 작성하지 않는다.
취합 이후에도 웹·서버 소스는 이름 폴더에 둔다. GitHub 저장소 전체를 받아 실행하고, 폴더 하나만 별도로 배포하는 방식으로 가정하지 않는다.

원문: [강사 제출 구조](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/08-SUBMISSION.md).
