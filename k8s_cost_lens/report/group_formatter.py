"""Formatter for grouped namespace cost reports."""
from __future__ import annotations

import csv
import io
from typing import List

from tabulate import tabulate

from k8s_cost_lens.metrics.namespace_grouper import GroupedCost


class GroupCostFormatter:
    """Renders a list of :class:`GroupedCost` objects as a table or CSV."""

    _HEADERS = [
        "Group",
        "Namespaces",
        "CPU (cores)",
        "Memory (GiB)",
        "Hourly ($)",
        "Monthly ($)",
    ]

    def __init__(self, costs: List[GroupedCost]) -> None:
        self._costs = costs

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for gc in self._costs:
            rows.append(
                [
                    gc.group_name,
                    ", ".join(gc.namespaces),
                    f"{gc.total_cpu_cores:.3f}",
                    f"{gc.total_memory_gib:.3f}",
                    f"{gc.total_hourly_usd:.4f}",
                    f"{gc.total_monthly_usd:.2f}",
                ]
            )
        return rows

    def as_table(self) -> str:
        """Return a human-readable table string."""
        rows = self._to_rows()
        return tabulate(rows, headers=self._HEADERS, tablefmt="github")

    def as_csv(self) -> str:
        """Return CSV-formatted string."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self._HEADERS)
        writer.writerows(self._to_rows())
        return buf.getvalue()

    def summary_line(self) -> str:
        """Return a one-line summary of totals across all groups."""
        total_hourly = sum(gc.total_hourly_usd for gc in self._costs)
        total_monthly = sum(gc.total_monthly_usd for gc in self._costs)
        group_count = len(self._costs)
        return (
            f"{group_count} group(s) | "
            f"Total hourly: ${total_hourly:.4f} | "
            f"Total monthly: ${total_monthly:.2f}"
        )
