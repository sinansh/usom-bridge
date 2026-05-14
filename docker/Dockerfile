# syntax=docker/dockerfile:1.6
# sgb-api-bridge: tek imaj, mode dispatcher ile hem all-in-one (Docker) hem split (K8s) destekler.
#
# Default davranis (docker run sgb-api-bridge):
#   - nginx /data/docs'u 80 portundan serve eder
#   - python sync.py --mode loop arka planda delta'yi saatte bir, full'u haftada bir tetikler
#
# Alternatif modlar (K8s CronJob ve manuel kullanim icin):
#   docker run --rm sgb-api-bridge sync-once delta
#   docker run --rm sgb-api-bridge sync-once full
#   docker run --rm sgb-api-bridge healthcheck
#   docker run -d sgb-api-bridge serve         # sadece HTTP, sync yok
#   docker run -d sgb-api-bridge loop          # sadece sync, HTTP yok

FROM python:3.11-slim AS build
RUN pip install --no-cache-dir --prefix=/install requests

FROM python:3.11-slim

LABEL org.opencontainers.image.title="SGB API Bridge" \
      org.opencontainers.image.description="SGB (eski USOM) tehdit beslemesini firewall'larin tuketebilecegi duz metin formatina cevirir" \
      org.opencontainers.image.source="https://github.com/bilsectr/sgb-api-bridge" \
      org.opencontainers.image.licenses="MIT"

# nginx ve curl (healthcheck icin)
RUN apt-get update \
 && apt-get install -y --no-install-recommends nginx curl \
 && rm -rf /var/lib/apt/lists/* /var/log/nginx/* \
 && rm /etc/nginx/sites-enabled/default

# Python paketleri
COPY --from=build /install /usr/local

# Uygulama
COPY scripts/sync.py /app/sync.py
COPY docker/nginx.conf /etc/nginx/conf.d/sgb-api-bridge.conf
COPY docker/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
 && mkdir -p /data/docs /data/state \
 && chown -R www-data:www-data /data \
 && ln -sf /dev/stdout /var/log/nginx/access.log \
 && ln -sf /dev/stderr /var/log/nginx/error.log \
 # Nginx PID dosyasini www-data yazabilsin
 && touch /var/run/nginx.pid \
 && chown www-data:www-data /var/run/nginx.pid \
 # cache dizinlerini www-data icin acik tut
 && chown -R www-data:www-data /var/lib/nginx /var/log/nginx

USER www-data
WORKDIR /data

EXPOSE 80
VOLUME ["/data"]

ENV SGB_BRIDGE_ROOT=/data \
    SGB_BRIDGE_DELTA_INTERVAL_SEC=3600 \
    SGB_BRIDGE_FULL_INTERVAL_DAYS=7 \
    PYTHONUNBUFFERED=1

HEALTHCHECK --interval=60s --timeout=5s --start-period=30s \
  CMD curl -fsS http://127.0.0.1/badge.json > /dev/null || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["all-in-one"]
