"""Formatter for cost forecast results."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import List

from tabulate import tabulate

from k8s_cost_lens.metrics.forecast import ForecastResult


@dataclass
class ForecastRow:
    namespace: str
    current_hourly: str
    forecasted_hourly: str
    forecasted_monthly: str
    slope: str
    direction: str


class ForecastReportFormatter:
    _HEADERS = [
        "Namespace",
        "Current $/hr",
        "Forecast $/hr",
        "Forecast $/mo",
        "Slope ($/hr/interval)",
        "Trend",
    ]

    def __init__(self, results: List[ForecastResult]) -> None:
        self._results = results

    def _to_rows(self) -> List[ForecastRow]:
        rows = []
        for r in self._results:
            rows.append(
                ForecastRow(
                    namespace=r.namespace,
                    current_hourly=f"{r.current_hourly:.4f}",
                    forecasted_hourly=f"{r.forecasted_hourly:.4f}",
                    forecasted_monthly=f"{r.forecasted_monthly:.2f}",
                    slope=f"{r.slope:.6f}",
                    direction=r.trend_direction,
                )
            )
        return rows

    def as_table(self) -> str:
        rows = self._to_rows()
        table_data = [
            [
                row.namespace,
                row.current_hourly,
                row.forecasted_hourly,
                row.forecasted_monthly,
                row.slope,
                row.direction,
            ]
            for row in rows
        ]
        return tabulate(table_data, headers=self._HEADERS, tablefmt="github")

    def as_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self._HEADERS)
        for row in self._to_rows():
            writer.writerow(
                [
                    row.namespace,
                    row.current_hourly,
                    row.forecasted_hourly,
                    row.forecasted_monthly,
                    row.slope,
                    row.direction,
                ]
            )
        return buf.getvalue()

    def result_count(self) -> int:
        return len(self._results)
