#!/usr/bin/env python3
"""
SGB Splunk TA Builder - SQLite'tan lookup CSV'lerini uretir ve TA-sgb-threatintel
icin tarball paketler.

Cikti:
  siem/splunk/out/TA-sgb-threatintel/        (kopyalanmis + lookup'lar dolu)
  siem/splunk/out/TA-sgb-threatintel.tar.gz  (Splunk UI 'Install app from file')

Lookup schema (3 CSV icin de ayni):
  value,connectiontype,description,criticality_level,source,first_seen_utc
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

__version__ = "1.0.0"

_ROOT_OVERRIDE = os.environ.get("SGB_BRIDGE_ROOT")
ROOT = Path(_ROOT_OVERRIDE) if _ROOT_OVERRIDE else Path(__file__).resolve().parent.parent
TA_SRC = ROOT / "siem" / "splunk" / "TA-sgb-threatintel"
OUT_DIR = ROOT / "siem" / "splunk" / "out"
TA_OUT = OUT_DIR / "TA-sgb-threatintel"
TARBALL = OUT_DIR / "TA-sgb-threatintel.tar.gz"

LOOKUP_FIELDS = ["value", "connectiontype", "description",
                 "criticality_level", "source", "first_seen_utc"]

# type -> lookup CSV adi
TYPE_TO_LOOKUP = {
    "ip":     "sgb_ip.csv",
    "ip6":    "sgb_ip.csv",      # ayni CSV; key alani text
    "domain": "sgb_domain.csv",
    "url":    "sgb_url.csv",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("splunk-ta")


def open_db_readonly() -> sqlite3.Connection:
    p = ROOT / "state" / "sgb.db"
    if not p.exists():
        raise SystemExit(f"DB bulunamadi: {p}")
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def write_lookups(conn: sqlite3.Connection) -> dict[str, int]:
    """Type -> lookup CSV; ayni dosyaya yazan tipler birlestirilir.
    Tie-break: ayni value icin en yuksek criticality kazansin."""
    lookups_dir = TA_OUT / "lookups"
    lookups_dir.mkdir(parents=True, exist_ok=True)

    # value -> en iyi row (in-memory; max ~470K satir, sorun degil)
    by_lookup: dict[str, dict[str, tuple]] = {}

    cur = conn.execute(
        """
        SELECT type, value_clean, connectiontype, category,
               criticality_level, source, first_seen_utc
          FROM indicators
         WHERE removed_at_utc IS NULL AND valid = 1 AND value_clean IS NOT NULL
         ORDER BY type, value_clean
        """
    )
    for row in cur:
        target = TYPE_TO_LOOKUP.get(row["type"])
        if not target:
            continue
        table = by_lookup.setdefault(target, {})
        new_row = (
            row["value_clean"],
            row["connectiontype"] or "",
            row["category"] or "",
            row["criticality_level"] if row["criticality_level"] is not None else "",
            row["source"] or "",
            row["first_seen_utc"] or "",
        )
        existing = table.get(row["value_clean"])
        if existing is None:
            table[row["value_clean"]] = new_row
        else:
            old_crit = existing[3] if isinstance(existing[3], int) else -1
            new_crit = new_row[3] if isinstance(new_row[3], int) else -1
            if new_crit > old_crit:
                table[row["value_clean"]] = new_row

    counts: dict[str, int] = {}
    # Var olmayan lookup'larin bile bos dosyasini olustur (Splunk yoksa hata verir).
    for fname in set(TYPE_TO_LOOKUP.values()):
        path = lookups_dir / fname
        rows = list(by_lookup.get(fname, {}).values())
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8", newline="\n") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(LOOKUP_FIELDS)
            for r in rows:
                w.writerow(r)
        tmp.replace(path)
        counts[fname] = len(rows)
        log.info(f"lookup {fname}: {len(rows)} kayit")
    return counts


def copy_static() -> None:
    """TA_SRC -> TA_OUT (lookups disinda her sey)."""
    if TA_OUT.exists():
        shutil.rmtree(TA_OUT)
    shutil.copytree(TA_SRC, TA_OUT, ignore=shutil.ignore_patterns("lookups"))
    # Lookups dizini sonra olusur
    (TA_OUT / "README.md").write_text(_readme_content(), encoding="utf-8")


def _readme_content() -> str:
    return f"""TA-sgb-threatintel
==================

SGB (Siber Guvenlik Baskanligi) threat indicator lookups + correlation rules.
Generated: {datetime.now(timezone.utc).isoformat()}

Kurulum:
  splunk install app TA-sgb-threatintel.tar.gz
  splunk restart

Yenileme (saatlik / delta sonrasi):
  - Yeni tarball'i UI'dan 'Update' veya
  - sadece lookups/*.csv'leri $SPLUNK_HOME/etc/apps/TA-sgb-threatintel/lookups/
    altina rsync et (Splunk restart gerekmez).
"""


def make_tarball() -> Path:
    if TARBALL.exists():
        TARBALL.unlink()
    with tarfile.open(TARBALL, "w:gz") as tf:
        tf.add(TA_OUT, arcname=TA_OUT.name)
    return TARBALL


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(lookup_counts: dict[str, int]) -> None:
    files = []
    for p in sorted(TA_OUT.rglob("*")):
        if p.is_file():
            files.append({
                "path": str(p.relative_to(TA_OUT)).replace("\\", "/"),
                "size_bytes": p.stat().st_size,
            })
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "builder_version": __version__,
        "lookup_counts": lookup_counts,
        "tarball": {
            "path": str(TARBALL.relative_to(OUT_DIR)).replace("\\", "/"),
            "sha256": sha256(TARBALL),
            "size_bytes": TARBALL.stat().st_size,
        },
        "files": files,
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    argparse.ArgumentParser().parse_args()
    log.info(f"== Splunk TA build (v{__version__}) ==")
    if not TA_SRC.exists():
        raise SystemExit(f"TA source yok: {TA_SRC}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    copy_static()
    conn = open_db_readonly()
    try:
        lookup_counts = write_lookups(conn)
    finally:
        conn.close()

    tarball = make_tarball()
    write_manifest(lookup_counts)
    log.info(f"OK: lookups={lookup_counts}")
    log.info(f"tarball: {tarball.relative_to(ROOT)} ({tarball.stat().st_size/1e6:.2f}MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
