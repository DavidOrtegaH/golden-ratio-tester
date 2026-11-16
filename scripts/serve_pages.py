"""Local Pages preview with the actual repository subpath, no Django fallback."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent / 'artifacts' / 'pages'


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        prefix = '/golden-ratio-tester/'
        if not urlsplit(self.path).path.startswith(prefix):
            self.send_error(404)
            return
        self.path = self.path[len(prefix) - 1:]
        super().do_GET()

    def log_message(self, *_):
        pass


if __name__ == '__main__':
    print('http://127.0.0.1:8002/golden-ratio-tester/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8002), Handler).serve_forever()
