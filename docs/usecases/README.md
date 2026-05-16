# SGB SIEM Use Case Library

SGB indicator feed'i kullanan **vendor-agnostik** use case kutuphanesi. Her
use case'in:

- Kanonik tanimi burada (bu dizinde, `UC-*.md`)
- QRadar implementasyonu: [siem/qradar/](../../siem/qradar/) (rule talimati + AQL)
- Splunk implementasyonu: [siem/splunk/TA-sgb-threatintel/](../../siem/splunk/TA-sgb-threatintel/) (savedsearch + macro)
- Severity formulu: [severity-matrix.md](../../siem/qradar/severity-matrix.md) (tek kaynak; her iki SIEM ona referans verir)

## ID konvansiyonu

```
UC-<CT>-<NNN>   CT = connectiontype kodu (PH/BC/AC/EK/MF/MM/MC/OT)
UC-XX-<NNN>     Cross-category / meta-rule
```

## Index

| ID | Title | CT | Severity (base) | Status |
|----|-------|----|------|--------|
| [UC-PH-001](UC-PH-001.md) | DNS query -> SGB phishing domain | PH | 5 | ready |
| [UC-PH-002](UC-PH-002.md) | Proxy HTTP -> SGB phishing URL | PH | 5 | ready |
| [UC-PH-003](UC-PH-003.md) | Email body link -> SGB phishing domain | PH | 6 | ready |
| [UC-BC-001](UC-BC-001.md) | Outbound to SGB Botnet C&C IP | BC | 8 | ready |
| [UC-BC-002](UC-BC-002.md) | DNS query -> SGB Botnet C&C domain | BC | 8 | ready |
| [UC-BC-003](UC-BC-003.md) | Periodic beacon to SGB IP (NetFlow) | BC | 8 | ready |
| [UC-AC-001](UC-AC-001.md) | Any SGB APT C&C match | AC | 10 | ready |
| [UC-AC-002](UC-AC-002.md) | Single asset, 3+ AC matches / 30 min | AC | 10 | ready |
| [UC-EK-001](UC-EK-001.md) | HTTP request to SGB Exploit Kit URL | EK | 8 | ready |
| [UC-EK-002](UC-EK-002.md) | IDS exploit alert + SGB EK IP/URL | EK | 9 | ready |
| [UC-MF-001](UC-MF-001.md) | Proxy download from SGB malware URL | MF | 7 | ready |
| [UC-MF-002](UC-MF-002.md) | EDR file fetched from SGB malware host | MF | 8 | ready |
| [UC-MM-001](UC-MM-001.md) | Outbound to SGB mining indicator | MM | 3 | ready |
| [UC-MM-002](UC-MM-002.md) | CPU spike + SGB MM indicator hit | MM | 5 | ready |
| [UC-MC-001](UC-MC-001.md) | Mobile/VPN -> SGB Mobile C&C indicator | MC | 7 | ready |
| [UC-MC-002](UC-MC-002.md) | MDM app traffic -> SGB MC | MC | 7 | ready |
| [UC-OT-001](UC-OT-001.md) | Any SGB OT match (info-only baseline) | OT | 3 | ready |
| [UC-XX-001](UC-XX-001.md) | Same asset hits 2+ distinct CTs / 24h | XX | 8 | ready |
| [UC-XX-002](UC-XX-002.md) | Asset re-infection: same indicator hit 2x in 7d | XX | 7 | ready |
| [UC-XX-003](UC-XX-003.md) | Org-wide criticality spike (avg crit > 7 / hr) | XX | - | ready |

## Coverage matrix

| CT | Data source ailesi |
|----|---------------------|
| PH | DNS, Proxy, Email |
| BC | Firewall, Proxy, NetFlow |
| AC | Tum kaynaklar (yuksek hassasiyetli match) |
| EK | Proxy, IDS, EDR |
| MF | Proxy, EDR, Email-link |
| MM | Firewall, NetFlow, EDR perf |
| MC | MDM, Mobile VPN, App gateway |
| OT | Generic |

## Use case eklemek

1. [_template.md](_template.md) kopyala -> `UC-<CT>-<NNN>.md`
2. README'deki Index tablosuna satir ekle
3. QRadar/Splunk tarafinda implementasyon ekle (AQL/macro) ve cross-link ver
4. (Opsiyonel) `docs/integrations/` altina yeni data source ingest guide yaz
