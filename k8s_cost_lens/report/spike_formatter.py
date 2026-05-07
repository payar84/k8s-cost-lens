"""Format CostSpikeDetector results for human-readable output."""
from __future__ import annotations

from typing import List

from tabulate import tabulate

from k8s_cost_lens.metrics.cost_spike import SpikeResult


class SpikeReportFormatter:
    """Render a list of SpikeResult objects as a table or CSV."""

    _HEADERS = [
        "Namespace",
        "Prev $/hr",
        "Curr $/hr",
        "Delta $/hr",
        "Change %",
        "Spike?",
    ]

    def __init__(self, results: List[SpikeResult]) -> None:
        self._results = results

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for r in self._results:
            pct = (
                f"{r.hourly_pct_change:+.1f}%"
                if r.hourly_pct_change is not None
                else "N/A"
            )
            rows.append(
                [
                    r.namespace,
                    f"{r.previous_hourly:.4f}",
                    f"{r.current_hourly:.4f}",
                    f"{r.hourly_delta:+.4f}",
                    pct,
                    "YES" if r.is_spike else "no",
                ]
            )
        return rows

    def as_table(self) -> str:
        rows = self._to_rows()
        return tabulate(rows, headers=self._HEADERS, tablefmt="github")

    def as_csv(self) -> str:
        lines = [",".join(self._HEADERS)]
        for row in self._to_rows():
            lines.append(",".join(row))
        return "\n".join(lines)

    def spike_count(self) -> int:
        return sum(1 for r in self._results if r.is_spike)

    def summary_line(self) -> str:
        total = len(self._results)
        spikes = self.spike_count()
        return (
            f"{spikes}/{total} namespace(s) exceeded the "
            f"{self._results[0].threshold_pct:.0f}% spike threshold."
            if self._results
            else "No namespaces to evaluate."
        )
