"""Tests for LabelFilter and LabelSelector."""
import pytest

from k8s_cost_lens.metrics.collector import NamespaceMetrics
from k8s_cost_lens.metrics.label_filter import LabelFilter, LabelSelector


def make_nm(namespace: str) -> NamespaceMetrics:
    return NamespaceMetrics(namespace=namespace, cpu_cores=0.5, memory_bytes=512 * 1024 * 1024)


LABEL_MAP = {
    "team-alpha": {"team": "alpha", "env": "prod"},
    "team-beta": {"team": "beta", "env": "prod"},
    "team-gamma": {"team": "gamma", "env": "staging"},
}

ALL_METRICS = [make_nm(ns) for ns in LABEL_MAP]


# ---------------------------------------------------------------------------
# LabelSelector.from_string
# ---------------------------------------------------------------------------

def test_from_string_empty_returns_empty_selector():
    sel = LabelSelector.from_string("")
    assert sel.labels == {}


def test_from_string_single_pair():
    sel = LabelSelector.from_string("env=prod")
    assert sel.labels == {"env": "prod"}


def test_from_string_multiple_pairs():
    sel = LabelSelector.from_string("env=prod,team=alpha")
    assert sel.labels == {"env": "prod", "team": "alpha"}


def test_from_string_invalid_raises():
    with pytest.raises(ValueError):
        LabelSelector.from_string("env")


def test_from_string_empty_key_raises():
    with pytest.raises(ValueError):
        LabelSelector.from_string("=prod")


# ---------------------------------------------------------------------------
# LabelSelector.matches
# ---------------------------------------------------------------------------

def test_matches_empty_selector_always_true():
    sel = LabelSelector()
    assert sel.matches({"team": "alpha"}) is True


def test_matches_exact_labels():
    sel = LabelSelector(labels={"team": "alpha", "env": "prod"})
    assert sel.matches({"team": "alpha", "env": "prod"}) is True


def test_matches_missing_key_returns_false():
    sel = LabelSelector(labels={"team": "alpha"})
    assert sel.matches({"env": "prod"}) is False


def test_matches_wrong_value_returns_false():
    sel = LabelSelector(labels={"env": "prod"})
    assert sel.matches({"env": "staging"}) is False


# ---------------------------------------------------------------------------
# LabelFilter.filter
# ---------------------------------------------------------------------------

def test_empty_selector_returns_all():
    lf = LabelFilter()
    result = lf.filter(ALL_METRICS, LABEL_MAP)
    assert len(result) == len(ALL_METRICS)


def test_filter_by_env_prod_returns_two():
    lf = LabelFilter(LabelSelector.from_string("env=prod"))
    result = lf.filter(ALL_METRICS, LABEL_MAP)
    names = {m.namespace for m in result}
    assert names == {"team-alpha", "team-beta"}


def test_filter_by_team_and_env_returns_one():
    lf = LabelFilter(LabelSelector.from_string("team=gamma,env=staging"))
    result = lf.filter(ALL_METRICS, LABEL_MAP)
    assert len(result) == 1
    assert result[0].namespace == "team-gamma"


def test_filter_no_match_returns_empty():
    lf = LabelFilter(LabelSelector.from_string("env=dev"))
    result = lf.filter(ALL_METRICS, LABEL_MAP)
    assert result == []


def test_filter_namespace_missing_from_label_map_excluded():
    extra = make_nm("unlabelled")
    lf = LabelFilter(LabelSelector.from_string("env=prod"))
    result = lf.filter(ALL_METRICS + [extra], LABEL_MAP)
    names = {m.namespace for m in result}
    assert "unlabelled" not in names
