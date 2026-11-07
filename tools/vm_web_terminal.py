#!/usr/bin/env python3
"""VM 웹 터미널(ttyd) 클라이언트 — SSH 포트가 닫혀 있고 https://aio-t1.isitsoft.kr/ssh/ 웹 터미널만 열려 있을 때,
브라우저 대신 그 웹 터미널에 붙어서 명령을 실행하고 파일을 주고받는다.

설치:  pip install websockets
설정 (환경변수, 저장소 루트 .env, 또는 이 파일 옆 .env):
  VM_WEB_URL   = https://aio-t1.isitsoft.kr/ssh/    (브라우저로 여는 웹 터미널 주소 · 기본값 설정됨)
  VM_USER      = toor
  VM_PASSWORD  = ****                               (.env에 넣어두면 무입력 자동 실행)

사용:
  python3 tools/vm_web_terminal.py run "docker ps"                   # 명령 실행 · 출력 · 종료 코드 그대로
  python3 tools/vm_web_terminal.py run "bash long.sh" --timeout 600  # 오래 걸리는 명령 (기본 120초)
  python3 tools/vm_web_terminal.py put ./local.tgz /home/toor/x.tgz  # 파일 올리기
  python3 tools/vm_web_terminal.py get /home/toor/out.json ./out.json  # 파일 받기
팁: 10분 넘는 작업은  run "nohup bash job.sh > ~/job.log 2>&1 &"  로 띄우고  run "tail -5 ~/job.log"  로 확인.
"""
import argparse, asyncio, base64, getpass, json, os, re, shlex, ssl, sys, uuid
from urllib.parse import urlparse

try:
    import websockets
except ImportError:
    sys.exit("websockets 패키지가 필요해요:  pip install websockets")

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\r")  # OSC는 BEL 또는 ESC\ 로 끝남 (VM 셸이 ESC]3008;…ESC\ 를 끼움)


