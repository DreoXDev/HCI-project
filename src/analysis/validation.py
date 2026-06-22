from __future__ import annotations

from pathlib import Path


class QuantitativeWarningLog:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def warn(self, message: str) -> None:
        self.messages.append(f"WARNING: {message}")

    def ok(self, message: str) -> None:
        self.messages.append(f"OK: {message}")

    def write(self, path: Path, heading: str = "Quantitative validation") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"# {heading}", "", *[f"- {message}" for message in self.messages], ""]
        path.write_text("\n".join(lines), encoding="utf-8")

