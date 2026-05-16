# UC-BC-002 — DNS query to SGB Botnet C&C domain

| Alan          | Deger |
|---------------|-------|
| ID            | UC-BC-002 |
| MITRE         | TA0011 / T1071.004 (DNS C2) |
| CT            | BC |
| Severity base | 8 |
| Data sources  | DNS query logs |
| Reference     | `SGB_BC_DOMAIN`, `SGB_DOMAIN_MAP` |

## Detection logic

UC-BC-001 IP-based, bu rule domain-based. Bot operatorleri C2'yi sik degistirir;
domain feed'i fast-flux ve DGA-baz takibi icin daha guvenilir. Iki rule ayri
calismali, ayni asset 1 saat icinde her ikisini de hit ederse meta-rule
(UC-XX-001) tetiklenir.

## QRadar

- Event Rule: `SGB_BC_DOMAIN` set + DNS sourcetype filter
- Action: severity = 8 (+ criticality modifier), add src to `SGB_INFECTED_HOSTS`

## Splunk

- Macro: extend `sgb_botnet_outbound_search` icin DNS variant (`sgb_botnet_dns_search`)
- Lookup: `sgb_domain_lookup`

## False positives

- Security tooling (VirusTotal, URLscan) malware domain'leri legitimate query yapabilir -> SOC asset list exception
- Sinkhole DNS (Conficker sinkhole vb.) SGB feed'inde olabilir; sinkhole'a query "good news" sayilir, severity'yi 3'e indir
