"""Estimates cloud spend per namespace based on collected resource metrics."""

from dataclasses import dataclass
from typing import Dict

from k8s_cost_lens.metrics.collector import NamespaceMetrics

# Default on-demand pricing approximations (USD/hour)
# Based on AWS us-east-1 general-purpose instances
DEFAULT_CPU_PRICE_PER_CORE_HOUR: float = 0.048   # ~$0.048 per vCPU/hour
DEFAULT_MEMORY_PRICE_PER_GB_HOUR: float = 0.006  # ~$0.006 per GB/hour


@dataclass
class NamespaceCost:
    namespace: str
    cpu_cost_hourly: float
    memory_cost_hourly: float
    total_cost_hourly: float
    total_cost_monthly: float
    cpu_cores_requested: float
    memory_gb_requested: float


class CostEstimator:
    def __init__(
        self,
        cpu_price_per_core_hour: float = DEFAULT_CPU_PRICE_PER_CORE_HOUR,
        memory_price_per_gb_hour: float = DEFAULT_MEMORY_PRICE_PER_GB_HOUR,
    ):
        self.cpu_price = cpu_price_per_core_hour
        self.memory_price = memory_price_per_gb_hour

    def estimate(self, metrics: Dict[str, NamespaceMetrics]) -> Dict[str, NamespaceCost]:
        """Compute hourly and monthly cost estimates for each namespace."""
        costs: Dict[str, NamespaceCost] = {}
        for ns, m in metrics.items():
            memory_gb = m.memory_requests_bytes / (1024 ** 3)
            cpu_cost = m.cpu_requests_cores * self.cpu_price
            mem_cost = memory_gb * self.memory_price
            total_hourly = cpu_cost + mem_cost
            costs[ns] = NamespaceCost(
                namespace=ns,
                cpu_cost_hourly=round(cpu_cost, 6),
                memory_cost_hourly=round(mem_cost, 6),
                total_cost_hourly=round(total_hourly, 6),
                total_cost_monthly=round(total_hourly * 24 * 30, 4),
                cpu_cores_requested=round(m.cpu_requests_cores, 4),
                memory_gb_requested=round(memory_gb, 4),
            )
        return costs
