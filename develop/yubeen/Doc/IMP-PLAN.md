# 지식 검색 RAG · IMP-PLAN

> 운영 기준: 팀장 배포 기본안으로 바로 구현한다. 이 문서의 기존 "합의·협의" 항목은 기준 적용 여부 확인이며, 기본안을 바꿀 때만 상대와 협의한다. 기준은 저장소 루트 docs/BASELINE-v0.md·DATA-AND-DB.md를 따른다.
작업 기준: [내 작업·협의 안내](WORK-GUIDE.md) · [내 협의 기록](HANDOFF.md). 공통 파일과 상대 폴더는 직접 고치지 않고 소유자에게 요청한다.

주 담당: **유빈님**. 지원 담당은 추가 배정.

> 상태: 단계 구성 초안. 모든 단계 미실행. 담당자가 SPEC의 요구 ID·실제 수정 파일·확인 명령을 채운 뒤 한 단계씩 구현한다.

## 파일 경계 · 저장소 루트 기준

`develop/yubeen/workflows/oke-index.json`과 `develop/yubeen/workflows/oke-search.json`. 본체 JSON의 검색 연결 변경은 문의 담당이 한다.

저장소는 PostgreSQL+pgvector다. 색인 구현 전에 지혜님과 확장·테이블·차원·권한을 합의한다. 테이블 변경은 지혜님의 마이그레이션에서 관리한다.

## 1단계 · 문서·검색 계약

- [ ] 할 일: 원본·권한 메타데이터와 search 입출력·오류 형식을 본체 담당과 정한다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: 일반/IT 권한과 빈 결과 예시 검토
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 2단계 · 색인

- [ ] 할 일: /docs를 읽어 청킹·임베딩·저장하고 분포와 권한별 색인 수를 잰다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: 실제 색인 수·메타데이터 확인
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 3단계 · 검색·품질

- [ ] 할 일: oke-search를 만들고 권한 필터·근거·검색 없음·품질 비교를 확인한다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: 문서별 근거와 일반/IT 권한 시험
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 4단계 · 연결·복구·문서

- [ ] 할 일: 본체와 연결하고 재색인·재시작 복구를 확인해 RAG 설계서에 측정값을 적는다.
- [ ] 연결된 SPEC ID: 담당자 작성
- [ ] 생성·수정 파일: 담당자 작성
- [ ] 확인 명령·시나리오: 담당자 작성
- [ ] 통과 기준: 복구 절차 재현과 관련 공통·팀 시나리오
- [ ] 실제 확인 결과·남은 문제·커밋: 실행 뒤 기록

## 단계별 에이전트 요청 예시

```text
이 역할의 SPEC.md와 IMP-PLAN.md, 공통 API-CONTRACT.md를 읽어.
내가 지정한 한 단계만 구현해. 담당 경로를 지키고 공통 계약 변경이 필요하면 영향을 알려줘.
수정 파일·검사 결과·내가 실행할 확인 명령을 보고해.
구현과 실제 확인을 구분하고, 확인 전 통과 체크를 하지 마.
```

단계 완료 후 담당자가 직접 확인하고 커밋한다. n8n push·test는 수업 규칙대로 사람이 수행한다. 다음 단계 진행 여부는 담당자가 판단하며, 기능이 연결되면 관련 회귀 시험을 한다.

## 공통 자료

- [주제](../../../docs/TOPIC.md) · [공통 API 계약](../../../docs/API-CONTRACT.md) · [역할표](../../../docs/ROLE-PLAN.md)
- [수업 방식과 연결 규칙](../../../docs/DEVELOPMENT-FLOW.md)
- 수업 원문: [05-RAG-DESIGN-GUIDE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/05-RAG-DESIGN-GUIDE.md) · [04-REFERENCE-ARCHITECTURE.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Lecture/80-82-Project/student/04-REFERENCE-ARCHITECTURE.md) · [VIBE-Q-TDOC.md](https://gl.isitsoft.kr/publicproj/aio-01d4-stu/-/blob/9ce9aceba6f66f2ec93a5a32ab23f3bedb06b9a4/Last3Mon/71/VIBE-Q-TDOC.md)
