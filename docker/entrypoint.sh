#!/bin/sh
set -e

# Komut dispatcher. K8s'de "command/args" ile, Docker'da direkt argument ile cagrilir.
#
# Modlar:
#   all-in-one      : nginx + python loop (default; loop pack rebuild yapar)
#   loop            : sadece python loop (+ opt pack rebuild)
#   serve           : sadece nginx
#   sync-once       : tek seferlik sync; ikinci arg full|delta|catalog-sync
#   pack            : export + build_pack + build_splunk_ta (DB hazirsa)
#   export          : sadece feeds/ uret
#   build-pack      : sadece QRadar pack
#   build-splunk-ta : sadece Splunk TA
#   push-qradar     : siem/qradar/out -> QRadar REST (SGB_QRADAR_HOST + SGB_QRADAR_TOKEN gerekli)
#   healthcheck     : stats.json fresh mi
#   sh / bash       : interaktif shell (debug)

MODE="${1:-all-in-one}"
shift 2>/dev/null || true

DATA_ROOT="${SGB_BRIDGE_ROOT:-/data}"
PACK_ENABLED="${SGB_BRIDGE_PACK_ENABLED:-1}"

# Veri dizinleri yoksa olustur
mkdir -p "$DATA_ROOT/docs" "$DATA_ROOT/state" "$DATA_ROOT/feeds" \
         "$DATA_ROOT/siem/qradar/out" "$DATA_ROOT/siem/splunk/out"

# Seed: volume/PVC bos ise imaja gomulu gecmis veriyi kopyala.
# -n (no-clobber): mevcut volume verisinin uzerine asla yazmaz.
if [ ! -f "$DATA_ROOT/state/seen_ids.json" ] && [ -d /app/seed ]; then
  echo "[entrypoint] $DATA_ROOT bos - imajdaki seed verisi kopyalaniyor"
  cp -rn /app/seed/docs/. "$DATA_ROOT/docs/" 2>/dev/null || true
  cp -rn /app/seed/state/. "$DATA_ROOT/state/" 2>/dev/null || true
  echo "[entrypoint] seed tamamlandi"
fi

# build_splunk_ta.py SGB_BRIDGE_ROOT/siem/splunk/TA-... arar; imajdaki template'i bag.
# Volume'a TA template yazmiyoruz: kullanici override edebilsin diye yalniz YOK ise symlink kuruyoruz.
if [ ! -e "$DATA_ROOT/siem/splunk/TA-sgb-threatintel" ]; then
  ln -sfn /app/siem/splunk/TA-sgb-threatintel "$DATA_ROOT/siem/splunk/TA-sgb-threatintel" 2>/dev/null \
    || cp -r /app/siem/splunk/TA-sgb-threatintel "$DATA_ROOT/siem/splunk/" 2>/dev/null || true
fi

run_python() {
  exec python "/app/scripts/$1" "${@:2}"
}

# Pack rebuild yardimcisi: DB yoksa veya disabled ise skip.
pack_rebuild() {
  if [ "$PACK_ENABLED" != "1" ]; then
    return 0
  fi
  if [ ! -f "$DATA_ROOT/state/sgb.db" ]; then
    echo "[entrypoint] pack-rebuild skip: $DATA_ROOT/state/sgb.db yok"
    return 0
  fi
  echo "[entrypoint] pack rebuild basliyor (feeds/ + qradar + splunk TA)"
  python /app/scripts/export.py           || echo "[entrypoint] export hata - devam"
  python /app/scripts/build_pack.py       || echo "[entrypoint] build_pack hata - devam"
  python /app/scripts/build_splunk_ta.py  || echo "[entrypoint] build_splunk_ta hata - devam"
  echo "[entrypoint] pack rebuild tamam"
}

case "$MODE" in
  all-in-one)
    echo "[entrypoint] all-in-one: nginx + python loop (delta+pack)"
    nginx
    # Ilk acilista catalog'lari da bir kez denemek isteyenler icin (online'sa):
    # python /app/scripts/sync.py --mode catalog-sync || true
    # Loop oncesi bir kez pack rebuild (seed verisinde DB varsa feeds/ dolu olsun)
    pack_rebuild
    # Loop sync: her delta sonrasi pack rebuild yapilacak (PACK_ENABLED=1 ise).
    # sync.py'nin loop modu kendi icinde pack yapmiyor; bunu kabuk ile saglıyoruz:
    if [ "$PACK_ENABLED" = "1" ]; then
      while :; do
        python /app/scripts/sync.py --mode delta || echo "[entrypoint] sync hata"
        pack_rebuild
        sleep "${SGB_BRIDGE_DELTA_INTERVAL_SEC:-3600}"
      done
    else
      exec python /app/scripts/sync.py --mode loop
    fi
    ;;
  loop)
    echo "[entrypoint] loop: sadece sync + (opt) pack rebuild"
    pack_rebuild
    if [ "$PACK_ENABLED" = "1" ]; then
      while :; do
        python /app/scripts/sync.py --mode delta || echo "[entrypoint] sync hata"
        pack_rebuild
        sleep "${SGB_BRIDGE_DELTA_INTERVAL_SEC:-3600}"
      done
    else
      exec python /app/scripts/sync.py --mode loop
    fi
    ;;
  serve)
    echo "[entrypoint] serve: sadece nginx"
    exec nginx -g 'daemon off;'
    ;;
  sync-once)
    SUBMODE="${1:-delta}"
    echo "[entrypoint] sync-once: $SUBMODE"
    exec python /app/scripts/sync.py --mode "$SUBMODE"
    ;;
  pack)
    echo "[entrypoint] pack: export + build_pack + build_splunk_ta"
    if [ ! -f "$DATA_ROOT/state/sgb.db" ]; then
      echo "HATA: $DATA_ROOT/state/sgb.db yok. Once 'sync-once full' calistir."
      exit 1
    fi
    python /app/scripts/export.py
    python /app/scripts/build_pack.py
    python /app/scripts/build_splunk_ta.py
    ;;
  export)         run_python export.py "$@" ;;
  build-pack)     run_python build_pack.py "$@" ;;
  build-splunk-ta) run_python build_splunk_ta.py "$@" ;;
  push-qradar)
    if [ -z "$SGB_QRADAR_HOST" ] || [ -z "$SGB_QRADAR_TOKEN" ]; then
      echo "HATA: SGB_QRADAR_HOST ve SGB_QRADAR_TOKEN env'leri gerekli"
      exit 1
    fi
    exec python /app/scripts/push_to_qradar.py --pack "$DATA_ROOT/siem/qradar/out" "$@"
    ;;
  healthcheck)
    exec python /app/scripts/sync.py --mode healthcheck
    ;;
  sh|bash)
    exec /bin/sh
    ;;
  *)
    exec "$MODE" "$@"
    ;;
esac
