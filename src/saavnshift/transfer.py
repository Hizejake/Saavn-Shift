from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from saavnshift.browser import get_chrome_executable_path
from saavnshift.config import TransferConfig
from saavnshift.csv_io import ensure_progress_csv, load_csv_rows, remove_row_by_identity, row_to_song, save_csv_rows
from saavnshift.jiosaavn import add_song_to_playlist, ensure_user_is_logged_in
from saavnshift.models import ProcessingResult, ProcessingStatus


def process_song_with_retry(page, song, playlist_name: str, config: TransferConfig) -> ProcessingResult:
    attempts = 0

    while attempts < config.max_retries:
        result = add_song_to_playlist(page, song, playlist_name, config.timeouts)
        if result.status is not ProcessingStatus.RETRY:
            return result

        attempts += 1
        print(f"Retry attempt {attempts}/{config.max_retries} for: {result.query}")
        page.wait_for_timeout(config.timeouts.between_retries)

    print(f"Failed after {config.max_retries} retries, skipping: {song.query}")
    return ProcessingResult(ProcessingStatus.SKIP, song.query, "Exceeded retry limit")


def run_transfer(config: TransferConfig) -> Path:
    progress_csv_path = ensure_progress_csv(config.csv_path, config.progress_csv_path, config.in_place)
    rows = load_csv_rows(progress_csv_path)
    remaining_rows = list(rows)

    print(f"Loaded {len(rows)} songs from {progress_csv_path}")
    print(f"Target playlist: {config.playlist_name}")

    launch_args: dict[str, object] = {"headless": config.headless}
    chrome_executable = get_chrome_executable_path()
    if chrome_executable:
        launch_args["executable_path"] = chrome_executable
        print(f"Using browser executable: {chrome_executable}")
    else:
        print("No Chrome executable detected; using Playwright bundled browser.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_args)
        context = browser.new_context(storage_state=str(config.auth_path))
        page = context.new_page()
        page.goto("https://www.jiosaavn.com")
        ensure_user_is_logged_in(page)

        for row in rows:
            song = row_to_song(row)
            result = process_song_with_retry(page, song, config.playlist_name, config)
            if result.status is ProcessingStatus.SUCCESS:
                remove_row_by_identity(remaining_rows, row)
                save_csv_rows(progress_csv_path, remaining_rows)
                print(f'Added "{result.query}" to playlist. {len(remaining_rows)} songs remaining.')

        print(f"\nFinished! {len(remaining_rows)} songs remaining in CSV.")
        if remaining_rows:
            print("Songs that couldn't be added are still in the CSV file.")
            print("You can re-run this command to retry them.")

        browser.close()

    return progress_csv_path
