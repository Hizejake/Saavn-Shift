from __future__ import annotations

import re
from collections.abc import Iterable

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

from saavnshift.config import Timeouts
from saavnshift.models import ProcessingResult, ProcessingStatus, SongEntry

SEARCH_RESULTS_SELECTOR = "ol.o-list-bare > li"
LOGIN_PATTERNS = [
    re.compile(r"Log in to create playlists", re.I),
    re.compile(r"Don't have a JioSaavn account", re.I),
    re.compile(r"Please log in", re.I),
    re.compile(r"Sign Up", re.I),
    re.compile(r"log in|sign in|create account", re.I),
]


def build_search_url(query: str) -> str:
    from urllib.parse import quote

    return f"https://www.jiosaavn.com/search/song/{quote(query)}"


def find_first_visible(locators: Iterable[Locator], timeout_ms: int) -> Locator | None:
    for locator in locators:
        candidate = locator.first
        try:
            candidate.wait_for(state="visible", timeout=timeout_ms)
            return candidate
        except PlaywrightTimeoutError:
            continue
    return None


def is_login_prompt_visible(page: Page) -> bool:
    for pattern in LOGIN_PATTERNS:
        try:
            if page.get_by_text(pattern).first.is_visible(timeout=1000):
                return True
        except PlaywrightTimeoutError:
            continue
    return False


def ensure_user_is_logged_in(page: Page) -> None:
    if is_login_prompt_visible(page):
        raise RuntimeError(
            "JioSaavn is not logged in for the automated browser. "
            "Please rerun `saavnshift login` before using `saavnshift transfer`."
        )


def dismiss_login_popup_if_present(page: Page, timeouts: Timeouts) -> bool:
    dialog_locators = [
        page.locator("[role='dialog']"),
        page.locator(".o-modal"),
        page.locator(".c-modal"),
        page.locator(".modal"),
        page.locator(".modal-dialog"),
        page.locator("[data-testid='modal']"),
    ]

    login_pattern = re.compile(r"log\s*in|sign\s*in|create.*account|email|phone", re.I)

    for dialog in dialog_locators:
        candidate = dialog.first
        try:
            if not candidate.is_visible(timeout=timeouts.login_popup_check):
                continue
        except PlaywrightTimeoutError:
            continue

        try:
            has_login_text = candidate.get_by_text(login_pattern).first.is_visible(timeout=timeouts.login_popup_check)
        except PlaywrightTimeoutError:
            has_login_text = False

        if not has_login_text:
            continue

        print("Login popup detected, attempting to dismiss...")
        close_locators = [
            candidate.locator("[aria-label='Close']"),
            candidate.locator(".o-modal__close"),
            candidate.locator(".c-modal__close"),
            candidate.locator("button.close"),
            candidate.locator("[data-dismiss='modal']"),
            candidate.locator(".modal-close"),
            candidate.locator("button[aria-label*='close' i]"),
        ]

        for close_button in close_locators:
            button = close_button.first
            try:
                if button.is_visible(timeout=timeouts.login_popup_check):
                    button.click(force=True)
                    print("Dismissed login popup via close button")
                    page.wait_for_timeout(timeouts.after_popup_dismiss)
                    return True
            except PlaywrightTimeoutError:
                continue

        page.keyboard.press("Escape")
        print("Dismissed login popup via Escape key")
        page.wait_for_timeout(timeouts.after_popup_dismiss)
        return True

    return False


