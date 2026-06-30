import sqlite3
from datetime import datetime
from .common import datetime_to_chromium_time


class ChromiumWriter:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode = DELETE")
        self.cached_urls: dict[str, int] = {}
        self.cached_visit_keys: set[tuple[int, int]] = set()
        self._load_cache()

    def _load_cache(self):
        for row in self.conn.execute("SELECT id, url FROM urls").fetchall():
            self.cached_urls[row[1]] = row[0]

        for row in self.conn.execute(
            "SELECT url, visit_time FROM visits"
        ).fetchall():
            self.cached_visit_keys.add((row[0], row[1]))

    def place_exists(self, url: str) -> bool:
        return url in self.cached_urls

    def get_place_id(self, url: str) -> int | None:
        return self.cached_urls.get(url)

    def add_place(self, url: str, title: str | None, visit_time: datetime) -> int:
        existing_id = self.cached_urls.get(url)
        if existing_id is not None:
            return existing_id

        cr_time = datetime_to_chromium_time(visit_time)
        self.conn.execute(
            """INSERT INTO urls
               (url, title, visit_count, typed_count, last_visit_time, hidden)
               VALUES (?, ?, 0, 0, ?, 0)""",
            (url, title, cr_time),
        )
        url_id = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        self.cached_urls[url] = url_id
        return url_id

    def visit_exists(self, url_id: int, visit_time: datetime) -> bool:
        cr_time = datetime_to_chromium_time(visit_time)
        return (url_id, cr_time) in self.cached_visit_keys

    def add_visit(
        self,
        url_id: int,
        visit_time: datetime,
        transition: int,
    ) -> bool:
        cr_time = datetime_to_chromium_time(visit_time)

        if (url_id, cr_time) in self.cached_visit_keys:
            return False

        self.conn.execute(
            """INSERT INTO visits
               (url, visit_time, from_visit, transition, visit_duration,
                incremented_omnibox_typed_score, is_known_to_sync)
               VALUES (?, ?, 0, ?, 0, 0, 1)""",
            (url_id, cr_time, transition),
        )
        self.cached_visit_keys.add((url_id, cr_time))
        return True

    def update_place_visit_count(self, url: str, last_visit_time: datetime):
        url_id = self.cached_urls.get(url)
        if url_id is None:
            return

        cr_time = datetime_to_chromium_time(last_visit_time)
        self.conn.execute(
            """UPDATE urls
               SET visit_count = visit_count + 1,
                   last_visit_time = MAX(IFNULL(last_visit_time, 0), ?)
               WHERE id = ?""",
            (cr_time, url_id),
        )

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
