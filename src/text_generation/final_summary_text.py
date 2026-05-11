from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..config import resolve_path
from .display_labels import prepare_display_table
from .italian import italian_display_text
from .templates import INTRO_TEMPLATE, METHODS_TEMPLATE


def _read_csv(path: str | Path) -> pd.DataFrame:
    target = resolve_path(path)
    return pd.read_csv(target, encoding="utf-8-sig") if target.exists() else pd.DataFrame()


def _safe_mean(df: pd.DataFrame, column: str) -> float | None:
    return float(df[column].mean()) if not df.empty and column in df else None


def _where_system(df: pd.DataFrame, system: str) -> pd.DataFrame:
    if df.empty or "system" not in df:
        return pd.DataFrame()
    return df[df["system"] == system]


def compute_final_comparison_score(config: dict) -> pd.DataFrame:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    weights = config.get("final_score", {}).get("weights", {})
    effectiveness = _read_csv("outputs/tables/user_test_effectiveness.csv")
    efficiency = _read_csv("outputs/tables/user_test_efficiency.csv")
    ueq = _read_csv("outputs/tables/ueq_summary.csv")
    nps = _read_csv("outputs/tables/nps_summary.csv")
    heuristics = _read_csv("outputs/tables/heuristics_summary.csv")
    rows = []
    for system in systems:
        eff_score = _safe_mean(_where_system(effectiveness, system), "completion_rate")
        time_mean = _safe_mean(_where_system(efficiency, system), "mean_seconds")
        ueq_score = _safe_mean(_where_system(ueq, system), "mean")
        nps_score = _safe_mean(_where_system(nps, system), "nps")
        heuristic_penalty = _safe_mean(_where_system(heuristics, system), "severity_mean")
        rows.append(
            {
                "system": system,
                "effectiveness": eff_score,
                "efficiency_seconds": time_mean,
                "ueq": ueq_score,
                "nps": nps_score,
                "heuristic_penalty": heuristic_penalty,
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["effectiveness_norm"] = result["effectiveness"].fillna(0)
    result["efficiency_norm"] = 1 - (result["efficiency_seconds"] / result["efficiency_seconds"].max()).fillna(0)
    result["ueq_norm"] = ((result["ueq"] - 1) / 6).fillna(0)
    result["nps_norm"] = ((result["nps"] + 100) / 200).fillna(0)
    result["heuristic_norm"] = 1 - (result["heuristic_penalty"] / 4).fillna(0)
    result["final_score"] = (
        result["effectiveness_norm"] * weights.get("effectiveness", 0.25)
        + result["efficiency_norm"] * weights.get("efficiency", 0.20)
        + result["ueq_norm"] * weights.get("ueq", 0.30)
        + result["nps_norm"] * weights.get("nps", 0.15)
        + result["heuristic_norm"] * weights.get("heuristic_penalty", 0.10)
    )
    return result


def generate_text_outputs(config: dict) -> None:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    snippets_dir = resolve_path("outputs/text_snippets")
    sections_dir = resolve_path("outputs/generated_report_sections")
    snippets_dir.mkdir(parents=True, exist_ok=True)
    sections_dir.mkdir(parents=True, exist_ok=True)

    intro = INTRO_TEMPLATE.format(system_1=systems[0], system_2=systems[1])
    methods = METHODS_TEMPLATE
    heuristics = _heuristics_text(systems)
    user_tests = _user_tests_text(systems)
    questionnaire = _questionnaire_text(systems)
    nps = _nps_text(systems)
    final = _final_text(config)

    outputs = {
        "intro.md": intro,
        "intro_summary.md": intro,
        "sample_summary.md": _sample_text(systems),
        "methods.md": methods,
        "heuristics.md": heuristics,
        "heuristic_conclusions.md": heuristics,
        "user_tests.md": user_tests,
        "user_test_effectiveness_conclusions.md": _user_test_effectiveness_text(systems),
        "user_test_efficiency_conclusions.md": _user_test_efficiency_text(systems),
        "questionnaire.md": questionnaire,
        "questionnaire_conclusions.md": questionnaire,
        "nps.md": nps,
        "nps_conclusions.md": nps,
        "conclusions.md": final,
        "final_comparative_conclusions.md": final,
        "redesign_recommendations.md": _redesign_text(),
        "limitations.md": _limitations_text(),
    }
    for name, text in outputs.items():
        (snippets_dir / name).write_text(italian_display_text(text), encoding="utf-8")

    sections = {
        "01_introduzione.md": intro,
        "02_valutazione_euristica.md": methods + "\n\n" + heuristics,
        "03_user_test.md": user_tests,
        "04_questionario.md": questionnaire + "\n\n" + nps,
        "05_conclusioni.md": final,
    }
    for name, text in sections.items():
        (sections_dir / name).write_text(italian_display_text(text), encoding="utf-8")

    final_scores = compute_final_comparison_score(config)
    if not final_scores.empty:
        table_path = resolve_path("outputs/tables/final_comparison.csv")
        md_path = resolve_path("outputs/tables_md/final_comparison.md")
        table_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        final_scores.round(config["analysis"].get("round_decimals", 2)).to_csv(table_path, index=False, encoding="utf-8-sig")
        md_path.write_text(prepare_display_table(final_scores.round(2)).to_markdown(index=False), encoding="utf-8")


def _heuristics_text(systems: list[str]) -> str:
    df = _read_csv("outputs/tables/heuristics_summary.csv")
    if df.empty:
        return "# Risultati valutazione euristica\n\nI dati euristici non sono disponibili o devono ancora essere consolidati."
    counts = {row["system"]: int(row["problems"]) for _, row in df.iterrows()}
    return (
        "# Risultati valutazione euristica\n\n"
        f"Dalla valutazione euristica sono emersi {counts.get(systems[0], 0)} problemi per {systems[0]} "
        f"e {counts.get(systems[1], 0)} problemi per {systems[1]}. Le tabelle esportate riportano severità media, "
        "mediana e priorità dei problemi."
    )


def _sample_text(systems: list[str]) -> str:
    nps = _read_csv("outputs/tables/nps_summary.csv")
    if nps.empty:
        return "# Campione\n\nLa descrizione del campione sara completata dopo l'import dei questionari."
    parts = [f"{row.system}: {int(row.total)} rispondenti questionario" for row in nps.itertuples() if pd.notna(row.total)]
    return "# Campione\n\n" + ("; ".join(parts) if parts else "Numerosita campione non disponibile.") + "."


def _user_tests_text(systems: list[str]) -> str:
    eff = _read_csv("outputs/tables/user_test_effectiveness.csv")
    speed = _read_csv("outputs/tables/user_test_efficiency.csv")
    if eff.empty or speed.empty:
        return "# Risultati user test\n\nI dati di user test non sono disponibili."
    completion = eff.groupby("system")["completion_rate"].mean()
    best = completion.idxmax()
    mean_time = speed.groupby("system")["mean_seconds"].mean()
    fastest = mean_time.idxmin()
    return (
        "# Risultati user test\n\n"
        f"Per quanto riguarda l'efficacia, {best} ottiene il tasso medio di completamento più alto. "
        f"L'analisi dei tempi mostra invece che {fastest} risulta mediamente più rapido nel completamento dei task."
    )


def _user_test_effectiveness_text(systems: list[str]) -> str:
    eff = _read_csv("outputs/tables/user_test_effectiveness.csv")
    if eff.empty:
        return "# Efficacia user test\n\nDati non disponibili."
    completion = eff.groupby("system")["completion_rate"].mean().sort_values(ascending=False)
    best = completion.index[0]
    gap = completion.iloc[0] - completion.iloc[-1] if len(completion) > 1 else 0
    return f"# Efficacia user test\n\n{best} mostra il tasso medio di completamento più alto. Il divario medio osservato e pari a {gap:.2%}."


def _user_test_efficiency_text(systems: list[str]) -> str:
    speed = _read_csv("outputs/tables/user_test_efficiency.csv")
    if speed.empty:
        return "# Efficienza user test\n\nDati non disponibili."
    means = speed.groupby("system")["mean_seconds"].mean().sort_values()
    fastest = means.index[0]
    return f"# Efficienza user test\n\n{fastest} risulta mediamente più rapido sui task osservati. Consultare gli asset task-by-task per verificare dove la differenza e più marcata."


def _questionnaire_text(systems: list[str]) -> str:
    ueq = _read_csv("outputs/tables/ueq_summary.csv")
    if ueq.empty:
        return "# Risultati UEQ\n\nI dati UEQ non sono disponibili."
    pivot = ueq.pivot(index="scale", columns="system", values="mean")
    winners = []
    for scale, row in pivot.iterrows():
        winners.append(f"{scale}: {row.idxmax()}")
    return "# Risultati UEQ\n\nDall'analisi UEQ emergono differenze tra le scale considerate. Migliori per scala: " + "; ".join(winners) + "."


def _nps_text(systems: list[str]) -> str:
    nps = _read_csv("outputs/tables/nps_summary.csv")
    if nps.empty or nps.get("total", pd.Series(dtype=float)).fillna(0).sum() == 0:
        return "# Risultati NPS\n\nIl Net Promoter Score non e stato calcolato perché il questionario non contiene una domanda NPS valida."
    best = nps.sort_values("nps", ascending=False).iloc[0]
    return f"# Risultati NPS\n\nIl Net Promoter Score evidenzia una maggiore propensione a consigliare {best['system']}, con valore pari a {best['nps']:.2f}."


def _final_text(config: dict) -> str:
    scores = compute_final_comparison_score(config)
    if scores.empty:
        return "# Conclusioni\n\nLa sintesi complessiva non e disponibile per dati insufficienti."
    best = scores.sort_values("final_score", ascending=False).iloc[0]
    other = scores.sort_values("final_score", ascending=False).iloc[-1]
    return (
        "# Conclusioni\n\n"
        f"Nel complesso, la sintesi interna dei risultati assegna a {best['system']} un punteggio complessivo superiore "
        f"rispetto a {other['system']}. Questo punteggio va interpretato come supporto alla lettura dei risultati, non come verita assoluta."
    )


def _redesign_text() -> str:
    return (
        "# Raccomandazioni di redesign\n\n"
        "1. Prioritizzare i problemi euristici con severità alta e alta ricorrenza tra valutatori.\n"
        "2. Ridurre passaggi, ambiguità e richieste di aiuto nei task con successo più basso.\n"
        "3. Migliorare gli item UEQ con differenza maggiore tra i due sistemi, verificando con screenshot e osservazioni qualitative."
    )


def _limitations_text() -> str:
    return (
        "# Limiti dello studio\n\n"
        "I risultati dipendono da numerosita campionaria, profilo dei partecipanti, task scelti e consolidamento manuale dei problemi. "
        "Le stime statistiche e di copertura vanno lette come supporto alla discussione critica, non come conclusioni automatiche."
    )
