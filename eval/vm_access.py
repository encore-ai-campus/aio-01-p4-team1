"""TLS-verified ttyd connection for read-only VM receipts; credentials stay in memory."""

import asyncio
import json
import re
import ssl
from uuid import uuid4
from urllib.parse import urlsplit


class VMTerminal:
    def __init__(self, url, username, password):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username:
            raise ValueError("VM_WEB_URL must be an HTTPS origin/path")
        self.url = f"wss://{parsed.netloc}{parsed.path.rstrip('/')}/ws"
        self.username, self.password = username, password
        self.buffer = ""

    async def __aenter__(self):
        import websockets
        self.ws = await websockets.connect(self.url, subprotocols=["tty"],
            ssl=ssl.create_default_context(), max_size=8_000_000,
            open_timeout=15, ping_interval=None)
        try:
            await self.ws.send(json.dumps({"AuthToken": "", "columns": 250, "rows": 50}))
            await self.until(r"login:\s*$")
            await self.send(self.username + "\r")
            await self.until(r"[Pp]assword:\s*$")
            self.buffer = ""
            await self.send(self.password + "\r")
            await self.until(r"[$#]\s*$")
        except BaseException:
            await self.ws.close()
            raise
        return self

    async def send(self, value):
        await self.ws.send(b"0" + value.encode())

    async def until(self, pattern, timeout=25):
        async def receive():
            while True:
                clean = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\r", "", self.buffer)
                if "Login incorrect" in clean or "Authentication failure" in clean:
                    raise PermissionError("VM authentication rejected")
                if re.search(pattern, clean):
                    return self.buffer
                value = await self.ws.recv()
                if isinstance(value, bytes):
                    value = value.decode("utf-8", "replace")
                if value.startswith("0"):
                    self.buffer += value[1:]
        return await asyncio.wait_for(receive(), timeout)

    async def run(self, command, timeout=30):
        mark = uuid4().hex
        self.buffer = ""
        await self.send(f"stty -echo; printf '\\nB{mark}\\n'; ( {command} ) 2>&1; printf '\\nE{mark}:%s\\n' $?\r")
        raw = await self.until(rf"E{mark}:\d+", timeout)
        clean = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\r", "", raw)
        body = clean.rsplit(f"B{mark}\n", 1)[-1]
        end = list(re.finditer(rf"E{mark}:(\d+)", body))[-1]
        return int(end.group(1)), body[:end.start()].strip()

    async def __aexit__(self, *exc):
        try:
            await self.send("exit\r")
        finally:
            await self.ws.close()
