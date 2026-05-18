#!/usr/bin/env python3
"""SGB -> STIX 2.1 indicator donusum yardimcilari.

Eskiden scripts/export.py icinde yasiyordu; SIEM paketleri (QRadar/Splunk)
kaldirildi ama TAXII servisi (build_taxii.py) ayni STIX semasini kullaniyor.
Bu modul yalniz TAXII'nin ihtiyac duydugu sabit ve fonksiyonlari icerir.
"""
from __future__ import annotations

import sqlite3
import uuid

# Deterministik STIX indicator id icin namespace (uuid5).
# Sabit: ayni SGB ID hep ayni STIX indicator id'sine donusur.
STIX_NS = uuid.UUID("c0ffee00-5664-4b1d-9c1d-5b00b50000d1")

SGB_IDENTITY_ID = "identity--" + str(
    uuid.uuid5(STIX_NS, "sgb-siber-guvenlik-baskanligi")
)

SOURCE_CONFIDENCE = {
    "US": 85,  # TR-CERT (eski USOM)
    "SB": 85,  # SGB
    "SO": 70,  # SOME/CERT
    "RS": 60,  # RSA
    "IH": 40,  # Ihbar
}

CT_TO_INDICATOR_TYPES = {
    "PH": ["malicious-activity"],
    "BC": ["malicious-activity"],
    "AC": ["malicious-activity"],
    "EK": ["malicious-activity"],
    "MF": ["malicious-activity"],
    "MM": ["malicious-activity"],
    "MC": ["malicious-activity"],
    "OT": ["unknown"],
}

CT_LABELS = {
    "PH": "phishing",
    "BC": "botnet-c2",
    "AC": "apt-c2",
    "EK": "exploit-kit",
    "MF": "malware-download",
    "MM": "mining",
    "MC": "mobile-c2",
    "OT": "other",
}
DESC_LABELS = {
    "PH": "phishing",
    "MD": "malware-distribution-domain",
    "MI": "malware-distribution-ip",
    "MU": "malware-distribution-url",
    "MC": "malware-command-center",
    "BP": "financial-phishing",
    "CA": "cyber-attack",
}


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _stix_pattern(typ: str, value: str) -> str | None:
    if typ == "domain":
        return f"[domain-name:value = '{_esc(value)}']"
    if typ == "url":
        return f"[url:value = '{_esc(value)}']"
    if typ == "ip":
        return f"[ipv4-addr:value = '{_esc(value)}']"
    if typ == "ip6":
        return f"[ipv6-addr:value = '{_esc(value)}']"
    if typ == "ip6net":
        # STIX'te tek bir IPv6 range standardi yok; ipv6-addr value CIDR ile
        # gozlemcilerin cogu tarafindan kabul ediliyor.
        return f"[ipv6-addr:value = '{_esc(value)}']"
    return None


def _indicator_id(sgb_id: int) -> str:
    return "indicator--" + str(uuid.uuid5(STIX_NS, f"sgb:{sgb_id}"))


def _identity_object() -> dict:
    return {
        "type": "identity",
        "spec_version": "2.1",
        "id": SGB_IDENTITY_ID,
        "created": "2020-01-01T00:00:00.000Z",
        "modified": "2020-01-01T00:00:00.000Z",
        "name": "Siber Guvenlik Baskanligi (SGB)",
        "identity_class": "organization",
        "contact_information": "https://siberguvenlik.gov.tr",
    }


def _to_stix_indicator(row: sqlite3.Row) -> dict | None:
    pattern = _stix_pattern(row["type"], row["value_clean"])
    if pattern is None:
        return None
    ct = row["connectiontype"]
    cat = row["category"]
    src = row["source"]
    labels = []
    if ct and ct in CT_LABELS:
        labels.append(CT_LABELS[ct])
    if cat and cat in DESC_LABELS and DESC_LABELS[cat] not in labels:
        labels.append(DESC_LABELS[cat])
    if not labels:
        labels = ["malicious-activity"]

    valid_from = (row["api_date"] or row["first_seen_utc"] or "").replace(" ", "T")
    if valid_from and not valid_from.endswith("Z") and "+" not in valid_from[10:]:
        valid_from = valid_from + "Z"

    return {
        "type": "indicator",
        "spec_version": "2.1",
        "id": _indicator_id(row["id"]),
        "created_by_ref": SGB_IDENTITY_ID,
        "created": (row["first_seen_utc"] or "").replace("+00:00", "Z"),
        "modified": (row["last_seen_utc"] or "").replace("+00:00", "Z"),
        "name": f"SGB {row['type']} indicator #{row['id']}",
        "pattern": pattern,
        "pattern_type": "stix",
        "pattern_version": "2.1",
        "valid_from": valid_from,
        "indicator_types": CT_TO_INDICATOR_TYPES.get(ct or "OT", ["malicious-activity"]),
        "labels": labels,
        "confidence": SOURCE_CONFIDENCE.get(src or "", 50),
        "external_references": [
            {
                "source_name": "sgb",
                "external_id": str(row["id"]),
                "url": "https://siberguvenlik.gov.tr",
            }
        ],
        "x_sgb_id": row["id"],
        "x_sgb_type": row["type"],
        "x_sgb_value": row["value_clean"],
        "x_sgb_connectiontype": ct,
        "x_sgb_description": cat,
        "x_sgb_source": src,
        "x_sgb_criticality": row["criticality_level"],
        "x_sgb_api_date": row["api_date"],
    }
