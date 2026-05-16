# UC-MC-002 — MDM app traffic to SGB Mobile C&C

| Alan          | Deger |
|---------------|-------|
| ID            | UC-MC-002 |
| MITRE         | TA0011 / T1437 + T1474 (Supply Chain) |
| CT            | MC |
| Severity base | 7 |
| Data sources  | MDM application telemetry, Mobile Threat Defense (Lookout, Zimperium) |
| Reference     | `SGB_MC_DOMAIN`, `SGB_MC_IP` |

## Detection logic

MDM/MTD'den gelen "app made network request" event'larini SGB MC feed'iyle
korelyaste. UC-MC-001'den daha hassas: hangi app yaptigini bilebiliyoruz,
container'lik MDM'de uninstall edilebilir.

## QRadar

- Event Rule on MDM sourcetype only
- Custom event property: `Mobile App Package` (com.example.pkg)
- Action: severity 7, MDM API ile app blacklist + device retire-trigger (manuel onayli)

## Splunk

- Saved search: `SGB - UC-MC-002 - MDM app C2`
- `| where sourcetype IN ("intune:app", "lookout") AND sgb_query_ct="MC"`

## False positives

- Yeni install edilen guvenlik arastirma app'i -> dev/research device exception
- Cloud DNS resolver bias (8.8.8.8 vs SGB DNS C&C IP'si yanlislikla feedeyse) -> review
