"""Network performance: normal conditions vs a controlled busy link.

IMPORTANT: a ping test is NOT a bandwidth test. Here we create a controlled load
(parallel downloads) and watch how latency, jitter and packet loss CHANGE while the
link is busy. We do not report a "speed". The downloaded byte count only proves that
the load was really applied.
"""
from __future__ import annotations

import threading
import time
import urllib.request
from typing import Callable, List, Optional, Tuple

from .latency_check import measure_latency
from .models import LoadInfo, ProbeStats


class LoadGenerator:
    """Downloads a file in several threads to keep the link busy (download direction only)."""

    def __init__(self, url: str, threads: int = 4, chunk_size: int = 65536, opener: Callable = urllib.request.urlopen):
        self.url = url
        self.threads = threads
        self.chunk_size = chunk_size
        self._opener = opener
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._bytes = 0
        self._workers: List[threading.Thread] = []
        self.errors: List[str] = []
        self._started_at = 0.0
        self.duration_s = 0.0

    @property
    def bytes_downloaded(self) -> int:
        with self._lock:
            return self._bytes

    def _worker(self) -> None:
        failures = 0
        while not self._stop.is_set() and failures < 3:
            try:
                request = urllib.request.Request(self.url, headers={"User-Agent": "A3-PS015-TC032-load-test"})
                with self._opener(request, timeout=5) as response:
                    while not self._stop.is_set():
                        chunk = response.read(self.chunk_size)
                        if not chunk:
                            break
                        with self._lock:
                            self._bytes += len(chunk)
            except Exception as exc:  # network errors are expected and reported, not hidden
                failures += 1
                with self._lock:
                    self.errors.append(str(exc)[:150])
                time.sleep(0.3)

    def start(self) -> None:
        self._started_at = time.perf_counter()
        for _ in range(self.threads):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self._workers.append(worker)

    def stop(self) -> None:
        self._stop.set()
        self.duration_s = round(time.perf_counter() - self._started_at, 1)
        for worker in self._workers:
            worker.join(timeout=2)


def measure_loaded(
    target: str,
    count: int,
    load_url: str,
    threads: int = 4,
    timeout_ms: int = 1000,
    interval_s: float = 0.2,
    ping_fn=None,
    progress=None,
    generator_factory: Callable[..., LoadGenerator] = LoadGenerator,
    warmup_s: float = 1.5,
    min_bytes: int = 500_000,
) -> Tuple[ProbeStats, LoadInfo]:
    """Run the same ping test as the baseline while the link is kept busy."""
    generator = generator_factory(load_url, threads)
    generator.start()
    try:
        time.sleep(warmup_s)  # let the downloads ramp up first
        stats = measure_latency(
            target, count=count, timeout_ms=timeout_ms, interval_s=interval_s,
            role="external", ping_fn=ping_fn, progress=progress,
        )
    finally:
        generator.stop()
    applied = generator.bytes_downloaded >= min_bytes
    error = ""
    if not applied:
        detail = generator.errors[0] if generator.errors else "too little data was downloaded"
        error = f"The busy-link load was not established ({detail})."
    info = LoadInfo(
        applied=applied,
        url=load_url,
        threads=threads,
        duration_s=generator.duration_s,
        bytes_downloaded=generator.bytes_downloaded,
        error=error,
    )
    return stats, info


def _fmt(value: Optional[float]) -> Optional[float]:
    return None if value is None else round(value, 1)


def compare_stats(baseline: Optional[ProbeStats], loaded: Optional[ProbeStats]) -> List[dict]:
    """Rows for the 'normal vs busy link' table and chart."""
    if baseline is None or loaded is None or not baseline.available or not loaded.available:
        return []
    rows = []
    for label, attr, unit in (
        ("Median latency", "median_ms", "ms"),
        ("Jitter", "jitter_ms", "ms"),
        ("Packet loss", "loss_pct", "%"),
    ):
        base_value = getattr(baseline, attr)
        load_value = getattr(loaded, attr)
        change = None if base_value is None or load_value is None else round(load_value - base_value, 1)
        rows.append({
            "Metric": label,
            "Unit": unit,
            "Normal": _fmt(base_value),
            "Busy link": _fmt(load_value),
            "Change": change,
        })
    return rows
