"""
Small helper for measuring elapsed wall-clock time in milliseconds.
"""

import time


class Timer:
    """Context-manager-free timer: call start(), then elapsed_ms() when done."""

    def __init__(self):
        self._start: float | None = None

    def start(self) -> None:
        self._start = time.perf_counter()

    def elapsed_ms(self) -> int:
        if self._start is None:
            raise RuntimeError("Timer.elapsed_ms() called before start()")
        return round((time.perf_counter() - self._start) * 1000)