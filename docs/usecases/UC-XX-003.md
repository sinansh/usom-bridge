# UC-XX-003 — Org-wide criticality spike (avg criticality > 7 per hour)

| Alan          | Deger |
|---------------|-------|
| ID            | UC-XX-003 |
| MITRE         | (cross — emergent campaign indicator) |
| CT            | XX (meta) |
| Severity base | dinamik (avg criticality'e gore 7-10) |
| Data sources  | Tum SGB notable event'lari |
| Reference     | `SGB_*_MAP` (criticality alani) |

## Detection logic

Saatlik penceredeki tum SGB match'lerinin ortalama `criticality_level`'i 7'yi
asarsa: organizasyon SGB high-criticality dalgasinin altinda demek. Bu genelde
SGB tarafinda yeni kampanya yayini (ornek: yaygin oltalama dalgasi) ile
korelasyonludur. SOC manager'a gunluk degil saatlik dashboard refresh.

```
window = 1h
trigger: avg(criticality_level) > 7 AND count(matches) > 50
severity_out = ceil(avg(criticality)) capped at 10
```

## QRadar

- Anomaly Detection rule on custom property "SGB Criticality"
- AQL search scheduled / 1h, threshold action

## Splunk

- Saved search: `index=notable sgb_*`
- `| stats avg(criticality_level) AS avg_crit count by date_hour | where avg_crit > 7 AND count > 50`

## False positives

- Yeni rule deployment ilk gun gurultu yapar -> 24h grace window
- SGB feed quality issue (yanlislikla tum kayitlar crit=9 isaretlendi) -> SGB API audit script (`scripts/sync.py` log'larinda kontrol)
