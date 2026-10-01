"""Narrow credential-free Ollama gateway for disposable worker containers."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

BODY_TIMEOUT = 10


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(BODY_TIMEOUT)

    def do_POST(self):
        # Never expose Ollama pull/create/delete/push or arbitrary upstream paths.
        if self.path not in {"/api/chat", "/api/generate", "/api/show"}:
            self.send_error(403)
            return
        try:
            self.connection.settimeout(BODY_TIMEOUT)
            lengths = self.headers.get_all("Content-Length", [])
            if self.headers.get("Transfer-Encoding") or len(lengths) != 1 or not lengths[0].isdigit():
                raise ValueError("framing")
            length = int(lengths[0])
            if not 0 < length <= 512_000:
                raise ValueError("size")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict) or body.get("model") != os.environ["SIGMA_GATEWAY_MODEL"]:
                raise ValueError("model")
            body["stream"] = False
            body["options"] = {"num_ctx": 8192, "num_predict": 4096}
            body["keep_alive"] = "5m"
            # Fixed local hostname; redirects and ambient proxies are disabled.
            request = Request("http://ollama:11434" + self.path,
                              data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            opener = build_opener(ProxyHandler({}), NoRedirect())
            with opener.open(request, timeout=300) as response:
                result = response.read(4 * 1024 * 1024 + 1)
            if len(result) > 4 * 1024 * 1024:
                raise ValueError("response size")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(result)))
            self.end_headers()
            self.wfile.write(result)
        except Exception:
            self.send_error(502, "Inference request rejected or unavailable")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    # A single bounded request at a time matches the shared Ollama parallelism.
    HTTPServer(("0.0.0.0", 8081), Handler).serve_forever()
