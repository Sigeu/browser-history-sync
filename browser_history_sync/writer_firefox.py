import sqlite3
from datetime import datetime
from urllib.parse import urlparse
from .common import (
    extract_host,
    make_rev_host,
    make_guid,
    cr_transition_to_fx_visit_type,
    datetime_to_firefox_time,
)


class FirefoxWriter:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.cached_origins: dict[str, int] = {}
        self.cached_places: dict[str, int] = {}
        self.cached_visit_keys: set[tuple[int, int]] = set()
        self._load_cache()

    def _load_cache(self):
        for row in self.conn.execute(
            "SELECT id, prefix, host FROM moz_origins"
        ).fetchall():
            key = f"{row[1]}|{row[2]}"
            self.cached_origins[key] = row[0]

        for row in self.conn.execute(
            "SELECT id, url FROM moz_places"
        ).fetchall():
            self.cached_places[row[1]] = row[0]

        for row in self.conn.execute(
            "SELECT place_id, visit_date FROM moz_historyvisits"
        ).fetchall():
            self.cached_visit_keys.add((row[0], row[1]))

    def _get_or_create_origin(self, url: str) -> int:
        parsed = urlparse(url)
        prefix = f"{parsed.scheme}://"
        host = parsed.netloc.split(":")[0]
        key = f"{prefix}|{host}"

        if key in self.cached_origins:
            return self.cached_origins[key]

        oid = self.conn.execute(
            "INSERT INTO moz_origins (prefix, host, frecency, recalc_frecency, recalc_alt_frecency) "
            "VALUES (?, ?, 0, 1, 1)",
            (prefix, host),
        ).lastrowid
        self.cached_origins[key] = oid
        return oid

    def place_exists(self, url: str) -> bool:
        return url in self.cached_places

    def get_place_id(self, url: str) -> int | None:
        return self.cached_places.get(url)

    def add_place(
        self,
        url: str,
        title: str | None,
        visit_time: datetime,
    ) -> int:
        existing_id = self.cached_places.get(url)
        if existing_id is not None:
            return existing_id

        host = extract_host(url)
        rev_host = make_rev_host(host) if host else "."
        guid = make_guid()
        origin_id = self._get_or_create_origin(url)

        self.conn.execute(
            """INSERT INTO moz_places
               (url, title, rev_host, visit_count, hidden, typed, frecency,
                last_visit_date, guid, foreign_count, url_hash, origin_id,
                recalc_frecency, recalc_alt_frecency)
               VALUES (?, ?, ?, 0, 0, 0, 25, NULL, ?, 0, 0, ?, 1, 1)""",
            (url, title, rev_host, guid, origin_id),
        )
        place_id = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        self.cached_places[url] = place_id
        return place_id

    def visit_exists(self, place_id: int, visit_time: datetime) -> bool:
        fx_time = datetime_to_firefox_time(visit_time)
        return (place_id, fx_time) in self.cached_visit_keys

    def add_visit(
        self,
        place_id: int,
        visit_time: datetime,
        chromium_transition: int,
    ) -> bool:
        fx_time = datetime_to_firefox_time(visit_time)

        if (place_id, fx_time) in self.cached_visit_keys:
            return False

        visit_type = cr_transition_to_fx_visit_type(chromium_transition)
        if visit_type is None:
            return False

        self.conn.execute(
            """INSERT INTO moz_historyvisits
               (from_visit, place_id, visit_date, visit_type, session, source)
               VALUES (0, ?, ?, ?, 0, 0)""",
            (place_id, fx_time, visit_type),
        )
        self.cached_visit_keys.add((place_id, fx_time))
        return True

    def update_place_visit_count(self, url: str, last_visit_time: datetime):
        place_id = self.cached_places.get(url)
        if place_id is None:
            return

        fx_time = datetime_to_firefox_time(last_visit_time)
        self.conn.execute(
            """UPDATE moz_places
               SET visit_count = visit_count + 1,
                   last_visit_date = MAX(IFNULL(last_visit_date, 0), ?),
                   frecency = (visit_count + 1) * 100
               WHERE id = ?""",
            (fx_time, place_id),
        )

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        self.conn.close()
