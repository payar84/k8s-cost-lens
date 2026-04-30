"""Tests for TagPolicyEnforcer."""
import pytest

from k8s_cost_lens.metrics.collector import NamespaceMetrics
from k8s_cost_lens.metrics.tag_policy import (
    TagPolicy,
    TagPolicyEnforcer,
    PolicyViolation,
)


def make_nm(namespace: str, labels: dict | None = None) -> NamespaceMetrics:
    return NamespaceMetrics(
        namespace=namespace,
        cpu_cores=0.1,
        memory_bytes=128 * 1024 * 1024,
        labels=labels or {},
    )


@pytest.fixture
def policy() -> TagPolicy:
    return TagPolicy(
        required_labels=["team", "env"],
        allowed_values={"env": ["prod", "staging", "dev"]},
    )


@pytest.fixture
def enforcer(policy: TagPolicy) -> TagPolicyEnforcer:
    return TagPolicyEnforcer(policy)


def test_no_violations_when_all_labels_present_and_valid(enforcer):
    nm = make_nm("ns-a", {"team": "platform", "env": "prod"})
    assert enforcer.check([nm]) == []


def test_missing_required_label_triggers_violation(enforcer):
    nm = make_nm("ns-b", {"team": "platform"})
    violations = enforcer.check([nm])
    assert len(violations) == 1
    assert "env" in violations[0].missing_tags


def test_invalid_allowed_value_triggers_violation(enforcer):
    nm = make_nm("ns-c", {"team": "sre", "env": "qa"})
    violations = enforcer.check([nm])
    assert len(violations) == 1
    assert "env" in violations[0].invalid_tags


def test_both_missing_and_invalid_in_same_violation(enforcer):
    nm = make_nm("ns-d", {"env": "qa"})  # missing 'team', invalid 'env'
    violations = enforcer.check([nm])
    assert len(violations) == 1
    v = violations[0]
    assert "team" in v.missing_tags
    assert "env" in v.invalid_tags


def test_multiple_namespaces_multiple_violations(enforcer):
    metrics = [
        make_nm("ok", {"team": "a", "env": "dev"}),
        make_nm("bad1", {}),
        make_nm("bad2", {"team": "b", "env": "unknown"}),
    ]
    violations = enforcer.check(metrics)
    assert len(violations) == 2
    namespaces = {v.namespace for v in violations}
    assert namespaces == {"bad1", "bad2"}


def test_is_compliant_true_when_no_violations(enforcer):
    nm = make_nm("ns", {"team": "x", "env": "staging"})
    assert enforcer.is_compliant([nm]) is True


def test_is_compliant_false_when_violation_exists(enforcer):
    nm = make_nm("ns", {})
    assert enforcer.is_compliant([nm]) is False


def test_empty_policy_never_violates():
    enforcer = TagPolicyEnforcer(TagPolicy())
    nm = make_nm("ns", {})
    assert enforcer.check([nm]) == []


def test_str_representation_includes_namespace():
    v = PolicyViolation(namespace="ns-x", missing_tags=["team"], invalid_tags={})
    assert "ns-x" in str(v)
    assert "team" in str(v)
