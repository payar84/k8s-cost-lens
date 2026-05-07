"""Heatmap data builder: buckets namespaces by cost intensity across time slots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class HeatmapCell:
    """A single cell in the cost heatmap."""
    namespace: str
    slot: int          # zero-based time slot index
    hourly_cost: float
    intensity: float   # 0.0 – 1.0 relative to the global max in the matrix

    def __str__(self) -> str:
        bar = int(self.intensity * 8)
        return f"{self.namespace}[slot={self.slot}] ${self.hourly_cost:.4f} {'█' * bar}"


@dataclass
class HeatmapRow:
    namespace: str
    cells: List[HeatmapCell] = field(default_factory=list)

    @property
    def peak_hourly(self) -> float:
        return max((c.hourly_cost for c in self.cells), default=0.0)


@dataclass
class CostHeatmap:
    rows: List[HeatmapRow] = field(default_factory=list)
    num_slots: int = 0

    def get_row(self, namespace: str) -> Optional[HeatmapRow]:
        for row in self.rows:
            if row.namespace == namespace:
                return row
        return None


class CostHeatmapBuilder:
    """Builds a cost heatmap from a sequence of per-slot namespace cost snapshots.

    Each snapshot is a list of ``NamespaceCost`` objects representing one time
    slot (e.g. one polling interval).  Intensity is normalised against the
    global maximum hourly cost across the entire matrix.
    """

    def __init__(self) -> None:
        self._slots: List[List[NamespaceCost]] = []

    def add_slot(self, costs: List[NamespaceCost]) -> None:
        """Append one time-slot of namespace costs."""
        self._slots.append(list(costs))

    def clear(self) -> None:
        self._slots.clear()

    def build(self) -> CostHeatmap:
        """Return a :class:`CostHeatmap` built from all added slots."""
        if not self._slots:
            return CostHeatmap()

        # Collect all namespace names in insertion order
        seen: Dict[str, None] = {}
        for slot in self._slots:
            for nc in slot:
                seen[nc.namespace] = None
        namespaces = list(seen.keys())

        # Build a lookup: slot_index -> {namespace: hourly_cost}
        slot_maps: List[Dict[str, float]] = [
            {nc.namespace: nc.hourly_cost for nc in slot}
            for slot in self._slots
        ]

        global_max = max(
            (v for sm in slot_maps for v in sm.values()),
            default=0.0,
        )

        rows: List[HeatmapRow] = []
        for ns in namespaces:
            cells: List[HeatmapCell] = []
            for idx, sm in enumerate(slot_maps):
                hourly = sm.get(ns, 0.0)
                intensity = (hourly / global_max) if global_max > 0 else 0.0
                cells.append(HeatmapCell(namespace=ns, slot=idx, hourly_cost=hourly, intensity=intensity))
            rows.append(HeatmapRow(namespace=ns, cells=cells))

        return CostHeatmap(rows=rows, num_slots=len(self._slots))
