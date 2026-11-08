# frontend · 직원·관리자 웹 화면

Next.js 코드·정적 자산·설정·의존성 잠금 파일을 포함한다. 이 폴더에서 다음을 실행한다.

```sh
npx --yes pnpm@9.15.4 install --frozen-lockfile
npx --yes pnpm@9.15.4 typecheck
npx --yes pnpm@9.15.4 build
```

개발 서버는 `npx --yes pnpm@9.15.4 dev`다. `BACKEND_ORIGIN`은 FastAPI 주소이며 기본값은 `http://127.0.0.1:8000`이다. 화면은 같은 출처의 `/api/`를 호출하고 Next.js 서버가 FastAPI로 프록시한다. `pnpm test` 스크립트는 있으나 현재 테스트 파일은 없다.

통합 실행·계정 초기화는 [로컬 배포 안내](../../deploy/LOCAL-MAC.md), 계정·권한·API는 [API 계약](../../docs/API-CONTRACT.md)을 따른다. build context는 이 `apps/frontend/`이며 환경 파일과 빌드 캐시는 제출하지 않는다.
