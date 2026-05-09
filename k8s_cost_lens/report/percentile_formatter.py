"""Formatter for cost-percentile analysis results."""
from __future__ import annotations

from typing import List

try:
    from tabulate import tabulate
except ImportError:  # pragma: no cover
    tabulate = None  # type: ignore

from k8s_cost_lens.metrics.cost_percentile import PercentileResult


class PercentileReportFormatter:
    """Render :class:`PercentileResult` collections as a table or CSV."""

    _HEADERS = [
        "Namespace",
        "Hourly ($)",
        "Hourly Pct",
        "Monthly ($)",
        "Monthly Pct",
    ]

    def __init__(self, results: List[PercentileResult]) -> None:
        self._results = sorted(
            results, key=lambda r: r.monthly_percentile, reverse=True
        )

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for r in self._results:
            rows.append(
                [
                    r.namespace,
                    f"{r.hourly_cost:.4f}",
                    f"{r.hourly_percentile:.1f}",
                    f"{r.monthly_cost:.2f}",
                    f"{r.monthly_percentile:.1f}",
                ]
            )
        return rows

    def as_table(self) -> str:
        rows = self._to_rows()
        if tabulate is not None:
            return tabulate(rows, headers=self._HEADERS, tablefmt="github")
        # Fallback: simple text table
        lines = ["  ".join(self._HEADERS)]
        for row in rows:
            lines.append("  ".join(row))
        return "\n".join(lines)

    def as_csv(self) -> str:
        lines = [",".join(self._HEADERS)]
        for row in self._to_rows():
            lines.append(",".join(row))
        return "\n".join(lines)

    def summary_line(self) -> str:
        if not self._results:
            return "No percentile data available."
        top = self._results[0]
        return (
            f"Highest-cost namespace: {top.namespace} "
            f"(monthly p{top.monthly_percentile:.1f})"
        )
