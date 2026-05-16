# UC-MF-001 — Proxy download from SGB malware URL

| Alan          | Deger |
|---------------|-------|
| ID            | UC-MF-001 |
| MITRE         | TA0002 / T1105 (Ingress Tool Transfer) |
| CT            | MF |
| Severity base | 7 |
| Data sources  | Web proxy / SWG |
| Reference     | `SGB_MF_URL`, `SGB_MF_DOMAIN`, `SGB_URL_MAP` |

## Detection logic

HTTP GET/POST'la SGB MF URL'den dosya indirildi (status 200 + body bytes > 1KB).
Indirim != execution; severity 7 ama EDR koreligyonu (UC-MF-002) ile 9'a cikar.

## QRadar

- Event Rule on proxy log source type: `URL in SGB_MF_URL AND HTTP status in (200,206) AND bytes_received > 1024`
- Action: severity 7, add to `SGB_DOWNLOADED_MALWARE` set with src_ip + URL

## Splunk

- Saved search: `SGB - UC-MF-001 - Malware URL download`
- `... | where sgb_url_ct="MF" AND http_status IN (200,206) AND bytes_in > 1024`

## False positives

- Security research downloads (sandbox, malware DB) -> exception by source asset
- AV vendor pattern download URL'leri yanlislikla feed'de olabilir -> SOC review whitelist
