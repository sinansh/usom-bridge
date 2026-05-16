# UC-AC-002 — Single asset, 3+ APT C&C matches in 30 minutes

| Alan          | Deger |
|---------------|-------|
| ID            | UC-AC-002 |
| MITRE         | TA0011, TA0001 (Initial Access / C2 onayi) |
| CT            | AC (aggregate) |
| Severity base | 10 (lockdown trigger) |
| Data sources  | Tum (UC-AC-001'in alt seti) |
| Reference     | `SGB_AC_IP`, `SGB_AC_DOMAIN`, `SGB_AC_URL` |
| Response      | PB-AC-002 (immediate host isolation) |

## Detection logic

UC-AC-001 her bir match icin alarm uretir; bu meta-rule **ayni asset** uzerinde
30 dakika icinde 3+ **distinct** AC indicator'i match ederse tetiklenir. Tek
match false positive olabilir (analyst test, threat hunting), ama 3+ ardisik
hemen hemen kesin compromise sinyalidir.

## QRadar

- Common Rule (aggregator): `when these rules match: UC-AC-001`
- Aggregation: `at least 3 times in 30 minutes with same source IP and different "SGB Indicator Value"`
- Action: severity 10, dispatch "SGB APT Confirmed", trigger SOAR host isolation playbook

## Splunk

- Saved search: `SGB - UC-AC-002 - APT confirmed (3+ matches)`
- `| stats dc(sgb_match_type, ...) AS distinct_matches by src_ip | where distinct_matches >= 3`

## False positives

- SOC sandbox/analyst host -> exception list (dedicated source asset group)
- Vulnerability scanner outbound traffic -> exception
