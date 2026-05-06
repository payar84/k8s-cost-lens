"""Per-namespace cost quota enforcement with soft and hard limits."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class QuotaLimit:
    """Soft and hard hourly/monthly cost limits for a namespace."""
    namespace: str
    soft_hourly: Optional[float] = None
    hard_hourly: Optional[float] = None
    soft_monthly: Optional[float] = None
    hard_monthly: Optional[float] = None


@dataclass
class QuotaResult:
    """Result of a quota check for a single namespace."""
    namespace: str
    hourly_cost: float
    monthly_cost: float
    soft_hourly_limit: Optional[float]
    hard_hourly_limit: Optional[float]
    soft_monthly_limit: Optional[float]
    hard_monthly_limit: Optional[float]

    @property
    def soft_hourly_breached(self) -> bool:
        return self.soft_hourly_limit is not None and self.hourly_cost > self.soft_hourly_limit

    @property
    def hard_hourly_breached(self) -> bool:
        return self.hard_hourly_limit is not None and self.hourly_cost > self.hard_hourly_limit

    @property
    def soft_monthly_breached(self) -> bool:
        return self.soft_monthly_limit is not None and self.monthly_cost > self.soft_monthly_limit

    @property
    def hard_monthly_breached(self) -> bool:
        return self.hard_monthly_limit is not None and self.monthly_cost > self.hard_monthly_limit

    @property
    def any_breached(self) -> bool:
        return (
            self.soft_hourly_breached
            or self.hard_hourly_breached
            or self.soft_monthly_breached
            or self.hard_monthly_breached
        )

    def severity(self) -> str:
        """Return 'hard', 'soft', or 'ok'."""
        if self.hard_hourly_breached or self.hard_monthly_breached:
            return "hard"
        if self.soft_hourly_breached or self.soft_monthly_breached:
            return "soft"
        return "ok"

    def __str__(self) -> str:
        return (
            f"QuotaResult({self.namespace}, severity={self.severity()}, "
            f"hourly={self.hourly_cost:.4f}, monthly={self.monthly_cost:.2f})"
        )


class CostQuotaChecker:
    """Check NamespaceCost values against configured quota limits."""

    def __init__(self, quotas: Optional[List[QuotaLimit]] = None) -> None:
        self._quotas: dict[str, QuotaLimit] = {
            q.namespace: q for q in (quotas or [])
        }

    def check(self, costs: List[NamespaceCost]) -> List[QuotaResult]:
        results: List[QuotaResult] = []
        for cost in costs:
            quota = self._quotas.get(cost.namespace)
            results.append(QuotaResult(
                namespace=cost.namespace,
                hourly_cost=cost.hourly_cost,
                monthly_cost=cost.monthly_cost,
                soft_hourly_limit=quota.soft_hourly if quota else None,
                hard_hourly_limit=quota.hard_hourly if quota else None,
                soft_monthly_limit=quota.soft_monthly if quota else None,
                hard_monthly_limit=quota.hard_monthly if quota else None,
            ))
        return results
