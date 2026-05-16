# SGB QRadar Pack

SGB indicator feed'inin QRadar Reference Set + Reference Map artifact'larina ve
buna dayali use case'lere donusturulmesi.

## Mimari

```
SQLite (state/sgb.db)
        |
        v
scripts/build_pack.py        --> siem/qradar/out/        (bootstrap CSV'ler)
scripts/push_to_qradar.py    --> QRadar REST API         (gunluk push)
                                 /api/reference_data/sets/bulk_load/{name}
                                 /api/reference_data/maps/bulk_load/{name}
```

Iki tur artifact:

- **Reference Set** (`SGB_<CT>_<TYPE>`): tek sutunlu (sadece value). Rule
  matcher'lari icin (`when ANY of these properties is contained in any of
  these reference sets`).
- **Reference Map** (`SGB_<TYPE>_Map`): key = value, value =
  `CT|DESC|CRIT|SRC`. Rule'lar eslesmeden sonra split edip event'a
  custom property olarak yazabilir → tek lookup'ta tam zenginlestirme.

## Naming konvansiyonu

```
SGB_PH_DOMAIN     SGB_BC_IP      SGB_AC_IP       SGB_EK_URL
SGB_PH_URL        SGB_BC_DOMAIN  SGB_MF_URL      SGB_MC_IP
SGB_PH_IP         SGB_MM_IP      SGB_MM_DOMAIN   ...
SGB_DOMAIN_MAP    SGB_IP_MAP     SGB_URL_MAP     SGB_IP6_MAP
```

CT degerleri: PH BC AC EK MF MM MC OT (kaynak: SGB address-connection-type).

## TTL stratejisi

Reference set'lerin **time_to_live** parametresi `25 hours` olarak set
edilir. Push her saat (veya delta sync sonrasi) yapildiginda entry'ler
her zaman canli kalir. Push 24+ saat dururde entry'ler dusup rule'lar
sessize gomulur (alarm: ekstra healthcheck).

## Kurulum (one-shot)

```bash
# 1. Pack'i uret
python scripts/build_pack.py

# 2. Cikti: siem/qradar/out/reference_sets/*.csv  (UI bootstrap icin)
#          siem/qradar/out/reference_maps/*.csv
#          siem/qradar/out/manifest.json

# 3. QRadar UI'dan ilk yukleme (opsiyonel - push script de yapabilir):
#    Admin > Reference Set Management > Import
#    CSV'leri tek tek import et

# 4. Veya API ile push:
export SGB_QRADAR_HOST=qradar.kurum.local
export SGB_QRADAR_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
python scripts/push_to_qradar.py --pack siem/qradar/out
```

## Rule + AQL

- **Use case kutuphanesi:** [docs/usecases/](../../docs/usecases/) — kanonik tanimlar
  burada (vendor-agnostik). Bu dizindeki QRadar implementasyon notlari
  oraya referans verir.
- `rules/`     — QRadar-spesifik notlar (XML/JSON export, vb.)
- `aql/`       — Hazir AQL search'ler (raporlar dahil)
- `severity-matrix.md` — connectiontype × criticality -> severity esleme
