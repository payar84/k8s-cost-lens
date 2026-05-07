"""Formatter for Top-N cost analysis results."""
from __future__ import annotations

from typing import List

try:
    from tabulate import tabulate
except ImportError:  # pragma: no cover
    tabulate = None  # type: ignore

from k8s_cost_lens.metrics.cost_topn import TopNResult


class TopNReportFormatter:
    """Render a list of :class:`TopNResult` objects as a table or CSV."""

    _HEADERS = ["Rank", "Namespace", "Hourly ($)", "Monthly ($)"]

    def __init__(self, results: List[TopNResult]) -> None:
        self._results = results

    def _to_rows(self) -> List[List]:
        return [
            [
                r.rank,
                r.namespace,
                f"{r.hourly_cost:.6f}",
                f"{r.monthly_cost:.4f}",
            ]
            for r in self._results
        ]

    def as_table(self) -> str:
        """Return a pretty-printed table string."""
        rows = self._to_rows()
        if tabulate is not None:
            return tabulate(rows, headers=self._HEADERS, tablefmt="github")
        # Fallback: plain text
        lines = ["\t".join(self._HEADERS)]
        for row in rows:
            lines.append("\t".join(str(c) for c in row))
        return "\n".join(lines)

    def as_csv(self) -> str:
        """Return CSV representation."""
        lines = [",".join(self._HEADERS)]
        for row in self._to_rows():
            lines.append(",".join(str(c) for c in row))
        return "\n".join(lines)

    def summary_line(self) -> str:
        """One-line summary: number of results shown."""
        return f"Top-{len(self._results)} namespaces by cost."
