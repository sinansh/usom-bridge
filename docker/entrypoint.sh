#!/bin/sh
set -e

# Komut dispatcher. K8s'de "command/args" ile, Docker'da direkt argument ile cagrilir.
#
# Modlar:
#   all-in-one   : nginx + python loop (default)
#   loop         : sadece python loop
#   serve        : sadece nginx
#   sync-once    : tek seferlik sync; ikinci arg full|delta|healthcheck
#   sh / bash    : interaktif shell (debug)

MODE="${1:-all-in-one}"
shift 2>/dev/null || true

# Veri dizinleri yoksa olustur
mkdir -p "${SGB_BRIDGE_ROOT:-/data}/docs" "${SGB_BRIDGE_ROOT:-/data}/state"

case "$MODE" in
  all-in-one)
    echo "[entrypoint] all-in-one mode: nginx + python loop"
    # Initial bootstrap'i da yapsin diye sync once delta tetikleyelim;
    # docs/ tamamen bossa nginx 404 doner. Loop modu kendi basina full'a karar verir.
    nginx
    exec python /app/sync.py --mode loop
    ;;
  loop)
    echo "[entrypoint] loop mode: sadece sync"
    exec python /app/sync.py --mode loop
    ;;
  serve)
    echo "[entrypoint] serve mode: sadece nginx"
    exec nginx -g 'daemon off;'
    ;;
  sync-once)
    SUBMODE="${1:-delta}"
    echo "[entrypoint] sync-once: $SUBMODE"
    exec python /app/sync.py --mode "$SUBMODE"
    ;;
  healthcheck)
    exec python /app/sync.py --mode healthcheck
    ;;
  sh|bash)
    exec /bin/sh
    ;;
  *)
    # Bilinmeyen komut: direkt exec
    exec "$MODE" "$@"
    ;;
esac
