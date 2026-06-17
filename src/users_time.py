from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats
import shutil

from .adapters.formbricks.normalization import comparable
from .config import resolve_path
from .plots import apply_project_theme, save_figure
from .visualization.theme import get_brand_palette


REQUIRED_COLUMNS = [
    "user_id",
    "app",
    "task_id",
    "task_name",
    "completion_time_sec",
    "success",
    "errors_count",
    "help_requests",
]

OPTIONAL_COLUMNS = [
    "notes",
    "start_time",
    "end_time",
    "device",
    "observer",
    "observer_id",
    "original_user_id",
    "completion_time_raw",
    "order",
]
TEMPLATE_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
TRUE_VALUES = {"true", "1", "yes", "si", "sì"}
FALSE_VALUES = {"false", "0", "no"}
LEGACY_SUCCESS_VALUES = {"c", "a"}
LEGACY_FAILURE_VALUES = {"f"}


@dataclass
class UsersTimeValidationResult:
    is_valid: bool
    messages: list[str]
    normalized: pd.DataFrame


def load_users_time_long(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(resolve_path(path), sep=None, engine="python", encoding="utf-8-sig")


def users_time_file(config: dict) -> Path:
    configured = config.get("users_time", {}).get("input_path")
    return resolve_path(configured or "data/raw/users_time.csv")


def users_time_enabled(config: dict) -> bool:
    return bool(config.get("users_time", {}).get("enabled", True))


def normalize_boolean(value: Any) -> bool | None:
    if pd.isna(value):
        return None
    normalized = comparable(value)
    if normalized in {comparable(item) for item in TRUE_VALUES} or normalized in LEGACY_SUCCESS_VALUES:
        return True
    if normalized in {comparable(item) for item in FALSE_VALUES} or normalized in LEGACY_FAILURE_VALUES:
        return False
    return None


def _normalize_task_id(value: Any) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    if not text:
        return ""
    if text.upper().startswith("T"):
        digits = "".join(ch for ch in text if ch.isdigit())
        return f"T{int(digits):02d}" if digits else text.upper()
    if text.replace(".", "", 1).isdigit():
        return f"T{int(float(text)):02d}"
    return text


def _task_name_map(tasks: list[dict[str, Any]] | None) -> dict[str, str]:
    return {_normalize_task_id(task.get("id")): str(task.get("name", "")) for task in tasks or []}


def validate_users_time_long(
    df: pd.DataFrame,
    required_columns: list[str] | None = None,
    *,
    expected_users: int = 24,
    tasks: list[dict[str, Any]] | None = None,
) -> UsersTimeValidationResult:
    required = required_columns or REQUIRED_COLUMNS
    messages: list[str] = []
    normalized = df.dropna(how="all").copy()
    empty_rows = len(df) - len(normalized)
    if empty_rows:
        messages.append(f"WARNING: {empty_rows} righe completamente vuote ignorate")

    if "task_id" in normalized.columns:
        normalized["task_id"] = normalized["task_id"].map(_normalize_task_id)
    if "task_name" not in normalized.columns and "task_label" in normalized.columns:
        normalized["task_name"] = normalized["task_label"]
    if "task_name" not in normalized.columns and "task_id" in normalized.columns:
        names = _task_name_map(tasks)
        normalized["task_name"] = normalized["task_id"].map(names).fillna(normalized["task_id"])

    missing = [column for column in required if column not in normalized.columns]
    if missing:
        messages.append(f"ERROR: colonne obbligatorie mancanti: {', '.join(missing)}")
        return UsersTimeValidationResult(False, messages, normalized)

    for column in ["user_id", "app", "task_id"]:
        empty = normalized[column].isna() | (normalized[column].astype(str).str.strip() == "")
        if empty.any():
            messages.append(f"ERROR: {int(empty.sum())} righe con `{column}` vuoto")

    normalized["completion_time_sec"] = pd.to_numeric(normalized["completion_time_sec"], errors="coerce")
    invalid_time = normalized["completion_time_sec"].isna() | (normalized["completion_time_sec"] < 0)
    if invalid_time.any():
        messages.append("ERROR: `completion_time_sec` deve essere numerico e >= 0")

    for column in ["errors_count", "help_requests"]:
        values = pd.to_numeric(normalized[column], errors="coerce").fillna(0)
        invalid = values.isna() | (values < 0) | (values % 1 != 0)
        if invalid.any():
            messages.append(f"ERROR: `{column}` deve essere un intero >= 0")
        normalized[column] = values.astype("Int64")

    success = normalized["success"].apply(normalize_boolean)
    if success.isna().any():
        messages.append("ERROR: `success` deve essere convertibile a booleano")
    normalized["success"] = success

    observed_users = normalized["user_id"].dropna().astype(str).str.strip().nunique()
    if observed_users and observed_users < expected_users:
        messages.append(f"WARNING: dataset parziale users_time: {observed_users}/{expected_users} utenti presenti")
    elif observed_users >= expected_users:
        messages.append(f"OK: dataset users_time finale: {observed_users}/{expected_users} utenti presenti")

    is_valid = not any(message.startswith("ERROR") for message in messages)
    if is_valid and not messages:
        messages.append("OK: users_time.csv valido")
    elif is_valid:
        messages.append("OK: users_time.csv valido con warning")
    return UsersTimeValidationResult(is_valid, messages, normalized)


def validate_users_time_file(
    path: str | Path,
    report_path: str | Path = "outputs/reports/users_time_validation_report.md",
    required_columns: list[str] | None = None,
    *,
    expected_users: int = 24,
    tasks: list[dict[str, Any]] | None = None,
) -> UsersTimeValidationResult:
    target = resolve_path(path)
    if not target.exists():
        result = UsersTimeValidationResult(False, [f"WARNING: file non trovato: {target}"], pd.DataFrame())
        write_validation_report(result, report_path, target)
        return result
    result = validate_users_time_long(load_users_time_long(target), required_columns, expected_users=expected_users, tasks=tasks)
    write_validation_report(result, report_path, target)
    return result


def write_validation_report(result: UsersTimeValidationResult, report_path: str | Path, source_path: str | Path) -> None:
    lines = [
        "# Users Time Validation Report",
        "",
        f"- File: `{source_path}`",
        f"- Esito: {'OK' if result.is_valid else 'ATTENZIONE'}",
        f"- Righe valide/importate: {len(result.normalized)}",
        "",
        "## Messaggi",
        "",
        *[f"- {message}" for message in result.messages],
        "",
    ]
    target = resolve_path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")


def summarize_users_time(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["app", "task_id", "task_name"], sort=True)
        .agg(
            n_users=("user_id", "nunique"),
            mean_time_sec=("completion_time_sec", "mean"),
            median_time_sec=("completion_time_sec", "median"),
            sd_time_sec=("completion_time_sec", "std"),
            q1_time_sec=("completion_time_sec", lambda s: s.quantile(0.25)),
            q3_time_sec=("completion_time_sec", lambda s: s.quantile(0.75)),
            success_rate=("success", "mean"),
            mean_errors=("errors_count", "mean"),
            mean_help_requests=("help_requests", "mean"),
        )
        .reset_index()
    )
    summary["iqr_time_sec"] = summary["q3_time_sec"] - summary["q1_time_sec"]
    summary = summary.drop(columns=["q1_time_sec", "q3_time_sec"])
    numeric = [
        "mean_time_sec",
        "median_time_sec",
        "sd_time_sec",
        "iqr_time_sec",
        "success_rate",
        "mean_errors",
        "mean_help_requests",
    ]
    summary[numeric] = summary[numeric].round(2)
    return summary[
        [
            "app",
            "task_id",
            "task_name",
            "n_users",
            "mean_time_sec",
            "median_time_sec",
            "sd_time_sec",
            "iqr_time_sec",
            "success_rate",
            "mean_errors",
            "mean_help_requests",
        ]
    ]


