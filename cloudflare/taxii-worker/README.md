# SGB TAXII Worker (Cloudflare)

`sgb-taxii.bilsec.tr` üzerinden TAXII 2.1 servisi sunar. Veriyi GitHub Pages'de
yayınlanan statik TAXII ağacından (`docs/taxii/`, üreten:
`scripts/build_taxii.py`) okur; TAXII semantik katmanını (Content-Type,
`added_after`/`limit`/`next` query mantığı, CORS, host rewrite, edge cache)
ekler.

## Geliştirme

```bash
cd cloudflare/taxii-worker
npm install
npm run dev        # wrangler dev (localhost:8787)
npm run typecheck
```

## Deploy

GitHub Actions otomatik deploy eder (push to `main`, path filter:
`cloudflare/taxii-worker/**`). Gereken repo secret'leri:

- `CLOUDFLARE_API_TOKEN` — `Workers Scripts:Edit` izinli token
- `CLOUDFLARE_ACCOUNT_ID`

Elle deploy:

```bash
wrangler deploy
```

## DNS / Custom Domain

Cloudflare zone `bilsec.tr` üzerinde:

1. `sgb-taxii` A/AAAA kaydı **gerekmez** — Workers custom domain otomatik route.
2. Wrangler `[[routes]]` bloğu `sgb-taxii.bilsec.tr/*` pattern'iyle bind eder.
3. İlk deploy sonrası Cloudflare dashboard → Workers → sgb-taxii → Triggers
   → Custom Domains'te `sgb-taxii.bilsec.tr` görünmelidir.

## Endpoint'ler

| Path | Anlam |
|---|---|
| `/taxii2/` | Discovery |
| `/api/` | API root |
| `/api/collections/` | Collections listesi |
| `/api/collections/{cid}/` | Collection metadata |
| `/api/collections/{cid}/objects/?added_after=&limit=&next=` | STIX envelope |
| `/api/collections/{cid}/manifest/?added_after=&limit=&next=` | Manifest envelope |
| `/api/collections/{cid}/objects/{stix-id}/` | Tek STIX objesi |

Collection ID'leri: `sgb-phishing`, `sgb-botnet-cc`, `sgb-apt-cc`,
`sgb-exploit-kit`, `sgb-malware-download`, `sgb-mining`, `sgb-mobile-cc`,
`sgb-other`.

## Test

```bash
# Discovery
curl -sH 'Accept: application/taxii+json;version=2.1' \
  https://sgb-taxii.bilsec.tr/taxii2/ | jq

# Collections
curl -s https://sgb-taxii.bilsec.tr/api/collections/ | jq

# Phishing — son 1 saatte değişen indicator'lar
curl -s "https://sgb-taxii.bilsec.tr/api/collections/sgb-phishing/objects/?added_after=$(date -u -d '1 hour ago' +%FT%T.000Z)&limit=100" | jq '.objects | length'
```

## Mimari notları

- Veri **upstream**: `https://bilsectr.github.io/sgb-api-bridge/taxii/...`
- Worker veri tutmaz; her istek için pages.json'a bakar, ilgili sayfayı çeker.
- Cloudflare edge cache TTL = `EDGE_CACHE_TTL` (default 300sn). Saatlik build
  ile uyumlu; SIEM client'lar için max 5 dk lag.
- `pages.json` daha kısa TTL (60sn) — yeni sayfa açılma anını yakalamak için.
- `__TAXII_BASE__` placeholder upstream JSON'ında durur; Worker
  `PUBLIC_BASE`'e rewrite eder. Bu sayede aynı statik ağacı Docker/K8s
  nginx (kendi host'uyla) de servis edebilir.
