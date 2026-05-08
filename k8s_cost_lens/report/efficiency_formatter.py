"""Formatter for cost efficiency scores."""
from __future__ import annotations

from typing import List, Optional

from tabulate import tabulate

from k8s_cost_lens.metrics.cost_efficiency import EfficiencyScore


def _fmt_pct(value: Optional[float]) -> str:
    return f"{value:.1%}" if value is not None else "n/a"


def _fmt_f(value: float, decimals: int = 3) -> str:
    return f"{value:.{decimals}f}"


class EfficiencyReportFormatter:
    """Render EfficiencyScore lists as table or CSV."""

    _HEADERS = [
        "Namespace",
        "Hourly ($)",
        "CPU Req",
        "CPU Used",
        "CPU Eff",
        "Mem Req (GiB)",
        "Mem Used (GiB)",
        "Mem Eff",
        "Overall Eff",
    ]

    def __init__(self, scores: List[EfficiencyScore]) -> None:
        self._scores = scores

    def _to_rows(self) -> List[list]:
        rows = []
        for s in self._scores:
            rows.append([
                s.namespace,
                _fmt_f(s.hourly_cost, 4),
                _fmt_f(s.cpu_requested),
                _fmt_f(s.cpu_used),
                _fmt_pct(s.cpu_efficiency),
                _fmt_f(s.mem_requested_gb),
                _fmt_f(s.mem_used_gb),
                _fmt_pct(s.mem_efficiency),
                _fmt_pct(s.overall_efficiency),
            ])
        return rows

    def as_table(self) -> str:
        return tabulate(self._to_rows(), headers=self._HEADERS, tablefmt="github")

    def as_csv(self) -> str:
        lines = [",".join(self._HEADERS)]
        for row in self._to_rows():
            lines.append(",".join(str(c) for c in row))
        return "\n".join(lines)

    def inefficiency_summary(self) -> str:
        """Return a one-line summary of the least-efficient namespace."""
        scored = [s for s in self._scores if s.overall_efficiency is not None]
        if not scored:
            return "No efficiency data available."
        worst = min(scored, key=lambda s: s.overall_efficiency)  # type: ignore[arg-type]
        return (
            f"Least efficient: {worst.namespace} "
            f"({_fmt_pct(worst.overall_efficiency)} overall)"
        )
