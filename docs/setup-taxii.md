# TAXII 2.1 Servisi

SGB tehdit beslemesini **TAXII 2.1** standardında, **STIX 2.1** indicator objeleri olarak sunar. Anonim erişim — public servis, kimlik doğrulama yok.

## Endpoint

| Dağıtım | TAXII base URL |
|---|---|
| GitHub Pages + Cloudflare (varsayılan) | `https://sgb-taxii.bilsec.tr/` |
| Self-hosted Docker | `http://<docker-host>/` |
| Self-hosted Kubernetes | `http://sgb-taxii.kurum.local/` (ingress örneği) |

## Discovery

```bash
curl -sH 'Accept: application/taxii+json;version=2.1' \
  https://sgb-taxii.bilsec.tr/taxii2/
```

```json
{
  "title": "SGB Threat Intelligence (TAXII 2.1)",
  "description": "Siber Guvenlik Baskanligi (SGB, eski USOM) acik tehdit beslemesinin TAXII 2.1 sunumu.",
  "default": "https://sgb-taxii.bilsec.tr/api/",
  "api_roots": ["https://sgb-taxii.bilsec.tr/api/"]
}
```

## Koleksiyonlar

Koleksiyonlar SGB API'sinin `connectiontype` taksonomisini birebir yansıtır. Bir koleksiyon farklı tipleri (domain, ipv4, ipv6, url) birlikte içerir — STIX pattern'i türü gösterir.

| Collection alias | İçerik (connectiontype) | Tipik SIEM kullanımı |
|---|---|---|
| `sgb-phishing` | `PH` — Phishing | Proxy/DNS/Mail block, kullanıcı tıklama detection |
| `sgb-botnet-cc` | `BC` — Botnet C&C | Outbound C2 beacon tespiti |
| `sgb-apt-cc` | `AC` — APT C&C | Yüksek öncelikli APT alerting |
| `sgb-exploit-kit` | `EK` — Exploit Kit | Web gateway block, exploit landing |
| `sgb-malware-download` | `MF` — Malware Download | EDR / endpoint block, payload host |
| `sgb-mining` | `MM` — Cryptomining | DNS/proxy block (browser + malware miner) |
| `sgb-mobile-cc` | `MC` — Mobile C&C | MDM / mobil ağ korelasyonu |
| `sgb-other` | `OT` — Diğer | Catch-all |

## Filtreleme

TAXII 2.1 spec'i:

```
GET /api/collections/{alias}/objects/?added_after=<ISO8601>&limit=<N>&next=<cursor>
GET /api/collections/{alias}/manifest/?added_after=<ISO8601>&limit=<N>&next=<cursor>
```

- `added_after`: bu zaman damgasından **sonra** içeriği değişen indicator'lar (STIX `modified` alanına bakar — yalnız anlamlı alan değişimi bunu bumplar, `last_seen` değil)
- `next`: önceki yanıtın `next` alanından gelen sayfa cursor'u
- Yanıt envelope'unda `more: true` varsa devamı için `next` cursor'unu kullan

### İlk dolum (full pull)

```bash
NEXT=""
while :; do
  RESP=$(curl -s "https://sgb-taxii.bilsec.tr/api/collections/sgb-phishing/objects/?limit=5000${NEXT:+&next=$NEXT}")
  echo "$RESP" | jq '.objects | length'
  MORE=$(echo "$RESP" | jq -r '.more')
  [ "$MORE" = "true" ] || break
  NEXT=$(echo "$RESP" | jq -r '.next')
done
```

### Saatlik incremental

```bash
SINCE=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S.000Z)
curl -s "https://sgb-taxii.bilsec.tr/api/collections/sgb-phishing/objects/?added_after=$SINCE"
```

## SIEM client örnekleri

### OpenCTI

`config.yml` → `connectors`:

```yaml
connector_taxii_sgb:
  type: EXTERNAL_IMPORT
  scope: stix2
  log_level: info
config:
  taxii_url: https://sgb-taxii.bilsec.tr/taxii2/
  collections:
    - sgb-phishing
    - sgb-botnet-cc
    - sgb-apt-cc
    - sgb-malware-download
  interval: 3600
```

### MISP

`Administration → Servers → Add TAXII server`:

- URL: `https://sgb-taxii.bilsec.tr/taxii2/`
- Auth: None
- Version: 2.1
- Collection: `sgb-phishing` (her use case için ayrı sunucu ekle veya `sgb-all` kullan)

### Microsoft Sentinel (Threat Intelligence — TAXII data connector)

- Friendly name: `SGB-Phishing`
- API root URL: `https://sgb-taxii.bilsec.tr/api/`
- Collection ID: `sgb-phishing`
- Polling frequency: `Hourly`

