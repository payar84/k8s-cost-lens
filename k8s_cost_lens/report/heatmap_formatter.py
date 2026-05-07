"""Formatter for :class:`CostHeatmap` — renders an ASCII grid and CSV output."""
from __future__ import annotations

from typing import List

from k8s_cost_lens.metrics.cost_heatmap import CostHeatmap

_SHADES = " ░▒▓█"


def _intensity_char(intensity: float) -> str:
    idx = min(int(intensity * (len(_SHADES) - 1)), len(_SHADES) - 1)
    return _SHADES[idx]


class HeatmapFormatter:
    """Renders a :class:`CostHeatmap` as a human-readable table or CSV."""

    def __init__(self, heatmap: CostHeatmap) -> None:
        self._heatmap = heatmap

    # ------------------------------------------------------------------
    def as_table(self) -> str:
        hm = self._heatmap
        if not hm.rows:
            return "No heatmap data available."

        ns_width = max(len(r.namespace) for r in hm.rows)
        ns_width = max(ns_width, 9)  # min header width

        slot_headers = [f"T{i:02d}" for i in range(hm.num_slots)]
        header = f"{'Namespace':<{ns_width}}  " + "  ".join(slot_headers)
        separator = "-" * len(header)

        lines: List[str] = [header, separator]
        for row in hm.rows:
            cells_str = "  ".join(
                f"{_intensity_char(c.intensity)} {c.hourly_cost:>6.4f}"
                for c in row.cells
            )
            lines.append(f"{row.namespace:<{ns_width}}  {cells_str}")

        lines.append(separator)
        lines.append(f"Slots: {hm.num_slots}  Namespaces: {len(hm.rows)}")
        return "\n".join(lines)

    def as_csv(self) -> str:
        hm = self._heatmap
        slot_headers = ",".join(f"slot_{i}_hourly" for i in range(hm.num_slots))
        lines: List[str] = [f"namespace,peak_hourly,{slot_headers}"]
        for row in hm.rows:
            slot_values = ",".join(f"{c.hourly_cost:.6f}" for c in row.cells)
            lines.append(f"{row.namespace},{row.peak_hourly:.6f},{slot_values}")
        return "\n".join(lines)

    def summary_line(self) -> str:
        hm = self._heatmap
        if not hm.rows:
            return "Heatmap is empty."
        peak_row = max(hm.rows, key=lambda r: r.peak_hourly)
        return (
            f"Heatmap: {len(hm.rows)} namespaces over {hm.num_slots} slots; "
            f"peak namespace: {peak_row.namespace} (${peak_row.peak_hourly:.4f}/hr)"
        )
