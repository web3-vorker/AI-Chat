import http.server
import os
import socketserver
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    os.chdir(root)

    port = int(os.getenv("PORT", "5500"))

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving frontend from {root}")
        print(f"URL: http://127.0.0.1:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()

