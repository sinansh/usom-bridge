# UC-EK-001 — HTTP request to SGB Exploit Kit URL

| Alan          | Deger |
|---------------|-------|
| ID            | UC-EK-001 |
| MITRE         | TA0002 / T1203 (Exploitation for Client Execution) |
| CT            | EK |
| Severity base | 8 |
| Data sources  | Web proxy / SWG, browser EDR |
| Reference     | `SGB_EK_URL`, `SGB_EK_DOMAIN`, `SGB_URL_MAP` |

## Detection logic

EK landing page'lere request. Useragent + referrer kombinasyonu sayesinde
drive-by indirme zincirini erken yakalama sansi var. Match -> high severity
cunku exploit zaten browser'a teslim edilmis sayilir.

## QRadar

- Event Rule: `URL in SGB_EK_URL`
- Optional enrichment: parse User-Agent; non-standard UA + EK URL -> +1 severity
- Action: notify SOC + push src_ip to `SGB_EXPLOITED_HOSTS`, EDR scan trigger

## Splunk

- Saved search: `SGB - UC-EK-001 - Exploit kit URL request`
- Tspun: `| lookup sgb_url_lookup value AS url OUTPUT connectiontype | where connectiontype="EK"`

## False positives

- Threat hunting / sandbox traffic -> exception
- Cached browser request from old session -> low signal, suppress if no UA / no referrer
