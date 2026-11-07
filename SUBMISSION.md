# submission · 제출 준비 브랜치

이 브랜치는 **오현님만 수정·커밋·병합·푸시**한다. 팀원은 main에 통합할 개인 개발 작업을 진행하고, 검토된 결과를 오현님에게 전달한다. 이는 팀 운영 공지이며 GitHub 권한·브랜치 보호를 설정했다는 뜻은 아니다.

현재 추가한 것은 제출용 9개 폴더의 README 안내뿐이다. 코드·워크플로우·데이터·시험 결과는 아직 취합하지 않았다. Git은 빈 디렉터리를 추적하지 않으므로 각 폴더의 README로 목적과 받을 결과를 안내한다.

## 폴더별 취합 대상

| 제출 폴더 | 받을 결과 | 개발 자료 제공 |
| --- | --- | --- |
| [frontend/](frontend/README.md) | 실행 가능한 웹 화면·의존성·빌드 설정 | 수언님 |
| [backend/](backend/README.md) | FastAPI·DB 모델·마이그레이션·의존성 | 지혜님 |
| [deploy/](deploy/README.md) | Compose·Dockerfile·환경변수 안내·배포 절차 | 지혜님, 수언님 화면 설정 |
| [workflows/](workflows/README.md) | 실제 n8n JSON 5종 | 다혁님·유빈님·원민님 |
| [knowledge/](knowledge/README.md) | 실제 사용한 지식 문서·출처·권한 정보 | 유빈님 |
| [data/](data/README.md) | 실제 사용한 가상 초기 데이터·매핑·준비 방법 | 지혜님·유빈님 |
| [cases/](cases/README.md) | 제공 공통 시나리오·팀 시나리오 5개 이상 | 원민님 |
| [requests/](requests/README.md) | 재현 가능한 시연·성능 측정 요청 | 원민님 |
| [runs/](runs/README.md) | 실제 시험·측정·실패·재시험 보고서 | 원민님, 기능 담당자 근거 |

개발 원본은 main의 develop/ 아래에 둔다. 기능 수정은 원본에서 먼저 진행한다. 오현님은 검토한 main 커밋을 기록하고 해당 결과를 제출 경로로 취합한다. 폴더를 옮긴 뒤 import·빌드 경로·Compose context·워크플로우 참조·시험 경로는 실제로 다시 검증해야 한다. 현재 안내가 실행 가능한 제출본을 뜻하지 않는다.

## 공통 문서는 main에서만 수정

- docs/ 전체와 기존 루트 공통 문서·계약·설정은 **main이 원본**이다. submission에서 직접 수정하거나 별도 제출 사본으로 복제하지 않는다.
- 문서의 내용·링크·경로를 바꿔야 하면 main에서 먼저 수정·검토한다. 개발 경로와 제출 경로가 다르면 main 문서에서 둘을 구분한다.
- main의 변경은 **main → submission merge로만** 가져온다. 파일 복사·cherry-pick·squash로 문서를 따로 동기화하지 않는다.
- submission → main 역병합은 하지 않는다. 제출본에서 발견한 기능·문서 문제는 main 원본에서 수정한 뒤 다시 반영한다.
- 병합 중 docs/ 충돌이 발생하면 중단하고 원인을 확인한다. submission 전용 문서 수정으로 해결해 두 원본을 만들지 않는다.
- 이 SUBMISSION.md와 위 9개 폴더 README는 제출 브랜치 전용 안내다. 공통 설계·실행 결과의 별도 원본으로 사용하지 않는다.

작업 트리가 깨끗한 상태에서 오현님이 최신 main을 확인한 뒤 다음 순서로 반영한다.

```sh
git fetch github
git switch main
git merge --ff-only github/main
git switch submission
git merge main
git diff main -- docs/
git push github submission
git switch main
```

git diff main -- docs/ 결과는 비어 있어야 한다. 충돌·검사 실패 시에는 push하지 않고 원인을 해결한다. 이 명령은 배포·시험을 대신하지 않는다.

## 최종 제출 기준 · Default branch

**선생님 제출 기준은 최종 제출 저장소의 기본 브랜치(Default branch)의 마지막 커밋이다.** submission 브랜치를 푸시한 것만으로 최종 제출이 완료되지 않는다.

최종 제출 시 오현님이 제출처·기본 브랜치를 확인하고, 검증한 submission 결과가 그 기본 브랜치에 반영됐는지 확인한다. 개발용 main으로 역병합해 제출하는 방식은 이 운영 규칙에 포함하지 않는다. 현재 저장소의 기본 브랜치·공개 범위·보호 설정은 이번 작업에서 변경하지 않는다.

과정 자료의 비공개 저장소·강사 초대·82일차 14:50 마감 기준과 최종 공지를 확인한다. 마감 이후에는 제출 커밋을 수정하지 않는다. 포크 여부와 제출처 권한은 최종 안내에 맞춘다.

공통 주제·설계·결과 문서는 [docs/](docs/README.md), 기존 취합 기준은 [팀장 제출 안내](develop/ohyun/SUBMISSION.md)를 참고한다. 기존 안내의 경로와 다른 제출 배치·실행법은 취합 단계에서 main 공통 문서에 먼저 반영한다.
