import sqlite3
import uuid
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

WK_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# Chromium transition qualifier for top-level navigations
CHAIN_QUALIFIER = 0x30000000

# Chromium core transition → Firefox visit_type
CR_TO_FX = {
    0: 1,  # LINK       → TRANSITION_LINK
    1: 2,  # TYPED      → TRANSITION_TYPED
    2: 3,  # BOOKMARK   → TRANSITION_BOOKMARK
    4: 1,  # SUBFRAME   → TRANSITION_LINK
    5: 5,  # GENERATED  → TRANSITION_REDIRECT
    6: 1,  # AUTO_TOP   → TRANSITION_LINK
    7: 1,  # FORM       → TRANSITION_LINK
    9: 2,  # KEYWORD    → TRANSITION_TYPED
}

# Firefox visit_type → Chromium core transition
FX_TO_CR = {
    1: 0,  # TRANSITION_LINK   → LINK
    2: 1,  # TRANSITION_TYPED  → TYPED
    3: 2,  # TRANSITION_BOOKMARK → AUTO_BOOKMARK
    5: 5,  # TRANSITION_REDIRECT_PERMANENT → GENERATED
    6: 5,  # TRANSITION_REDIRECT_TEMPORARY → GENERATED
}

# Visit types to skip when reading source
SKIP_FX_TYPES = {4, 7, 8, 9}   # EMBED, DOWNLOAD, FRAMED_LINK, RELOAD
SKIP_CR_CORES = {3, 8}         # AUTO_SUBFRAME, RELOAD


@dataclass
class Visit:
    url: str
    title: str | None
    visit_time: datetime
    transition: int
    from_visit: int | None
    visit_duration: int


def chromium_time_to_datetime(us: int) -> datetime:
    return WK_EPOCH + timedelta(microseconds=us)


def datetime_to_chromium_time(dt: datetime) -> int:
    delta = dt - WK_EPOCH
    return delta.days * 86400 * 1_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def firefox_time_to_datetime(us: int) -> datetime:
    return UNIX_EPOCH + timedelta(microseconds=us)


def datetime_to_firefox_time(dt: datetime) -> int:
    delta = dt - UNIX_EPOCH
    return delta.days * 86400 * 1_000_000 + delta.seconds * 1_000_000 + delta.microseconds


def fx_visit_type_to_cr_transition(fx_type: int) -> int | None:
    core = FX_TO_CR.get(fx_type)
    if core is None:
        return None
    return core | CHAIN_QUALIFIER


def cr_transition_to_fx_visit_type(cr_transition: int) -> int | None:
    core = cr_transition & 0xFF
    if core in SKIP_CR_CORES:
        return None
    return CR_TO_FX.get(core, 1)


def detect_db_type(path: str) -> str:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA query_only = ON")
    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    conn.close()
    if "moz_places" in tables and "moz_historyvisits" in tables:
        return "firefox"
    if "urls" in tables and "visits" in tables:
        return "chromium"
    raise ValueError(
        f"Cannot detect database type: {path}\n"
        "  Expected Firefox (moz_places/moz_historyvisits) "
        "or Chromium (urls/visits) schema"
    )


def extract_host(url: str) -> str:
    if "://" not in url:
        return ""
    without_scheme = url.split("://", 1)[1]
    return without_scheme.split("/")[0].split(":")[0]


def make_rev_host(host: str) -> str:
    return host[::-1] + "."


def make_guid() -> str:
    raw = uuid.uuid4().bytes
    return base64url_encode(raw[:9])


def base64url_encode(data: bytes) -> str:
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    result = []
    bits = 0
    bit_count = 0
    for byte in data:
        bits = (bits << 8) | byte
        bit_count += 8
        while bit_count >= 6:
            bit_count -= 6
            result.append(chars[(bits >> bit_count) & 0x3F])
    if bit_count > 0:
        result.append(chars[(bits << (6 - bit_count)) & 0x3F])
    return "".join(result)
