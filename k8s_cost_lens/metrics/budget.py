"""Namespace budget tracking: compare estimated costs against defined budgets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class BudgetStatus:
    namespace: str
    hourly_budget: Optional[float]
    monthly_budget: Optional[float]
    hourly_cost: float
    monthly_cost: float

    @property
    def hourly_usage_pct(self) -> Optional[float]:
        if self.hourly_budget and self.hourly_budget > 0:
            return (self.hourly_cost / self.hourly_budget) * 100.0
        return None

    @property
    def monthly_usage_pct(self) -> Optional[float]:
        if self.monthly_budget and self.monthly_budget > 0:
            return (self.monthly_cost / self.monthly_budget) * 100.0
        return None

    @property
    def hourly_exceeded(self) -> bool:
        return (
            self.hourly_budget is not None
            and self.hourly_cost > self.hourly_budget
        )

    @property
    def monthly_exceeded(self) -> bool:
        return (
            self.monthly_budget is not None
            and self.monthly_cost > self.monthly_budget
        )

    @property
    def any_exceeded(self) -> bool:
        return self.hourly_exceeded or self.monthly_exceeded


@dataclass
class NamespaceBudgetChecker:
    """Check namespace costs against per-namespace budget limits."""

    # Maps namespace -> (hourly_budget, monthly_budget); None means no limit.
    hourly_budgets: Dict[str, float] = field(default_factory=dict)
    monthly_budgets: Dict[str, float] = field(default_factory=dict)

    def set_budget(
        self,
        namespace: str,
        *,
        hourly: Optional[float] = None,
        monthly: Optional[float] = None,
    ) -> None:
        if hourly is not None:
            self.hourly_budgets[namespace] = hourly
        if monthly is not None:
            self.monthly_budgets[namespace] = monthly

    def check(self, costs: List[NamespaceCost]) -> List[BudgetStatus]:
        statuses: List[BudgetStatus] = []
        for nc in costs:
            statuses.append(
                BudgetStatus(
                    namespace=nc.namespace,
                    hourly_budget=self.hourly_budgets.get(nc.namespace),
                    monthly_budget=self.monthly_budgets.get(nc.namespace),
                    hourly_cost=nc.hourly_cost,
                    monthly_cost=nc.monthly_cost,
                )
            )
        return statuses

    def exceeded(self, costs: List[NamespaceCost]) -> List[BudgetStatus]:
        """Return only namespaces that have exceeded at least one budget."""
        return [s for s in self.check(costs) if s.any_exceeded]
