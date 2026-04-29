"""Formatter for cost allocation reports."""
from __future__ import annotations

import csv
import io
from typing import List

try:
    from tabulate import tabulate
except ImportError:  # pragma: no cover
    tabulate = None  # type: ignore[assignment]

from k8s_cost_lens.metrics.allocation import AllocationResult


class AllocationReportFormatter:
    """Renders AllocationResult lists as table or CSV."""

    _HEADERS = [
        "Namespace",
        "Share %",
        "Hourly ($)",
        "Monthly ($)",
    ]

    def __init__(self, results: List[AllocationResult]) -> None:
        self._results = sorted(results, key=lambda r: r.share_pct, reverse=True)

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for r in self._results:
            rows.append(
                [
                    r.namespace,
                    f"{r.share_pct:.2f}",
                    f"{r.allocated_hourly:.6f}",
                    f"{r.allocated_monthly:.4f}",
                ]
            )
        return rows

    def as_table(self) -> str:
        """Return a human-readable table string."""
        rows = self._to_rows()
        if tabulate is not None:
            return tabulate(rows, headers=self._HEADERS, tablefmt="github")
        # Fallback: simple aligned text
        lines = ["  ".join(self._HEADERS)]
        for row in rows:
            lines.append("  ".join(row))
        return "\n".join(lines)

    def as_csv(self) -> str:
        """Return CSV-formatted string."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self._HEADERS)
        writer.writerows(self._to_rows())
        return buf.getvalue()

    def total_allocated_hourly(self) -> float:
        return sum(r.allocated_hourly for r in self._results)

    def total_allocated_monthly(self) -> float:
        return sum(r.allocated_monthly for r in self._results)
