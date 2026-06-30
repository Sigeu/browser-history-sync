import sqlite3
from .common import chromium_time_to_datetime, Visit, SKIP_CR_CORES


def read_history(db_path: str, include_hidden: bool = False) -> list[Visit]:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA query_only = ON")
    conn.row_factory = sqlite3.Row

    hidden_filter = "" if include_hidden else "AND u.hidden = 0"

    rows = conn.execute(f"""
        SELECT u.url AS url_str, u.title, u.hidden,
               v.visit_time, v.transition, v.from_visit, v.visit_duration
        FROM visits v
        JOIN urls u ON v.url = u.id
        WHERE 1=1 {hidden_filter}
        ORDER BY v.visit_time ASC
    """).fetchall()

    visits: list[Visit] = []

    for row in rows:
        if not include_hidden and row["hidden"] != 0:
            continue

        core = row["transition"] & 0xFF
        if core in SKIP_CR_CORES:
            continue

        from_visit: int | None = row["from_visit"]
        if from_visit == 0:
            from_visit = None

        visits.append(
            Visit(
                url=row["url_str"],
                title=row["title"],
                visit_time=chromium_time_to_datetime(row["visit_time"]),
                transition=row["transition"],
                from_visit=from_visit,
                visit_duration=row["visit_duration"],
            )
        )

    conn.close()
    return visits