def load_env() -> dict:
    env = {}
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)
    for path in (
        os.path.join(repo_root, ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(here, ".env"),
    ):
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    env.update({k: v for k, v in os.environ.items() if k.startswith("VM_")})
    return env


ENV = {}
WEB = ""
WS_URL = ""
USER = "toor"
PW = ""


def init_config() -> None:
    global ENV, WEB, WS_URL, USER, PW
    ENV = load_env()
    WEB = ENV.get("VM_WEB_URL", "https://aio-t1.isitsoft.kr/ssh/").rstrip("/")
    if not WEB:
        sys.exit("VM_WEB_URL을 정해 주세요 (예: https://aio-t1.isitsoft.kr/ssh/)")
    u = urlparse(WEB)
    WS_URL = f"{'wss' if u.scheme == 'https' else 'ws'}://{u.netloc}{u.path}/ws"
    USER = ENV.get("VM_USER", "toor")
    PW = ENV.get("VM_PASSWORD") or (getpass.getpass(f"{USER} 비밀번호: ") if sys.stdin.isatty() else "")
    if not PW:
        sys.exit("VM_PASSWORD가 설정되지 않았습니다. 저장소 루트 .env 파일에 VM_PASSWORD=... 를 추가해 주세요.")


class Term:
    """웹 터미널 한 번 접속 = 로그인 → 일 → exit"""

    def __init__(self):
        self.ws, self.buf = None, ""

    async def __aenter__(self):
        ssl_ctx = None
        if WS_URL.startswith("wss"):
            ssl_ctx = ssl.create_default_context()
            if ENV.get("VM_INSECURE_SSL", "1") == "1":  # macOS python.org 빌드는 인증서 체인 검증 실패 → 팀 VM 전용으로 끔
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
        self.ws = await websockets.connect(WS_URL, subprotocols=["tty"], ssl=ssl_ctx,
                                           max_size=None, open_timeout=20, ping_interval=None)
        await self.ws.send(json.dumps({"AuthToken": "", "columns": 250, "rows": 50}))
        await self.until(r"login:\s*$", 30)
        await self.send(USER + "\r")
        await self.until(r"[Pp]assword:\s*$")
        self.buf = ""
        await self.send(PW + "\r")
        await self.until(r"[$#]\s*$", 30)
        return self

    async def __aexit__(self, *exc):
        try:
            await self.send("exit\r")
            await self.ws.close()
        except Exception:
            pass

    async def send(self, text) -> None:
        await self.ws.send(b"0" + (text.encode() if isinstance(text, str) else text))

    async def until(self, pat: str, t: float = 25) -> str:
        loop = asyncio.get_event_loop()
        end = loop.time() + t
        while not re.search(pat, self.buf):
            left = end - loop.time()
            if left <= 0:
                raise TimeoutError(f"{pat!r} 를 기다리다 시간 초과. 마지막 화면: {ANSI.sub('', self.buf)[-300:]!r}")
            msg = await asyncio.wait_for(self.ws.recv(), left)
            if isinstance(msg, bytes):
                msg = msg.decode("utf-8", "replace")
            if msg[:1] == "0":  # ttyd: '0' = 터미널 출력
                self.buf += msg[1:]
        return self.buf

    async def run(self, cmd: str, timeout: float) -> tuple[int, str]:
        mark = uuid.uuid4().hex[:10]
        self.buf = ""
        await self.send(f"stty -echo; echo B{mark}; ( {cmd} ) 2>&1; echo E{mark}:$?\r")
        out = ANSI.sub("", await self.until(rf"E{mark}:\d+", timeout))
        body = out.rsplit(f"B{mark}\n", 1)[-1]
        m = list(re.finditer(rf"E{mark}:(\d+)", body))
        return (int(m[-1].group(1)) if m else 1), (body[:m[-1].start()] if m else body)


async def cmd_run(cmd: str, timeout: float) -> int:
    async with Term() as t:
        code, out = await t.run(cmd, timeout)
    sys.stdout.write(out.replace(PW, "***"))
    return code


async def cmd_put(local: str, remote: str) -> int:
    b64 = base64.b64encode(open(local, "rb").read())
    async with Term() as t:
        mark = uuid.uuid4().hex[:10]
        tmp = f"/tmp/.put-{mark}"
        remote_q = shlex.quote(remote)
        t.buf = ""
        # 터미널을 raw로 바꿔 base64를 줄 길이 제한 없이 흘려 넣고, 정확한 길이만큼만 읽음
        await t.send(f"stty raw -echo; head -c {len(b64)} > {tmp}; stty sane; base64 -d {tmp} > {remote_q} && rm -f {tmp} && wc -c {remote_q}; echo E{mark}:$?\r")
        await asyncio.sleep(1.0)
        for i in range(0, len(b64), 16384):
            await t.send(b64[i:i + 16384])
            await asyncio.sleep(0.02)
        out = ANSI.sub("", await t.until(rf"E{mark}:\d+", 300))
    m = list(re.finditer(rf"E{mark}:(\d+)", out))
    code = int(m[-1].group(1)) if m else 1
    print(f"올림 {local} → {remote} ({os.path.getsize(local)} bytes) · 종료 코드 {code}")
    return code


async def cmd_get(remote: str, local: str) -> int:
    async with Term() as t:
        code, out = await t.run(f"base64 -w0 -- {shlex.quote(remote)}", 300)
    if code != 0:
        sys.stderr.write(out)
        return code
    data = re.sub(r"[^A-Za-z0-9+/=]", "", out)
    open(local, "wb").write(base64.b64decode(data, validate=True))
    print(f"받음 {remote} → {local} ({os.path.getsize(local)} bytes)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="VM 웹 터미널(ttyd)로 명령 실행 · 파일 주고받기")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="명령 실행"); r.add_argument("command"); r.add_argument("--timeout", type=float, default=120)
    p = sub.add_parser("put", help="파일 올리기"); p.add_argument("local"); p.add_argument("remote")
    g = sub.add_parser("get", help="파일 받기"); g.add_argument("remote"); g.add_argument("local")
    a = ap.parse_args()
    init_config()
    if a.cmd == "run":
        return asyncio.run(cmd_run(a.command, a.timeout))
    if a.cmd == "put":
        return asyncio.run(cmd_put(a.local, a.remote))
    return asyncio.run(cmd_get(a.remote, a.local))


if __name__ == "__main__":
    sys.exit(main())
