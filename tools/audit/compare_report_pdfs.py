from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - exercised by CLI users without deps.
    raise SystemExit("Missing dependency: install `pypdf` to run the PDF audit.") from exc


@dataclass(frozen=True)
class PageText:
    page: int
    title: str
    text: str
    fingerprint: str


SOURCE_OF_TRUTH = [
    ("Dati numerici, metriche, grafici, UEQ, benchmark, p-value", "Toolchain / CSV / Python"),
    ("Testi editoriali approvati a mano", "Presentazione manuale, se piu curata e non obsoleta"),
    ("Titoli sezioni e ordine finale delle macro-sezioni", "Presentazione manuale, se coerente con la struttura finale"),
    ("Dati App Store, download, rating, date", "Config/dati aggiornati della toolchain, non testo vecchio manuale"),
    ("Appendici e materiali finali", "Presentazione manuale, salvo duplicati/ridondanze"),
    ("Layout/stile grafico generale", "Template PPTX + config tema"),
]

UEQ_SANITY_CHECKS = [
    "Scala trasformata UEQ: usare risultati su range -3..+3, non medie raw 1..7.",
    "Mapping item -> scale: mantenere la mappa ufficiale in config/ueq_items.yml.",
    "Benchmark category: usare soglie ufficiali centralizzate in config/ueq_benchmark_thresholds.yml e src.analysis.ueq_benchmark.",
    "P-value e test per dimensione: derivare dai CSV/table output della pipeline.",
    "N valido: verificare il numero utenti finiti/importati prima di commentare differenze sottili.",
    "Deck finale: nessuna slide ufficiale UEQ deve presentare raw mean 1..7 come risultato principale.",
]


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9àèéìòùç ]+", "", text)
    return text.strip()


def _title_from_text(text: str, fallback: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:8]:
        cleaned = re.sub(r"\s+", " ", line)
        if 4 <= len(cleaned) <= 90:
            return cleaned
    return fallback


def read_pdf(path: Path) -> list[PageText]:
    reader = PdfReader(str(path))
    pages: list[PageText] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.replace("\x00", "").strip()
        fingerprint = hashlib.sha1(_normalize(text).encode("utf-8")).hexdigest()[:12]
        pages.append(PageText(index, _title_from_text(text, f"Page {index}"), text, fingerprint))
    return pages


