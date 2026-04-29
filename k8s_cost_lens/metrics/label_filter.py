"""Filter namespace metrics by Kubernetes labels."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from k8s_cost_lens.metrics.collector import NamespaceMetrics


@dataclass
class LabelSelector:
    """A set of key=value label requirements that must ALL match."""

    labels: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_string(cls, selector: str) -> "LabelSelector":
        """Parse a comma-separated 'key=value,key2=value2' selector string."""
        if not selector or not selector.strip():
            return cls()
        pairs: Dict[str, str] = {}
        for part in selector.split(","):
            part = part.strip()
            if "=" not in part:
                raise ValueError(f"Invalid label selector segment: {part!r}")
            k, v = part.split("=", 1)
            k, v = k.strip(), v.strip()
            if not k:
                raise ValueError(f"Empty key in label selector segment: {part!r}")
            pairs[k] = v
        return cls(labels=pairs)

    def matches(self, namespace_labels: Dict[str, str]) -> bool:
        """Return True when every required label is present with the expected value."""
        for k, v in self.labels.items():
            if namespace_labels.get(k) != v:
                return False
        return True


class LabelFilter:
    """Filter a list of NamespaceMetrics using a LabelSelector."""

    def __init__(self, selector: Optional[LabelSelector] = None) -> None:
        self._selector = selector or LabelSelector()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter(
        self,
        metrics: List[NamespaceMetrics],
        label_map: Dict[str, Dict[str, str]],
    ) -> List[NamespaceMetrics]:
        """Return only those metrics whose namespace matches the selector.

        Args:
            metrics:   List of NamespaceMetrics to filter.
            label_map: Mapping of namespace name -> label dict.
        """
        if not self._selector.labels:
            return list(metrics)
        return [
            m
            for m in metrics
            if self._selector.matches(label_map.get(m.namespace, {}))
        ]
