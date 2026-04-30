"""Tag-based cost policy enforcement for namespace metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from k8s_cost_lens.metrics.collector import NamespaceMetrics


@dataclass
class PolicyViolation:
    namespace: str
    missing_tags: List[str]
    invalid_tags: Dict[str, str]  # tag -> reason

    def __str__(self) -> str:
        parts = []
        if self.missing_tags:
            parts.append(f"missing={','.join(self.missing_tags)}")
        if self.invalid_tags:
            inv = ",".join(f"{k}:{v}" for k, v in self.invalid_tags.items())
            parts.append(f"invalid={inv}")
        return f"PolicyViolation(namespace={self.namespace}, {'; '.join(parts)})"


@dataclass
class TagPolicy:
    required_labels: List[str] = field(default_factory=list)
    allowed_values: Dict[str, List[str]] = field(default_factory=dict)


class TagPolicyEnforcer:
    """Checks NamespaceMetrics labels against a TagPolicy."""

    def __init__(self, policy: TagPolicy) -> None:
        self._policy = policy

    def check(self, metrics: List[NamespaceMetrics]) -> List[PolicyViolation]:
        violations: List[PolicyViolation] = []
        for nm in metrics:
            labels = nm.labels or {}
            missing = [
                req for req in self._policy.required_labels if req not in labels
            ]
            invalid: Dict[str, str] = {}
            for tag, allowed in self._policy.allowed_values.items():
                if tag in labels and labels[tag] not in allowed:
                    invalid[tag] = (
                        f"'{labels[tag]}' not in allowed {allowed}"
                    )
            if missing or invalid:
                violations.append(
                    PolicyViolation(
                        namespace=nm.namespace,
                        missing_tags=missing,
                        invalid_tags=invalid,
                    )
                )
        return violations

    def is_compliant(self, metrics: List[NamespaceMetrics]) -> bool:
        return len(self.check(metrics)) == 0
