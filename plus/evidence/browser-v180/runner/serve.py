"""Static server for the lane-local v1.8.0 site. /r-shiny/shinylive/webr/ is served read-only from a
checkout whose tree for that path equals 1cb3f84 (tree b62859ec7fe6415e5562ecca33387c8f018bcfc9)."""
import functools, http.server, os, sys
site, webr, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
PREFIX = '/r-shiny/shinylive/webr/'
class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split('?', 1)[0].split('#', 1)[0]
        if p.startswith(PREFIX):
            rel = http.server.SimpleHTTPRequestHandler.translate_path(self, '/' + p[len(PREFIX):])
            return os.path.join(webr, os.path.relpath(rel, site))
        return super().translate_path(path)
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(H, directory=site)).serve_forever()
