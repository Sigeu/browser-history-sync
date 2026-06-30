import sqlite3
from .common import firefox_time_to_datetime, fx_visit_type_to_cr_transition, Visit, SKIP_FX_TYPES


def read_history(db_path: str, include_hidden: bool = False) -> list[Visit]:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA query_only = ON")
    conn.row_factory = sqlite3.Row

    hidden_filter = "" if include_hidden else "AND p.hidden = 0"

    rows = conn.execute(f"""
        SELECT p.url, p.title, p.hidden,
               v.visit_date, v.visit_type, v.from_visit
        FROM moz_historyvisits v
        JOIN moz_places p ON v.place_id = p.id
        WHERE v.visit_date IS NOT NULL {hidden_filter}
        ORDER BY v.visit_date ASC
    """).fetchall()

    visits: list[Visit] = []

    for row in rows:
        if not include_hidden and row["hidden"] != 0:
            continue

        fx_type = row["visit_type"]
        if fx_type in SKIP_FX_TYPES:
            continue

        cr_transition = fx_visit_type_to_cr_transition(fx_type)
        if cr_transition is None:
            continue

        from_visit: int | None = row["from_visit"]
        if from_visit == 0:
            from_visit = None

        visits.append(
            Visit(
                url=row["url"],
                title=row["title"],
                visit_time=firefox_time_to_datetime(row["visit_date"]),
                transition=cr_transition,
                from_visit=from_visit,
                visit_duration=0,
            )
        )

    conn.close()
    return visits
