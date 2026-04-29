"""Formatter helpers for anomaly detection results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from k8s_cost_lens.metrics.anomaly import AnomalyResult


@dataclass
class AnomalyReportFormatter:
    """Renders a list of AnomalyResult objects as a human-readable table or CSV."""

    results: List[AnomalyResult]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def as_table(self) -> str:
        if not self.results:
            return "No anomaly data available."

        header = f"{'Namespace':<30} {'Hourly ($)':>12} {'Mean ($)':>12} {'Z-Score':>9} {'Status':>10}"
        separator = "-" * len(header)
        rows = [header, separator]
        for r in self.results:
            z_str = f"{r.z_score:>9.2f}" if r.z_score is not None else f"{'N/A':>9}"
            status = "ANOMALY" if r.is_anomaly else "OK"
            rows.append(
                f"{r.namespace:<30} {r.hourly_cost:>12.4f} {r.mean_hourly:>12.4f} {z_str} {status:>10}"
            )
        return "\n".join(rows)

    def as_csv(self) -> str:
        lines = ["namespace,hourly_cost,mean_hourly,stddev_hourly,z_score,is_anomaly"]
        for r in self.results:
            z_str = f"{r.z_score:.4f}" if r.z_score is not None else ""
            lines.append(
                f"{r.namespace},{r.hourly_cost:.4f},{r.mean_hourly:.4f},"
                f"{r.stddev_hourly:.4f},{z_str},{r.is_anomaly}"
            )
        return "\n".join(lines)

    def anomaly_count(self) -> int:
        return sum(1 for r in self.results if r.is_anomaly)

    def summary_line(self) -> str:
        total = len(self.results)
        flagged = self.anomaly_count()
        return f"{flagged}/{total} namespace(s) flagged as anomalous."
