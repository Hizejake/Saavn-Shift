from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def derive_working_copy_path(csv_path: Path) -> Path:
    if csv_path.suffix:
        return csv_path.with_name(f"{csv_path.stem}.working{csv_path.suffix}")
    return csv_path.with_name(f"{csv_path.name}.working.csv")


@dataclass(slots=True)
class Timeouts:
    search_results: int = 4000
    playlist_popup: int = 2000
    menu_item: int = 3000
    playlist_option: int = 5000
    playlist_add_request: int = 7000
    login_popup_check: int = 100
    after_popup_dismiss: int = 300
    after_escape: int = 500
    after_add_to_playlist: int = 600
    after_successful_add: int = 1500
    between_retries: int = 1000


@dataclass(slots=True)
class TransferConfig:
    playlist_name: str
    csv_path: Path
    auth_path: Path = Path("auth.json")
    working_copy_path: Path | None = None
    in_place: bool = False
    headless: bool = False
    max_retries: int = 3
    timeouts: Timeouts = field(default_factory=Timeouts)

    @property
    def progress_csv_path(self) -> Path:
        if self.in_place:
            return self.csv_path
        if self.working_copy_path is not None:
            return self.working_copy_path
        return derive_working_copy_path(self.csv_path)
