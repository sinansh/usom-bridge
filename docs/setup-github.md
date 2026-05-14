# GitHub Pages kurulumu (fork edip kendi reponda)

Bu rehber, projeyi kendi GitHub hesabına fork edip Pages üzerinden yayımlaman içindir. Hâlihazırda `bilsectr/sgb-api-bridge` reposunu kullanıyorsan zaten her şey hazır — direkt aşağıdaki "Feed URL'leri ve cihaz örnekleri" bölümüne atla.

## Repo'yu hazırla

```bash
gh repo create sgb-api-bridge --public --clone --template bilsectr/sgb-api-bridge
cd sgb-api-bridge
```

Veya manuel fork: GitHub UI'ndan "Fork" → kendi hesabın altına klonla.

## 1. Workflow permission'larını ayarla

Repo → **Settings** → **Actions** → **General** → **Workflow permissions**:
- ✓ **Read and write permissions** seç
- ✓ "Allow GitHub Actions to create and approve pull requests" (auto-retrigger için gerekli)
- **Save**

## 2. GitHub Pages'i aç

Repo → **Settings** → **Pages**:
- Source: **Deploy from a branch**
- Branch: `main` / folder: `/docs`
- **Save**

## 3. İlk full sync'i tetikle

Repo → **Actions** → **Sync (full, weekly)** → **Run workflow** → branch `main` → **Run workflow**.

İlk full sync ~5-10 saat sürer. SGB rate-limit'i nedeniyle workflow runner timeout'a takılabilir; bu durumda son adım otomatik olarak yeni workflow tetikler ve resume eder. 1-2 zincir sonra `docs/*.txt` dolar.

İlerlemeyi izle: Actions sekmesi → çalışan workflow → `Run python scripts/sync.py --mode full` adımındaki canlı log.

## 4. Doğrulama

Birinci full sync zinciri tamamen bittiğinde:

- `https://<USERNAME>.github.io/sgb-api-bridge/` → landing açılır
- `https://<USERNAME>.github.io/sgb-api-bridge/stats.json` → `last_update_utc` dolu, `in_progress` null
- `https://<USERNAME>.github.io/sgb-api-bridge/domain-list.txt` → ~450K satır

## 5. README ve index.html'de URL'leri güncelle

`bilsectr` → `<USERNAME>` ile değiştir:

```bash
grep -rl "bilsectr.github.io" . | xargs sed -i 's|bilsectr.github.io|<USERNAME>.github.io|g'
grep -rl "bilsectr/sgb-api-bridge" . | xargs sed -i 's|bilsectr/sgb-api-bridge|<USERNAME>/sgb-api-bridge|g'
git commit -am "Personalize URLs" && git push
```

## Feed URL'leri ve cihaz örnekleri

| Tür | URL |
|---|---|
| Domain | `https://<USERNAME>.github.io/sgb-api-bridge/domain-list.txt` |
| IPv4 | `https://<USERNAME>.github.io/sgb-api-bridge/ip-list.txt` |
| URL | `https://<USERNAME>.github.io/sgb-api-bridge/url-list.txt` |
| IPv6 | `https://<USERNAME>.github.io/sgb-api-bridge/ip6-list.txt` |
| IPv6 subnet | `https://<USERNAME>.github.io/sgb-api-bridge/ip6net-list.txt` |

### FortiGate (CLI)

```
config system external-resource
    edit "SGB-Domain"
        set type domain
        set resource "https://<USERNAME>.github.io/sgb-api-bridge/domain-list.txt"
        set refresh-rate 60
    next
    edit "SGB-IP"
        set type address
        set resource "https://<USERNAME>.github.io/sgb-api-bridge/ip-list.txt"
        set refresh-rate 60
    next
end
```

### Sophos XG / Firewall

Web Admin → System → Hosts and services → IP host group → **Import from URL** ile URL'leri ekle.

### Palo Alto

```
set external-list SGB-IP type ip url https://<USERNAME>.github.io/sgb-api-bridge/ip-list.txt recurring hourly
set external-list SGB-Domain type domain url https://<USERNAME>.github.io/sgb-api-bridge/domain-list.txt recurring hourly
```

### pfSense (pfBlockerNG)

Firewall → pfBlockerNG → IPv4 → Add → URL alanına IPv4 listesini gir. DNSBL altına domain listesini ekle.

### Pi-hole

Adlist olarak ekle:

```
https://<USERNAME>.github.io/sgb-api-bridge/domain-list.txt
```

Sonra `pihole -g` ile yenile.

### Squid

```
acl sgb_blacklist dstdomain "/etc/squid/sgb-domain-list.txt"
http_access deny sgb_blacklist
```

```cron
17 * * * * curl -sf https://<USERNAME>.github.io/sgb-api-bridge/domain-list.txt -o /etc/squid/sgb-domain-list.txt && systemctl reload squid
```

## Sorun giderme

- **Pages 404**: Settings → Pages'te source `/docs` mu, branch `main` mi? "GitHub Pages" job'unun Actions'ta yeşil olduğunu kontrol et.
- **Workflow "permission denied"**: 1. adımdaki "Read and write permissions" set edilmemiş.
- **Full sync hep timeout yiyor**: SGB çok agresif rate-limit uyguluyor demektir. `scripts/sync.py`'da `SLEEP_OK_FULL = 1.0` değerini 2.0'a çıkar, push'la.
- **state/seen_ids.json bozulduysa**: dosyayı sil, fresh start için her tip'i sıfırla:
  ```json
  {"domain":{"max_id":0,"last_full_sync":null,"last_delta_sync":null}, "url":{...}, ...}
  ```
