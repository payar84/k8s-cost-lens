"""Tests for CostQuotaChecker."""
import pytest
from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_quota import (
    CostQuotaChecker,
    QuotaLimit,
    QuotaResult,
)


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
    )


@pytest.fixture
def checker() -> CostQuotaChecker:
    return CostQuotaChecker([
        QuotaLimit(
            namespace="team-a",
            soft_hourly=0.10,
            hard_hourly=0.20,
            soft_monthly=72.0,
            hard_monthly=144.0,
        ),
        QuotaLimit(namespace="team-b", hard_monthly=50.0),
    ])


def test_no_quotas_returns_ok_for_all():
    c = CostQuotaChecker()
    costs = [make_cost("ns-x", 1.0), make_cost("ns-y", 2.0)]
    results = c.check(costs)
    assert len(results) == 2
    assert all(r.severity() == "ok" for r in results)
    assert all(not r.any_breached for r in results)


def test_within_soft_limit_is_ok(checker):
    results = checker.check([make_cost("team-a", 0.05)])
    r = results[0]
    assert r.severity() == "ok"
    assert not r.soft_hourly_breached
    assert not r.hard_hourly_breached


def test_soft_hourly_breach(checker):
    results = checker.check([make_cost("team-a", 0.15)])
    r = results[0]
    assert r.soft_hourly_breached
    assert not r.hard_hourly_breached
    assert r.severity() == "soft"


def test_hard_hourly_breach(checker):
    results = checker.check([make_cost("team-a", 0.25)])
    r = results[0]
    assert r.hard_hourly_breached
    assert r.severity() == "hard"


def test_hard_monthly_breach_only(checker):
    # team-b only has hard_monthly=50.0
    results = checker.check([make_cost("team-b", 0.10)])
    r = results[0]
    # 0.10 * 720 = 72 > 50
    assert r.hard_monthly_breached
    assert r.severity() == "hard"


def test_namespace_without_quota_is_ok(checker):
    results = checker.check([make_cost("unknown-ns", 999.0)])
    r = results[0]
    assert r.severity() == "ok"
    assert not r.any_breached


def test_multiple_namespaces_checked_independently(checker):
    costs = [make_cost("team-a", 0.25), make_cost("team-b", 0.01)]
    results = checker.check(costs)
    by_ns = {r.namespace: r for r in results}
    assert by_ns["team-a"].severity() == "hard"
    # 0.01 * 720 = 7.2 < 50 => ok
    assert by_ns["team-b"].severity() == "ok"


def test_str_representation():
    r = QuotaResult(
        namespace="demo",
        hourly_cost=0.5,
        monthly_cost=360.0,
        soft_hourly_limit=0.1,
        hard_hourly_limit=1.0,
        soft_monthly_limit=None,
        hard_monthly_limit=None,
    )
    s = str(r)
    assert "demo" in s
    assert "hard" not in s or "soft" in s
