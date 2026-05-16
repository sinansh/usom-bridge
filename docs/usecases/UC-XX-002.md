# UC-XX-002 — Asset re-infection: same indicator hit twice within 7 days

| Alan          | Deger |
|---------------|-------|
| ID            | UC-XX-002 |
| MITRE         | TA0003 (Persistence) — IR ineffectiveness signal |
| CT            | XX (meta) |
| Severity base | 7 |
| Data sources  | Tum |
| Reference     | `SGB_*` (herhangi bir indicator) |

## Detection logic

Ayni asset 7 gun icinde ayni indicator'a (tip + value) yeniden hit ettiyse:
- Onceki incident kapatildi ama remediation eksik kalmis
- Veya yeni infeksiyon ayni infrastructure'a bagandi (persist mechanism var)

Bu rule SOC operations metrigi olarak da kullanilir (re-infection rate).

## QRadar

- Reference Set: `SGB_ASSET_HIT_HISTORY` (key=asset|indicator, value=last_seen, TTL 7d)
- Rule: `when SGB match AND lookup hit returns existing -> escalate`

## Splunk

- Saved search: `index=notable sgb_*` 7d window
- `| stats dc(_time) AS hits count AS total values(sgb_ct) AS ct by src_ip sgb_indicator_value | where hits >= 2`

## False positives

- Cron-based scanner / monitoring repeat -> exception
- Kullanici cihazinda bookmark olarak kaydedilmis phishing link tekrar tikleniyor -> kullanici uyarisi + browser plugin
