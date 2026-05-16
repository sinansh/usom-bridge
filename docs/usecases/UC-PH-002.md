# UC-PH-002 — Proxy HTTP request to SGB phishing URL

| Alan          | Deger |
|---------------|-------|
| ID            | UC-PH-002 |
| MITRE         | TA0001 / T1566.002 |
| CT            | PH |
| Severity base | 5 |
| Data sources  | Web proxy / SWG (Bluecoat, Forcepoint, Zscaler, Squid) |
| Reference     | `SGB_PH_URL`, `SGB_URL_MAP` |

## Detection logic

Proxy `url` veya `http.url` alani `SGB_PH_URL` ile eslestiyse offense ac.
PH-001 (DNS) ile arasindaki fark: DNS-over-HTTPS / IP-direct request'lerde
DNS hit alinmaz; proxy yine de yakalar. Iki rule de aktif olmali (komplementer
kapsama).

## QRadar

- Event Rule: `when any of (URL, "HTTP URL Host") is in SGB_PH_URL`
- Filter: `srcnetwork in Trusted`
- Action: severity = 5 + criticality modifier; `SGB_SUSPECTED_HOSTS` set'ine src ekle

## Splunk

- Macro: `sgb_proxy_phishing_search` (eklenecek; sgb_url_lookup ile)
- Saved search: `SGB - UC-PH-002 - Proxy phishing URL`

## False positives

- Threat intel research yapan analyst workstation -> exception
- Email gateway URL rewriting (Proofpoint, Mimecast) original'i obscure edebilir; rewriting'i decode eden parsing kuralina ihtiyac var
