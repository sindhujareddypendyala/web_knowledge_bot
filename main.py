"""
Web Knowledge Bot Integrated Project Entrypoint.

Provides a unified interface to run backend services, bot chat loops, or test suites.
"""
from __future__ import annotations

import sys
import subprocess


def run_backend() -> None:
    print("🚀 Starting FastAPI backend server on http://127.0.0.1:8000 ...")
    try:
        subprocess.run(["uvicorn", "app:app", "--reload"], cwd="backend", shell=True)
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped.")


def run_bot() -> None:
    print("💬 Starting RAG Bot CLI chat loop...")
    try:
        subprocess.run(["python", "app.py"], cwd="bot", shell=True)
    except KeyboardInterrupt:
        print("\n👋 Bot CLI stopped.")


def run_tests() -> None:
    print("🧪 Running backend test suite...")
    subprocess.run(["python", "-m", "pytest"], cwd="backend", shell=True)


def print_help() -> None:
    print("=" * 60)
    print("Web Knowledge Bot Integrated Entrypoint")
    print("=" * 60)
    print("Commands:")
    print("  python main.py backend  - Start the FastAPI backend server")
    print("  python main.py bot      - Run the bot CLI chat loop")
    print("  python main.py test     - Run the backend test suite")
    print("=" * 60)


def main() -> None:
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1].lower().strip()
    if cmd == "backend":
        run_backend()
    elif cmd == "bot":
        run_bot()
    elif cmd == "test":
        run_tests()
    else:
        print(f"Unknown command: {cmd}")
        print_help()


if __name__ == "__main__":
    main()
