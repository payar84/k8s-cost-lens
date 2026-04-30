"""Formatter for tag policy violation reports."""
from __future__ import annotations

import csv
import io
from typing import List

from tabulate import tabulate

from k8s_cost_lens.metrics.tag_policy import PolicyViolation


class TagPolicyReportFormatter:
    """Renders PolicyViolation lists as table or CSV."""

    _HEADERS = ["Namespace", "Missing Labels", "Invalid Labels", "Compliant"]

    def __init__(self, violations: List[PolicyViolation]) -> None:
        self._violations = violations

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for v in self._violations:
            missing = ", ".join(sorted(v.missing_tags)) if v.missing_tags else "-"
            invalid = (
                ", ".join(f"{k}: {val}" for k, val in sorted(v.invalid_tags.items()))
                if v.invalid_tags
                else "-"
            )
            rows.append([v.namespace, missing, invalid, "No"])
        return rows

    def as_table(self) -> str:
        rows = self._to_rows()
        if not rows:
            return "No tag policy violations found."
        return tabulate(rows, headers=self._HEADERS, tablefmt="github")

    def as_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self._HEADERS)
        writer.writerows(self._to_rows())
        return buf.getvalue()

    def violation_count(self) -> int:
        return len(self._violations)

    def summary_line(self) -> str:
        n = self.violation_count()
        if n == 0:
            return "All namespaces are tag-policy compliant."
        return f"{n} namespace(s) violate the tag policy."
