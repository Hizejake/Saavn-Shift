from __future__ import annotations

import csv
import shutil
from pathlib import Path

from saavnshift.models import SongEntry

TRACK_COLUMNS = ("Track name", "track", "song", "title")
ARTIST_COLUMNS = ("Artist name", "artist", "artists")


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader if any((value or "").strip() for value in row.values())]


def save_csv_rows(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def extract_column_value(row: dict[str, str], column_names: tuple[str, ...]) -> str:
    for column_name in column_names:
        value = row.get(column_name, "")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def row_to_song(row: dict[str, str]) -> SongEntry:
    return SongEntry(
        row=row,
        track_name=extract_column_value(row, TRACK_COLUMNS),
        artist_name=extract_column_value(row, ARTIST_COLUMNS),
    )


def ensure_progress_csv(source_path: Path, progress_path: Path, in_place: bool) -> Path:
    if in_place:
        return source_path
    if not progress_path.exists():
        shutil.copyfile(source_path, progress_path)
    return progress_path


def remove_row_by_identity(rows: list[dict[str, str]], target: dict[str, str]) -> None:
    for index, row in enumerate(rows):
        if row is target:
            rows.pop(index)
            return
