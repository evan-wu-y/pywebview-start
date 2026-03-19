from __future__ import annotations

import argparse
import os
import platform
import sys
import threading
from datetime import datetime
from pathlib import Path
from time import time
from typing import TypedDict

import webview


class BasicTaskResult(TypedDict):
    task: str
    message: str
    now: str
    platform: str
    python_version: str


class Api:
    def run_basic_task(self, task: str = "demo task") -> BasicTaskResult:
        task_name = task.strip() or "demo task"
        return {
            "task": task_name,
            "message": f"Python completed task: {task_name}",
            "now": datetime.now().isoformat(timespec="seconds"),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        }


def set_interval(interval_seconds: float):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()

            def loop():
                while not stopped.wait(interval_seconds):
                    function(*args, **kwargs)

            thread = threading.Thread(target=loop, daemon=True)
            thread.start()
            return stopped

        return wrapper

    return decorator


@set_interval(1)
def update_ticker(window: webview.Window) -> None:
    window.state.ticker = int(time())


def get_entrypoint(dev: bool = False) -> str:
    dev_url = os.getenv("PYWEBVIEW_DEV_SERVER_URL", "http://localhost:5173")
    if dev:
        return dev_url

    candidates: list[Path] = []

    # PyInstaller runtime: bundled files are under sys._MEIPASS
    if getattr(sys, "frozen", False):
        frozen_base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend(
            [
                frozen_base / "gui" / "index.html",
                exe_dir / "gui" / "index.html",
            ]
        )

    root = Path(__file__).resolve().parent.parent
    candidates.extend(
        [
            root / "gui" / "index.html",
            root / "dist" / "index.html",
            root / "Resources" / "gui" / "index.html",
        ]
    )

    for path in candidates:
        if path.exists():
            return str(path)

    raise FileNotFoundError(
        "Cannot find frontend entrypoint. Run `pnpm frontend:dev` first, "
        "or launch with `python src/index.py --dev`."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pywebview app.")
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Load frontend from Vite dev server "
        "(PYWEBVIEW_DEV_SERVER_URL, default http://localhost:5173).",
    )
    args = parser.parse_args()

    entrypoint = get_entrypoint(dev=args.dev)
    window = webview.create_window("pywebview-start", entrypoint, js_api=Api())
    window.events.loaded += lambda: update_ticker(window)
    webview.start(debug=args.dev)


if __name__ == "__main__":
    main()
