# SGB Severity Matrix

QRadar (ve Splunk) tarafindaki butun rule'lar bu tabloyu referans alir.
Matristen donen sayi: QRadar `severity` alani (1-10).

## Connectiontype baz severity

| CT | Anlam              | Base | Notlar                              |
|----|--------------------|------|-------------------------------------|
| AC | APT C&C            |  10  | En yuksek; APT eslemeleri her zaman offense |
| BC | Botnet C&C         |   8  | Calisan bir bot var demek           |
| EK | Exploit Kit        |   8  | Aktif sömuru zinciri               |
| MF | Malware Download   |   7  | Henuz calismadi olabilir            |
| MC | Mobile C&C         |   7  | Yalniz MDM/mobil log source'larinda |
| PH | Phishing           |   5  | Volume yuksek; credential exposure  |
| MM | Mining             |   3  | Policy ihlali; performans etkisi    |
| OT | Other              |   3  | Bilgi amacli                        |

## Criticality_level modifier

`final_severity = clamp(base + ((criticality_level - 5) / 2), 1, 10)`

- Pratikte: criticality 8+ → +1.5 → +2 (yuvarlanmis)
- criticality ≤ 3 → -1
- criticality 4-7 → degisiklik yok

## Source confidence modifier (offense açma esigi)

- Source ∈ {US, SB, SO} → offense ac
- Source = RS → offense ac, severity -1
- Source = IH → **offense açma**, sadece kayit at (yuksek FP)

## QRadar uygulama

Rule'larda dogrudan if/else degil; bu mantik **reference map** üzerinden:

```
when the event matches a reference map (SGB_IP_MAP)
  set Magnitude Severity based on lookup value field [0] (CT)
  set Custom Property "SGB_CT" = lookup value field [0]
  set Custom Property "SGB_DESC" = lookup value field [1]
  set Custom Property "SGB_CRIT" = lookup value field [2]
  set Custom Property "SGB_SRC" = lookup value field [3]
```

Splunk tarafinda ayni matrix `eval severity = case(...)` ile uygulanir
(bkz. `siem/splunk/`).
