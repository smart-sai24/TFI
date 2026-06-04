from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter


@dataclass
class ApiMetricsCollector:
    started_at: float = field(default_factory=perf_counter)
    request_count: int = 0
    error_count: int = 0
    latencies_ms: list[float] = field(default_factory=list)

    def record(self, latency_ms: float, status_code: int) -> None:
        self.request_count += 1
        if status_code >= 500:
            self.error_count += 1
        self.latencies_ms.append(latency_ms)
        if len(self.latencies_ms) > 1000:
            self.latencies_ms = self.latencies_ms[-1000:]

    def snapshot(self) -> list[dict[str, str]]:
        uptime_seconds = max(perf_counter() - self.started_at, 0.001)
        sorted_latencies = sorted(self.latencies_ms)
        p95_latency = 0.0
        if sorted_latencies:
            index = min(int(round((len(sorted_latencies) - 1) * 0.95)), len(sorted_latencies) - 1)
            p95_latency = sorted_latencies[index]
        error_rate = (self.error_count / self.request_count * 100) if self.request_count else 0.0
        return [
            {'name': 'API uptime', 'value': f'{uptime_seconds / 60:.1f} min', 'status': 'Live'},
            {'name': 'Requests served', 'value': str(self.request_count), 'status': 'Live'},
            {'name': 'P95 latency', 'value': f'{p95_latency:.0f} ms', 'status': 'Live'},
            {'name': 'Error rate', 'value': f'{error_rate:.2f}%', 'status': 'Live' if error_rate < 1 else 'Watch'},
        ]


api_metrics_collector = ApiMetricsCollector()
