#!/usr/bin/env python3
"""
SGB QRadar Pack Builder - SQLite'tan QRadar reference set + map CSV'lerini uretir.

Cikti: siem/qradar/out/
  reference_sets/SGB_<CT>_<TYPE>.csv   Tek sutun (value). UI 'Import' icin.
  reference_maps/SGB_<TYPE>_MAP.csv    key,value -> value: "CT|DESC|CRIT|SRC"
  manifest.json                         Tum dosya/checksum/count.

Bu CSV'ler ayni zamanda push_to_qradar.py tarafindan REST API'ye gonderilir.
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
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

__version__ = "1.0.0"

_ROOT_OVERRIDE = os.environ.get("SGB_BRIDGE_ROOT")
ROOT = Path(_ROOT_OVERRIDE) if _ROOT_OVERRIDE else Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "siem" / "qradar" / "out"

# QRadar reference set isim mapping:
#   type -> QRadar element type
TYPE_TO_QRADAR_ELEMENT = {
    "domain":  ("DOMAIN",  "ALN"),
    "url":     ("URL",     "ALN"),
    "ip":      ("IP",      "IP"),
    "ip6":     ("IP6",     "ALN"),  # QRadar IPv6 ALN olarak tutmak en saglikli
    "ip6net":  ("IP6NET",  "ALN"),
}

# Map isimleri (type basina tek map)
TYPE_TO_MAP = {
    "domain":  "SGB_DOMAIN_MAP",
    "url":     "SGB_URL_MAP",
    "ip":      "SGB_IP_MAP",
    "ip6":     "SGB_IP6_MAP",
    "ip6net":  "SGB_IP6NET_MAP",
}

# Reference set TTL onerisi (push script kullaniyor)
DEFAULT_TTL_HOURS = 25

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("pack")


def open_db_readonly() -> sqlite3.Connection:
    p = ROOT / "state" / "sgb.db"
    if not p.exists():
        raise SystemExit(f"DB bulunamadi: {p}")
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def clean_dir(d: Path) -> None:
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[list[str]], header: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        if header:
            w.writerow(header)
        for row in rows:
            w.writerow(row)
    tmp.replace(path)


def build_reference_sets(conn: sqlite3.Connection) -> dict[str, dict]:
    """Connectiontype x type kombinasyonu basina set."""
    out: dict[tuple[str, str], list[str]] = defaultdict(list)
    cur = conn.execute(
        """
        SELECT DISTINCT type, connectiontype, value_clean
          FROM indicators
         WHERE removed_at_utc IS NULL
           AND valid = 1
           AND connectiontype IS NOT NULL
           AND value_clean IS NOT NULL
         ORDER BY type, connectiontype, value_clean
        """
    )
    for row in cur:
        out[(row["connectiontype"], row["type"])].append(row["value_clean"])

    sets_meta: dict[str, dict] = {}
    set_dir = OUT_DIR / "reference_sets"
    for (ct, typ), values in sorted(out.items()):
        type_label, element_type = TYPE_TO_QRADAR_ELEMENT[typ]
        name = f"SGB_{ct.upper()}_{type_label}"
        path = set_dir / f"{name}.csv"
        # QRadar UI Import: tek sutun, header'siz CSV.
        write_csv(path, [[v] for v in values])
        sets_meta[name] = {
            "path": str(path.relative_to(OUT_DIR)).replace("\\", "/"),
            "element_type": element_type,
            "connectiontype": ct,
            "indicator_type": typ,
            "count": len(values),
            "ttl_hours": DEFAULT_TTL_HOURS,
        }
        log.info(f"set {name}: {len(values)} kayit")
    return sets_meta


def build_reference_maps(conn: sqlite3.Connection) -> dict[str, dict]:
    """Type basina tek map: value -> CT|DESC|CRIT|SRC."""
    maps: dict[str, dict[str, str]] = {typ: {} for typ in TYPE_TO_MAP}
    cur = conn.execute(
        """
        SELECT id, type, value_clean, connectiontype, category, criticality_level, source
          FROM indicators
         WHERE removed_at_utc IS NULL
           AND valid = 1
           AND value_clean IS NOT NULL
         ORDER BY type, value_clean
        """
    )
    for row in cur:
        typ = row["type"]
        if typ not in maps:
            continue
        # Ayni key tekrar gelirse: en yuksek criticality'i kazandir.
        composite = "|".join([
            row["connectiontype"] or "OT",
            row["category"] or "",
            str(row["criticality_level"] if row["criticality_level"] is not None else ""),
            row["source"] or "",
        ])
        existing = maps[typ].get(row["value_clean"])
        if existing is None:
            maps[typ][row["value_clean"]] = composite
        else:
            # Tie-break: daha yuksek criticality_level kazansin
            try:
                old_crit = int(existing.split("|")[2] or 0)
            except ValueError:
                old_crit = 0
            new_crit = row["criticality_level"] or 0
            if new_crit > old_crit:
                maps[typ][row["value_clean"]] = composite

    maps_meta: dict[str, dict] = {}
    map_dir = OUT_DIR / "reference_maps"
    for typ, kv in maps.items():
        name = TYPE_TO_MAP[typ]
        path = map_dir / f"{name}.csv"
        # Map CSV: key,value. QRadar UI Import: 2 sutun, header'siz.
        write_csv(path, [[k, v] for k, v in sorted(kv.items())])
        type_label, element_type = TYPE_TO_QRADAR_ELEMENT[typ]
        maps_meta[name] = {
            "path": str(path.relative_to(OUT_DIR)).replace("\\", "/"),
            "indicator_type": typ,
            "key_element_type": element_type,
            "value_label": "CT|DESC|CRIT|SRC",
            "count": len(kv),
            "ttl_hours": DEFAULT_TTL_HOURS,
        }
        log.info(f"map {name}: {len(kv)} kayit")
    return maps_meta


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(sets_meta: dict, maps_meta: dict) -> None:
    files = []
    for p in sorted(OUT_DIR.rglob("*")):
        if p.is_file() and p.name != "manifest.json":
            files.append({
                "path": str(p.relative_to(OUT_DIR)).replace("\\", "/"),
                "size_bytes": p.stat().st_size,
                "sha256": sha256(p),
            })
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "builder_version": __version__,
        "default_ttl_hours": DEFAULT_TTL_HOURS,
        "reference_sets": sets_meta,
        "reference_maps": maps_meta,
        "files": files,
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    argparse.ArgumentParser().parse_args()
    log.info(f"== QRadar pack build (v{__version__}) ==")
    clean_dir(OUT_DIR)
    conn = open_db_readonly()
    try:
        sets_meta = build_reference_sets(conn)
        maps_meta = build_reference_maps(conn)
    finally:
        conn.close()
    write_manifest(sets_meta, maps_meta)
    log.info(
        f"OK: {len(sets_meta)} reference set + {len(maps_meta)} reference map "
        f"-> {OUT_DIR.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
