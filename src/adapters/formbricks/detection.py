from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .normalization import comparable


TAG_RE = re.compile(r"\[([^\]]+)\]")


@dataclass(frozen=True)
class ColumnTags:
    raw: str
    tags: tuple[str, ...]
    label: str

    def has(self, tag: str) -> bool:
        return comparable(tag) in {comparable(item) for item in self.tags}

    def system(self, known_systems: list[str]) -> str | None:
        tag_values = {comparable(item) for item in self.tags}
        for system in known_systems:
            if comparable(system) in tag_values:
                return system
        for system in known_systems:
            if comparable(system) in comparable(self.raw):
                return system
        return None


def parse_column_tags(column: str) -> ColumnTags:
    tags = tuple(tag.strip() for tag in TAG_RE.findall(str(column)))
    label = TAG_RE.sub("", str(column)).strip()
    return ColumnTags(raw=str(column), tags=tags, label=label)


def is_metadata_column(column: str, metadata_columns: list[str]) -> bool:
    column_cmp = comparable(column)
    metadata = {comparable(item) for item in metadata_columns}
    return column_cmp in metadata or column_cmp.endswith("option id")


def find_by_alias(columns: list[str], aliases: list[str]) -> str | None:
    alias_values = [comparable(alias) for alias in aliases if comparable(alias)]
    for column in columns:
        column_cmp = comparable(column)
        if any(alias == column_cmp or alias in column_cmp or column_cmp in alias for alias in alias_values):
            return column
    return None


def first_index_containing(columns: list[str], needle: str) -> int | None:
    needle_cmp = comparable(needle)
    if not needle_cmp:
        return None
    for index, column in enumerate(columns):
        if needle_cmp in comparable(column):
            return index
    return None


def tagged_columns(columns: list[str], tag: str, systems: list[str] | None = None) -> list[str]:
    found = []
    for column in columns:
        parsed = parse_column_tags(column)
        if parsed.has(tag) and (systems is None or parsed.system(systems) in systems):
            found.append(column)
    return found


def column_matches_field(column: str, field: dict[str, Any]) -> bool:
    parsed = parse_column_tags(column)
    aliases = [field.get("id", ""), *field.get("aliases", [])]
    return parsed.has(field.get("tag", "")) or find_by_alias([column], aliases) is not None

