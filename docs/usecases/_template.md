# UC-XX-NNN — <Kisa baslik>

| Alan          | Deger |
|---------------|-------|
| ID            | UC-XX-NNN |
| Title         | (insan-okunabilir baslik) |
| MITRE         | TAxxxx / Txxxx |
| Connectiontype| <PH/BC/AC/EK/MF/MM/MC/OT/XX> |
| Severity base | 1-10 (severity-matrix.md formulu uygulanir) |
| Data sources  | (DNS, Proxy, Firewall, EDR, Email, MDM, ...) |
| Reference     | SGB_<CT>_<TYPE>, SGB_<TYPE>_MAP |
| Response      | PB-XX-NNN (varsa) |

## Detection logic (vendor-agnostik)

(Bir paragraf + opsiyonel pseudo-code. Hangi alan hangi feed'e karsi
matchlenir, hangi filtreler uygulanir, hangi suppress mantigi var.)

## QRadar

- Reference set/map: `SGB_*`
- Rule turu: Event Rule / Flow Rule / Common Rule
- AQL test: [siem/qradar/aql/uc-xx-nnn-test.aql](../../siem/qradar/aql/)

## Splunk

- Saved search: `SGB - UC-XX-NNN - <title>`
- Macro: `sgb_<name>_search` (siem/splunk/TA-sgb-threatintel/default/macros.conf)
- Lookup: sgb_<ip|domain|url>.csv

## False positive notlari

- (Bilinen FP kaynaklari + suppress/exception onerileri)
- Source=IH icin guvenirlik dusurme stratejisi

## Response playbook

- (PB-XX-NNN'a referans, varsa)
- Manuel triage adimlari, otomasyona uygunluk degerlendirmesi
