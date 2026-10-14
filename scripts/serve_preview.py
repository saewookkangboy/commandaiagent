"""Local static preview with Vercel-like clean URLs and a real 404 status.
Production hosting uses the existing Vercel static dist configuration, not this server.
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import argparse

ROOT = Path(__file__).resolve().parents[1] / 'dist'

class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urlsplit(self.path).path
        resolved = Path(self.translate_path(path)).resolve()
        # Existing public directory routes serve their index without a redirect.
        if resolved.is_relative_to(ROOT) and (resolved / 'index.html').is_file():
            self.path = path.rstrip('/') + '/index.html'
        elif resolved.is_relative_to(ROOT) and resolved.with_suffix('.html').is_file() and not resolved.suffix:
            self.path = path + '.html'
        super().do_GET()

    def end_headers(self):
        self.send_header('X-Robots-Tag', 'noindex, nofollow')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        if code != 404:
            return super().send_error(code, message, explain)
        body = (ROOT / '404.html').read_bytes()
        self.send_response(404)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4173)
    args = parser.parse_args()
    print(f'Preview serving {ROOT} on 0.0.0.0:{args.port}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', args.port), PreviewHandler).serve_forever()
