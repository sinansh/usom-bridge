#!/usr/bin/env python3
"""
SGB QRadar Pusher - build_pack.py'in urettigi pack'i QRadar'a yukler.

Endpoints (QRadar REST API):
  POST /api/reference_data/sets               -> set olustur (idempotent: 409 ise gec)
  POST /api/reference_data/sets/bulk_load/{n} -> JSON array of strings (merge)
  POST /api/reference_data/maps               -> map olustur
  POST /api/reference_data/maps/bulk_load/{n} -> JSON object {key: value}

Auth: SEC header (Admin > Authorized Services > Add Token).
TLS: --insecure ile self-signed sertifikalari kabul et (lab/poc).

Idempotency:
- Set/map yoksa olusturur (time_to_live verir).
- Mevcutsa atlar (HTTP 409); zaten bulk_load merge yapar.
- Stale entry'ler TTL ile dusupr; manuel purge yok (rule referansi bozulmasin).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import requests
import urllib3

__version__ = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("push")


def make_session(token: str, insecure: bool) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "SEC": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": f"sgb-qradar-pusher/{__version__}",
        # QRadar API versiyonu - 15.0+ stabil; gerekirse override edilebilir.
        "Version": "15.0",
    })
    if insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        s.verify = False
    return s


def ensure_set(s: requests.Session, host: str, name: str, element_type: str, ttl_hours: int) -> None:
    """Set yoksa olustur. Varsa 409 alip gec."""
    url = f"https://{host}/api/reference_data/sets"
    params = {
        "name": name,
        "element_type": element_type,
        "time_to_live": f"{ttl_hours} hours",
        "timeout_type": "LAST_SEEN",
    }
    r = s.post(url, params=params, timeout=60)
    if r.status_code in (200, 201):
        log.info(f"  + set olusturuldu: {name}")
    elif r.status_code == 409:
        log.debug(f"  = set mevcut: {name}")
    else:
        log.error(f"  ! set olusturma hatasi {name}: HTTP {r.status_code} {r.text[:200]}")
        r.raise_for_status()


def ensure_map(s: requests.Session, host: str, name: str, key_type: str, ttl_hours: int) -> None:
    url = f"https://{host}/api/reference_data/maps"
    params = {
        "name": name,
        "key_label": "indicator",
        "element_type": key_type,
        "time_to_live": f"{ttl_hours} hours",
        "timeout_type": "LAST_SEEN",
    }
    r = s.post(url, params=params, timeout=60)
    if r.status_code in (200, 201):
        log.info(f"  + map olusturuldu: {name}")
    elif r.status_code == 409:
        log.debug(f"  = map mevcut: {name}")
    else:
        log.error(f"  ! map olusturma hatasi {name}: HTTP {r.status_code} {r.text[:200]}")
        r.raise_for_status()


def bulk_load_set(s: requests.Session, host: str, name: str, values: list[str]) -> None:
    url = f"https://{host}/api/reference_data/sets/bulk_load/{name}"
    r = s.post(url, data=json.dumps(values), timeout=300)
    if r.status_code not in (200, 201):
        log.error(f"  ! bulk_load set {name}: HTTP {r.status_code} {r.text[:300]}")
        r.raise_for_status()
    log.info(f"  -> set {name}: {len(values)} value pushed")


def bulk_load_map(s: requests.Session, host: str, name: str, kv: dict[str, str]) -> None:
    url = f"https://{host}/api/reference_data/maps/bulk_load/{name}"
    r = s.post(url, data=json.dumps(kv), timeout=300)
    if r.status_code not in (200, 201):
        log.error(f"  ! bulk_load map {name}: HTTP {r.status_code} {r.text[:300]}")
        r.raise_for_status()
    log.info(f"  -> map {name}: {len(kv)} kv pushed")


def read_set_csv(path: Path) -> list[str]:
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def read_map_csv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        # QRadar map value virgul icerebilir; split sadece ilk virgulden.
        k, _, v = ln.partition(",")
        out[k.strip()] = v.strip()
    return out


def push(pack_dir: Path, host: str, token: str, insecure: bool, dry_run: bool, only: str | None) -> int:
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"manifest yok: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    s = make_session(token, insecure)

    sets = manifest.get("reference_sets") or {}
    maps = manifest.get("reference_maps") or {}

    if only:
        sets = {k: v for k, v in sets.items() if only in k}
        maps = {k: v for k, v in maps.items() if only in k}
        log.info(f"filter --only '{only}': {len(sets)} set + {len(maps)} map")

    total_set_rows = 0
    total_map_rows = 0
    t0 = time.time()

    log.info(f"== Reference Sets ({len(sets)}) ==")
    for name, meta in sorted(sets.items()):
        values = read_set_csv(pack_dir / meta["path"])
        log.info(f"[set] {name}: {len(values)} satir")
        if dry_run:
            continue
        ensure_set(s, host, name, meta["element_type"], meta["ttl_hours"])
        if values:
            bulk_load_set(s, host, name, values)
            total_set_rows += len(values)

    log.info(f"== Reference Maps ({len(maps)}) ==")
    for name, meta in sorted(maps.items()):
        kv = read_map_csv(pack_dir / meta["path"])
        log.info(f"[map] {name}: {len(kv)} satir")
        if dry_run:
            continue
        ensure_map(s, host, name, meta["key_element_type"], meta["ttl_hours"])
        if kv:
            bulk_load_map(s, host, name, kv)
            total_map_rows += len(kv)

    dt = time.time() - t0
    log.info(
        f"OK ({'DRY' if dry_run else 'LIVE'}): {total_set_rows} set rows, "
        f"{total_map_rows} map rows, {dt:.1f}s"
    )
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pack", default="siem/qradar/out", help="Pack dizini")
    p.add_argument("--host", default=None, help="QRadar host (env: SGB_QRADAR_HOST)")
    p.add_argument("--token", default=None, help="SEC token (env: SGB_QRADAR_TOKEN)")
    p.add_argument("--insecure", action="store_true", help="TLS dogrulamasini atla")
    p.add_argument("--dry-run", action="store_true", help="POST gondermez")
    p.add_argument("--only", default=None, help="Sadece isminde bu substring olanlari push et")
    args = p.parse_args()

    import os
    host = args.host or os.environ.get("SGB_QRADAR_HOST")
    token = args.token or os.environ.get("SGB_QRADAR_TOKEN")
    if not args.dry_run and (not host or not token):
        raise SystemExit("--host ve --token (veya SGB_QRADAR_HOST/SGB_QRADAR_TOKEN env) gerekli")

    pack_dir = Path(args.pack).resolve()
    return push(pack_dir, host or "dry", token or "dry", args.insecure, args.dry_run, args.only)


if __name__ == "__main__":
    sys.exit(main())