def similarity(a: str, b: str) -> float:
    a_norm = _normalize(a)
    b_norm = _normalize(b)
    if not a_norm and not b_norm:
        return 1.0
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def map_pages(manual: list[PageText], generated: list[PageText]) -> list[dict[str, object]]:
    generated_by_title: dict[str, list[PageText]] = {}
    for page in generated:
        generated_by_title.setdefault(_normalize(page.title), []).append(page)

    rows: list[dict[str, object]] = []
    for page in manual:
        title_key = _normalize(page.title)
        candidates = generated_by_title.get(title_key, generated)
        scored = sorted(
            (
                (
                    0.65 * similarity(page.title, candidate.title)
                    + 0.35 * similarity(page.text, candidate.text)
                    - min(abs(page.page - candidate.page), 20) * 0.002,
                    candidate,
                )
                for candidate in candidates
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        score, best = scored[0] if scored else (0.0, None)
        rows.append(
            {
                "manual_page": page.page,
                "manual_title": page.title,
                "generated_page": best.page if best else None,
                "generated_title": best.title if best else "",
                "score": max(score, 0.0),
                "same_title": bool(best and title_key == _normalize(best.title)),
                "same_fingerprint": bool(best and page.fingerprint == best.fingerprint),
                "needs_review": score < 0.55 if best else True,
            }
        )
    return rows


def _markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return out


def write_report(manual_path: Path, generated_path: Path, out_path: Path, manual: list[PageText], generated: list[PageText]) -> None:
    mapping = map_pages(manual, generated)
    matched_generated = {int(row["generated_page"]) for row in mapping if row["generated_page"]}

    same_title_different_text = [
        row
        for row in mapping
        if row["same_title"] and not row["same_fingerprint"] and float(row["score"]) < 0.98
    ]
    similar_order_changed = [
        row
        for row in mapping
        if row["generated_page"] and abs(int(row["manual_page"]) - int(row["generated_page"])) > 2 and float(row["score"]) >= 0.55
    ]
    manual_only = [row for row in mapping if row["needs_review"]]
    generated_only = [page for page in generated if page.page not in matched_generated]

    lines: list[str] = [
        "# Manual vs Generated Report Audit",
        "",
        f"- Manual PDF: `{manual_path}`",
        f"- Generated PDF: `{generated_path}`",
        f"- Manual pages: {len(manual)}",
        f"- Generated pages: {len(generated)}",
        "",
        "## Source Of Truth Rules",
        "",
        *_markdown_table(["Tipo contenuto", "Source of truth preferita"], SOURCE_OF_TRUTH),
        "",
        "## Estimated Page Mapping",
        "",
        *_markdown_table(
            ["manual", "manual title", "generated", "generated title", "score", "review"],
            [
                [
                    row["manual_page"],
                    row["manual_title"],
                    row["generated_page"] or "-",
                    row["generated_title"],
                    f"{float(row['score']):.2f}",
                    "yes" if row["needs_review"] else "no",
                ]
                for row in mapping
            ],
        ),
        "",
        "## Manual Slides Needing Review",
        "",
    ]
    if manual_only:
        lines.extend(
            _markdown_table(
                ["manual", "title", "best generated", "score"],
                [[row["manual_page"], row["manual_title"], row["generated_page"] or "-", f"{float(row['score']):.2f}"] for row in manual_only],
            )
        )
    else:
        lines.append("No low-similarity manual pages detected.")

    lines.extend(["", "## Generated Slides Without Strong Manual Match", ""])
    if generated_only:
        lines.extend(_markdown_table(["generated", "title", "fingerprint"], [[p.page, p.title, p.fingerprint] for p in generated_only]))
    else:
        lines.append("No generated-only pages detected by the greedy mapping.")

    lines.extend(["", "## Same Title But Different Text", ""])
    if same_title_different_text:
        lines.extend(
            _markdown_table(
                ["manual", "generated", "title", "score"],
                [[row["manual_page"], row["generated_page"], row["manual_title"], f"{float(row['score']):.2f}"] for row in same_title_different_text],
            )
        )
    else:
        lines.append("No same-title pages with relevant text drift detected.")

    lines.extend(["", "## Similar Text In Different Order", ""])
    if similar_order_changed:
        lines.extend(
            _markdown_table(
                ["manual", "generated", "manual title", "generated title", "score"],
                [
                    [row["manual_page"], row["generated_page"], row["manual_title"], row["generated_title"], f"{float(row['score']):.2f}"]
                    for row in similar_order_changed
                ],
            )
        )
    else:
        lines.append("No high-similarity order changes detected.")

    lines.extend(
        [
            "",
            "## Possible Static Text Candidates",
            "",
            "Review the same-title/different-text rows above. Copy manual text only when it is editorially better and does not reintroduce stale app-store numbers, old benchmark categories, or obsolete UEQ wording.",
            "",
            "## Possible Slide Toggles",
            "",
            "Use the generated-only and manual-only lists to decide which slide ids should be enabled, disabled, or moved in `config/slides.yaml` and `config/appendices.yaml`.",
            "",
            "## UEQ Sanity Checks",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in UEQ_SANITY_CHECKS)
    lines.extend(["", "## Notes", "", "This audit is heuristic. It is intended to guide review, not to replace manual editorial judgment."])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare manual and generated HCI report PDFs.")
    parser.add_argument("--manual", required=True, type=Path)
    parser.add_argument("--generated", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    if not args.manual.exists():
        raise SystemExit(f"Manual PDF not found: {args.manual}")
    if not args.generated.exists():
        raise SystemExit(f"Generated PDF not found: {args.generated}")

    manual = read_pdf(args.manual)
    generated = read_pdf(args.generated)
    write_report(args.manual, args.generated, args.out, manual, generated)
    print(args.out)


if __name__ == "__main__":
    main()
