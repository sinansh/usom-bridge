# UC-AC-001 — SGB APT C&C Match (Any Direction, Any Log Source)

| Alan          | Deger |
|---------------|-------|
| ID            | UC-AC-001 |
| Title         | APT C&C indicator herhangi bir eslesme |
| MITRE         | TA0011 / T1071 + TA0001 (Initial Access genel) |
| Severity      | 10 (her zaman) |
| Data sources  | Tum log source'lar (firewall, proxy, DNS, EDR, mail) |
| Reference     | `SGB_AC_IP`, `SGB_AC_DOMAIN`, `SGB_AC_URL` |
| Response      | PB-AC-001 (P1 incident, CSIRT/SOC manager paging, lockdown) |

## QRadar Rule

**Tip:** Generic high-priority rule. **AC eslesmesi enderdir; her birine
P1 muamelesi yapilir.**

```
when any of these properties (Source IP, Dest IP, URL, Hostname,
  DNS Query, File Hash, Email From, Email To) is contained in any of these
  reference sets:
    SGB_AC_IP, SGB_AC_DOMAIN, SGB_AC_URL
```

**Response:**
- Magnitude severity: 10 (fixed)
- Dispatch event: "SGB APT C2 Match - <hostname/ip>"
- Annotate offense + auto-assign to "APT" category
- Add source asset to `SGB_AC_TARGETS` (kalici)
- SOAR webhook + SMS + email
- (Opsiyonel) firewall block list'e push (otomasyon onayli ise)

## Notlar

- AC eslesmeleri her zaman manuel triage gerektirir; auto-block sadece
  source IH degilse uygulanmali.
- 30 dakika icinde ayni hostta 3+ AC match -> ayri meta-rule (`UC-AC-002`).