def add_song_to_playlist(page: Page, song: SongEntry, playlist_name: str, timeouts: Timeouts) -> ProcessingResult:
    search_query = song.query
    if not search_query:
        return ProcessingResult(ProcessingStatus.SKIP, search_query, "Missing track or artist info")

    print(f"Searching: {search_query}")
    try:
        page.goto(build_search_url(search_query), wait_until="domcontentloaded")
    except Exception as exc:  # pragma: no cover - Playwright/network behavior
        return ProcessingResult(ProcessingStatus.RETRY, search_query, f"Navigation failed: {exc}")

    ensure_user_is_logged_in(page)

    try:
        page.wait_for_selector(SEARCH_RESULTS_SELECTOR, timeout=timeouts.search_results)
    except PlaywrightTimeoutError:
        pass

    dismiss_login_popup_if_present(page, timeouts)

    search_results = page.locator(SEARCH_RESULTS_SELECTOR)
    if search_results.first.count() == 0:
        print(f"No search results found, skipping: {search_query}")
        return ProcessingResult(ProcessingStatus.SKIP, search_query, "No search results found")

    first_result = search_results.first
    more_options_button = first_result.locator("[aria-label='More Options'], .c-btn-overflow[role='button']").first
    if more_options_button.count() == 0:
        print(f"'More Options' button not found, skipping: {search_query}")
        return ProcessingResult(ProcessingStatus.SKIP, search_query, "Missing More Options button")

    first_result.hover()
    dismiss_login_popup_if_present(page, timeouts)
    more_options_button.click(force=True)
    page.wait_for_timeout(timeouts.after_add_to_playlist)
    ensure_user_is_logged_in(page)

    add_to_playlist_button = find_first_visible(
        [
            page.get_by_text(re.compile(r"Add\s*to\s*Playlist", re.I)),
            page.locator("text=/Add\\s*to\\s*Playlist/i"),
            page.locator("[role='menuitem']").filter(has_text=re.compile(r"Add\s*to\s*Playlist", re.I)),
            page.locator("[aria-label*='Add to Playlist' i], [title*='Add to Playlist' i]"),
        ],
        timeouts.menu_item + 2000,
    )

    if add_to_playlist_button is None:
        print(f"'Add to Playlist' option not found, skipping: {search_query}")
        return ProcessingResult(ProcessingStatus.SKIP, search_query, "Missing Add to Playlist action")

    dismiss_login_popup_if_present(page, timeouts)
    add_to_playlist_button.scroll_into_view_if_needed()
    try:
        add_to_playlist_button.click()
    except Exception as exc:  # pragma: no cover - Playwright click behavior
        return ProcessingResult(ProcessingStatus.SKIP, search_query, f"Could not click Add to Playlist: {exc}")

    ensure_user_is_logged_in(page)

    try:
        page.wait_for_timeout(timeouts.after_add_to_playlist)
    except Exception as exc:  # pragma: no cover
        return ProcessingResult(ProcessingStatus.RETRY, search_query, f"Browser closed while opening playlist modal: {exc}")

    modal = find_first_visible(
        [
            page.locator("aside.c-modal.active.sub-menu"),
            page.locator("aside.c-modal.active"),
            page.locator("[role='dialog']"),
            page.locator(".o-modal.active"),
            page.locator(".c-modal.active"),
        ],
        timeouts.playlist_popup,
    )

    if modal is None:
        print("Playlist modal not detected, likely login popup interference. Retrying...")
        page.keyboard.press("Escape")
        page.wait_for_timeout(timeouts.after_escape)
        return ProcessingResult(ProcessingStatus.RETRY, search_query, "Playlist modal not detected")

    playlist_pattern = re.compile(rf"^\s*{re.escape(playlist_name)}(?:\s*\(|\s*$)", re.I)
    print(f'Looking for playlist: "{playlist_name}"...')

    target_playlist_button = find_first_visible(
        [
            modal.locator("a.c-nav__link").filter(has_text=playlist_pattern),
            modal.locator("button, [role='button'], [role='option'], [role='menuitem']").filter(has_text=playlist_pattern),
            modal.locator("a, span, div, li").filter(has_text=playlist_pattern),
        ],
        timeouts.playlist_option,
    )

    if target_playlist_button is None:
        print(f"Playlist '{playlist_name}' not found in add-to-playlist UI. Retrying...")
        return ProcessingResult(ProcessingStatus.RETRY, search_query, "Playlist option not visible")

    matched_text = (target_playlist_button.text_content() or "").strip() or playlist_name
    print(f'Found playlist item: "{matched_text}"')
    print(f'Selecting playlist: "{playlist_name}"...')

    try:
        target_playlist_button.scroll_into_view_if_needed()
        with page.expect_response(lambda response: "__call=playlist.add" in response.url, timeout=timeouts.playlist_add_request) as response_info:
            target_playlist_button.click()
        response = response_info.value

        if not response.ok:
            return ProcessingResult(
                ProcessingStatus.RETRY,
                search_query,
                f"playlist.add returned HTTP {response.status}",
            )

        try:
            modal.wait_for(state="hidden", timeout=timeouts.playlist_add_request)
        except PlaywrightTimeoutError:
            return ProcessingResult(ProcessingStatus.RETRY, search_query, "Playlist modal stayed open after click")

        dismiss_login_popup_if_present(page, timeouts)
    except Exception as exc:  # pragma: no cover - browser timing behavior
        return ProcessingResult(ProcessingStatus.RETRY, search_query, f"Playlist selection failed: {exc}")

    page.wait_for_timeout(timeouts.after_successful_add)
    return ProcessingResult(ProcessingStatus.SUCCESS, search_query)
