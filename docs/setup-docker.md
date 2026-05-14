# Docker kurulumu

Tek konteyner ile SGB API Bridge'i ayağa kaldır. İçinde nginx + sync loop birlikte çalışır.

## Önkoşullar

- Docker 20.10+ (compose v2 ile)
- Host'tan SGB API'sine (`https://siberguvenlik.gov.tr`) erişim. Proxy varsa Docker daemon ayarlarında `HTTPS_PROXY` set edilmeli.
- ~1 GB disk (state + feed dosyaları için).

## Hızlı başlangıç

```bash
docker run -d \
  --name sgb-api-bridge \
  -p 8080:80 \
  -v sgb-api-bridge-data:/data \
  --restart unless-stopped \
  ghcr.io/bilsectr/sgb-api-bridge:latest
```

Konteyner ayağa kalkar, internal loop ilk **full sync**'i otomatik başlatır (state boş olduğu için). Bu işlem **5-10 saat** sürebilir. Sırasında:

- HTTP 8080 portu zaten dinlenir ama feed dosyaları henüz boş.
- `docker logs -f sgb-api-bridge` ile ilerlemeyi izleyebilirsin.

Full sync bitince loop her saatte delta sync çalıştırır.

## docker-compose ile

```bash
git clone https://github.com/bilsectr/sgb-api-bridge.git
cd sgb-api-bridge
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml logs -f
```

## Feed URL'leri

```
http://<host-ip>:8080/domain-list.txt
http://<host-ip>:8080/ip-list.txt
http://<host-ip>:8080/url-list.txt
http://<host-ip>:8080/ip6-list.txt
http://<host-ip>:8080/ip6net-list.txt
http://<host-ip>:8080/stats.json
```

FortiGate konfigürasyonu:

```
config system external-resource
    edit "SGB-Domain"
        set type domain
        set resource "http://10.0.0.5:8080/domain-list.txt"
        set refresh-rate 60
    next
    edit "SGB-IP"
        set type address
        set resource "http://10.0.0.5:8080/ip-list.txt"
        set refresh-rate 60
    next
end
```

## HTTPS önerisi

Konteyner kendisi sadece HTTP konuşur. Üretimde **reverse proxy** ile HTTPS sonlandırması yap:

- Traefik, Caddy, nginx-proxy ile otomatik Let's Encrypt
- Veya kurumsal CA ile statik sertifika

Caddy ile en kısa örnek:

```caddyfile
sgb-feed.kurum.local {
    reverse_proxy localhost:8080
}
```

## Manuel komutlar

```bash
# Tek seferlik full sync (debug icin)
docker run --rm -v sgb-api-bridge-data:/data \
  ghcr.io/bilsectr/sgb-api-bridge:latest sync-once full

# Tek seferlik delta
docker exec sgb-api-bridge /entrypoint.sh sync-once delta

# Health check
docker exec sgb-api-bridge /entrypoint.sh healthcheck

# Container icinde shell
docker exec -it sgb-api-bridge sh

# State sifirlamak (dikkat: full bootstrap'i tekrarlatir)
docker run --rm -v sgb-api-bridge-data:/data alpine \
  sh -c "rm -rf /data/state /data/docs"
```

## Yapılandırma (env variables)

| Variable | Default | Açıklama |
|---|---|---|
| `SGB_BRIDGE_ROOT` | `/data` | State ve feed dosyalarının kök dizini |
| `SGB_BRIDGE_DELTA_INTERVAL_SEC` | `3600` | Loop modunda delta sync sıklığı (sn) |
| `SGB_BRIDGE_FULL_INTERVAL_DAYS` | `7` | Full sync sıklığı (gün) |
| `TZ` | `UTC` | Konteyner saat dilimi (loglar için) |

## Sorun giderme

- **404 dönüyor**: Henüz full sync bitmemiştir. `docker logs sgb-api-bridge` ile durumu izle. `cat /data/state/seen_ids.json` ile resume_page hâlâ var mı bak.
- **Konteyner sürekli restart oluyor**: SGB API'sine erişim yok ya da disk dolu. `docker logs sgb-api-bridge --tail 200` incele.
- **`Permission denied` /data altında**: Volume'un sahibi yanlış UID. Container `www-data` (UID 33) ile çalışır. Host'ta `chown -R 33:33 /var/lib/docker/volumes/sgb-api-bridge-data/_data` ile düzelt.
- **İmaj çekilemiyor**: Air-gapped ortamlarda `docker save / load` ile transferle:
  ```bash
  docker pull ghcr.io/bilsectr/sgb-api-bridge:latest
  docker save ghcr.io/bilsectr/sgb-api-bridge:latest | gzip > sgb-api-bridge.tar.gz
  # Hedef makineye kopyala:
  gunzip -c sgb-api-bridge.tar.gz | docker load
  ```

## İmajı kendin build etmek (supply-chain güvenliği)

```bash
git clone https://github.com/bilsectr/sgb-api-bridge.git
cd sgb-api-bridge
docker build -f docker/Dockerfile -t kurum/sgb-api-bridge:1.0 .
docker push kurum-registry.local/sgb-api-bridge:1.0
```
