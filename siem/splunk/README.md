# SGB Splunk TA

`TA-sgb-threatintel` - SGB indicator lookup'lari + 3 baslangic use case alarmi
+ overview dashboard.

## Mimari

```
SQLite (state/sgb.db)
        |
        v
scripts/build_splunk_ta.py
        |
        |--> siem/splunk/TA-sgb-threatintel/  (static config; commit'li)
        |--> siem/splunk/out/TA-sgb-threatintel/  (build cikti)
        +--> siem/splunk/out/TA-sgb-threatintel.tar.gz  (deploy artifact)
```

## Kurulum

```bash
# 1. Bootstrap
python scripts/sync.py --mode full
python scripts/build_splunk_ta.py

# 2. Splunk'a yukle
# UI: Apps > Manage Apps > Install app from file > out/TA-sgb-threatintel.tar.gz
# CLI:
splunk install app siem/splunk/out/TA-sgb-threatintel.tar.gz -auth admin:****
splunk restart
```

## Yenileme (delta sonrasi)

Yalnizca lookup CSV'leri degisirse Splunk restart gerekmez:

```bash
python scripts/sync.py --mode delta
python scripts/build_splunk_ta.py
rsync -av siem/splunk/out/TA-sgb-threatintel/lookups/ \
  splunk:/opt/splunk/etc/apps/TA-sgb-threatintel/lookups/
```

## Iclerik

| Dosya / Konfig          | Amaci |
|-------------------------|-------|
| `lookups/sgb_ip.csv`    | IP (v4/v6) indicator lookup |
| `lookups/sgb_domain.csv`| Domain indicator lookup |
| `lookups/sgb_url.csv`   | URL indicator lookup |
| `default/transforms.conf` | Lookup tanimlari |
| `default/props.conf`      | Otomatik lookup'lar (src_ip, dest_ip, query, url) |
| `default/macros.conf`     | `sgb_severity`, `sgb_trusted_source` + use case search makrolari |
| `default/savedsearches.conf` | UC-PH-001, UC-BC-001, UC-AC-001 alarmlari |
| `default/data/ui/views/sgb_overview.xml` | Dashboard |

## Use case kutuphanesi

Kanonik use case tanimlari (her iki SIEM icin): [docs/usecases/](../../docs/usecases/)

## Use Case eslesmesi (QRadar ile)

| Splunk saved search                  | QRadar UC | Aciklama |
|--------------------------------------|-----------|----------|
| `SGB - UC-PH-001 - Phishing DNS query` | UC-PH-001 | DNS sorgu eslesmesi |
| `SGB - UC-BC-001 - Botnet C2 outbound` | UC-BC-001 | C2 outbound IP eslesmesi |
| `SGB - UC-AC-001 - APT C2 match (any)` | UC-AC-001 | APT herhangi bir eslesme; P1 |

Severity formulu: `severity-matrix.md` (QRadar tarafiyla bire bir uyumlu;
`sgb_severity` macro icinde implement edilmis).

## Production tuning

- `props.conf`'taki `[default]` cok genistir; ortaminizda log hacmi yuksek
  ise `[sourcetype::pan:traffic]`, `[sourcetype::stream:dns]`, vb. ile
  daraltin.
- Splunk Enterprise Security varsa lookup'lari KV Store collection olarak
  yukleyebilir ve Threat Intelligence Framework'e `local_*_intel.conf`
  ile baglayabilirsiniz (S5'te yapilacak).
