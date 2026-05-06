"""Formatter for cost quota check results."""
from __future__ import annotations

from typing import List

try:
    from tabulate import tabulate
    _HAS_TABULATE = True
except ImportError:
    _HAS_TABULATE = False

from k8s_cost_lens.metrics.cost_quota import QuotaResult

_NA = "—"


def _fmt_limit(value: float | None) -> str:
    return f"${value:.4f}" if value is not None else _NA


def _fmt_monthly(value: float | None) -> str:
    return f"${value:.2f}" if value is not None else _NA


class QuotaReportFormatter:
    """Render quota results as a table or CSV."""

    def __init__(self, results: List[QuotaResult]) -> None:
        self._results = results

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for r in self._results:
            rows.append([
                r.namespace,
                f"${r.hourly_cost:.4f}",
                _fmt_limit(r.soft_hourly_limit),
                _fmt_limit(r.hard_hourly_limit),
                f"${r.monthly_cost:.2f}",
                _fmt_monthly(r.soft_monthly_limit),
                _fmt_monthly(r.hard_monthly_limit),
                r.severity().upper(),
            ])
        return rows

    def as_table(self) -> str:
        headers = [
            "Namespace",
            "Hourly",
            "Soft H-Limit",
            "Hard H-Limit",
            "Monthly",
            "Soft M-Limit",
            "Hard M-Limit",
            "Severity",
        ]
        rows = self._to_rows()
        if _HAS_TABULATE:
            return tabulate(rows, headers=headers, tablefmt="github")
        header_line = " | ".join(headers)
        separator = "-" * len(header_line)
        data_lines = [" | ".join(row) for row in rows]
        return "\n".join([header_line, separator] + data_lines)

    def as_csv(self) -> str:
        headers = [
            "namespace", "hourly_cost",
            "soft_hourly_limit", "hard_hourly_limit",
            "monthly_cost", "soft_monthly_limit", "hard_monthly_limit",
            "severity",
        ]
        lines = [",".join(headers)]
        for r in self._results:
            lines.append(",".join([
                r.namespace,
                f"{r.hourly_cost:.6f}",
                str(r.soft_hourly_limit) if r.soft_hourly_limit is not None else "",
                str(r.hard_hourly_limit) if r.hard_hourly_limit is not None else "",
                f"{r.monthly_cost:.4f}",
                str(r.soft_monthly_limit) if r.soft_monthly_limit is not None else "",
                str(r.hard_monthly_limit) if r.hard_monthly_limit is not None else "",
                r.severity(),
            ]))
        return "\n".join(lines)

    def breached_count(self) -> int:
        return sum(1 for r in self._results if r.any_breached)

    def summary_line(self) -> str:
        total = len(self._results)
        breached = self.breached_count()
        hard = sum(1 for r in self._results if r.severity() == "hard")
        return (
            f"Quota check: {total} namespace(s) checked, "
            f"{breached} breached ({hard} hard, {breached - hard} soft)."
        )
