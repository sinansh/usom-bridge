"""
SGB indicator + catalog veritabani katmani (SQLite).

Tek dosya: state/sgb.db. Idempotent upsert; full sync sonrasi reconcile ile
silinen kayitlar removed_at_utc damgalanir. Mevcut docs/*-list.txt akisini
bozmaz - paralel yazim icin tasarlandi.

Schema notu: API'deki 'desc' alani internal olarak 'category' kolonunda tutulur
(SQL keyword cakismasini onlemek + kisalik). Bu kolonun lookup degerleri
catalogs tablosunda kind='description' altinda durur (endpoint:
/api/address-description/index, SGB taksonomisi: PH/MD/MI/MU/MC/BP/CA).
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SCHEMA_VERSION = 2

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS indicators (
    id                INTEGER PRIMARY KEY,
    type              TEXT NOT NULL,
    value_raw         TEXT NOT NULL,
    value_clean       TEXT,
    valid             INTEGER NOT NULL DEFAULT 0,
    category          TEXT,
    connectiontype    TEXT,
    source            TEXT,
    criticality_level INTEGER,
    api_date          TEXT,
    first_seen_utc    TEXT NOT NULL,
    last_seen_utc     TEXT NOT NULL,
    last_changed_utc  TEXT,
    removed_at_utc    TEXT
);
CREATE INDEX IF NOT EXISTS idx_ind_type    ON indicators(type);
CREATE INDEX IF NOT EXISTS idx_ind_ct      ON indicators(connectiontype);
CREATE INDEX IF NOT EXISTS idx_ind_cat     ON indicators(category);
CREATE INDEX IF NOT EXISTS idx_ind_crit    ON indicators(criticality_level);
CREATE INDEX IF NOT EXISTS idx_ind_src     ON indicators(source);
CREATE INDEX IF NOT EXISTS idx_ind_removed ON indicators(removed_at_utc);
CREATE INDEX IF NOT EXISTS idx_ind_type_valid ON indicators(type, valid, removed_at_utc);

CREATE TABLE IF NOT EXISTS catalogs (
    kind        TEXT NOT NULL,
    code        TEXT NOT NULL,
    tr_title    TEXT,
    en_title    TEXT,
    tr_desc     TEXT,
    en_desc     TEXT,
    fetched_utc TEXT NOT NULL,
    PRIMARY KEY (kind, code)
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    mode        TEXT,
    started_utc TEXT,
    ended_utc   TEXT,
    ok          INTEGER,
    counts_json TEXT,
    error       TEXT
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path(root: Path) -> Path:
    return root / "state" / "sgb.db"


def connect(root: Path) -> sqlite3.Connection:
    p = db_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)
    _migrate(conn)
    conn.execute(
        "INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Sema migration'lari. CREATE TABLE IF NOT EXISTS yeni kurulumlari
    halleder; bu fonksiyon eski DB'leri ileri tasir.
    """
    cols = {row[1] for row in conn.execute("PRAGMA table_info(indicators)")}
    if "last_changed_utc" not in cols:
        # schema_version 1 -> 2: STIX 'modified' icin stabil timestamp.
        # Mevcut kayitlar icin first_seen_utc ile baslatiriz; ilk smart upsert'te
        # gercek degisiklik varsa bumplar.
        conn.execute("ALTER TABLE indicators ADD COLUMN last_changed_utc TEXT")
        conn.execute(
            "UPDATE indicators SET last_changed_utc = first_seen_utc "
            "WHERE last_changed_utc IS NULL"
        )


