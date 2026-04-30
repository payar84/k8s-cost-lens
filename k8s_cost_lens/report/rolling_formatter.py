"""Formatter for rolling-average cost reports."""
from __future__ import annotations

import csv
import io
from typing import List

from k8s_cost_lens.metrics.cost_roller import RollingCost

_HEADERS = ["Namespace", "Avg Hourly ($)", "Avg Monthly ($)", "Samples"]


class RollingCostFormatter:
    """Renders a list of RollingCost objects as a table or CSV."""

    def __init__(self, costs: List[RollingCost], window_size: int) -> None:
        self._costs = costs
        self._window_size = window_size

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for rc in self._costs:
            rows.append([
                rc.namespace,
                f"{rc.avg_hourly:.4f}",
                f"{rc.avg_monthly:.2f}",
                str(rc.sample_count),
            ])
        return rows

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def as_table(self) -> str:
        col_widths = [len(h) for h in _HEADERS]
        rows = self._to_rows()
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        def fmt_row(cells: List[str]) -> str:
            return "  ".join(c.ljust(col_widths[i]) for i, c in enumerate(cells))

        sep = "-" * (sum(col_widths) + 2 * (len(_HEADERS) - 1))
        lines = [
            f"Rolling Cost Report (window={self._window_size})",
            sep,
            fmt_row(_HEADERS),
            sep,
        ]
        for row in rows:
            lines.append(fmt_row(row))
        lines.append(sep)
        return "\n".join(lines)

    def as_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(_HEADERS)
        writer.writerows(self._to_rows())
        return buf.getvalue()

    def summary_line(self) -> str:
        if not self._costs:
            return "No rolling cost data available."
        total_hourly = sum(rc.avg_hourly for rc in self._costs)
        total_monthly = sum(rc.avg_monthly for rc in self._costs)
        return (
            f"Cluster rolling avg: ${total_hourly:.4f}/hr  "
            f"${total_monthly:.2f}/mo  "
            f"(window={self._window_size}, namespaces={len(self._costs)})"
        )
