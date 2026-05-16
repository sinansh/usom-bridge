# UC-OT-001 — Any SGB "Other" category match (informational baseline)

| Alan          | Deger |
|---------------|-------|
| ID            | UC-OT-001 |
| MITRE         | (kategori belirsiz) |
| CT            | OT |
| Severity base | 3 |
| Data sources  | Tum kaynaklar (genis kapsam) |
| Reference     | `SGB_OT_IP`, `SGB_OT_DOMAIN`, `SGB_OT_URL` |

## Detection logic

`connectiontype=OT` SGB tarafinda sinifi tam belli olmayan indicator'lardir.
Bu rule offense **acmaz** — sadece event'a log atar ve `SGB_OT_MATCHES`
counter'ina ekler. Aggregated trend bir CT'ye kayarsa (orn. OT'nin %30'u
ayni asset'ten geliyor) ayri review rule'u tetiklenir.

## QRadar

- Event Rule with `Magnitude = 1` (do NOT create offense)
- Action: log only + add to `SGB_OT_OBSERVED` (24h TTL)

## Splunk

- Saved search: `SGB - UC-OT-001 - OT baseline (info)`
- enableSched=1, alert_type=number of events > 100 / hour (anomaly threshold)

## False positives

- Cogu match zaten informational; FP kavrami burada gecerli degil.
- Tehlike: feed'in OT bucket'i buyurse alarm gurultusu artar -> threshold ayarini SGB delta'larin sonrasi haftalik incele
