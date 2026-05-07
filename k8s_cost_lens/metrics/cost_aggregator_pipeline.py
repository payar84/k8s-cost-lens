"""Pipeline that chains cost transformations: filter → sort → top-N → normalize."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.label_filter import LabelFilter, LabelSelector
from k8s_cost_lens.metrics.cost_sorter import CostSorter, SortKey, SortOrder
from k8s_cost_lens.metrics.cost_topn import CostTopNAnalyzer
from k8s_cost_lens.metrics.cost_normalizer import CostNormalizer, NormalizedCost


@dataclass
class PipelineResult:
    """Holds the output of each pipeline stage for inspection."""

    filtered: List[NamespaceCost]
    sorted_costs: List[NamespaceCost]
    top_n: List[NamespaceCost]
    normalized: List[NormalizedCost]

    def __len__(self) -> int:  # noqa: D105
        return len(self.normalized)


@dataclass
class CostAggregatorPipeline:
    """Composable pipeline that applies a fixed sequence of cost transformations.

    Stages
    ------
    1. Label filter  – keep only namespaces whose labels match *selector*.
    2. Sort          – rank by *sort_key* / *sort_order*.
    3. Top-N         – retain only the first *top_n* entries (0 = keep all).
    4. Normalize     – compute each namespace's share of the total cost.
    """

    selector: LabelSelector = field(default_factory=LabelSelector)
    sort_key: SortKey = SortKey.MONTHLY
    sort_order: SortOrder = SortOrder.DESC
    top_n: int = 0  # 0 means no limit

    # internal helpers – created lazily
    _sorter: CostSorter = field(init=False, repr=False)
    _normalizer: CostNormalizer = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._sorter = CostSorter(key=self.sort_key, order=self.sort_order)
        self._normalizer = CostNormalizer()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def run(
        self,
        costs: List[NamespaceCost],
        namespace_labels: Optional[dict[str, dict[str, str]]] = None,
    ) -> PipelineResult:
        """Execute all pipeline stages and return a :class:`PipelineResult`.

        Parameters
        ----------
        costs:
            Raw per-namespace cost estimates.
        namespace_labels:
            Mapping of ``{namespace: {label_key: label_value}}`` used by the
            label-filter stage.  Pass *None* or an empty dict to skip filtering.
        """
        # Stage 1 – label filter
        if namespace_labels and self.selector.pairs:
            lf = LabelFilter(selector=self.selector)
            filtered = lf.filter(costs, namespace_labels)
        else:
            filtered = list(costs)

        # Stage 2 – sort
        ranked = self._sorter.sort(filtered)
        sorted_costs = [r.cost for r in ranked]

        # Stage 3 – top-N
        if self.top_n > 0:
            analyzer = CostTopNAnalyzer(n=self.top_n, key=self.sort_key)
            top_result = analyzer.analyze(sorted_costs)
            top_costs = [m.cost for m in top_result.metrics]
        else:
            top_costs = sorted_costs

        # Stage 4 – normalize
        normalized = self._normalizer.normalize(top_costs)

        return PipelineResult(
            filtered=filtered,
            sorted_costs=sorted_costs,
            top_n=top_costs,
            normalized=normalized,
        )
