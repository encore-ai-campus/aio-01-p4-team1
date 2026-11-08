# frontend · 웹 화면 제출 코드

`main-backup` 기준 커밋 `b8448d0`의 `develop/sueon/`에서 `src/`, `public/`, 의존성·잠금 파일과 Next.js·TypeScript 설정을 복사했다. 개발 원본과 VM 빌드 경로는 그대로 유지한다.

이 폴더에서 `pnpm install --frozen-lockfile` 후 `pnpm typecheck`, `pnpm build`를 실행한다. `pnpm test` 스크립트는 있지만 현재 원본에 테스트 파일이 없어 실행 시 종료 코드 1을 반환한다. 개발 서버는 `pnpm dev`이며, `BACKEND_ORIGIN`은 FastAPI 주소로 설정한다. 기본값은 `http://127.0.0.1:8000`이다. 로그인·관리자 등 실제 연동 절차는 [개발 원본 안내](../develop/sueon/README.md)를 따른다.

`node_modules/`, `.next/`, `trash-bin/`과 환경 파일은 취합하지 않았다. 화면은 FastAPI의 `/api/`를 프록시로 호출한다. 기능 수정은 개발 원본에서 진행한 뒤 제출본에 반영한다.

W03 제출 경로에서 pnpm 9.15.4로 잠금 파일 고정 설치, TypeScript 검사와 Next.js 프로덕션 빌드를 통과했다. 실제 VM·인증 사용자 흐름은 이번 이관에서 재시험하지 않았다.
