"""Tests for NamespaceBudgetChecker and BudgetStatus."""
import pytest

from k8s_cost_lens.metrics.budget import BudgetStatus, NamespaceBudgetChecker
from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
    )


@pytest.fixture()
def checker() -> NamespaceBudgetChecker:
    c = NamespaceBudgetChecker()
    c.set_budget("team-a", hourly=1.0, monthly=500.0)
    c.set_budget("team-b", monthly=100.0)
    return c


def test_no_budgets_returns_statuses_with_none_limits():
    c = NamespaceBudgetChecker()
    costs = [make_cost("default", 0.5)]
    statuses = c.check(costs)
    assert len(statuses) == 1
    s = statuses[0]
    assert s.hourly_budget is None
    assert s.monthly_budget is None
    assert not s.hourly_exceeded
    assert not s.monthly_exceeded


def test_within_budget_not_exceeded(checker):
    costs = [make_cost("team-a", 0.5)]
    statuses = checker.check(costs)
    assert len(statuses) == 1
    assert not statuses[0].hourly_exceeded
    assert not statuses[0].monthly_exceeded
    assert not statuses[0].any_exceeded


def test_hourly_budget_exceeded(checker):
    costs = [make_cost("team-a", 2.0)]
    statuses = checker.check(costs)
    assert statuses[0].hourly_exceeded
    assert statuses[0].any_exceeded


def test_monthly_budget_exceeded(checker):
    # team-b has only a monthly budget of 100.0
    costs = [make_cost("team-b", 0.2)]  # 0.2 * 720 = 144 > 100
    statuses = checker.check(costs)
    assert not statuses[0].hourly_exceeded
    assert statuses[0].monthly_exceeded
    assert statuses[0].any_exceeded


def test_usage_pct_calculated_correctly(checker):
    costs = [make_cost("team-a", 0.5)]
    s = checker.check(costs)[0]
    assert s.hourly_usage_pct == pytest.approx(50.0)
    assert s.monthly_usage_pct == pytest.approx((0.5 * 720 / 500.0) * 100.0)


def test_usage_pct_none_when_no_budget():
    c = NamespaceBudgetChecker()
    s = BudgetStatus(
        namespace="x", hourly_budget=None, monthly_budget=None,
        hourly_cost=1.0, monthly_cost=720.0,
    )
    assert s.hourly_usage_pct is None
    assert s.monthly_usage_pct is None


def test_exceeded_filters_only_violations(checker):
    costs = [
        make_cost("team-a", 0.5),   # within budget
        make_cost("team-b", 0.2),   # monthly exceeded
        make_cost("other", 10.0),   # no budget defined -> not exceeded
    ]
    violations = checker.exceeded(costs)
    assert len(violations) == 1
    assert violations[0].namespace == "team-b"


def test_set_budget_overwrites_existing():
    c = NamespaceBudgetChecker()
    c.set_budget("ns", hourly=1.0)
    c.set_budget("ns", hourly=5.0)
    assert c.hourly_budgets["ns"] == 5.0
