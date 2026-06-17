from pathlib import Path
import subprocess


def test_repository_does_not_ship_demo_datasets() -> None:
    tracked = subprocess.run(["git", "ls-files", "data"], check=True, capture_output=True, text=True).stdout.splitlines()
    forbidden = [
        path
        for path in tracked
        if Path(path).name != ".gitkeep"
        and any(token in Path(path).name.lower() for token in ("demo", "example", "template"))
    ]
    assert forbidden == []


def test_generated_outputs_are_gitignored() -> None:
    ignore_file = Path(".gitignore").read_text(encoding="utf-8")
    assert "outputs/**" in ignore_file
    assert "reports/**" in ignore_file
    assert "data/**" in ignore_file
