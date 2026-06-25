from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_config_slide_manifest_has_unique_ids_and_known_generators() -> None:
    manifest = _load_yaml("config/slides.yaml")
    slides = manifest["slides"]
    ids = [slide["id"] for slide in slides]
    allowed = {"static", "static_text", "table", "chart", "chart_table", "appendix"}

    assert len(ids) == len(set(ids))
    assert all(slide.get("enabled") in {True, False} for slide in slides)
    assert {slide["generator"] for slide in slides}.issubset(allowed)
    assert all(slide.get("section") for slide in slides)


def test_modular_config_files_are_present() -> None:
    for path in [
        "config/project.yaml",
        "config/apps.yaml",
        "config/theme.yaml",
        "config/presentation.yaml",
        "config/analysis.yaml",
        "config/slides.yaml",
        "config/appendices.yaml",
        "config/texts/it.yaml",
        "config/ueq.yaml",
    ]:
        assert (ROOT / path).exists()


def test_data_templates_and_schemas_are_present() -> None:
    for path in [
        "templates/data/evaluators_template.csv",
        "templates/data/heuristic_findings_template.csv",
        "templates/data/user_tests_template.csv",
        "templates/data/ueq_survey_template.csv",
        "templates/data/tasks_template.csv",
        "schemas/evaluators.schema.json",
        "schemas/heuristic_findings.schema.json",
        "schemas/user_tests.schema.json",
        "schemas/ueq_survey.schema.json",
        "schemas/tasks.schema.json",
    ]:
        assert (ROOT / path).exists()


def test_future_student_documentation_entrypoints_are_present() -> None:
    for path in [
        "docs/getting-started.md",
        "docs/data-requirements.md",
        "docs/presentation-guide.md",
        "docs/configuration.md",
        "docs/ueq-methodology.md",
        "docs/heuristic-evaluation.md",
        "docs/user-testing.md",
        "docs/pipeline.md",
        "docs/project-adaptation-guide.md",
        "docs/template-guide.md",
        "docs/template-cleanup-report.md",
    ]:
        assert (ROOT / path).exists()


def test_template_audit_tool_is_present() -> None:
    assert (ROOT / "tools/audit_pptx_template.py").exists()
