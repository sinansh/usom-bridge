# UC-MM-002 — CPU spike + SGB MM indicator hit (composite)

| Alan          | Deger |
|---------------|-------|
| ID            | UC-MM-002 |
| MITRE         | TA0040 / T1496 |
| CT            | MM (composite) |
| Severity base | 5 (UC-MM-001'i upgrade eden composite) |
| Data sources  | EDR perf telemetry / OS metrics + SGB MM hit (UC-MM-001) |
| Reference     | `SGB_MM_IP`, `SGB_MM_DOMAIN` |

## Detection logic

UC-MM-001 alone is policy-grade; composite mantik:
- 5 dk icinde host'tan SGB_MM_* hit
- Ayni hostta son 1 saatte CPU avg > %85 (vs baseline)
- Network egress'in %20'sinden fazlasi mining destination'a

Composite match = aktif mining process kesinligi yuksek.

## QRadar

- Common Rule combining UC-MM-001 + EDR custom event "high CPU asset"
- Time correlation: 1 hour window, same asset

## Splunk

- Saved search: join EDR perf + sgb_dest_ct="MM"
- `| stats values(perf.cpu_pct) AS cpu by host | where cpu > 85`

## False positives

- ML training, video render -> exception by asset role
- Build server CPU spikes -> exception
