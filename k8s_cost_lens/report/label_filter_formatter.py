"""Format label-filtered cost results for display."""
from __future__ import annotations

from typing import Dict, List

from tabulate import tabulate

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.label_filter import LabelSelector


class LabelFilterReportFormatter:
    """Render a filtered subset of NamespaceCost objects with selector context."""

    def __init__(
        self,
        costs: List[NamespaceCost],
        selector: LabelSelector,
        label_map: Dict[str, Dict[str, str]],
    ) -> None:
        self._costs = costs
        self._selector = selector
        self._label_map = label_map

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def as_table(self) -> str:
        """Return a human-readable table with label columns."""
        label_keys = sorted(
            {k for labels in self._label_map.values() for k in labels}
        )
        headers = ["Namespace"] + label_keys + ["CPU$/hr", "Mem$/hr", "Total$/hr", "Total$/mo"]
        rows = []
        for c in sorted(self._costs, key=lambda x: x.namespace):
            ns_labels = self._label_map.get(c.namespace, {})
            label_vals = [ns_labels.get(k, "") for k in label_keys]
            rows.append(
                [c.namespace]
                + label_vals
                + [
                    f"{c.cpu_cost_hourly:.4f}",
                    f"{c.memory_cost_hourly:.4f}",
                    f"{c.total_hourly:.4f}",
                    f"{c.total_monthly:.4f}",
                ]
            )
        selector_str = (
            ",".join(f"{k}={v}" for k, v in sorted(self._selector.labels.items()))
            or "<none>"
        )
        header_note = f"Label selector: {selector_str}  |  Matching namespaces: {len(self._costs)}"
        table = tabulate(rows, headers=headers, tablefmt="github")
        return f"{header_note}\n{table}"

    def as_csv(self) -> str:
        """Return CSV output for the filtered costs."""
        label_keys = sorted(
            {k for labels in self._label_map.values() for k in labels}
        )
        headers = ["namespace"] + label_keys + ["cpu_cost_hourly", "memory_cost_hourly", "total_hourly", "total_monthly"]
        lines = [",".join(headers)]
        for c in sorted(self._costs, key=lambda x: x.namespace):
            ns_labels = self._label_map.get(c.namespace, {})
            label_vals = [ns_labels.get(k, "") for k in label_keys]
            row = (
                [c.namespace]
                + label_vals
                + [
                    f"{c.cpu_cost_hourly:.6f}",
                    f"{c.memory_cost_hourly:.6f}",
                    f"{c.total_hourly:.6f}",
                    f"{c.total_monthly:.6f}",
                ]
            )
            lines.append(",".join(row))
        return "\n".join(lines)
