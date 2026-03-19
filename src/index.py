from __future__ import annotations

import argparse
import asyncio
import os
import platform
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import time
from typing import Callable, TypedDict

import webview


class BasicTaskResult(TypedDict):
    task: str
    message: str
    now: str
    platform: str
    python_version: str


class ActionResult(TypedDict):
    ok: bool
    message: str
    status: str


@dataclass(frozen=True)
class TaskStatus:
    IDLE: str = "idle"
    RUNNING: str = "running"
    CANCELED: str = "canceled"
    DONE: str = "done"
    FAILED: str = "failed"


class TaskState:
    def __init__(self) -> None:
        self.status = TaskStatus.IDLE
        self._window: webview.Window | None = None

    def attach_window(self, window: webview.Window) -> None:
        self._window = window
        self._window.state.task_status = TaskStatus.IDLE
        self._window.state.task_log = ""
        self._window.state.task_progress = 0
        self._window.state.ticker = int(time())

    def set_status(self, status: str) -> None:
        self.status = status
        if self._window is not None:
            self._window.state.task_status = status

    def set_progress(self, value: int) -> None:
        if self._window is not None:
            self._window.state.task_progress = value

    def log(self, message: str) -> None:
        if self._window is None:
            return
        current = self._window.state.task_log or ""
        self._window.state.task_log = f"{current}{message}\n"

    def clear_log(self) -> None:
        if self._window is None:
            return
        self._window.state.task_log = ""


async def run_heavy_task(
    task_name: str,
    report_progress: Callable[[int], None],
    log: Callable[[str], None],
) -> None:
    total_steps = 10
    log(f"Task started: {task_name}")
    for step in range(1, total_steps + 1):
        # Simulate async heavy work. Replace this part with real Playwright logic.
        await asyncio.sleep(100)
        progress = int(step * 100 / total_steps)
        report_progress(progress)
        log(f"[{task_name}] step {step}/{total_steps} ({progress}%)")
    log(f"Task finished: {task_name}")


class AsyncTaskManager:
    def __init__(self, state: TaskState) -> None:
        self._state = state
        self._loop = asyncio.new_event_loop()
        self._lock = threading.Lock()
        self._task: asyncio.Task[None] | None = None
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _heavy_task(self, task_name: str) -> None:
        await run_heavy_task(
            task_name=task_name,
            report_progress=self._state.set_progress,
            log=self._state.log,
        )

    def _on_task_done(self, task: asyncio.Task[None]) -> None:
        with self._lock:
            self._task = None
        if task.cancelled():
            self._state.set_status(TaskStatus.CANCELED)
            self._state.log("Task canceled")
            return
        exc = task.exception()
        if exc is not None:
            self._state.set_status(TaskStatus.FAILED)
            self._state.log(f"Task failed: {exc}")
            return
        self._state.set_status(TaskStatus.DONE)

    def _start_task_on_loop(self, task_name: str) -> None:
        with self._lock:
            if self._task is not None and not self._task.done():
                return
            self._task = self._loop.create_task(self._heavy_task(task_name))
            self._task.add_done_callback(self._on_task_done)
        self._state.set_status(TaskStatus.RUNNING)
        self._state.set_progress(0)

    def start(self, task_name: str = "heavy-demo") -> ActionResult:
        with self._lock:
            if self._task is not None and not self._task.done():
                return {
                    "ok": False,
                    "message": "任务已在运行中",
                    "status": self._state.status,
                }
        self._loop.call_soon_threadsafe(
            self._start_task_on_loop, task_name.strip() or "heavy-demo"
        )
        return {"ok": True, "message": "任务已启动", "status": TaskStatus.RUNNING}

    def stop(self) -> ActionResult:
        with self._lock:
            if self._task is None or self._task.done():
                return {
                    "ok": False,
                    "message": "当前没有运行中的任务",
                    "status": self._state.status,
                }
            task = self._task
        self._loop.call_soon_threadsafe(task.cancel)
        self._state.set_status(TaskStatus.CANCELED)
        self._state.log("Cancellation requested")
        return {"ok": True, "message": "已发送取消请求", "status": TaskStatus.CANCELED}


class Api:
    def __init__(self) -> None:
        self._state = TaskState()
        self._manager = AsyncTaskManager(self._state)

    def attach_window(self, window: webview.Window) -> None:
        self._state.attach_window(window)

    def run_basic_task(self, task: str = "demo task") -> BasicTaskResult:
        task_name = task.strip() or "demo task"
        return {
            "task": task_name,
            "message": f"Python completed task: {task_name}",
            "now": datetime.now().isoformat(timespec="seconds"),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        }

    def start_heavy_task(self, task_name: str = "heavy-demo") -> ActionResult:
        return self._manager.start(task_name)

    def stop_heavy_task(self) -> ActionResult:
        return self._manager.stop()

    def clear_task_log(self) -> ActionResult:
        self._state.clear_log()
        return {"ok": True, "message": "日志已清空", "status": self._state.status}


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
        frozen_base = Path(
            getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent)
        )
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

    api = Api()
    entrypoint = get_entrypoint(dev=args.dev)
    window = webview.create_window("pywebview-start", entrypoint, js_api=api)
    api.attach_window(window)
    window.events.loaded += lambda: update_ticker(window)
    webview.start(debug=args.dev)


if __name__ == "__main__":
    main()
