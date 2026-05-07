"""Formatter for cost-velocity analysis results."""
from __future__ import annotations

import csv
import io
from typing import List

from tabulate import tabulate

from k8s_cost_lens.metrics.cost_velocity import VelocityResult

_HEADERS = ["Namespace", "Hourly Velocity ($/h²)", "Monthly Velocity ($/mo/h)", "Direction"]


class VelocityReportFormatter:
    """Render :class:`VelocityResult` lists as human-readable tables or CSV."""

    def __init__(self, results: List[VelocityResult]) -> None:
        self._results = results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for r in self._results:
            sign = "+" if r.hourly_velocity >= 0 else ""
            rows.append(
                [
                    r.namespace,
                    f"{sign}{r.hourly_velocity:.8f}",
                    f"{sign}{r.monthly_velocity:.6f}",
                    r.direction,
                ]
            )
        return rows

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def as_table(self) -> str:
        """Return a pretty-printed table string."""
        rows = self._to_rows()
        return tabulate(rows, headers=_HEADERS, tablefmt="github")

    def as_csv(self) -> str:
        """Return CSV representation."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(_HEADERS)
        writer.writerows(self._to_rows())
        return buf.getvalue()

    def rising_count(self) -> int:
        """Number of namespaces with rising cost velocity."""
        return sum(1 for r in self._results if r.direction == "rising")

    def falling_count(self) -> int:
        """Number of namespaces with falling cost velocity."""
        return sum(1 for r in self._results if r.direction == "falling")

    def summary_line(self) -> str:
        """One-line summary suitable for dashboards."""
        total = len(self._results)
        return (
            f"{total} namespace(s) analysed — "
            f"{self.rising_count()} rising, "
            f"{self.falling_count()} falling, "
            f"{total - self.rising_count() - self.falling_count()} stable"
        )
