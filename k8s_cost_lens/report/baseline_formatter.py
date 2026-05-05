"""Formatter for baseline comparison diffs."""
from __future__ import annotations

from typing import List, Optional

from tabulate import tabulate

from k8s_cost_lens.metrics.cost_baseline import BaselineDiff


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%"


def _fmt_delta(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}${value:.4f}"


class BaselineComparisonFormatter:
    """Renders a list of BaselineDiff objects as a table or CSV."""

    def __init__(self, baseline_name: str, diffs: List[BaselineDiff]) -> None:
        self._name = baseline_name
        self._diffs = diffs

    def _to_rows(self) -> List[List[str]]:
        rows = []
        for d in sorted(self._diffs, key=lambda x: x.namespace):
            rows.append(
                [
                    d.namespace,
                    f"${d.baseline_hourly:.4f}",
                    f"${d.current_hourly:.4f}",
                    _fmt_delta(d.hourly_delta),
                    _fmt_pct(d.hourly_pct_change),
                    f"${d.baseline_monthly:.2f}",
                    f"${d.current_monthly:.2f}",
                    _fmt_delta(d.monthly_delta),
                ]
            )
        return rows

    def as_table(self) -> str:
        headers = [
            "Namespace",
            "Base $/hr",
            "Curr $/hr",
            "Δ $/hr",
            "% Change",
            "Base $/mo",
            "Curr $/mo",
            "Δ $/mo",
        ]
        rows = self._to_rows()
        table = tabulate(rows, headers=headers, tablefmt="github")
        return f"Baseline comparison: '{self._name}'\n{table}"

    def as_csv(self) -> str:
        headers = [
            "namespace",
            "baseline_hourly",
            "current_hourly",
            "delta_hourly",
            "pct_change",
            "baseline_monthly",
            "current_monthly",
            "delta_monthly",
        ]
        lines = [",".join(headers)]
        for d in sorted(self._diffs, key=lambda x: x.namespace):
            pct = "" if d.hourly_pct_change is None else f"{d.hourly_pct_change:.2f}"
            lines.append(
                ",".join(
                    [
                        d.namespace,
                        f"{d.baseline_hourly:.6f}",
                        f"{d.current_hourly:.6f}",
                        f"{d.hourly_delta:.6f}",
                        pct,
                        f"{d.baseline_monthly:.4f}",
                        f"{d.current_monthly:.4f}",
                        f"{d.monthly_delta:.4f}",
                    ]
                )
            )
        return "\n".join(lines)
