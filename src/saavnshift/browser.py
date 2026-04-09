from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path


def _file_exists(path: str | os.PathLike[str] | None) -> bool:
    return bool(path) and Path(path).exists()


def get_chrome_executable_path() -> str | None:
    env_path = os.getenv("CHROME_EXECUTABLE_PATH") or os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
    if _file_exists(env_path):
        return str(Path(env_path))

    system = platform.system().lower()
    candidates: list[str | None] = []

    if system == "windows":
        local_app_data = os.getenv("LOCALAPPDATA")
        program_files = os.getenv("ProgramFiles")
        program_files_x86 = os.getenv("ProgramFiles(x86)")
        candidates.extend(
            [
                f"{local_app_data}\\Google\\Chrome\\Application\\chrome.exe" if local_app_data else None,
                f"{program_files}\\Google\\Chrome\\Application\\chrome.exe" if program_files else None,
                f"{program_files_x86}\\Google\\Chrome\\Application\\chrome.exe" if program_files_x86 else None,
            ]
        )
    elif system == "darwin":
        candidates.extend(
            [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            ]
        )
    else:
        candidates.extend(
            [
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
            ]
        )

    for candidate in candidates:
        if _file_exists(candidate):
            return str(Path(candidate))

    if system not in {"windows", "darwin"}:
        for name in ["google-chrome-stable", "google-chrome", "chromium-browser", "chromium"]:
            resolved = shutil.which(name)
            if _file_exists(resolved):
                return str(Path(resolved))

    return None