def upsert_indicators(
    conn: sqlite3.Connection,
    records: Iterable[dict],
    typ: str,
    clean_fn,
    valid_fn,
) -> tuple[int, int, int]:
    """Bir sayfa kayit'i upsert eder.

    Donus: (inserted, updated, max_id_in_batch).
    first_seen_utc yalniz INSERT'te yazilir; last_seen_utc her run'da yenilenir;
    removed_at_utc gorulen kayitta NULL'a cekilir (yeniden aktiflesme destegi).
    """
    now = _now_utc()
    inserted = 0
    updated = 0
    max_id = 0
    cur = conn.cursor()
    for rec in records:
        try:
            rid = int(rec.get("id"))
        except (TypeError, ValueError):
            continue
        if rid > max_id:
            max_id = rid
        raw = rec.get("url") or ""
        cleaned = clean_fn(raw, typ)
        is_valid = 1 if (cleaned and valid_fn(cleaned, typ)) else 0
        crit = rec.get("criticality_level")
        try:
            crit = int(crit) if crit is not None else None
        except (TypeError, ValueError):
            crit = None
        params = (
            rid,
            typ,
            raw,
            cleaned or None,
            is_valid,
            rec.get("desc"),
            rec.get("connectiontype"),
            rec.get("source"),
            crit,
            rec.get("date"),
            now,  # first_seen (only used on INSERT)
            now,  # last_seen
            now,  # last_changed (INSERT'te now; UPDATE'te asagidaki CASE karar verir)
        )
        # SQLite UPSERT: yeni kayitta first_seen=last_changed=now; mevcut kayitta
        # first_seen KORUNUR, last_seen her zaman yenilenir, last_changed YALNIZ
        # anlamli alan degistiyse bumplar (STIX 'modified' stabilitesi icin).
        # Bu sayede saatlik full sync'te degismeyen kayitlarin STIX cikti'si
        # byte-identical kalir -> git diff sifir.
        cur.execute(
            """
            INSERT INTO indicators(
                id, type, value_raw, value_clean, valid,
                category, connectiontype, source, criticality_level,
                api_date, first_seen_utc, last_seen_utc, last_changed_utc
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                last_changed_utc = CASE
                    WHEN COALESCE(indicators.value_clean,'')       != COALESCE(excluded.value_clean,'')
                      OR COALESCE(indicators.category,'')          != COALESCE(excluded.category,'')
                      OR COALESCE(indicators.connectiontype,'')    != COALESCE(excluded.connectiontype,'')
                      OR COALESCE(indicators.source,'')            != COALESCE(excluded.source,'')
                      OR COALESCE(indicators.criticality_level,-1) != COALESCE(excluded.criticality_level,-1)
                      OR COALESCE(indicators.api_date,'')          != COALESCE(excluded.api_date,'')
                      OR COALESCE(indicators.valid,0)              != COALESCE(excluded.valid,0)
                      OR indicators.removed_at_utc IS NOT NULL
                    THEN excluded.last_seen_utc
                    ELSE indicators.last_changed_utc
                END,
                type              = excluded.type,
                value_raw         = excluded.value_raw,
                value_clean       = excluded.value_clean,
                valid             = excluded.valid,
                category          = excluded.category,
                connectiontype    = excluded.connectiontype,
                source            = excluded.source,
                criticality_level = excluded.criticality_level,
                api_date          = excluded.api_date,
                last_seen_utc     = excluded.last_seen_utc,
                removed_at_utc    = NULL
            """,
            params,
        )
        if cur.rowcount == 1:
            # SQLite UPSERT rowcount=1 hem insert hem update icin doner;
            # ayrimi changes() ile yapmiyoruz, toplami "touched" sayariz.
            updated += 1
    conn.commit()
    # inserted/updated ayrimi onemli degil; cagiri tarafinda toplam "touched"
    # yeterli. Ileride istenirse changes() ile ayirabiliriz.
    return (0, updated, max_id)


def mark_removed_by_cutoff(conn: sqlite3.Connection, typ: str, cutoff_utc: str) -> int:
    """Full sync reconcile: cutoff_utc'den once last_seen olan ve henuz removed
    olmayan kayitlari damgalar. Cutoff = full run'in baslangic zamani.

    Resume-safe: yarida kesilip devam eden full sync'lerde de calisir, cunku
    full sync'in basinda upsert edilmemis tum ID'ler cutoff'tan eski kalir.
    """
    now = _now_utc()
    cur = conn.execute(
        """
        UPDATE indicators
           SET removed_at_utc = ?
         WHERE type = ?
           AND removed_at_utc IS NULL
           AND last_seen_utc < ?
        """,
        (now, typ, cutoff_utc),
    )
    affected = cur.rowcount
    conn.commit()
    return affected


def upsert_catalog(conn: sqlite3.Connection, kind: str, models: Iterable[dict]) -> int:
    now = _now_utc()
    cur = conn.cursor()
    n = 0
    for m in models:
        cur.execute(
            """
            INSERT INTO catalogs(kind, code, tr_title, en_title, tr_desc, en_desc, fetched_utc)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(kind, code) DO UPDATE SET
                tr_title    = excluded.tr_title,
                en_title    = excluded.en_title,
                tr_desc     = excluded.tr_desc,
                en_desc     = excluded.en_desc,
                fetched_utc = excluded.fetched_utc
            """,
            (
                kind,
                m.get("id"),
                m.get("tr_title"),
                m.get("en_title"),
                m.get("tr_desc"),
                m.get("en_desc"),
                now,
            ),
        )
        n += 1
    conn.commit()
    return n


def start_run(conn: sqlite3.Connection, mode: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sync_runs(mode, started_utc, ok) VALUES(?,?,0)",
        (mode, _now_utc()),
    )
    conn.commit()
    return cur.lastrowid


def finish_run(
    conn: sqlite3.Connection,
    run_id: int,
    ok: bool,
    counts: dict | None = None,
    error: str | None = None,
) -> None:
    conn.execute(
        "UPDATE sync_runs SET ended_utc=?, ok=?, counts_json=?, error=? WHERE id=?",
        (_now_utc(), 1 if ok else 0, json.dumps(counts) if counts else None, error, run_id),
    )
    conn.commit()


def counts_by_type(conn: sqlite3.Connection) -> dict[str, int]:
    cur = conn.execute(
        """
        SELECT type, COUNT(*)
          FROM indicators
         WHERE removed_at_utc IS NULL AND valid = 1
         GROUP BY type
        """
    )
    return {row[0]: row[1] for row in cur.fetchall()}