def users_time_stat_tests(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    rows = []
    for (task_id, task_name), group in df.groupby(["task_id", "task_name"], sort=True):
        app_values = {app: group[group["app"].map(comparable) == comparable(app)] for app in systems}
        if any(values.empty for values in app_values.values()):
            continue
        left = app_values[systems[0]][["user_id", "completion_time_sec"]]
        right = app_values[systems[1]][["user_id", "completion_time_sec"]]
        paired = left.merge(right, on="user_id", suffixes=("_left", "_right"))
        if len(paired) >= 2:
            result = stats.wilcoxon(paired["completion_time_sec_left"], paired["completion_time_sec_right"])
            test_name = "Wilcoxon signed-rank"
            p_value = result.pvalue
        else:
            result = stats.mannwhitneyu(left["completion_time_sec"], right["completion_time_sec"], alternative="two-sided")
            test_name = "Mann-Whitney U"
            p_value = result.pvalue
        rows.append(
            {
                "task_id": task_id,
                "task_name": task_name,
                "metric": "completion_time_sec",
                "test": test_name,
                "p_value": round(float(p_value), 4),
                "interpretation": "Differenza significativa" if p_value < 0.05 else "Differenza non significativa",
            }
        )
    return pd.DataFrame(rows, columns=["task_id", "task_name", "metric", "test", "p_value", "interpretation"])


def analyze_users_time(
    config: dict,
    input_path: str | Path | None = None,
    output_tables_dir: str | Path = "outputs/tables",
    output_figures_dir: str | Path = "outputs/figures",
    output_text_dir: str | Path = "outputs/texts/analysis",
    report_path: str | Path = "outputs/reports/users_time_validation_report.md",
) -> dict[str, pd.DataFrame]:
    path = resolve_path(input_path) if input_path else users_time_file(config)
    validation = validate_users_time_file(
        path,
        report_path,
        config.get("users_time", {}).get("required_columns"),
        tasks=config.get("users_time", {}).get("tasks", []),
    )
    if not validation.is_valid:
        if not path.exists():
            return {"summary": pd.DataFrame(), "stat_tests": pd.DataFrame()}
        raise ValueError("; ".join(validation.messages))
    df = validation.normalized
    summary = summarize_users_time(df)
    stat_tests = users_time_stat_tests(df, config)

    tables_dir = resolve_path(output_tables_dir)
    markdown_dir = tables_dir / "markdown"
    tables_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(tables_dir / "users_time_clean.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(tables_dir / "users_time_summary.csv", index=False)
    summary.to_markdown(markdown_dir / "users_time_summary.md", index=False)
    summary.to_csv(tables_dir / "users_time_summary_by_app_task.csv", index=False, encoding="utf-8-sig")
    summary.to_markdown(markdown_dir / "users_time_summary_by_app_task.md", index=False)
    by_app = summarize_users_time_by_app(df)
    by_app.to_csv(tables_dir / "users_time_summary_by_app.csv", index=False, encoding="utf-8-sig")
    stat_tests.to_csv(tables_dir / "users_time_stat_tests.csv", index=False)

    _plot_users_time(df, summary, config, output_figures_dir)
    write_users_time_interpretation(summary, output_text_dir, config)
    write_user_testing_summary(summary, by_app, output_text_dir)
    export_user_testing_plot_aliases(output_figures_dir)
    return {"summary": summary, "stat_tests": stat_tests}


def summarize_users_time_by_app(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("app", sort=True)
        .agg(
            n_task_runs=("user_id", "size"),
            n_users=("user_id", "nunique"),
            mean_time_sec=("completion_time_sec", "mean"),
            median_time_sec=("completion_time_sec", "median"),
            success_rate=("success", "mean"),
            mean_errors=("errors_count", "mean"),
            mean_help_requests=("help_requests", "mean"),
        )
        .reset_index()
    )
    numeric = ["mean_time_sec", "median_time_sec", "success_rate", "mean_errors", "mean_help_requests"]
    summary[numeric] = summary[numeric].round(2)
    return summary


def _plot_users_time(df: pd.DataFrame, summary: pd.DataFrame, config: dict, output_figures_dir: str | Path) -> None:
    out = resolve_path(output_figures_dir)
    apply_project_theme(config)
    palette = get_brand_palette(config)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=summary, x="task_id", y="mean_time_sec", hue="app", palette=palette, ax=ax)
    ax.set_title("Tempo medio per task")
    ax.set_xlabel("Task")
    ax.set_ylabel("Secondi")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, out / "users_time_mean_by_task.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=summary, x="task_id", y="median_time_sec", hue="app", palette=palette, ax=ax)
    ax.set_title("Tempo mediano per task")
    ax.set_xlabel("Task")
    ax.set_ylabel("Secondi")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, out / "users_time_median_by_task.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df, x="task_id", y="completion_time_sec", hue="app", palette=palette, ax=ax)
    ax.set_title("Distribuzione tempi per task")
    ax.set_xlabel("Task")
    ax.set_ylabel("Secondi")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, out / "users_time_boxplot_by_task.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=summary, x="task_id", y="success_rate", hue="app", palette=palette, ax=ax)
    ax.set_ylim(0, 1)
    ax.set_title("Success rate per task")
    ax.set_xlabel("Task")
    ax.set_ylabel("Success rate")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, out / "users_time_success_rate.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=summary, x="task_id", y="mean_errors", hue="app", palette=palette, ax=ax)
    ax.set_title("Errori medi per task")
    ax.set_xlabel("Task")
    ax.set_ylabel("Errori medi")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, out / "users_time_errors_by_task.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df, x="app", y="completion_time_sec", hue="app", palette=palette, legend=False, ax=ax)
    ax.set_title("Distribuzione tempi per app")
    ax.set_xlabel("")
    ax.set_ylabel("Secondi")
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, out / "users_time_distribution_by_app.png")


