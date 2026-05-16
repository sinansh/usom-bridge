# syntax=docker/dockerfile:1.6
# sgb-api-bridge: tek imaj, mode dispatcher ile hem all-in-one (Docker) hem split (K8s) destekler.
#
# Default davranis (docker run sgb-api-bridge):
#   - nginx /data/docs ve /data/feeds'i 80 portundan serve eder
#   - python sync.py --mode loop arka planda delta'yi saatte bir tetikler
#   - Default'ta her delta sonrasi SIEM Pack (feeds/ + qradar pack + splunk TA) rebuild edilir
#     (kapatmak icin SGB_BRIDGE_PACK_ENABLED=0)
#
# Alternatif modlar (K8s CronJob ve manuel kullanim icin):
#   docker run --rm sgb-api-bridge sync-once delta
#   docker run --rm sgb-api-bridge sync-once full
#   docker run --rm sgb-api-bridge pack            # export + build_pack + build_splunk_ta
#   docker run --rm sgb-api-bridge export
#   docker run --rm sgb-api-bridge build-pack
#   docker run --rm sgb-api-bridge build-splunk-ta
#   docker run --rm sgb-api-bridge push-qradar     # SGB_QRADAR_HOST + SGB_QRADAR_TOKEN env'leri gerekir
#   docker run --rm sgb-api-bridge healthcheck
#   docker run -d sgb-api-bridge serve              # sadece HTTP, sync yok
#   docker run -d sgb-api-bridge loop               # sadece sync + (opt) pack, HTTP yok
#
# HTTP endpoint'ler (default serve modunda):
#   /                                                  HTML ana sayfa
#   /domain-list.txt /ip-list.txt /url-list.txt ...    geriye uyumlu duz feed'ler
#   /feeds/sgb-master.csv                              master kanonik tablo
#   /feeds/sgb-master.jsonl                            JSON Lines
#   /feeds/stix/sgb-{type}.stix2.json                  STIX 2.1 bundle (per-type)
#   /feeds/by-connectiontype/*.txt                     CT bazli slice'lar
#   /feeds/index.json                                  manifest (sha256 + size)
#   /siem/splunk/out/TA-sgb-threatintel.tar.gz         Splunk TA paketi
#   /siem/qradar/out/manifest.json                     QRadar pack manifest
#   /stats.json                                        SQLite + count'lar dahil saglik

FROM python:3.11-slim AS build
RUN pip install --no-cache-dir --prefix=/install requests

FROM python:3.11-slim

LABEL org.opencontainers.image.title="SGB API Bridge" \
      org.opencontainers.image.description="SGB (eski USOM) tehdit beslemesini firewall + SIEM artifact'larina cevirir" \
      org.opencontainers.image.source="https://github.com/bilsectr/sgb-api-bridge" \
      org.opencontainers.image.licenses="MIT"

# nginx + curl (healthcheck) + tar (extract/push utility)
RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx curl tar \
 && rm -rf /var/lib/apt/lists/* /var/log/nginx/* \
 && rm /etc/nginx/sites-enabled/default

# Python paketleri
COPY --from=build /install /usr/local

# Uygulama - tum scripts/ dizini (sync.py artik sgb_db'yi import ediyor; export/build_pack vb. de var)
COPY scripts/ /app/scripts/
# Splunk TA template kaynagi (build_splunk_ta.py SGB_BRIDGE_ROOT/siem/splunk/TA-... arar; entrypoint
# /data/siem/splunk/TA-sgb-threatintel -> /app/siem/splunk/TA-sgb-threatintel symlink kurar)
COPY siem/splunk/TA-sgb-threatintel/ /app/siem/splunk/TA-sgb-threatintel/
# nginx + entrypoint
COPY docker/nginx.conf /etc/nginx/conf.d/sgb-api-bridge.conf
COPY docker/entrypoint.sh /entrypoint.sh

# Seed verisi: repo'daki gecmis feed'ler + state + (varsa) SQLite DB imaja gomulur.
# Fresh container (bos volume) ilk acilista bunu /data'ya kopyalar, full sync gerekmez.
COPY docs /app/seed/docs
COPY state /app/seed/state

RUN chmod +x /entrypoint.sh \
 && mkdir -p /data/docs /data/state /data/feeds /data/siem/qradar/out /data/siem/splunk/out \
 && chown -R www-data:www-data /data /app \
 && ln -sf /dev/stdout /var/log/nginx/access.log \
 && ln -sf /dev/stderr /var/log/nginx/error.log \
 && touch /var/run/nginx.pid \
 && chown www-data:www-data /var/run/nginx.pid \
 && chown -R www-data:www-data /var/lib/nginx /var/log/nginx

USER www-data
WORKDIR /data

EXPOSE 80
VOLUME ["/data"]

# Builder'lar SGB_BRIDGE_ROOT'u kullanir (default /data).
# PYTHONPATH=/app/scripts: sync.py'nin "import sgb_db" yapabilmesi icin.
ENV SGB_BRIDGE_ROOT=/data \
    SGB_BRIDGE_DELTA_INTERVAL_SEC=3600 \
    SGB_BRIDGE_RECONCILE_EVERY=24 \
    SGB_BRIDGE_PACK_ENABLED=1 \
    PYTHONPATH=/app/scripts \
    PYTHONUNBUFFERED=1

HEALTHCHECK --interval=60s --timeout=5s --start-period=30s \
  CMD curl -fsS http://127.0.0.1/stats.json > /dev/null || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["all-in-one"]
