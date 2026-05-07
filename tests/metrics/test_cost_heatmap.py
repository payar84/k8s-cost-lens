"""Tests for CostHeatmapBuilder and CostHeatmap."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_heatmap import CostHeatmapBuilder, HeatmapCell


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
        cpu_cost=hourly * 0.6,
        memory_cost=hourly * 0.4,
    )


@pytest.fixture()
def builder() -> CostHeatmapBuilder:
    return CostHeatmapBuilder()


def test_empty_builder_returns_empty_heatmap(builder):
    hm = builder.build()
    assert hm.rows == []
    assert hm.num_slots == 0


def test_single_slot_single_namespace(builder):
    builder.add_slot([make_cost("ns-a", 0.5)])
    hm = builder.build()
    assert len(hm.rows) == 1
    assert hm.num_slots == 1
    assert hm.rows[0].namespace == "ns-a"
    assert len(hm.rows[0].cells) == 1


def test_intensity_is_one_for_single_cell(builder):
    builder.add_slot([make_cost("ns-a", 1.0)])
    hm = builder.build()
    assert hm.rows[0].cells[0].intensity == pytest.approx(1.0)


def test_intensity_zero_for_zero_cost(builder):
    builder.add_slot([make_cost("ns-a", 0.0)])
    hm = builder.build()
    assert hm.rows[0].cells[0].intensity == pytest.approx(0.0)


def test_multiple_slots_produce_correct_num_cells(builder):
    builder.add_slot([make_cost("ns-a", 1.0), make_cost("ns-b", 2.0)])
    builder.add_slot([make_cost("ns-a", 3.0), make_cost("ns-b", 0.5)])
    hm = builder.build()
    assert hm.num_slots == 2
    for row in hm.rows:
        assert len(row.cells) == 2


def test_global_max_normalisation(builder):
    """The cell with the highest cost should have intensity == 1.0."""
    builder.add_slot([make_cost("ns-a", 1.0), make_cost("ns-b", 4.0)])
    builder.add_slot([make_cost("ns-a", 2.0), make_cost("ns-b", 0.5)])
    hm = builder.build()
    all_cells: list[HeatmapCell] = [
        cell for row in hm.rows for cell in row.cells
    ]
    max_intensity = max(c.intensity for c in all_cells)
    assert max_intensity == pytest.approx(1.0)


def test_missing_namespace_in_later_slot_defaults_to_zero(builder):
    builder.add_slot([make_cost("ns-a", 1.0), make_cost("ns-b", 2.0)])
    builder.add_slot([make_cost("ns-a", 1.5)])  # ns-b absent
    hm = builder.build()
    ns_b_row = hm.get_row("ns-b")
    assert ns_b_row is not None
    assert ns_b_row.cells[1].hourly_cost == pytest.approx(0.0)


def test_peak_hourly_is_max_across_slots(builder):
    builder.add_slot([make_cost("ns-a", 0.3)])
    builder.add_slot([make_cost("ns-a", 0.9)])
    builder.add_slot([make_cost("ns-a", 0.1)])
    hm = builder.build()
    assert hm.rows[0].peak_hourly == pytest.approx(0.9)


def test_clear_resets_builder(builder):
    builder.add_slot([make_cost("ns-a", 1.0)])
    builder.clear()
    hm = builder.build()
    assert hm.rows == []


def test_get_row_returns_none_for_unknown_namespace(builder):
    builder.add_slot([make_cost("ns-a", 1.0)])
    hm = builder.build()
    assert hm.get_row("ns-z") is None
