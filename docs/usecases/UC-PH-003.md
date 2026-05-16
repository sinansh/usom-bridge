# UC-PH-003 — Email body link points to SGB phishing domain/URL

| Alan          | Deger |
|---------------|-------|
| ID            | UC-PH-003 |
| MITRE         | TA0001 / T1566.002 |
| CT            | PH |
| Severity base | 6 (delivered email -> exposure asamasi) |
| Data sources  | Mail gateway / SEG (Proofpoint, Mimecast, Cisco ESA, M365 ATP) |
| Reference     | `SGB_PH_DOMAIN`, `SGB_PH_URL` |

## Detection logic

Mail gateway log'larindaki `url`, `body_url`, `recipient`, `sender` alanlari.
Eslesme inbound'tan sonra olsa bile (header'larda decoded URL var) offense ac;
mailbox icindeki URL'ler tikrlandiginda PH-001/002 zaten yakalar - bu rule
"erken uyari" katmanidir.

## QRadar

- Event Rule on mail log source type only
- Property: parse edilen `Body URL` / `Embedded URL` -> `SGB_PH_DOMAIN` veya `SGB_PH_URL`
- Action: notify ITSec + add recipient to `SGB_PHISH_TARGETS` set (TTL 30d)

## Splunk

- Saved search: `SGB - UC-PH-003 - Email phishing link delivered`
- Lookup ile: `| lookup sgb_domain_lookup value AS body_domain OUTPUT connectiontype`

## False positives

- Pen-test / phishing simulasyon URL'leri -> simulation domain exception list
- Email tagged "External" + URL = legitimate news site -> beyaz liste
