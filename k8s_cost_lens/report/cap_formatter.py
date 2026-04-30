"""Formatter for cost-cap violation reports."""
from __future__ import annotations

import csv
import io
from typing import List, Optional

from k8s_cost_lens.metrics.cost_cap import CapViolation

_HEADERS = [
    "Namespace",
    "Actual Hourly ($)",
    "Cap Hourly ($)",
    "Hourly Exceeded",
    "Actual Monthly ($)",
    "Cap Monthly ($)",
    "Monthly Exceeded",
]


def _fmt(value: Optional[float]) -> str:
    return f"{value:.4f}" if value is not None else "—"


class CapReportFormatter:
    def __init__(self, violations: List[CapViolation]) -> None:
        self._violations = violations

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for v in self._violations:
            rows.append([
                v.namespace,
                f"{v.actual_hourly:.4f}",
                _fmt(v.cap_hourly),
                "YES" if v.hourly_exceeded() else "no",
                f"{v.actual_monthly:.4f}",
                _fmt(v.cap_monthly),
                "YES" if v.monthly_exceeded() else "no",
            ])
        return rows

    def as_table(self) -> str:
        if not self._violations:
            return "No cost-cap violations detected."
        col_widths = [len(h) for h in _HEADERS]
        rows = self._to_rows()
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))
        sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        header_line = "|".join(f" {_HEADERS[i]:<{col_widths[i]}} " for i in range(len(_HEADERS)))
        lines = [sep, f"|{header_line}|", sep]
        for row in rows:
            line = "|".join(f" {row[i]:<{col_widths[i]}} " for i in range(len(row)))
            lines.append(f"|{line}|")
        lines.append(sep)
        return "\n".join(lines)

    def as_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(_HEADERS)
        writer.writerows(self._to_rows())
        return buf.getvalue()

    def violation_count(self) -> int:
        return len(self._violations)

    def summary_line(self) -> str:
        n = self.violation_count()
        return f"{n} cap violation{'s' if n != 1 else ''} detected."
