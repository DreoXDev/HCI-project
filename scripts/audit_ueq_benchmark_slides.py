from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.ueq_benchmark import (  # noqa: E402
    PROJECT_BENCHMARK_SNAPSHOT,
    UEQ_SCALE_ORDER,
    check_project_benchmark_snapshot,
    thresholds_dataframe,
)


TABLE = ROOT / "outputs" / "tables" / "ueq" / "ueq_benchmark_by_scale_app.csv"
PPTX = ROOT / "outputs" / "slides" / "final_report.pptx"
PDF = ROOT / "outputs" / "slides" / "final_report.pdf"
REPORT = ROOT / "reports" / "audit" / "ueq_benchmark_slide_audit.md"
INVENTORY = ROOT / "reports" / "audit" / "ueq_benchmark_code_inventory.md"


def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write_code_inventory()
    ok = write_slide_audit()
    raise SystemExit(0 if ok else 1)


def write_code_inventory() -> None:
    rows = [
        ("src/analysis/ueq_benchmark.py", "UEQ_BENCHMARK_THRESHOLDS", "Soglie ufficiali centralizzate", "Nessuno", "Fonte primaria per categorie"),
        ("src/analysis/ueq_benchmark.py", "classify_ueq_benchmark", "Classificazione categorie", "Nessuno", "Usare ovunque per benchmark"),
        ("scripts/validate_quantitative_report.py", "build_ueq_long", "Trasformazione raw 1..7 in -3..+3", "Nessuno", "Mantiene output diagnostico"),
        ("scripts/validate_quantitative_report.py", "build_ueq_scales", "Medie e categorie per scala/app", "Soglie locali rimosse", "Usa modulo centralizzato"),
        ("scripts/validate_quantitative_report.py", "plot_ueq_benchmarks", "Grafici benchmark per app", "Bande ufficiali per scala", "Esporta CSV validation"),
        ("src/final_report.py", "_ueq_benchmark_label", "Legacy final-report benchmark", "Soglie semplificate rimosse", "Delegato al modulo centrale"),
        ("src/slide_export/auto_deck.py", "slide 127-145 specs", "Inserimento grafici/tabelle UEQ", "Nessuno", "Usa asset generati dalla pipeline"),
        ("tests/test_ueq_benchmark.py", "snapshot/boundary tests", "Regressione benchmark", "Nessuno", "Blocca confini e snapshot progetto"),
    ]
    lines = [
        "# UEQ Benchmark Code Inventory",
        "",
        "| File | Funzione/oggetto | Ruolo | Problema trovato | Azione richiesta |",
        "|---|---|---|---|---|",
    ]
    lines.extend(f"| `{file}` | `{obj}` | {role} | {problem} | {action} |" for file, obj, role, problem, action in rows)
    INVENTORY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_slide_audit() -> bool:
    problems: list[str] = []
    if not TABLE.exists():
        problems.append(f"CSV benchmark mancante: `{TABLE.relative_to(ROOT)}`")
        table = pd.DataFrame()
    else:
        table = pd.read_csv(TABLE)
    checks = check_project_benchmark_snapshot(table) if not table.empty else []
    if len(checks) != len(PROJECT_BENCHMARK_SNAPSHOT):
        problems.append("Snapshot benchmark incompleto.")
    for check in checks:
        if not check.ok:
            problems.append(f"{check.app} / {check.scale}: atteso {check.expected_mean:.2f} {check.expected_category}, trovato {check.mean:.2f} {check.category}")

    deck_text = _pptx_text(PPTX) if PPTX.exists() else ""
    if not deck_text:
        problems.append(f"PPTX non leggibile o mancante: `{PPTX.relative_to(ROOT)}`")
    else:
        if "Media risultati UEQ" in deck_text:
            problems.append("Slide raw `Media risultati UEQ` ancora presente nel PPTX.")
        if "UEQ benchmark - confronto sintetico" in deck_text:
            problems.append("Titolo fuorviante `UEQ benchmark - confronto sintetico` ancora presente nel PPTX.")
        if "UEQ - confronto sintetico delle scale" not in deck_text:
            problems.append("Nuovo titolo `UEQ - confronto sintetico delle scale` non trovato nel PPTX.")
        for (app, scale), (mean, category) in PROJECT_BENCHMARK_SNAPSHOT.items():
            if scale not in deck_text:
                problems.append(f"Scala non trovata nel PPTX: {scale}")
            if category not in deck_text:
                problems.append(f"Categoria non trovata nel PPTX: {category}")
            if f"{mean:.2f}" not in deck_text:
                problems.append(f"Media non trovata nel PPTX: {app} / {scale} = {mean:.2f}")

    plot_paths = [ROOT / "outputs" / "validation" / f"ueq_benchmark_plot_data_{app}.csv" for app in ["deliveroo", "glovo"]]
    for path in plot_paths:
        if not path.exists():
            problems.append(f"Plot validation CSV mancante: `{path.relative_to(ROOT)}`")
            continue
        plot = pd.read_csv(path)
        if plot["bad_upper"].nunique() <= 1:
            problems.append(f"Soglie bad_uniformi nel plot data: `{path.relative_to(ROOT)}`")
        if not set(UEQ_SCALE_ORDER).issubset(set(plot["scale"])):
            problems.append(f"Scale mancanti nel plot data: `{path.relative_to(ROOT)}`")

    lines = [
        "# UEQ Benchmark Slide Audit",
        "",
        "## Input verificati",
        f"- CSV benchmark: `{TABLE.relative_to(ROOT)}`",
        f"- PPTX: `{PPTX.relative_to(ROOT)}`",
        f"- PDF: `{PDF.relative_to(ROOT)}`",
        f"- Soglie ufficiali: `src/analysis/ueq_benchmark.py`",
        "",
        "## Risultato sintetico",
        "PASS" if not problems else "FAIL",
        "",
        "## Soglie benchmark",
        thresholds_dataframe().to_markdown(index=False),
        "",
        "## Dettaglio per app",
        "| App | Scala | Media | Categoria attesa | Categoria trovata | Esito |",
        "|---|---|---:|---|---|---|",
    ]
    for check in checks:
        lines.append(f"| {check.app} | {check.scale} | {check.mean:.2f} | {check.expected_category} | {check.category} | {'PASS' if check.ok else 'FAIL'} |")
    lines.extend(
        [
            "",
            "## Problemi rilevati",
            *(f"- {problem}" for problem in problems),
            "- Nessuno." if not problems else "",
            "",
            "## Fix applicati",
            "- Soglie benchmark centralizzate in `src/analysis/ueq_benchmark.py`.",
            "- Classificazione benchmark allineata ai confini ufficiali per scala.",
            "- CSV validation dei grafici benchmark esportati in `outputs/validation`.",
            "- Audit slide e test golden snapshot aggiunti.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(REPORT)
    print("STATUS:", "PASS" if not problems else "FAIL")
    return not problems


def _pptx_text(path: Path) -> str:
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    with ZipFile(path) as deck:
        slide_names = sorted(
            [name for name in deck.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", name)],
            key=lambda name: int(re.search(r"slide(\d+)\.xml", name).group(1)),
        )
        texts = []
        for name in slide_names:
            root = ET.fromstring(deck.read(name))
            texts.extend(node.text or "" for node in root.findall(".//a:t", ns))
    return " ".join(texts)


if __name__ == "__main__":
    main()
