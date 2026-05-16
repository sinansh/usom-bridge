# UC-PH-001 — SGB Phishing DNS Query

| Alan          | Deger |
|---------------|-------|
| ID            | UC-PH-001 |
| Title         | Internal host -> SGB phishing domain DNS query |
| MITRE         | TA0001 / T1566.002 (Spearphishing Link) |
| Severity      | base=5 (CT=PH) + criticality modifier (bkz. severity-matrix.md) |
| Data sources  | DNS query logs (BIND, Windows DNS, Infoblox, Cisco Umbrella) |
| Reference     | `SGB_PH_DOMAIN` (set) + `SGB_DOMAIN_MAP` (zenginlestirme) |
| Response      | PB-PH-001 (kullanici uyari + URL block + EDR scan) |

## QRadar Rule (UI talimati)

**Tip:** Event Rule

**Test:**
```
when the event QID is one of the following: DNS Query QIDs
AND when any of these event properties (URL/Hostname) is contained in
   any of these reference set(s): SGB_PH_DOMAIN
AND when the destination network is one of the following: Trusted
```

**Response:**
- Dispatch new event named "SGB Phishing DNS"
- Magnitude severity: 5 (base, criticality modifier rule action ile)
- Annotate offense: "SGB phishing domain match"
- Reference set: add source IP to `SGB_SUSPECTED_HOSTS`
- (Opsiyonel) email notification

## False positive notlari

- SGB IH (ihbar) kaynakli domain'ler yuksek FP'li: ya source=IH'yi reference
  set'ten ayri tut (`SGB_PH_DOMAIN_IH`), ya da rule'da `SGB_SRC != "IH"`
  filter ekle.
- Threat intel research yapan asset'ler (SOC analyst workstation, sandbox)
  → exception list.

## AQL test sorgusu

Bkz. `aql/uc-ph-001-test.aql`.
