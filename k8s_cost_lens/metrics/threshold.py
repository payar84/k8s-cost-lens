"""Threshold alerting for namespace cost estimates."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class ThresholdViolation:
    namespace: str
    hourly_cost: float
    monthly_cost: float
    hourly_limit: Optional[float]
    monthly_limit: Optional[float]

    @property
    def exceeded_hourly(self) -> bool:
        return self.hourly_limit is not None and self.hourly_cost > self.hourly_limit

    @property
    def exceeded_monthly(self) -> bool:
        return self.monthly_limit is not None and self.monthly_cost > self.monthly_limit

    def __str__(self) -> str:
        parts: List[str] = []
        if self.exceeded_hourly:
            parts.append(
                f"hourly ${self.hourly_cost:.4f} > limit ${self.hourly_limit:.4f}"
            )
        if self.exceeded_monthly:
            parts.append(
                f"monthly ${self.monthly_cost:.2f} > limit ${self.monthly_limit:.2f}"
            )
        return f"[{self.namespace}] " + "; ".join(parts)


@dataclass
class CostThresholdChecker:
    """Check namespace costs against configurable per-namespace or global thresholds."""

    global_hourly_limit: Optional[float] = None
    global_monthly_limit: Optional[float] = None
    # namespace -> (hourly_limit, monthly_limit)
    namespace_limits: Dict[str, tuple[Optional[float], Optional[float]]] = field(
        default_factory=dict
    )

    def set_namespace_limit(
        self,
        namespace: str,
        hourly: Optional[float] = None,
        monthly: Optional[float] = None,
    ) -> None:
        self.namespace_limits[namespace] = (hourly, monthly)

    def check(self, costs: List[NamespaceCost]) -> List[ThresholdViolation]:
        """Return a list of violations for all namespaces that exceed their limits."""
        violations: List[ThresholdViolation] = []
        for nc in costs:
            ns_hourly, ns_monthly = self.namespace_limits.get(
                nc.namespace, (None, None)
            )
            hourly_limit = ns_hourly if ns_hourly is not None else self.global_hourly_limit
            monthly_limit = ns_monthly if ns_monthly is not None else self.global_monthly_limit

            v = ThresholdViolation(
                namespace=nc.namespace,
                hourly_cost=nc.hourly_cost,
                monthly_cost=nc.monthly_cost,
                hourly_limit=hourly_limit,
                monthly_limit=monthly_limit,
            )
            if v.exceeded_hourly or v.exceeded_monthly:
                violations.append(v)
        return violations
