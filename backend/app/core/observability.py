"""Lightweight observability primitives for metrics and telemetry snapshots."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from threading import Lock


@dataclass(slots=True)
class RequestMetric:
    """One completed request observation."""

    method: str
    path: str
    status_code: int
    duration_ms: float


class ObservabilityStore:
    """In-memory metrics sink used to expose backend operational telemetry."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._request_count = 0
        self._error_count = 0
        self._status_counter: Counter[str] = Counter()
        self._path_counter: Counter[str] = Counter()
        self._recent_requests: deque[RequestMetric] = deque(maxlen=500)
        self._error_types: Counter[str] = Counter()
        self._path_durations: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=200))

    def record_request(self, *, method: str, path: str, status_code: int, duration_ms: float) -> None:
        """Capture one completed request for aggregated metrics and percentiles."""

        with self._lock:
            self._request_count += 1
            self._status_counter[str(status_code)] += 1
            self._path_counter[path] += 1
            self._recent_requests.append(
                RequestMetric(method=method, path=path, status_code=status_code, duration_ms=duration_ms)
            )
            self._path_durations[path].append(duration_ms)

    def record_error(self, *, error_type: str) -> None:
        """Track one error occurrence to monitor failure rates."""

        with self._lock:
            self._error_count += 1
            self._error_types[error_type] += 1

    def snapshot(self) -> dict[str, object]:
        """Return a metrics snapshot safe for API serialization."""

        with self._lock:
            busiest_paths = [
                {
                    "path": path,
                    "count": count,
                    "avg_duration_ms": round(sum(self._path_durations[path]) / len(self._path_durations[path]), 2)
                    if self._path_durations[path]
                    else 0.0,
                    "p95_duration_ms": self._quantile(self._path_durations[path], 0.95),
                }
                for path, count in self._path_counter.most_common(10)
            ]

            recent = [
                {
                    "method": metric.method,
                    "path": metric.path,
                    "status_code": metric.status_code,
                    "duration_ms": metric.duration_ms,
                }
                for metric in list(self._recent_requests)[-20:]
            ]

            return {
                "request_count": self._request_count,
                "error_count": self._error_count,
                "status_counts": dict(self._status_counter),
                "error_types": dict(self._error_types),
                "busiest_paths": busiest_paths,
                "recent_requests": recent,
            }

    @staticmethod
    def _quantile(values: deque[float], quantile: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        index = int((len(ordered) - 1) * quantile)
        return round(ordered[index], 2)


observability_store = ObservabilityStore()
