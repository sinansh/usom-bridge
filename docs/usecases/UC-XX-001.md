# UC-XX-001 — Same asset hits 2+ distinct CTs within 24h

| Alan          | Deger |
|---------------|-------|
| ID            | UC-XX-001 |
| MITRE         | TA0011 / multi-stage |
| CT            | XX (meta) |
| Severity base | 8 (single CT severity'lerini overrride eder) |
| Data sources  | Tum (UC-PH/BC/AC/EK/MF/MM/MC olusturduklarini agregat eder) |
| Reference     | `SGB_*_MAP` (CT bilgisi map'ten cikar) |

## Detection logic

Ayni kaynak asset 24 saat icinde **birden fazla farkli connectiontype**'a hit
ettiyse multi-stage compromise sansi yuksek - tek bir CT'yi tek basina
sigorta etmek yeterli degil. Ornek: PH + MF + BC = phishing -> download -> C2
zinciri.

```
window = 24h
group_by = src_asset
distinct_count(connectiontype) >= 2
=> escalate
```

## QRadar

- Aggregator: `UC-PH-* OR UC-BC-* OR UC-AC-* OR UC-EK-* OR UC-MF-* OR UC-MM-* OR UC-MC-*`
- Group by source IP, distinct count of "SGB_CT" custom property
- Action: severity 8, offense category = "SGB Multi-Stage Compromise"

## Splunk

- Saved search: 24h scheduled, `index=notable sgb_*`
- `| stats dc(sgb_ct) AS n_cts values(sgb_ct) AS ct_list by src_ip | where n_cts >= 2`

## False positives

- Threat intel research / SOC analyst workstation -> exception
- NAT'lar tum kullanicilari tek IP'de toplar -> NAT subnet exception listesi gerekli
