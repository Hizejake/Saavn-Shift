from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from saavnshift.config import TransferConfig, derive_working_copy_path
from saavnshift.csv_io import ARTIST_COLUMNS, TRACK_COLUMNS, ensure_progress_csv, extract_column_value, row_to_song
from saavnshift.jiosaavn import build_search_url


class CsvIoTests(unittest.TestCase):
    def test_extract_column_value_returns_first_non_empty_match(self) -> None:
        row = {"title": "  Song Name  ", "artist": "Artist Name"}
        self.assertEqual(extract_column_value(row, TRACK_COLUMNS), "Song Name")
        self.assertEqual(extract_column_value(row, ARTIST_COLUMNS), "Artist Name")

    def test_row_to_song_builds_query(self) -> None:
        row = {"Track name": "Track", "Artist name": "Artist"}
        song = row_to_song(row)
        self.assertEqual(song.query, "Track Artist")

    def test_working_copy_path_appends_working_before_suffix(self) -> None:
        path = Path("My Spotify Library.csv")
        self.assertEqual(derive_working_copy_path(path), Path("My Spotify Library.working.csv"))

    def test_transfer_config_uses_working_copy_by_default(self) -> None:
        config = TransferConfig(playlist_name="SJ1", csv_path=Path("songs.csv"))
        self.assertEqual(config.progress_csv_path, Path("songs.working.csv"))

    def test_ensure_progress_csv_copies_source_when_needed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "songs.csv"
            progress = temp_path / "songs.working.csv"
            source.write_text("Track name,Artist name\nTrack,Artist\n", encoding="utf-8")

            resolved = ensure_progress_csv(source, progress, in_place=False)

            self.assertEqual(resolved, progress)
            self.assertTrue(progress.exists())
            self.assertEqual(progress.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))

    def test_build_search_url_encodes_spaces(self) -> None:
        url = build_search_url("Track Name Artist Name")
        self.assertIn("Track%20Name%20Artist%20Name", url)


if __name__ == "__main__":
    unittest.main()
