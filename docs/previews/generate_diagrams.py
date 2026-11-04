"""문서용 설계 SVG 생성. 서비스·n8n·DB에 접속하지 않는다."""
from pathlib import Path
from html import escape

OUT = Path(__file__).resolve().parents[1] / "images" / "planned"
COLORS = {"flow": "#245de8", "code": "#596d88", "ai": "#8755ce", "db": "#15836c", "branch": "#b47a24", "error": "#bd5050"}


def make(name, title, owner, nodes, edges, notes):
    width, height = 1380, 1030
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           f'<title id="title">{escape(title)}</title><desc id="desc">구현 전 설계안. {escape(owner)}. 노드 유형과 주요 분기를 설명한다.</desc>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#8092aa"/></marker></defs>',
           '<rect width="1380" height="1030" fill="#f4f7fc"/>',
           '<style>text{font-family:"Apple SD Gothic Neo","Malgun Gothic",sans-serif}.title{font-size:30px;font-weight:750;fill:#17243a}.sub{font-size:17px;fill:#61728b}.node{font-size:22px;font-weight:700;fill:#17243a}.type{font-size:14px;font-weight:700}.detail{font-size:17px;fill:#586b84}.label{font-size:15px;fill:#516883;paint-order:stroke;stroke:#f4f7fc;stroke-width:7px;stroke-linejoin:round}</style>',
           '<rect x="40" y="34" width="108" height="27" rx="13" fill="#e1eaff"/><text x="94" y="53" text-anchor="middle" font-size="13" fill="#245de8">구현 전 설계</text>',
           f'<text class="title" x="40" y="103">{escape(title)}</text>',
           f'<text class="sub" x="40" y="136">{escape(owner)}</text>']
    lookup = {n[0]: n for n in nodes}
    for src, dst, label, route in edges:
        a, b = lookup[src], lookup[dst]
        ax, ay, bx, by = a[1], a[2], b[1], b[2]
        if route:
            points = route
        elif ay == by:
            points = [(ax + 350 if bx > ax else ax, ay + 55), (bx if bx > ax else bx + 350, by + 55)]
        elif ax == bx:
            points = [(ax + 175, ay + 110), (bx + 175, by)]
        else:
            points = [(ax + 175, ay + 110), (ax + 175, by - 25), (bx + 175, by - 25), (bx + 175, by)]
        pts = " ".join(f"{x},{y}" for x, y in points)
        out.append(f'<polyline points="{pts}" fill="none" stroke="#8092aa" stroke-width="2.5" marker-end="url(#arrow)"/>')
        if label:
            x, y = points[len(points)//2]
            if len(points) == 2 and points[0][1] == points[1][1]:
                # 좌우 카드 사이 100px 안에서 긴 한글 연결 문구도 보이게 한다.
                lines, current, units = [], "", 0
                for char in label:
                    unit = 1 if ord(char) > 255 else 0.55
                    if units + unit > 6 and current:
                        lines.append(current.strip())
                        current, units = "", 0
                    current += char
                    units += unit
                if current.strip():
                    lines.append(current.strip())
                x = (points[0][0] + points[1][0]) / 2
                for i, part in enumerate(lines):
                    yy = y - 10 - (len(lines)-1-i)*17
                    out.append(f'<text class="label" style="font-size:13px" text-anchor="middle" x="{x}" y="{yy}">{escape(part)}</text>')
            elif max(px for px, _ in points) > 1300:
                y = (min(py for _, py in points) + max(py for _, py in points)) / 2
                for i, part in enumerate(label.split()):
                    out.append(f'<text class="label" style="font-size:13px" x="1300" y="{y+i*19}">{escape(part)}</text>')
            else:
                out.append(f'<text class="label" x="{x+8}" y="{y-10}">{escape(label)}</text>')
    for node_id, x, y, title_, type_, detail, kind in nodes:
        color = COLORS[kind]
        out += [f'<rect x="{x}" y="{y}" width="350" height="110" rx="13" fill="white" stroke="#dce4ef"/>',
                f'<rect x="{x}" y="{y}" width="6" height="110" rx="3" fill="{color}"/>',
                f'<text class="type" x="{x+19}" y="{y+26}" fill="{color}">{escape(type_)}</text>',
                f'<text class="node" x="{x+19}" y="{y+57}">{escape(title_)}</text>',
                f'<text class="detail" x="{x+19}" y="{y+86}">{escape(detail)}</text>']
    out.append('<rect x="40" y="884" width="1300" height="112" rx="12" fill="#eaf0fa"/>')
    for i, note in enumerate(notes):
        out.append(f'<text class="detail" x="60" y="{913+i*28}">{escape(note)}</text>')
    out.append('</svg>')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.svg").write_text("\n".join(out), encoding="utf-8")


def node(id_, col, row, title, type_, detail, kind="flow"):
    return (id_, 40 + col*450, 180 + row*175, title, type_, detail, kind)


def main():
    make("flow-support", "문의 본체 · oke-support", "다혁님 · 정해진 흐름을 Code / IF / Switch로 제어 · LLM 역할 3개", [
        node("a",0,0,"문의 받기","Webhook + Header Auth","공통 요청 · X-Team-Key"),
        node("b",1,0,"입력·직원·주입 검사","Code + HTTP Request","권한 확인 · 400 / 차단", "code"),
        node("c",2,0,"문의 분류","AI Agent · triage","유형 · 긴급도 · 부족한 정보", "ai"),
        node("d",2,1,"보완·긴급·답변 분기","Switch / IF","attempt 1·2 질문 / 3 이상 이관", "branch"),
        node("e",1,1,"검색·본인 접수 조회","HTTP Request ×2 → Merge","oke-search + 기존 티켓 조회"),
        node("f",0,1,"근거로 답변 초안","AI Agent · writer + Code","허용 근거만 · 출처 형식 검사", "ai"),
        node("g",0,2,"초안 검증","AI Agent · verifier + Code","근거 · 정책 · 개인정보 확인", "ai"),
        node("h",1,2,"최종 처리 결정","Code / IF","점수·검증·권한 모두 확인", "code"),
        node("i",2,2,"응답 조합·전달","Code → Respond to Webhook","route · 근거 · ticket · security"),
        node("j",2,3,"IT팀 접수 호출","HTTP Request · oke-handoff","티켓·알림 결과 보존")],
        [("a","b","",None),("b","c","",None),("c","d","",None),("d","e","답변 경로",None),("e","f","허용 근거",None),("f","g","",None),("g","h","",None),("h","i","검증 통과",None),
         ("d","i","보완 질문",None),("d","j","긴급·조치",[(1290,410),(1330,410),(1330,760),(1290,760)]),
         ("h","j","근거·검증 부족",[(665,640),(665,760),(940,760)]),
         ("j","i","이관 결과",[(1115,705),(1115,640)])],
        ["긴급은 이관을 먼저 시도한 뒤 근거·본인 상태를 보강한다. 후속 실패로 재접수하지 않는다.","검색·접수는 두 갈래 구조이며 실제 동시 실행·소요시간은 구현 후 확인한다.","각 Agent에 Chat Model 연결. 검색은 HTTP/DB 처리이고 추가 LLM Agent로 세지 않는다."])
    make("flow-index", "규정 색인 · oke-index", "유빈님 · 지혜님이 준비한 rag 테이블에 문서 단위로 저장", [
        node("a",0,0,"색인 요청","Webhook + Header Auth","수동 색인 · 설정·원본 확인"),
        node("b",1,0,"규정 목록·본문 가져오기","HTTP Request → Split Out","/docs · 문서별 본문 조회"),
        node("c",2,0,"권한·해시·청크 만들기","Code","all / it · 절 단위 기본청킹", "code"),
        node("d",2,1,"변경 여부 확인","IF / Code","같은 원본·설정이면 건너뜀", "branch"),
        node("e",1,1,"문서 임베딩","HTTP Request · 임베딩 API안","동일 모델 · 유한 수치 3072개"),
        node("f",0,1,"문서·청크 교체","Postgres · 단일 거래","rag.documents / rag.chunks", "db"),
        node("g",0,2,"처리 결과 집계","Code → Respond to Webhook","성공·건너뜀·실패와 건수", "code"),
        node("h",2,2,"실패 문서 기록","오류 출력 → Code","부분 저장 금지 · 다음 실행 재처리", "error")],
        [("a","b","",None),("b","c","",None),("c","d","",None),("d","e","변경 있음",None),("e","f","검증한 벡터",None),("f","g","",None),("d","h","권한·형식 오류",None),
         ("e","h","임베딩 오류",[(840,410),(885,410),(885,510),(1000,510),(1000,530)]),("h","g","실패 집계",None),
         ("d","g","변경 없음",[(1290,410),(1330,410),(1330,690),(215,690),(215,640)]),
         ("f","h","DB 실패",[(215,465),(215,505),(1115,505),(1115,530)])],
        ["임베딩 호출 방식은 초기 구현안이다. 참조 In-Memory 저장 노드를 그대로 운영에 쓰지 않는다.","DB 교체는 한 연결의 거래로 구현한다. 필요한 DB 함수·마이그레이션은 지혜님과 연결한다.","원본 삭제·권한 축소 시 이전 공개 청크가 검색되지 않게 처리하고 별도 시험한다."])
    make("flow-search", "권한별 검색 · oke-search", "유빈님 · 본체가 검증한 access_levels로 후보를 먼저 제한", [
        node("a",0,0,"검색 요청","Webhook + Header Auth","query · access_levels · top_k"),
        node("b",1,0,"요청·권한 목록 검사","Code / IF","허용된 all 또는 all+it", "code"),
        node("c",2,0,"질의 임베딩","HTTP Request · 임베딩 API안","문서와 같은 모델·3072차원"),
        node("d",2,1,"허용 후보에서 검색","Postgres · 바인딩 쿼리","권한 WHERE → cosine → top3", "db"),
        node("e",1,1,"근거 응답 구성","Code","doc · section · text · score", "code"),
        node("f",0,1,"검색 결과 반환","Respond to Webhook","200 · 근거 있음 또는 빈 목록"),
        node("g",2,2,"장애 응답","오류 출력 → Respond","503 · search_unavailable", "error")],
        [("a","b","",None),("b","c","",None),("c","d","",None),("d","e","",None),("e","f","",None),("c","g","API 장애",[(1290,235),(1330,235),(1330,585),(1290,585)]),("d","g","DB 장애",None)],
        ["일반 직원에게 it 문서가 후보·근거·LLM 입력으로 들어가지 않아야 한다.","빈 후보는 200 / no_evidence, 검색 장애는 503으로 구분한다. 입력 오류 세부는 계약에 반영 후 적용.","점수는 1 - cosine distance. 자동 답변 임계값은 측정 후 본체와 함께 확정한다."])
    make("flow-handoff", "티켓·알림·실패 수습 · oke-handoff", "원민님 · 업무 이관 모듈이며 Agent 간 자율 Handoff 패턴이 아님", [
        node("a",0,0,"이관 요청·입력 검사","Webhook → Code","검증한 직원 · request_id · priority"),
        node("b",1,0,"저장 대상 선택","Switch · SERVICE_MODE","app: FastAPI / practice: data-api", "branch"),
        node("c",2,0,"티켓 생성·중복 확인","HTTP Request · POST /tickets","key = request_id · 같은 티켓"),
        node("d",2,1,"상태별 제한 재시도","IF / Code","401·403 무재시도 · 시간 상한", "branch"),
        node("e",1,1,"티켓 결과 보존","Code","성공·중복·불명확·실패 구별", "code"),
        node("f",0,1,"알림 저장","HTTP Request · POST /alerts","app은 event_key 중복 억제"),
        node("g",0,2,"미완료 작업 보관","HTTP Request · POST /dlq","필요할 때 · 실패 단계·가린 입력"),
        node("h",1,2,"ACK로 결과 조합","Code","ticket · reason · alerted · dlq", "code"),
        node("i",2,2,"본체에 결과 반환","Respond to Webhook","예상 저장 장애도 처리 결과 전달")],
        [("a","b","",None),("b","c","",None),("c","d","",None),("d","e","완료·상한 도달",None),("e","f","",None),("f","g","실패 시도 독립",None),("g","h","",None),("h","i","",None),
         ("d","c","일시 오류·동일 키",[(1290,410),(1330,410),(1330,235),(1290,235)])],
        ["티켓 성공·알림 실패면 티켓은 유지하고 미완료 알림 단계만 복구한다. 정상은 DLQ를 만들지 않는다.","알림 실패로 DLQ 시도를 건너뛰지 않는다. 모든 플래그는 실제 저장 ACK 기준.","두 모드는 한 대상만 활성화하며 DLQ 요청·응답 형식은 대상별 어댑터로 맞춘다."])
    make("flow-errors", "예상 밖 오류 안전망 · oke-errors", "원민님 · 오류 원본 실행과 연결하고 수습 경로가 다시 무한 호출되지 않게 종료", [
        node("a",0,0,"예상 밖 실행 실패","Error Trigger","게시·부모 errorWorkflow 설정" ,"error"),
        node("b",1,0,"가린 오류 요약","Code","execution ID · 노드 · 사유", "code"),
        node("c",2,0,"기록 대상 선택","Switch · SERVICE_MODE","app / practice 중 하나", "branch"),
        node("d",2,1,"운영 알림 시도","HTTP Request · /alerts","요청·비밀번호·stack 원문 제외"),
        node("e",1,1,"DLQ 기록 시도","HTTP Request · /dlq","request_id 미상이면 execution_ref"),
        node("f",0,1,"수습 결과 기록·종료","Code","각 ACK·실패를 구별 · 유한 종료", "code")],
        [("a","b","",None),("b","c","",None),("c","d","",None),("d","e","알림 실패도 계속",None),("e","f","",None)],
        ["예상 HTTP·LLM 장애는 본체/이관의 오류 출력에서 수습하고 이 모듈은 예상 밖 버그를 맡는다.","이 흐름은 부모 Webhook에 대신 응답하지 않는다. errors 자신을 자기 Error Workflow로 연결하지 않는다.","오류 재현·부모 실행 ID·수습 실행 ID·알림/DLQ 결과는 원민님 보고서로 전달한다."])
    make("flow-backend", "로그인·권한·업무 저장 연결", "지혜님 · 수언님 화면 / 다혁님 본체 / 원민님 저장 호출 / 유빈님 DB 연결", [
        node("a",0,0,"직원·관리자 화면","Next.js · 수언님","브라우저는 같은 출처 /api만"),
        node("b",1,0,"인증·업무 API","FastAPI · 지혜님","세션·권한·Pydantic·소유권"),
        node("c",2,0,"문의 판단 요청","HTTP · oke-support","제공 직원 name과 공통 요청"),
        node("d",2,1,"새 업무 저장 API","/tickets · /alerts · /dlq","별도 X-Api-Key · 원민님 연결"),
        node("e",1,1,"업무 DB·거래","PostgreSQL · app","계정·문의·티켓·알림·DLQ", "db"),
        node("f",0,1,"RAG 저장 기반","PostgreSQL + pgvector · rag","DDL 지혜님 / 색인·검색 유빈님", "db")],
        [("a","b","",None),("b","c","",None),("c","d","이관 모듈에서",None),("d","e","",None),("b","e","업무 기록",None),("e","f","같은 인스턴스·별도 스키마",None)],
        ["관리자 발급·첫 비밀번호 변경·직원 본인 기록·IT팀 관리자 권한을 서버에서 검사한다.","기본 데이터 6명, 새 티켓 T-2001부터. 담당자 assignee는 IT팀 직원 employees.id.","실제 제공 API·DB·실행법과 OpenAPI가 준비되면 각 소비자가 Mock에서 실제 호출로 연결한다."])
    make("flow-team", "기능을 연결하는 여섯 역할", "오현님은 공통 기준·우선순위·인계 결과·병합·시연 준비를 관리", [
        node("a",0,0,"수언님 · 사용자 화면","로그인 / 질문 / 관리자","직원이 사용할 화면과 API 연결"),
        node("b",1,0,"지혜님 · API·DB·환경","FastAPI / PostgreSQL / Compose","신원·저장·공통 실행 기반", "db"),
        node("c",2,0,"다혁님 · 문의 본체","oke-support / LLM 3역할","분류·보완·답변·검증", "ai"),
        node("d",2,1,"유빈님 · 근거 검색","oke-index / oke-search","문서 → 벡터 → 권한별 근거", "db"),
        node("e",1,1,"원민님 · 이관·시험","oke-handoff / oke-errors","중복·오류 수습·시험 보고서", "error"),
        node("f",0,1,"오현님 · 통합 관리","변경 파일 / 확인 방법 / 실제 결과","담당별 인계·막힘·배포·제출", "code")],
        [("a","b","화면↔API",None),("b","c","같은 공통 요청",None),("c","d","검색 계약",None),("d","e","권한·장애 시험 자료",None),("e","f","시험·수정·재시험",None)],
        ["흐름은 주요 인계 관계다. 상세 연결 상대는 개인 README와 COORDINATION의 C01~C09를 따른다.","개인 폴더에서 기본안대로 개발하고, 공통 계약 변경 때만 지정 상대와 검토한다.","P0 기반 → P1 필수 연결·시험 → P2 선택 고도화. 구현 상태와 결정 상태를 따로 기록한다."])


if __name__ == "__main__":
    main()