def write_users_time_interpretation(summary: pd.DataFrame, output_text_dir: str | Path, config: dict) -> None:
    systems = [config["project"]["system_1"], config["project"]["system_2"]]
    lines = ["# Users Time Interpretation", ""]
    if summary.empty:
        lines.append("Dataset users-time non disponibile.")
    else:
        pivot = summary.pivot_table(index=["task_id", "task_name"], columns="app", values="mean_time_sec")
        wins = {system: 0 for system in systems}
        differences = []
        for (task_id, task_name), row in pivot.iterrows():
            available = [system for system in systems if system in row and pd.notna(row[system])]
            if len(available) < 2:
                continue
            faster = min(available, key=lambda system: row[system])
            wins[faster] += 1
            differences.append((abs(row[systems[0]] - row[systems[1]]), task_id, task_name, faster))
        lines.append(
            f"Sui tempi medi, {systems[0]} risulta più rapido in {wins.get(systems[0], 0)} task, "
            f"mentre {systems[1]} risulta più rapido in {wins.get(systems[1], 0)} task."
        )
        if differences:
            diff, task_id, task_name, faster = max(differences, key=lambda item: item[0])
            lines.append(f"La differenza maggiore e sulla task {task_id} ({task_name}), dove {faster} e più rapido di {diff:.2f} secondi.")
        low_success = summary[summary["success_rate"] < 0.8]
        if not low_success.empty:
            items = ", ".join(f"{row.app} {row.task_id}" for row in low_success.itertuples())
            lines.append(f"Success rate sotto 0.80 rilevato per: {items}.")
        high_errors = summary[summary["mean_errors"] > 1]
        if not high_errors.empty:
            items = ", ".join(f"{row.app} {row.task_id}" for row in high_errors.itertuples())
            lines.append(f"Errori medi superiori a 1 rilevati per: {items}.")
    target = resolve_path(output_text_dir) / "users_time_interpretation.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n\n".join(lines) + "\n", encoding="utf-8")


