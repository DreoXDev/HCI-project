import pandas as pd
import pytest

from scripts import validate_quantitative_report as quantitative


def test_normalize_task_outcome_handles_common_variants() -> None:
    assert quantitative.normalize_task_outcome("Successo") == "success"
    assert quantitative.normalize_task_outcome("Aiuto richiesto") == "partial_success"
    assert quantitative.normalize_task_outcome("Non completato") == "failure"


def test_absolute_effectiveness_counts_partial_success_as_error() -> None:
    df = pd.DataFrame(
        [
            {"participant_id": "U1", "task_id": "T01", "task_name": "Task 1", "app": "Deliveroo", "binary_success_for_absolute_effectiveness": 1},
            {"participant_id": "U2", "task_id": "T01", "task_name": "Task 1", "app": "Deliveroo", "binary_success_for_absolute_effectiveness": 0},
            {"participant_id": "U3", "task_id": "T01", "task_name": "Task 1", "app": "Deliveroo", "binary_success_for_absolute_effectiveness": 0},
        ]
    )
    thresholds = {"effectiveness": {"critical_error_max_rate": 1 / 24}}

    result = quantitative._absolute_effectiveness_by_task_app(df, thresholds)

    assert result["observed_error_count"].iloc[0] == 2
    assert result["absolute_effectiveness_rate"].iloc[0] == pytest.approx(1 / 3)


def test_effectiveness_task_detail_counts_sum_to_users() -> None:
    df = pd.DataFrame(
        [
            {"participant_id": "U1", "task_id": "T01", "task_name": "Task 1", "app": "Deliveroo", "completed": 1, "completed_autonomously": 1, "help_requested": 0, "critical_error": 0, "failed": 0},
            {"participant_id": "U2", "task_id": "T01", "task_name": "Task 1", "app": "Deliveroo", "completed": 1, "completed_autonomously": 0, "help_requested": 1, "critical_error": 1, "failed": 0},
            {"participant_id": "U1", "task_id": "T01", "task_name": "Task 1", "app": "Glovo", "completed": 1, "completed_autonomously": 1, "help_requested": 0, "critical_error": 0, "failed": 0},
            {"participant_id": "U2", "task_id": "T01", "task_name": "Task 1", "app": "Glovo", "completed": 0, "completed_autonomously": 0, "help_requested": 0, "critical_error": 1, "failed": 1},
        ]
    )

    result = quantitative._effectiveness_task_detail(df)

    for row in result.itertuples(index=False):
        assert row.success_autonomous + row.error_or_non_autonomous_count == row.n_users
        assert 0 <= row.effectiveness_rate <= 1
        assert 0 <= row.autonomous_rate <= 1


def test_efficiency_oet_detail_uses_configured_thresholds() -> None:
    df = pd.DataFrame(
        [
            {"participant_id": "U1", "task_id": "T01", "task_name": "Task 1", "app": "Deliveroo", "time_seconds": 40, "included_in_efficiency_analysis": 1},
            {"participant_id": "U2", "task_id": "T01", "task_name": "Task 1", "app": "Deliveroo", "time_seconds": 50, "included_in_efficiency_analysis": 1},
            {"participant_id": "U1", "task_id": "T01", "task_name": "Task 1", "app": "Glovo", "time_seconds": 30, "included_in_efficiency_analysis": 1},
            {"participant_id": "U2", "task_id": "T01", "task_name": "Task 1", "app": "Glovo", "time_seconds": 35, "included_in_efficiency_analysis": 1},
        ]
    )
    thresholds = {"efficiency": {"task_oet_seconds": {"T01": 45}}}

    result = quantitative._efficiency_oet_detail(df, thresholds)

    assert set(result["app"]) == {"Deliveroo", "Glovo"}
    assert set(result["oet_seconds"]) == {45.0}
    assert result["delta_median_seconds"].notna().all()


def test_efficiency_all_user_times_wide_includes_mean_and_std() -> None:
    df = pd.DataFrame(
        [
            {"participant_id": "U1", "task_id": "T01", "app": "Deliveroo", "time_seconds": 10, "outcome_3class": "success"},
            {"participant_id": "U1", "task_id": "T02", "app": "Deliveroo", "time_seconds": 20, "outcome_3class": "success"},
            {"participant_id": "U1", "task_id": "T03", "app": "Deliveroo", "time_seconds": 30, "outcome_3class": "success"},
            {"participant_id": "U1", "task_id": "T01", "app": "Glovo", "time_seconds": 40, "outcome_3class": "success"},
            {"participant_id": "U1", "task_id": "T02", "app": "Glovo", "time_seconds": 50, "outcome_3class": "success"},
            {"participant_id": "U1", "task_id": "T03", "app": "Glovo", "time_seconds": 60, "outcome_3class": "success"},
        ]
    )

    result = quantitative._efficiency_all_user_times_wide(df)

    assert list(result.columns) == ["user_id", "D_T1", "D_T2", "D_T3", "G_T1", "G_T2", "G_T3", "Media", "Dev. standard"]
    assert result["Media"].iloc[0] == pytest.approx(35.0)
    assert result["Dev. standard"].iloc[0] == pytest.approx(pd.Series([10, 20, 30, 40, 50, 60]).std(ddof=1))


