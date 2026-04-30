"""Cost cap enforcement: define per-namespace spending caps and check compliance."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class CapViolation:
    namespace: str
    cap_hourly: Optional[float]
    cap_monthly: Optional[float]
    actual_hourly: float
    actual_monthly: float

    def hourly_exceeded(self) -> bool:
        return self.cap_hourly is not None and self.actual_hourly > self.cap_hourly

    def monthly_exceeded(self) -> bool:
        return self.cap_monthly is not None and self.actual_monthly > self.cap_monthly

    def __str__(self) -> str:
        parts: List[str] = []
        if self.hourly_exceeded():
            parts.append(
                f"hourly ${self.actual_hourly:.4f} > cap ${self.cap_hourly:.4f}"
            )
        if self.monthly_exceeded():
            parts.append(
                f"monthly ${self.actual_monthly:.4f} > cap ${self.cap_monthly:.4f}"
            )
        return f"[{self.namespace}] " + ", ".join(parts)


@dataclass
class CostCapChecker:
    """Check namespace costs against configurable hourly/monthly caps."""

    hourly_caps: Dict[str, float] = field(default_factory=dict)
    monthly_caps: Dict[str, float] = field(default_factory=dict)
    default_hourly_cap: Optional[float] = None
    default_monthly_cap: Optional[float] = None

    def check(self, costs: List[NamespaceCost]) -> List[CapViolation]:
        violations: List[CapViolation] = []
        for cost in costs:
            ns = cost.namespace
            h_cap = self.hourly_caps.get(ns, self.default_hourly_cap)
            m_cap = self.monthly_caps.get(ns, self.default_monthly_cap)
            v = CapViolation(
                namespace=ns,
                cap_hourly=h_cap,
                cap_monthly=m_cap,
                actual_hourly=cost.total_hourly,
                actual_monthly=cost.total_monthly,
            )
            if v.hourly_exceeded() or v.monthly_exceeded():
                violations.append(v)
        return violations
