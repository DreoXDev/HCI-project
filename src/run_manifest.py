from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import resolve_path


def _git_value(args: list[str]) -> str | None:
    try:
        completed = subprocess.run(["git", *args], cwd=resolve_path("."), capture_output=True, text=True, check=False, timeout=5)
    except Exception:
        return None
    value = completed.stdout.strip()
    return value or None


def git_context() -> dict[str, str | None]:
    return {
        "branch": _git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "commit": _git_value(["rev-parse", "--short", "HEAD"]),
        "status": _git_value(["status", "--short"]),
    }


def collect_output_status() -> dict[str, Any]:
    outputs = {}
    for raw in [
        "outputs/slides/final_report.pptx",
        "outputs/slides/final_report.pdf",
        "outputs/slides/final_report_updated.pdf",
        "outputs/reports/final_data_validation.md",
        "outputs/reports/final_quality_check.md",
        "outputs/slide_manifest.json",
    ]:
        path = resolve_path(raw)
        outputs[raw] = {
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "modified": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat() if path.exists() else None,
        }
    return outputs


def write_pipeline_run_manifest(config: dict[str, Any], *, command: str, started_at: datetime | None = None) -> tuple[Path, Path]:
    finished_at = datetime.now(timezone.utc)
    started = started_at or finished_at
    manifest: dict[str, Any] = {
        "command": command,
        "started_at": started.isoformat(),
        "finished_at": finished_at.isoformat(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "git": git_context(),
        "project": config.get("project", {}),
        "paths": config.get("paths", {}),
        "outputs": collect_output_status(),
    }
    reports = resolve_path("outputs/reports")
    reports.mkdir(parents=True, exist_ok=True)
    json_path = reports / "pipeline_run.json"
    md_path = reports / "pipeline_run.md"
    json_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Pipeline Run Manifest",
        "",
        f"- Command: `{command}`",
        f"- Started: {manifest['started_at']}",
        f"- Finished: {manifest['finished_at']}",
        f"- Python: {manifest['python']}",
        f"- Platform: {manifest['platform']}",
        f"- Git branch: {manifest['git']['branch']}",
        f"- Git commit: {manifest['git']['commit']}",
        "",
        "## Outputs",
        "",
        "| Path | Exists | Size bytes | Modified |",
        "| --- | --- | --- | --- |",
    ]
    for path, details in manifest["outputs"].items():
        lines.append(f"| `{path}` | {details['exists']} | {details['size_bytes'] or ''} | {details['modified'] or ''} |")
    lines.extend(["", "## Notes", "", "Generated automatically by `src.run_manifest.write_pipeline_run_manifest`."])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path, json_path


def doctor_report() -> tuple[str, bool]:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("Python >= 3.11", sys.version_info >= (3, 11), sys.version.split()[0]))
    for module in ["pandas", "numpy", "matplotlib", "seaborn", "scipy", "pptx", "yaml", "PIL"]:
        try:
            __import__(module)
            checks.append((f"Python module `{module}`", True, "installed"))
        except Exception as exc:
            checks.append((f"Python module `{module}`", False, type(exc).__name__))
    libreoffice = shutil.which("soffice") or shutil.which("libreoffice") or "C:/Program Files/LibreOffice/program/soffice.exe"
    libreoffice_path = Path(libreoffice)
    checks.append(("LibreOffice PDF export", bool(shutil.which("soffice") or shutil.which("libreoffice") or libreoffice_path.exists()), str(libreoffice)))
    for raw in ["config.yaml", "slides/config/slide_deck.yml", "slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx"]:
        path = resolve_path(raw)
        checks.append((f"Required file `{raw}`", path.exists(), str(path)))
    try:
        from .slide_export.pptx_generator import validate_template_structure

        template_messages = validate_template_structure("slides/templates/Deliveroo_vs_Glovo_clean_python_ready_template.pptx")
    except Exception as exc:
        template_messages = [str(exc)]
    checks.append(
        (
            "PowerPoint template structure",
            not template_messages,
            "OK" if not template_messages else "; ".join(template_messages[:3]),
        )
    )
    output_dir = resolve_path("outputs")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".doctor_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        checks.append(("Outputs directory writable", True, str(output_dir)))
    except Exception as exc:
        checks.append(("Outputs directory writable", False, str(exc)))

    ok = all(item[1] for item in checks)
    lines = ["# HCI Project Doctor", "", "| Check | Status | Detail |", "| --- | --- | --- |"]
    for label, passed, detail in checks:
        lines.append(f"| {label} | {'OK' if passed else 'FAIL'} | {detail} |")
    lines.extend(["", f"STATUS: {'OK' if ok else 'FAIL'}"])
    return "\n".join(lines) + "\n", ok
