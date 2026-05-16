# UC-MM-001 — Outbound to SGB mining indicator

| Alan          | Deger |
|---------------|-------|
| ID            | UC-MM-001 |
| MITRE         | TA0040 / T1496 (Resource Hijacking) |
| CT            | MM |
| Severity base | 3 (policy/perf) |
| Data sources  | Firewall, NetFlow, Proxy, DNS |
| Reference     | `SGB_MM_IP`, `SGB_MM_DOMAIN`, `SGB_IP_MAP` |

## Detection logic

Cryptomining pool / wallet host'lara bagantilar. Cogu zaman APT degil
"unauthorized resource usage" - bu yuzden severity 3, ama infrastructure
abuse yine de IR ticket gerektirir. Sik sik containerized workload veya
compromised vendor library iceriyor.

## QRadar

- Event/Flow Rule: `dest_ip in SGB_MM_IP OR DNS query in SGB_MM_DOMAIN`
- Action: severity 3, add to `SGB_MINING_HOSTS`, weekly summary report

## Splunk

- Saved search: `SGB - UC-MM-001 - Mining pool outbound`
- Lookup ile dest_ip + query

## False positives

- IT admin'in test/dev kullaniminda crypto wallet -> exception
- Browser extension'larda dolayli mining (CoinHive vb. block edilmiyorsa) -> kullaniciya bilgilendirme yeterli
