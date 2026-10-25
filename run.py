"""AI School OS - Phase 3B/4.2 dev server.

Launches the FastAPI application which:
  * exposes the JSON REST API under /api/ (including /api/chat)
  * serves the refactored frontend from app/ (index.html, dashboard.html,
    classroom.html, css/, js/, assets/)

Run:
    python run.py   # then open http://localhost:8000/
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
PORT = int(os.environ.get("PORT", "8000"))


def main() -> None:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"AI School OS serving http://localhost:{PORT}/")
    print(f"Frontend static files: {APP_DIR}")
    uvicorn.run("core.main:app", host="127.0.0.1", port=PORT, reload=False)


if __name__ == "__main__":
    main()
