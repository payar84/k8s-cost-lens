"""Formatter for side-by-side namespace cost comparisons across two time windows."""

from dataclasses import dataclass
from typing import List, Optional
import io
import csv

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class ComparisonRow:
    namespace: str
    hourly_before: float
    hourly_after: float
    monthly_before: float
    monthly_after: float
    hourly_diff: float
    monthly_diff: float
    hourly_diff_pct: Optional[float]
    monthly_diff_pct: Optional[float]


class CostComparisonFormatter:
    """Formats a before/after cost comparison for a set of namespaces."""

    _HEADERS = [
        "Namespace",
        "Hourly Before ($)",
        "Hourly After ($)",
        "Hourly Diff ($)",
        "Hourly Diff (%)",
        "Monthly Before ($)",
        "Monthly After ($)",
        "Monthly Diff ($)",
        "Monthly Diff (%)",
    ]

    def __init__(
        self,
        before: List[NamespaceCost],
        after: List[NamespaceCost],
    ) -> None:
        self._before = {c.namespace: c for c in before}
        self._after = {c.namespace: c for c in after}

    def _to_rows(self) -> List[ComparisonRow]:
        namespaces = sorted(set(self._before) | set(self._after))
        rows: List[ComparisonRow] = []
        for ns in namespaces:
            b = self._before.get(ns)
            a = self._after.get(ns)
            h_before = b.hourly_cost if b else 0.0
            h_after = a.hourly_cost if a else 0.0
            m_before = b.monthly_cost if b else 0.0
            m_after = a.monthly_cost if a else 0.0
            h_diff = h_after - h_before
            m_diff = m_after - m_before
            h_pct = (h_diff / h_before * 100) if h_before else None
            m_pct = (m_diff / m_before * 100) if m_before else None
            rows.append(
                ComparisonRow(
                    namespace=ns,
                    hourly_before=h_before,
                    hourly_after=h_after,
                    monthly_before=m_before,
                    monthly_after=m_after,
                    hourly_diff=h_diff,
                    monthly_diff=m_diff,
                    hourly_diff_pct=h_pct,
                    monthly_diff_pct=m_pct,
                )
            )
        return rows

    def as_table(self) -> str:
        rows = self._to_rows()
        lines = ["  ".join(self._HEADERS)]
        for r in rows:
            h_pct = f"{r.hourly_diff_pct:+.1f}" if r.hourly_diff_pct is not None else "N/A"
            m_pct = f"{r.monthly_diff_pct:+.1f}" if r.monthly_diff_pct is not None else "N/A"
            lines.append(
                f"{r.namespace}  "
                f"{r.hourly_before:.4f}  {r.hourly_after:.4f}  "
                f"{r.hourly_diff:+.4f}  {h_pct}  "
                f"{r.monthly_before:.2f}  {r.monthly_after:.2f}  "
                f"{r.monthly_diff:+.2f}  {m_pct}"
            )
        return "\n".join(lines)

    def as_csv(self) -> str:
        rows = self._to_rows()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self._HEADERS)
        for r in rows:
            h_pct = f"{r.hourly_diff_pct:+.1f}" if r.hourly_diff_pct is not None else "N/A"
            m_pct = f"{r.monthly_diff_pct:+.1f}" if r.monthly_diff_pct is not None else "N/A"
            writer.writerow([
                r.namespace,
                f"{r.hourly_before:.4f}",
                f"{r.hourly_after:.4f}",
                f"{r.hourly_diff:+.4f}",
                h_pct,
                f"{r.monthly_before:.2f}",
                f"{r.monthly_after:.2f}",
                f"{r.monthly_diff:+.2f}",
                m_pct,
            ])
        return buf.getvalue()