Tekrarla — her connectiontype için ayrı data connector.

### Splunk ES — TAXII2 Modular Input

```
[taxii2://SGB-Phishing]
url = https://sgb-taxii.bilsec.tr/taxii2/
collection = sgb-phishing
interval = 3600
```

### IBM QRadar — Threat Intelligence (TAXII 2.1)

`Admin → Threat Intelligence → Add TAXII Feed`:

- Server URL: `https://sgb-taxii.bilsec.tr/taxii2/`
- API Root: `https://sgb-taxii.bilsec.tr/api/`
- Collection: `sgb-phishing` (her biri ayrı feed)
- Poll interval: 1 hour

## Use Case Library eşleştirmesi

Bu repo'daki [SIEM use case library](usecases/) doğrudan TAXII koleksiyonlarına haritalanır:

| Use case prefix | TAXII collection |
|---|---|
| [`UC-PH-*`](usecases/) | `sgb-phishing` |
| [`UC-BC-*`](usecases/) | `sgb-botnet-cc` |
| [`UC-AC-*`](usecases/) | `sgb-apt-cc` |
| [`UC-EK-*`](usecases/) | `sgb-exploit-kit` |
| [`UC-MF-*`](usecases/) | `sgb-malware-download` |
| [`UC-MM-*`](usecases/) | `sgb-mining` |
| [`UC-MC-*`](usecases/) | `sgb-mobile-cc` |
| [`UC-OT-*`](usecases/) | `sgb-other` |
| [`UC-XX-*`](usecases/) (çapraz) | İlgili tüm collection'lara abone ol |

Pratik: SIEM'de her UC için **bir TAXII feed + bir reference set/lookup** ilişkisi kur. Veri akar, rule'lar bu lookup'a göre tetiklenir.

## STIX 2.1 indicator şeması

Örnek bir kayıt:

```json
{
  "type": "indicator",
  "spec_version": "2.1",
  "id": "indicator--<deterministic-uuidv5>",
  "created_by_ref": "identity--<sgb>",
  "created": "2026-05-15T14:36:11.037Z",
  "modified": "2026-05-15T14:36:11.037Z",
  "name": "SGB domain indicator #951512",
  "pattern": "[domain-name:value = 'kotuornek.example']",
  "pattern_type": "stix",
  "pattern_version": "2.1",
  "valid_from": "2026-05-15T14:36:11.037Z",
  "indicator_types": ["malicious-activity"],
  "labels": ["phishing"],
  "confidence": 85,
  "external_references": [
    {"source_name": "sgb", "external_id": "951512", "url": "https://siberguvenlik.gov.tr"}
  ],
  "x_sgb_id": 951512,
  "x_sgb_type": "domain",
  "x_sgb_connectiontype": "PH",
  "x_sgb_description": "PH",
  "x_sgb_source": "US",
  "x_sgb_criticality": 8,
  "x_sgb_api_date": "2026-05-15 14:36:11"
}
```

Notlar:

- `modified` yalnız anlamlı alan (connectiontype/category/source/criticality/api_date/value) değiştiğinde güncellenir. Saatlik full sync ile dahi değişmeyen indicator için stabil kalır → `added_after` ile yapılan incremental poll gereksiz veri çekmez.
- `id` deterministik (UUIDv5(namespace, "sgb:{id}")) — bir kayıt silinip API'ye geri eklense bile aynı STIX id'sini alır → SIEM'de duplicate oluşmaz.
- `confidence`: `source` koduna göre map'lenir (US/SB=85, SO=70, RS=60, IH=40).
- `x_sgb_*` özel alanlar: SIEM tarafında ek pivot/filtrasyon için.

## Operasyonel notlar

- **Tazelik**: Saatte bir tam sync (`scripts/sync.py --mode full` + `scripts/build_taxii.py`); SGB API yarım saatte güncelliyor → max ~75 dk lag. Cloudflare edge cache TTL 300 sn → SIEM polling cevabı dakikalar içinde.
- **Silmeler**: SGB listeden kayıt çıkarabiliyor. Saatlik full sync bunları reconcile eder; o kayıt artık TAXII envelope'unda dönmez (STIX `revoked` flag'i şu an yok — eklenmesi ileride değerlendirilebilir).
- **Kendi domain'inle servis**: `docker/` veya `k8s/` ile çalıştırırsan nginx aynı statik TAXII ağacını kendi host'unla servis eder (`__TAXII_BASE__` placeholder host'a rewrite olur). Detay: [setup-docker.md](setup-docker.md), [setup-k8s.md](setup-k8s.md).
