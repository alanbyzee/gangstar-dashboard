#!/usr/bin/env python3
"""
Gangstar 运营看板本地服务
- 静态托管本目录（HQ排期日历.html / Gangstar运营看板.html / fan_data.json ...）
- POST /api/fan-refresh  -> 写入刷新请求标记，并立即触发后台读取（subprocess 调 node refresh_fans.js --write）
  浏览器端「刷新粉丝数」按钮即调用此接口，真正读取 4 平台最新数据后写回 fan_data.json
- 对所有响应加 no-store，避免 fan_data.json 被缓存
"""
import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
REQ_PATH = os.path.abspath(os.path.join(ROOT, "..", ".workbuddy", "fan_refresh_request.json"))

NODE = "/Users/alan/.workbuddy/binaries/node/versions/22.22.2/bin/node"
NODE_PATH = "/Users/alan/.workbuddy/binaries/node/workspace/node_modules"
REFRESH_SCRIPT = os.path.join(ROOT, "refresh_fans.js")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        # 允许 file:// 直接打开的页面跨域访问（origin 为 null）
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path.rstrip("/") == "/api/fan-refresh":
            try:
                length = int(self.headers.get("Content-Length", 0) or 0)
                body = self.rfile.read(length) if length else b"{}"
                try:
                    payload = json.loads(body.decode("utf-8") or "{}")
                except Exception:
                    payload = {}
            except Exception:
                payload = {}
            req = {
                "pending": True,
                "requested_at": datetime.now(timezone.utc).isoformat(),
                "platforms": payload.get("platforms", ["instagram", "facebook", "youtube", "x"]),
            }
            try:
                os.makedirs(os.path.dirname(REQ_PATH), exist_ok=True)
                with open(REQ_PATH, "w", encoding="utf-8") as f:
                    json.dump(req, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            # 真正触发后台读取（subprocess 调 node 脚本，不阻塞当前响应）
            triggered = False
            try:
                env = os.environ.copy()
                env["NODE_PATH"] = NODE_PATH
                with open("/tmp/gangstar_refresh.log", "a") as logf:
                    subprocess.Popen(
                        [NODE, REFRESH_SCRIPT, "--write"],
                        env=env, cwd=ROOT, stdout=logf, stderr=subprocess.STDOUT,
                    )
                triggered = True
            except Exception as e:
                triggered = False
            if triggered:
                self._send_json({"ok": True, "msg": "刷新已触发，后台正在读取（约30秒），读取完成后看板会自动更新"})
            else:
                self._send_json({"ok": False, "msg": "刷新触发失败，请稍后重试或在对话里让我刷新"}, code=500)
        else:
            self._send_json({"ok": False, "error": "not found"}, code=404)

    def log_message(self, fmt, *args):
        sys.stdout.write("[gangstar-server] " + (fmt % args) + "\n")


def main():
    port = 8787
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Gangstar 运营看板服务已启动: http://127.0.0.1:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
