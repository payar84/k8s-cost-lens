"""Formatter for cost threshold violation reports."""
from __future__ import annotations

import csv
import io
from typing import List

from tabulate import tabulate

from k8s_cost_lens.metrics.threshold import ThresholdViolation


class ThresholdReportFormatter:
    """Renders a list of ThresholdViolation objects as table or CSV."""

    _HEADERS = ["Namespace", "Type", "Limit ($)", "Actual ($)", "Exceeded By ($)"]

    def __init__(self, violations: List[ThresholdViolation]) -> None:
        self._violations = violations

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for v in self._violations:
            exceeded_by = v.actual - v.limit
            rows.append(
                [
                    v.namespace,
                    v.violation_type,
                    f"{v.limit:.4f}",
                    f"{v.actual:.4f}",
                    f"{exceeded_by:.4f}",
                ]
            )
        return rows

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def as_table(self) -> str:
        """Return a human-readable table string."""
        rows = self._to_rows()
        if not rows:
            return "No threshold violations detected."
        return tabulate(rows, headers=self._HEADERS, tablefmt="github")

    def as_csv(self) -> str:
        """Return violations formatted as CSV."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self._HEADERS)
        writer.writerows(self._to_rows())
        return buf.getvalue()

    def violation_count(self) -> int:
        """Return the total number of violations."""
        return len(self._violations)

    def summary_line(self) -> str:
        """Return a one-line summary suitable for CLI output."""
        count = self.violation_count()
        if count == 0:
            return "All namespaces are within configured cost thresholds."
        return f"{count} threshold violation(s) detected across {len({v.namespace for v in self._violations})} namespace(s)."
