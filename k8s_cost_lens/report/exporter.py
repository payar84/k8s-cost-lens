"""Exports cost reports to various output destinations."""

from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path
from typing import List

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.report.formatter import CostReportFormatter


class CostReportExporter:
    """Writes formatted cost reports to files or stdout."""

    def __init__(self, costs: List[NamespaceCost]) -> None:
        self._costs = costs
        self._formatter = CostReportFormatter(costs)

    def to_stdout_table(self) -> None:
        """Print a human-readable table to stdout."""
        print(self._formatter.as_table())

    def to_file_csv(self, path: str | os.PathLike) -> Path:
        """Write CSV report to *path* and return the resolved Path."""
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(self._formatter.as_csv(), encoding="utf-8")
        return dest

    def to_file_json(self, path: str | os.PathLike) -> Path:
        """Write JSON report to *path* and return the resolved Path."""
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        records = [
            {
                "namespace": c.namespace,
                "cpu_cores": c.cpu_cores,
                "memory_gib": c.memory_gib,
                "hourly_cost_usd": round(c.hourly_cost_usd, 6),
                "monthly_cost_usd": round(c.monthly_cost_usd, 4),
            }
            for c in self._costs
        ]
        dest.write_text(
            json.dumps({"namespaces": records}, indent=2), encoding="utf-8"
        )
        return dest

    def to_string_json(self) -> str:
        """Return the JSON report as a string (useful for API responses)."""
        records = [
            {
                "namespace": c.namespace,
                "cpu_cores": c.cpu_cores,
                "memory_gib": c.memory_gib,
                "hourly_cost_usd": round(c.hourly_cost_usd, 6),
                "monthly_cost_usd": round(c.monthly_cost_usd, 4),
            }
            for c in self._costs
        ]
        return json.dumps({"namespaces": records}, indent=2)
