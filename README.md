# SaavnShift

SaavnShift is a packaged Python rewrite of a JioSaavn playlist transfer workflow powered by Playwright.

## Credit

This project was inspired by the original JavaScript repo by Adithya-Sakaray:

- https://github.com/Adithya-Sakaray/SaavnSync

This rewrite keeps the same spirit while reorganizing the tool as a Python package with a CLI and safer CSV-progress handling.

## What it does

- Saves a reusable JioSaavn login session
- Reads songs from exported CSV files
- Searches each song on JioSaavn
- Adds the first matching result to a target playlist
- Keeps resumable progress in a working CSV

## Why this version is safer

The original JavaScript script updated the source CSV directly. This package defaults to creating a working copy so your original export remains untouched unless you explicitly opt into `--in-place`.

## Get a CSV with TuneMyMusic

If your playlist is currently on Spotify, YouTube Music, Apple Music, or another supported service, you can export it to a CSV file with TuneMyMusic.

1. Open https://www.tunemymusic.com/.
2. Choose your source music service and sign in if TuneMyMusic asks for access.
3. Select the playlist, liked songs, or library items you want to export.
4. Choose `Export to file` as the destination.
5. Let TuneMyMusic generate the file, then download the CSV export to your computer.
6. Place the file somewhere convenient and pass its path to `saavnshift transfer`.

Example:

```powershell
saavnshift transfer --playlist "SJ1" --csv "C:\Users\arpan\Downloads\My Spotify Library.csv" --auth-path auth.json
```

SaavnShift looks for common song-title and artist columns such as `Track name`, `track`, `song`, `title`, `Artist name`, `artist`, and `artists`.

## Install

```powershell
cd C:\Users\arpan\OneDrive\Desktop\code\SaavnShift
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
```

If you want Playwright's bundled Chromium as a fallback:

```powershell
python -m playwright install chromium
```

## Login

```powershell
saavnshift login --auth-path auth.json
```

This opens JioSaavn in a headed browser. Log in manually, then press Enter in the terminal to save the browser session.

## Transfer songs

```powershell
saavnshift transfer --playlist "SJ1" --csv "My Spotify Library.csv" --auth-path auth.json
```

By default, this creates a resumable working file next to the source CSV:

- `My Spotify Library.working.csv`

If you want to mutate the source CSV instead:

```powershell
saavnshift transfer --playlist "SJ1" --csv "My Spotify Library.csv" --in-place
```

You can also choose a custom working copy path:

```powershell
saavnshift transfer --playlist "SJ1" --csv songs.csv --working-copy progress.csv
```

## Notes

- Headless mode may be blocked by JioSaavn's anti-bot protections. Headed mode is the default for that reason.
- The automation still relies on JioSaavn's live UI, so selector drift can break it over time.
- The script clicks the first song result that JioSaavn returns.

## Development

Run the tests with:

```powershell
python -m unittest discover -s tests
```
