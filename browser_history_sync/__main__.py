import argparse
import sys
from .common import detect_db_type
from .sync_engine import (
    chromium_to_firefox,
    firefox_to_chromium,
    chromium_to_chromium,
    firefox_to_firefox,
)

ENGINE_MAP = {
    ("chromium", "firefox"): chromium_to_firefox,
    ("firefox", "chromium"): firefox_to_chromium,
    ("chromium", "chromium"): chromium_to_chromium,
    ("firefox", "firefox"): firefox_to_firefox,
}

LABEL_MAP = {
    "chromium": "Chromium",
    "firefox": "Firefox",
}


def main():
    parser = argparse.ArgumentParser(
        description="Merge browsing history between two browser databases"
    )
    parser.add_argument("db1", help="Path to first history database")
    parser.add_argument("db2", help="Path to second history database")
    parser.add_argument("--include-hidden", action="store_true",
                        help="Include hidden URLs (e.g. subframe resources)")
    parser.add_argument("--commit-every", type=int, default=500,
                        help="Commit every N records (default: 500)")
    args = parser.parse_args()

    try:
        t1 = detect_db_type(args.db1)
        t2 = detect_db_type(args.db2)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  {args.db1}  →  {LABEL_MAP[t1]}")
    print(f"  {args.db2}  →  {LABEL_MAP[t2]}")
    print(f"  Direction: {t1} → {t2}")
    print()

    engine = ENGINE_MAP.get((t1, t2))
    if engine is None:
        print(f"Error: unsupported direction {t1} → {t2}", file=sys.stderr)
        sys.exit(1)

    engine(
        source_db=args.db1,
        dest_db=args.db2,
        include_hidden=args.include_hidden,
        commit_every=args.commit_every,
    )


if __name__ == "__main__":
    main()
