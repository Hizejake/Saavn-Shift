from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProcessingStatus(str, Enum):
    SUCCESS = "success"
    SKIP = "skip"
    RETRY = "retry"


@dataclass(frozen=True)
class SongEntry:
    row: dict[str, str]
    track_name: str
    artist_name: str

    @property
    def query(self) -> str:
        return " ".join(part for part in [self.track_name, self.artist_name] if part).strip()


@dataclass(frozen=True)
class ProcessingResult:
    status: ProcessingStatus
    query: str
    reason: str = ""