def write_user_testing_summary(summary: pd.DataFrame, by_app: pd.DataFrame, output_text_dir: str | Path) -> None:
    lines = ["# User testing summary", ""]
    if summary.empty:
        lines.append("Dataset osservazionale non disponibile.")
    else:
        total_users = int(summary["n_users"].max()) if "n_users" in summary else 0
        lines.append(f"Dataset finale: {total_users} utenti osservati su Deliveroo e Glovo.")
        for row in by_app.itertuples(index=False):
            lines.append(
                f"- {row.app}: media {row.mean_time_sec:.2f}s, mediana {row.median_time_sec:.2f}s, "
                f"successo {row.success_rate:.0%}, errori medi {row.mean_errors:.2f}."
            )
    target = resolve_path(output_text_dir).parent / "user_testing_summary.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_user_testing_plot_aliases(output_figures_dir: str | Path) -> None:
    root = resolve_path(output_figures_dir) / "dark"
    aliases = {
        "users_time_mean_by_task.png": "mean_time_by_task_app.png",
        "users_time_median_by_task.png": "median_time_by_task_app.png",
        "users_time_distribution_by_app.png": "time_distribution_by_app.png",
    }
    out = resolve_path("outputs/plots/user_testing")
    out.mkdir(parents=True, exist_ok=True)
    for source_name, alias_name in aliases.items():
        source = root / source_name
        if source.exists():
            shutil.copy2(source, out / alias_name)
