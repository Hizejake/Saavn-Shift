from __future__ import annotations

import argparse
from pathlib import Path

from saavnshift.auth import save_login_session
from saavnshift.config import TransferConfig
from saavnshift.transfer import run_transfer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="saavnshift", description="Transfer songs into a JioSaavn playlist.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    login_parser = subparsers.add_parser("login", help="Log into JioSaavn and save auth state.")
    login_parser.add_argument("--auth-path", type=Path, default=Path("auth.json"))
    login_parser.add_argument("--headless", action="store_true", help="Launch the browser in headless mode.")

    transfer_parser = subparsers.add_parser("transfer", help="Transfer songs from a CSV into a JioSaavn playlist.")
    transfer_parser.add_argument("--playlist", required=True, help="Target JioSaavn playlist name.")
    transfer_parser.add_argument("--csv", type=Path, required=True, help="Source CSV export.")
    transfer_parser.add_argument("--auth-path", type=Path, default=Path("auth.json"))
    transfer_parser.add_argument("--working-copy", type=Path, help="Optional resumable progress CSV.")
    transfer_parser.add_argument("--in-place", action="store_true", help="Mutate the source CSV instead of creating a working copy.")
    transfer_parser.add_argument("--headless", action="store_true", help="Run the browser headlessly.")
    transfer_parser.add_argument("--max-retries", type=int, default=3, help="Retry count when JioSaavn UI is flaky.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "login":
        save_login_session(auth_path=args.auth_path, headless=args.headless)
        return 0

    if args.command == "transfer":
        config = TransferConfig(
            playlist_name=args.playlist.strip(),
            csv_path=args.csv,
            auth_path=args.auth_path,
            working_copy_path=args.working_copy,
            in_place=args.in_place,
            headless=args.headless,
            max_retries=args.max_retries,
        )
        run_transfer(config)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
