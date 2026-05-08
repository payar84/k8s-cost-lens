"""Cost efficiency scoring: ratio of requested vs actual resource utilization."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class EfficiencyScore:
    namespace: str
    hourly_cost: float
    cpu_requested: float   # cores
    cpu_used: float        # cores
    mem_requested_gb: float
    mem_used_gb: float
    cpu_efficiency: Optional[float]   # 0-1, None when requested == 0
    mem_efficiency: Optional[float]   # 0-1, None when requested == 0
    overall_efficiency: Optional[float]  # average of available scores

    def __str__(self) -> str:
        eff = f"{self.overall_efficiency:.1%}" if self.overall_efficiency is not None else "n/a"
        return f"EfficiencyScore({self.namespace}, overall={eff})"


def _ratio(used: float, requested: float) -> Optional[float]:
    if requested <= 0.0:
        return None
    return min(used / requested, 1.0)


class CostEfficiencyAnalyzer:
    """Compute efficiency scores by comparing requested vs used resources."""

    def score(
        self,
        costs: List[NamespaceCost],
        cpu_used: dict[str, float],
        mem_used_gb: dict[str, float],
    ) -> List[EfficiencyScore]:
        """Return efficiency scores for each namespace.

        Args:
            costs: estimated namespace costs (contain requested resources).
            cpu_used: mapping of namespace -> actual CPU cores used.
            mem_used_gb: mapping of namespace -> actual memory used in GiB.
        """
        results: List[EfficiencyScore] = []
        for nc in costs:
            ns = nc.namespace
            cpu_req = nc.cpu_cores
            mem_req = nc.memory_gb
            cu = cpu_used.get(ns, 0.0)
            mu = mem_used_gb.get(ns, 0.0)

            cpu_eff = _ratio(cu, cpu_req)
            mem_eff = _ratio(mu, mem_req)

            scores = [s for s in (cpu_eff, mem_eff) if s is not None]
            overall = sum(scores) / len(scores) if scores else None

            results.append(
                EfficiencyScore(
                    namespace=ns,
                    hourly_cost=nc.hourly_cost,
                    cpu_requested=cpu_req,
                    cpu_used=cu,
                    mem_requested_gb=mem_req,
                    mem_used_gb=mu,
                    cpu_efficiency=cpu_eff,
                    mem_efficiency=mem_eff,
                    overall_efficiency=overall,
                )
            )
        return results
