# UC-EK-002 — IDS exploit alert correlated with SGB EK indicator

| Alan          | Deger |
|---------------|-------|
| ID            | UC-EK-002 |
| MITRE         | TA0002 / T1190 + T1203 |
| CT            | EK (composite) |
| Severity base | 9 |
| Data sources  | IDS/IPS (Snort, Suricata, Palo Alto Threat) + Web proxy |
| Reference     | `SGB_EK_IP`, `SGB_EK_URL` |

## Detection logic

Tek bir kaynaktan match yetersiz; iki signal kombinasyonu yuksek hassasiyetli:
- IDS alert (sid in browser-exploit, file-flash-exploit, vb. category)
- AYNI src/dest pair'i 5 dk icinde `SGB_EK_*` set'ine match etti

Tek basina IDS alert sik FP uretir; SGB feed onayi compromise olasiligi'ni
guclendirir.

## QRadar

- Common Rule: `when IDS exploit category event + when SGB_EK_* match` on same src/dst within 300s
- Action: severity 9, dispatch "SGB EK + IDS confirmed"

## Splunk

- Saved search: join across `index=ids` + `index=proxy` with `sgb_url_ct="EK" OR sgb_dest_ct="EK"`
- transaction span=5m src_ip dest_ip

## False positives

- IDS false positive + irrelevant EK match -> SOC review queue (severity'i tampon olarak 7'ye dusur, otomatik response yapma)
