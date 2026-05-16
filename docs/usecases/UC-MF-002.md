# UC-MF-002 — EDR fetched file from SGB malware host (composite)

| Alan          | Deger |
|---------------|-------|
| ID            | UC-MF-002 |
| MITRE         | TA0002 / T1105 + TA0005 (Defense Evasion) |
| CT            | MF (composite) |
| Severity base | 8 |
| Data sources  | EDR file-create / network telemetry + Proxy |
| Reference     | `SGB_MF_DOMAIN`, `SGB_MF_IP`, `SGB_MF_URL` |

## Detection logic

EDR'dan "file written by process" + ayni process network'te SGB MF host'una
bagandi. UC-MF-001'den daha guclu sinyal: dosyanin diske dustugu netlesti.
Otomatik EDR isolate trigger uygun.

## QRadar

- Event Rule on EDR sourcetype: `Process Network Connection` + `Destination Host in SGB_MF_DOMAIN` + within 60s `File Create` by same process_guid
- Action: severity 8, EDR isolate API call (SOAR), forensic snapshot

## Splunk

- Saved search join: `index=edr action=process_network` + `index=edr action=file_create` on process_guid, span 60s
- Lookup ile both sides enriched

## False positives

- Software update (Microsoft, Adobe) downloads -> trusted publisher exception
- Sandbox / detonation environment -> dedicated host group exception
