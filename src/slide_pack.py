from __future__ import annotations

from pathlib import Path

import pandas as pd

from .asset_manifest import build_assets_manifest
from .config import resolve_path


def _read(path: str | Path) -> str:
    target = resolve_path(path)
    return target.read_text(encoding="utf-8") if target.exists() else "Da completare manualmente: output non ancora generato."


def _asset_list(manifest: pd.DataFrame, section: str, limit: int = 12) -> list[str]:
    subset = manifest[manifest["section"] == section].head(limit) if not manifest.empty else pd.DataFrame()
    return [f"- `{row.path}` ({row.asset_type}, {row.priority})" for row in subset.itertuples()]


def build_slide_pack(config: dict) -> None:
    pack = resolve_path("outputs/slide_pack")
    pack.mkdir(parents=True, exist_ok=True)
    manifest = build_assets_manifest(pack / "assets_manifest.csv")

    sections = [
        ("00_index.md", "Indice asset slide", "general", "Usare questo file come mappa iniziale degli output generati.", ["outputs/slide_pack/assets_manifest.csv"]),
        ("01_intro.md", "Introduzione", "intro", _read("outputs/text_snippets/intro_summary.md") + "\n\n" + _read("outputs/text_snippets/sample_description.md"), []),
        ("02_heuristics.md", "Valutazione euristica", "heuristics", _read("outputs/text_snippets/heuristic_conclusions.md") + "\n\n" + _read("outputs/text_snippets/heuristics_problem_coverage.md") + "\n\n" + _read("outputs/text_snippets/dark_patterns_summary.md"), []),
        ("03_user_tests.md", "User test", "user_tests", _read("outputs/text_snippets/user_test_effectiveness_conclusions.md") + "\n\n" + _read("outputs/text_snippets/user_test_efficiency_conclusions.md"), []),
        ("04_questionnaire.md", "Questionario UEQ e NPS", "questionnaire", _read("outputs/text_snippets/questionnaire_conclusions.md") + "\n\n" + _read("outputs/text_snippets/nps_conclusions.md") + "\n\n" + _read("outputs/text_snippets/questionnaire_selected_items.md"), []),
        ("05_conclusions.md", "Conclusioni", "conclusions", _read("outputs/text_snippets/final_comparative_conclusions.md") + "\n\n" + _read("outputs/text_snippets/redesign_recommendations.md") + "\n\n" + _read("outputs/text_snippets/limitations.md"), []),
    ]
    for filename, title, section, text, extra_assets in sections:
        lines = [f"# {title}", "", "## Asset consigliati", ""]
        assets = [f"- `{asset}`" for asset in extra_assets] if extra_assets else _asset_list(manifest, section)
        lines.extend(assets if assets else ["- Da generare con `python -m src.cli all --plot-style both`."])
        lines.extend(["", "## Testo suggerito", "", text, "", "## Note da completare manualmente", "", "- Inserire screenshot dei flussi Deliveroo/Glovo dove rilevanti.", "- Verificare che le conclusioni siano coerenti con la discussione del gruppo.", ""])
        (pack / filename).write_text("\n".join(lines), encoding="utf-8")
    build_executive_summary(config)


def build_executive_summary(config: dict) -> None:
    scores_path = resolve_path("outputs/tables/final_comparison.csv")
    scores = pd.read_csv(scores_path) if scores_path.exists() else pd.DataFrame()
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    if not scores.empty and "final_score" in scores:
        best = scores.sort_values("final_score", ascending=False).iloc[0]["system"]
        result = f"La sintesi quantitativa interna favorisce {best}, da leggere come supporto alla discussione e non come verdetto automatico."
    else:
        result = "La sintesi finale richiede la lettura combinata di user test, euristiche, UEQ e NPS."
    lines = [
        "# Executive Summary",
        "",
        "## Risultato principale",
        result,
        "",
        f"## {systems[0]}",
        "Punti di forza:",
        "- Da completare sulla base degli asset generati.",
        "",
        "Criticita:",
        "- Da completare sulla base di euristiche, task critici e UEQ.",
        "",
        f"## {systems[1]}",
        "Punti di forza:",
        "- Da completare sulla base degli asset generati.",
        "",
        "Criticita:",
        "- Da completare sulla base di euristiche, task critici e UEQ.",
        "",
        "## Evidenze statistiche principali",
        f"- User test: {_read('outputs/text_snippets/user_test_effectiveness_conclusions.md').splitlines()[-1] if resolve_path('outputs/text_snippets/user_test_effectiveness_conclusions.md').exists() else 'consultare gli asset task-by-task.'}",
        f"- UEQ: {_read('outputs/text_snippets/questionnaire_conclusions.md').splitlines()[-1] if resolve_path('outputs/text_snippets/questionnaire_conclusions.md').exists() else 'consultare ueq_summary.csv.'}",
        f"- NPS: {_read('outputs/text_snippets/nps_conclusions.md').splitlines()[-1] if resolve_path('outputs/text_snippets/nps_conclusions.md').exists() else 'consultare nps_breakdown.csv.'}",
        f"- Euristiche: {_read('outputs/text_snippets/heuristic_conclusions.md').splitlines()[-1] if resolve_path('outputs/text_snippets/heuristic_conclusions.md').exists() else 'consultare heuristics_summary.csv.'}",
        "",
        "## Raccomandazioni",
        "1. Correggere prima i problemi ad alta severita e alta ricorrenza.",
        "2. Ridurre errori e richieste di aiuto nei task con successo piu basso.",
        "3. Intervenire sugli item UEQ con differenze maggiori tra le app.",
        "",
    ]
    resolve_path("outputs/slide_pack/executive_summary.md").write_text("\n".join(lines), encoding="utf-8")
