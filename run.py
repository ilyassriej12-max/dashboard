"""AI School OS - Phase 3A frontend entry (static file server).

This is a lightweight development server for the refactored frontend.
It serves the app/ directory so dashboard.html / classroom.html partials
are loaded over HTTP (required for fetch() of the view partials).

Phase 3B will replace this with a FastAPI app mounting /api/dashboard
and /api/chat.
"""

from http.server import SimpleHTTPRequestHandler
import os
import sys

PORT = int(os.environ.get("PORT", "8000"))
APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def translate_path(self, path):
        # Serve index.html for the root path.
        path = super().translate_path(path)
        if os.path.isdir(path):
            index = os.path.join(path, "index.html")
            if os.path.exists(index):
                return index
        return path


def main():
    os.chdir(APP_DIR)
    handler = Handler
    with __import__("socketserver").TCPServer(("", PORT), handler) as httpd:
        print(f"AI School OS serving http://localhost:{PORT}/")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
