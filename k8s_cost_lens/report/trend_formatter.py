"""Formatter for cost trend reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from k8s_cost_lens.metrics.trend import NamespaceTrend


@dataclass
class TrendRow:
    namespace: str
    current_hourly: float
    previous_hourly: float
    delta_hourly: float
    percent_change: Optional[float]
    direction: str


class TrendReportFormatter:
    """Formats NamespaceTrend data into human-readable tables or CSV."""

    _HEADERS = [
        "Namespace",
        "Curr $/hr",
        "Prev $/hr",
        "Delta $/hr",
        "Change %",
        "Direction",
    ]

    def __init__(self, trends: List[NamespaceTrend]) -> None:
        self._trends = trends

    def _to_rows(self) -> List[TrendRow]:
        rows: List[TrendRow] = []
        for t in self._trends:
            pct = t.percent_change
            if t.delta > 0:
                direction = "↑ UP"
            elif t.delta < 0:
                direction = "↓ DOWN"
            else:
                direction = "→ FLAT"
            rows.append(
                TrendRow(
                    namespace=t.namespace,
                    current_hourly=t.current_cost.hourly_cost,
                    previous_hourly=t.previous_cost,
                    delta_hourly=t.delta,
                    percent_change=pct,
                    direction=direction,
                )
            )
        return rows

    def as_table(self) -> str:
        rows = self._to_rows()
        col_widths = [max(len(h), 12) for h in self._HEADERS]

        def fmt_row(values: List[str]) -> str:
            return "  ".join(v.ljust(col_widths[i]) for i, v in enumerate(values))

        lines = [fmt_row(self._HEADERS), "-" * (sum(col_widths) + 2 * (len(col_widths) - 1))]
        for r in rows:
            pct_str = f"{r.percent_change:+.1f}%" if r.percent_change is not None else "N/A"
            lines.append(
                fmt_row([
                    r.namespace,
                    f"{r.current_hourly:.4f}",
                    f"{r.previous_hourly:.4f}",
                    f"{r.delta_hourly:+.4f}",
                    pct_str,
                    r.direction,
                ])
            )
        return "\n".join(lines)

    def as_csv(self) -> str:
        rows = self._to_rows()
        lines = [",".join(self._HEADERS)]
        for r in rows:
            pct_str = f"{r.percent_change:.4f}" if r.percent_change is not None else ""
            lines.append(
                ",".join([
                    r.namespace,
                    f"{r.current_hourly:.4f}",
                    f"{r.previous_hourly:.4f}",
                    f"{r.delta_hourly:.4f}",
                    pct_str,
                    r.direction,
                ])
            )
        return "\n".join(lines)
