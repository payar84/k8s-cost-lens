"""Group namespaces by label prefix or custom mapping for rolled-up cost reporting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class GroupedCost:
    """Aggregated cost for a logical group of namespaces."""

    group_name: str
    namespaces: List[str]
    total_hourly_usd: float
    total_monthly_usd: float
    total_cpu_cores: float
    total_memory_gib: float

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"GroupedCost(group={self.group_name!r}, "
            f"namespaces={self.namespaces}, "
            f"hourly=${self.total_hourly_usd:.4f})"
        )


class NamespaceGrouper:
    """Groups NamespaceCost objects by a configurable mapping.

    Parameters
    ----------
    mapping:
        Dict mapping group_name -> list of namespace names that belong to it.
        Namespaces not present in any group are placed in the ``default_group``.
    default_group:
        Name used for ungrouped namespaces.  Defaults to ``"other"``.
    """

    def __init__(
        self,
        mapping: Optional[Dict[str, List[str]]] = None,
        default_group: str = "other",
    ) -> None:
        self._mapping: Dict[str, List[str]] = mapping or {}
        self._default_group = default_group
        # Build reverse lookup: namespace -> group
        self._reverse: Dict[str, str] = {}
        for group, namespaces in self._mapping.items():
            for ns in namespaces:
                self._reverse[ns] = group

    def group(self, costs: List[NamespaceCost]) -> List[GroupedCost]:
        """Return a list of GroupedCost objects."""
        buckets: Dict[str, List[NamespaceCost]] = {}
        for cost in costs:
            group_name = self._reverse.get(cost.namespace, self._default_group)
            buckets.setdefault(group_name, []).append(cost)

        result: List[GroupedCost] = []
        for group_name, members in sorted(buckets.items()):
            result.append(
                GroupedCost(
                    group_name=group_name,
                    namespaces=sorted(c.namespace for c in members),
                    total_hourly_usd=sum(c.hourly_usd for c in members),
                    total_monthly_usd=sum(c.monthly_usd for c in members),
                    total_cpu_cores=sum(c.cpu_cores for c in members),
                    total_memory_gib=sum(c.memory_gib for c in members),
                )
            )
        return result
