"""Formatter for budget status reports."""
from __future__ import annotations

import csv
import io
from typing import List

from tabulate import tabulate

from k8s_cost_lens.metrics.budget import BudgetStatus


class BudgetReportFormatter:
    """Renders a list of BudgetStatus objects as human-readable or CSV output."""

    # Column headers
    _HEADERS = [
        "Namespace",
        "Hourly ($)",
        "Hourly Limit ($)",
        "Hourly %",
        "Monthly ($)",
        "Monthly Limit ($)",
        "Monthly %",
        "Exceeded",
    ]

    def __init__(self, statuses: List[BudgetStatus]) -> None:
        self._statuses = statuses

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for s in self._statuses:
            hourly_pct = f"{s.hourly_usage_pct:.1f}" if s.hourly_usage_pct is not None else "N/A"
            monthly_pct = f"{s.monthly_usage_pct:.1f}" if s.monthly_usage_pct is not None else "N/A"
            hourly_limit = f"{s.hourly_limit:.4f}" if s.hourly_limit is not None else "N/A"
            monthly_limit = f"{s.monthly_limit:.2f}" if s.monthly_limit is not None else "N/A"
            exceeded = "YES" if (s.hourly_exceeded or s.monthly_exceeded) else "no"
            rows.append([
                s.namespace,
                f"{s.hourly_cost:.4f}",
                hourly_limit,
                hourly_pct,
                f"{s.monthly_cost:.2f}",
                monthly_limit,
                monthly_pct,
                exceeded,
            ])
        return rows

    def as_table(self) -> str:
        """Return a formatted table string."""
        rows = self._to_rows()
        return tabulate(rows, headers=self._HEADERS, tablefmt="github")

    def as_csv(self) -> str:
        """Return CSV string."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self._HEADERS)
        writer.writerows(self._to_rows())
        return buf.getvalue()

    def exceeded_count(self) -> int:
        """Return the number of namespaces that have exceeded any budget."""
        return sum(1 for s in self._statuses if s.hourly_exceeded or s.monthly_exceeded)

    def summary_line(self) -> str:
        """Return a one-line summary."""
        total = len(self._statuses)
        over = self.exceeded_count()
        return f"{over}/{total} namespace(s) over budget."
