"""Formatter for CostRegressionAnalyzer results."""
from __future__ import annotations

from typing import List

try:
    from tabulate import tabulate
except ImportError:  # pragma: no cover
    tabulate = None  # type: ignore

from k8s_cost_lens.metrics.cost_regression import RegressionResult


def _arrow(slope: float) -> str:
    if slope > 1e-6:
        return "↑"
    if slope < -1e-6:
        return "↓"
    return "→"


class RegressionReportFormatter:
    """Renders regression results as a table or CSV."""

    _HEADERS = ["Namespace", "Slope ($/interval)", "R²", "Trend", "Next Hourly ($)", "Next Monthly ($)"]

    def __init__(self, results: List[RegressionResult]) -> None:
        self._results = results

    def _to_rows(self) -> List[list]:
        rows = []
        for r in self._results:
            rows.append([
                r.namespace,
                f"{r.slope_hourly:+.5f}",
                f"{r.r_squared:.3f}",
                _arrow(r.slope_hourly),
                f"{r.predicted_next_hourly:.4f}",
                f"{r.predicted_next_monthly:.2f}",
            ])
        return rows

    def as_table(self) -> str:
        rows = self._to_rows()
        if tabulate is not None:
            return tabulate(rows, headers=self._HEADERS, tablefmt="github")
        lines = ["  ".join(self._HEADERS)]
        for row in rows:
            lines.append("  ".join(str(c) for c in row))
        return "\n".join(lines)

    def as_csv(self) -> str:
        lines = [",".join(self._HEADERS)]
        for row in self._to_rows():
            lines.append(",".join(str(c) for c in row))
        return "\n".join(lines)

    def summary_line(self) -> str:
        if not self._results:
            return "No regression data available."
        rising = sum(1 for r in self._results if r.slope_hourly > 1e-6)
        falling = sum(1 for r in self._results if r.slope_hourly < -1e-6)
        flat = len(self._results) - rising - falling
        return f"Regression: {len(self._results)} namespaces — {rising} rising, {falling} falling, {flat} flat."
