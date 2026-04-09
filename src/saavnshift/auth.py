from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from saavnshift.browser import get_chrome_executable_path
from saavnshift.jiosaavn import ensure_user_is_logged_in, is_login_prompt_visible


def save_login_session(auth_path: Path, headless: bool = False) -> None:
    auth_path.parent.mkdir(parents=True, exist_ok=True)

    launch_args: dict[str, object] = {"headless": headless}
    chrome_executable = get_chrome_executable_path()
    if chrome_executable:
        launch_args["executable_path"] = chrome_executable
        print(f"Launching browser using: {chrome_executable}")
    else:
        print("No Chrome executable detected; using Playwright bundled browser.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_args)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.jiosaavn.com")

        print("Login manually in the browser.")
        print("After login press ENTER here.")
        input()

        if is_login_prompt_visible(page):
            browser.close()
            raise SystemExit(
                "It looks like you are not fully logged in yet. "
                "Please complete login in the browser and then run the command again."
            )

        ensure_user_is_logged_in(page)
        context.storage_state(path=str(auth_path))
        print(f"Login saved to {auth_path}")
        browser.close()
