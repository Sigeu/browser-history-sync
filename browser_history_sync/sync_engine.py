from .common import Visit
from .reader_chromium import read_history as read_chromium
from .reader_firefox import read_history as read_firefox
from .writer_chromium import ChromiumWriter
from .writer_firefox import FirefoxWriter


def _run_sync(
    label: str,
    reader_fn,
    writer,
    source_db: str,
    dest_db: str,
    include_hidden: bool = False,
    commit_every: int = 500,
):
    print(f"Reading {label} history from: {source_db}")
    visits = reader_fn(source_db, include_hidden=include_hidden)
    print(f"  Found {len(visits)} visits")
    print(f"Writing to: {dest_db}")

    new_places = 0
    new_visits = 0
    skipped_places = 0
    skipped_visits = 0

    for i, visit in enumerate(visits):
        if not writer.place_exists(visit.url):
            place_id = writer.add_place(visit.url, visit.title, visit.visit_time)
            new_places += 1
        else:
            place_id = writer.get_place_id(visit.url)
            skipped_places += 1

        if not writer.visit_exists(place_id, visit.visit_time):
            added = writer.add_visit(place_id, visit.visit_time, visit.transition)
            if added:
                new_visits += 1
                writer.update_place_visit_count(visit.url, visit.visit_time)
            else:
                skipped_visits += 1
        else:
            skipped_visits += 1

        if (i + 1) % commit_every == 0:
            writer.commit()
            print(f"  Progress: {i + 1}/{len(visits)} visits processed")

    writer.commit()
    writer.close()

    print(f"\nSummary:")
    print(f"  New places (URLs): {new_places}")
    print(f"  New visits:        {new_visits}")
    print(f"  Skipped places:    {skipped_places}")
    print(f"  Skipped visits:    {skipped_visits}")
    print(f"  Total processed:   {len(visits)} visits")

    return new_places, new_visits


def chromium_to_firefox(
    source_db: str,
    dest_db: str,
    include_hidden: bool = False,
    commit_every: int = 500,
):
    writer = FirefoxWriter(dest_db)
    return _run_sync(
        "Chromium", read_chromium, writer,
        source_db, dest_db, include_hidden, commit_every,
    )


def firefox_to_chromium(
    source_db: str,
    dest_db: str,
    include_hidden: bool = False,
    commit_every: int = 500,
):
    writer = ChromiumWriter(dest_db)
    return _run_sync(
        "Firefox", read_firefox, writer,
        source_db, dest_db, include_hidden, commit_every,
    )


def chromium_to_chromium(
    source_db: str,
    dest_db: str,
    include_hidden: bool = False,
    commit_every: int = 500,
):
    writer = ChromiumWriter(dest_db)
    return _run_sync(
        "Chromium", read_chromium, writer,
        source_db, dest_db, include_hidden, commit_every,
    )


def firefox_to_firefox(
    source_db: str,
    dest_db: str,
    include_hidden: bool = False,
    commit_every: int = 500,
):
    writer = FirefoxWriter(dest_db)
    return _run_sync(
        "Firefox", read_firefox, writer,
        source_db, dest_db, include_hidden, commit_every,
    )