def test_selected_ueq_item_tables_require_existing_items() -> None:
    item_desc = pd.DataFrame(
        [
            {"item": "Q01", "left_anchor": "fastidioso", "right_anchor": "piacevole", "scale": "Attractiveness", "app": "Deliveroo", "n": 2, "raw_min": 2, "raw_q1": 2.5, "raw_mean": 3, "raw_median": 3, "raw_q3": 3.5, "raw_max": 4},
            {"item": "Q01", "left_anchor": "fastidioso", "right_anchor": "piacevole", "scale": "Attractiveness", "app": "Glovo", "n": 2, "raw_min": 4, "raw_q1": 4.5, "raw_mean": 5, "raw_median": 5, "raw_q3": 5.5, "raw_max": 6},
        ]
    )
    item_tests = pd.DataFrame(
        [
            {"item": "Q01", "scale": "Attractiveness", "primary_test": "Wilcoxon signed-rank", "statistic": 0.0, "p_value": 0.05, "effect_size": 0.5, "winner": "Glovo", "interpretation": "vantaggio descrittivo"},
        ]
    )

    stats, tests = quantitative._selected_ueq_item_tables(item_desc, item_tests, [{"id": "Q01", "label": "Fastidioso - Piacevole", "scale": "Attractiveness"}])

    assert len(stats) == 2
    assert len(tests) == 1
    assert stats["item_label"].iloc[0] == "Fastidioso - Piacevole"


def test_ueq_sample_style_tables_include_zones_and_distribution() -> None:
    item_desc = pd.DataFrame(
        [
            {
                "item": "Q01",
                "left_anchor": "fastidioso",
                "right_anchor": "piacevole",
                "scale": "Attractiveness",
                "app": "Deliveroo",
                "n": 3,
                "transformed_mean": 1.0,
                "transformed_std": 0.5,
            },
            {
                "item": "Q01",
                "left_anchor": "fastidioso",
                "right_anchor": "piacevole",
                "scale": "Attractiveness",
                "app": "Glovo",
                "n": 3,
                "transformed_mean": -1.0,
                "transformed_std": 0.5,
            },
        ]
    )
    scale_desc = pd.DataFrame(
        [
            {"scale": "Attractiveness", "app": "Deliveroo", "mean": 1.0, "std": 0.5, "n": 3, "ci95_low": 0.7, "ci95_high": 1.3},
            {"scale": "Attractiveness", "app": "Glovo", "mean": -1.0, "std": 0.5, "n": 3, "ci95_low": -1.3, "ci95_high": -0.7},
        ]
    )
    q_long = pd.DataFrame(
        [
            {"app": "Deliveroo", "item": "Q01", "raw_value": 5},
            {"app": "Deliveroo", "item": "Q01", "raw_value": 6},
            {"app": "Deliveroo", "item": "Q01", "raw_value": 7},
        ]
    )

    item_stats = quantitative._ueq_item_stats_by_app(item_desc)
    scale_stats = quantitative._ueq_scale_stats_by_app(scale_desc)
    distribution = quantitative._ueq_response_distribution_by_item(q_long)
    analysis = quantitative._ueq_item_analysis_table(item_stats, "Deliveroo")

    assert set(scale_stats["zone_class"]) == {"positive", "negative"}
    assert distribution["percent"].sum() == pytest.approx(1.0)
    assert list(analysis.columns) == ["Domanda", "Media", "Varianza", "Dev. standard", "N", "Valore sinistro", "Valore destro", "Sottogruppo", "Zona"]


def test_ueq_statistical_tests_by_scale_keeps_all_six_dimensions() -> None:
    scale_tests = pd.DataFrame(
        [
            {
                "scale": scale,
                "mean_deliveroo": 0.1,
                "mean_glovo": 0.7,
                "difference_glovo_minus_deliveroo": 0.6,
                "primary_test": "Wilcoxon signed-rank",
                "statistic": 1.0,
                "p_value": 0.014 if scale == "Stimulation" else 0.04,
                "interpretation": "significativa",
            }
            for scale in ["Attractiveness", "Perspicuity", "Efficiency", "Dependability", "Stimulation", "Novelty"]
        ]
    )

    out = quantitative._ueq_statistical_tests_by_scale(scale_tests)

    assert len(out) == 6
    assert "Stimulation" in set(out["scale"])
    assert list(out["scale"]) == ["Attractiveness", "Perspicuity", "Efficiency", "Dependability", "Stimulation", "Novelty"]


def test_ueq_benchmark_by_scale_app_separates_simple_zone_from_benchmark() -> None:
    scale_stats = pd.DataFrame(
        [
            {
                "app": "Deliveroo",
                "scale_name": "Attractiveness",
                "mean": 0.83,
                "std_dev": 0.5,
                "n": 24,
                "ci_low": 0.5,
                "ci_high": 1.1,
                "zone_class": "positive",
                "benchmark_category": "Below Average",
                "benchmark_threshold_source": "UEQ Handbook general benchmark",
            }
        ]
    )

    out = quantitative._ueq_benchmark_by_scale_app(scale_stats)

    assert out.loc[0, "simple_zone"] == "positive"
    assert out.loc[0, "benchmark_category"] == "Below Average"
