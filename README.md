# Browser History Sync

[中文文档](README.zh.md)

Merge browsing history between Firefox and Chromium-based browsers (Chrome, Vivaldi, Edge, Brave, Opera, Zen, etc.) — and between profiles of the same browser.

## Why

Browser vendors limit history sync to a few months and it often fails. This tool gives you full control: merge history from multiple profiles, migrate between browsers, or back up your data — all offline, no cloud involved.

## How it works

Both Firefox and Chromium store history in SQLite databases. This tool reads visits from one database and writes missing ones to another, deduplicating by `(url, visit_timestamp)`.

| Browser | Database file | Tables |
|---------|--------------|--------|
| **Firefox** (Firefox, Zen, Waterfox, etc.) | `places.sqlite` | `moz_places`, `moz_historyvisits` |
| **Chromium** (Chrome, Edge, Vivaldi, Brave, Opera, etc.) | `History` | `urls`, `visits` |

## Usage

```bash
python3 -m browser_history_sync <db1> <db2> [options]
```

The tool auto-detects the type of each database and syncs in the correct direction.

**Examples:**

```bash
# Merge Chromium history into Firefox (Linux)
python3 -m browser_history_sync \
    ~/.config/google-chrome/Default/History \
    ~/.mozilla/firefox/xxxx.default-esr/places.sqlite

# Merge Firefox history into Chromium (macOS)
python3 -m browser_history_sync \
    ~/Library/Application\ Support/Firefox/Profiles/xxxx.default/places.sqlite \
    ~/Library/Application\ Support/Google/Chrome/Default/History

# Merge two Firefox profiles (Windows)
python3 -m browser_history_sync \
    "C:\Users\<You>\AppData\Roaming\Mozilla\Firefox\Profiles\xxxx.default\places.sqlite" \
    "C:\Users\<You>\AppData\Roaming\Mozilla\Firefox\Profiles\yyyy.default\places.sqlite"
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--commit-every N` | 500 | Commit every N records |
| `--include-hidden` | — | Include hidden URLs (subframe resources, etc.) |

> **Important:** Close all browsers before running. The database files are locked when the browser is running.

## Idempotent

Running the same sync multiple times produces the same result — only new visits are added, nothing is duplicated or overwritten.

```
1st sync:  db_a → db_b  →  db_b += visits from db_a that db_b doesn't have
2nd sync:  db_a → db_b  →  nothing changes (all visits already exist in db_b)
```

## Requirements

Python 3.10+ (standard library only — no pip install needed).

## File structure

```
browser_history_sync/
  __main__.py           CLI entry point (python -m browser_history_sync)
  __init__.py
  common.py             Shared types, timestamp conversion, DB type detection
  reader_chromium.py    Read Chromium History → list of visits
  reader_firefox.py     Read Firefox places.sqlite → list of visits
  writer_chromium.py    Write visits into Chromium History
  writer_firefox.py     Write visits into Firefox places.sqlite
  sync_engine.py        Sync orchestration logic
```

## License

Apache 2.0
