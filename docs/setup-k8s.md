# Kubernetes kurulumu

CronJob (sync) + Deployment (nginx serve) + PVC (state ve feed'ler) ile native Kubernetes deployment.

## Önkoşullar

- Kubernetes 1.24+
- Default StorageClass (RWO yeterli; `local-path`, `gp2`, `csi-...` vb.)
- Cluster'ın ghcr.io'ya erişimi veya kendi private registry'ne mirror
- Cluster içinden SGB API'sine (`https://www.siberguvenlik.gov.tr`) çıkış

## Manifestler

Hepsi `k8s/` klasöründe, kustomize ile organize:

```
k8s/
├── kustomization.yaml
├── namespace.yaml
├── pvc.yaml                   # /data icin 1Gi PVC (RWO)
├── cronjob-delta.yaml         # saatte bir (:23)
├── cronjob-full.yaml          # Pazar 03:00 UTC
├── deployment.yaml            # nginx serve (replicas=1)
├── service.yaml               # ClusterIP :80
└── ingress.yaml.example       # opsiyonel
```

## Kurulum

```bash
git clone https://github.com/bilsectr/sgb-api-bridge.git
cd sgb-api-bridge
kubectl apply -k k8s/
```

Veya bash ile direkt:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/cronjob-delta.yaml
kubectl apply -f k8s/cronjob-full.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## İlk bootstrap

CronJob'lar tetiklendiğinde çalışır. İlk full sync'in hemen başlamasını istersen elle Job oluştur:

```bash
kubectl -n sgb-api-bridge create job --from=cronjob/sgb-sync-full bootstrap
kubectl -n sgb-api-bridge logs -f job/bootstrap
```

Full sync 5-10 saat sürer. `activeDeadlineSeconds: 36000` (10h) ile sınırlı; takılırsa pod öldürülür, ama state ve partial dosyalar PVC'de kalır. Bir sonraki run resume eder.

## Feed'lere erişim

### Cluster içinden

Cluster içindeki diğer pod'lardan: `http://sgb-api-bridge.sgb-api-bridge.svc.cluster.local/domain-list.txt`

### Cluster dışından — Port-forward (test)

```bash
kubectl -n sgb-api-bridge port-forward svc/sgb-api-bridge 8080:80
curl http://localhost:8080/domain-list.txt
```

### Cluster dışından — Ingress

`k8s/ingress.yaml.example` dosyasını kopyala:

```bash
cp k8s/ingress.yaml.example k8s/ingress.yaml
# host'u kendi domain'inle degistir
kubectl apply -f k8s/ingress.yaml
```

Veya `kustomization.yaml` içinde Ingress satırını yorumdan çıkar.

### Cluster dışından — NodePort

`service.yaml`'da `type: ClusterIP` → `type: NodePort` yapıp `nodePort: 30880` ekle. Sonra `http://<node-ip>:30880/domain-list.txt`.

## Yapılandırma

### Schedule değiştirme

`cronjob-delta.yaml` / `cronjob-full.yaml` içindeki `schedule:` alanını değiştir. Tüm CronJob spec'i.

### İmaj tag'i sabitleme

`kustomization.yaml`'da:

```yaml
images:
  - name: ghcr.io/bilsectr/sgb-api-bridge
    newTag: v1.0.0
```

Production'da `latest` yerine sabit tag öneririz.

### Private registry mirror

İmajı kendi registry'nize taşıyın:

```bash
docker pull ghcr.io/bilsectr/sgb-api-bridge:latest
docker tag ghcr.io/bilsectr/sgb-api-bridge:latest registry.kurum.local/sgb-api-bridge:1.0
docker push registry.kurum.local/sgb-api-bridge:1.0
```

Kustomization:

```yaml
images:
  - name: ghcr.io/bilsectr/sgb-api-bridge
    newName: registry.kurum.local/sgb-api-bridge
    newTag: "1.0"
```

### Proxy

Cluster proxy gerektiriyorsa CronJob'lardaki `env:` listesine ekle:

```yaml
- name: HTTPS_PROXY
  value: "http://proxy.kurum.local:8080"
- name: HTTP_PROXY
  value: "http://proxy.kurum.local:8080"
- name: NO_PROXY
  value: "localhost,127.0.0.1,.svc,.cluster.local"
```

## İzleme

```bash
# CronJob durumu
kubectl -n sgb-api-bridge get cronjobs

# Son Job'lar
kubectl -n sgb-api-bridge get jobs --sort-by=.status.startTime

# Bir job'un log'u
kubectl -n sgb-api-bridge logs job/sgb-sync-delta-<hash>

# Serve pod'unun durumu
kubectl -n sgb-api-bridge get pods -l app.kubernetes.io/component=serve

# stats.json
kubectl -n sgb-api-bridge exec deploy/sgb-serve -- cat /data/docs/stats.json
```

## Sorun giderme

- **PVC `Pending`**: cluster'ın default StorageClass'ı yok ya da PV provisioner çalışmıyor. `kubectl get storageclass` ile kontrol et, `pvc.yaml`'a `storageClassName:` ekle.
- **CronJob hiç çalışmıyor**: cluster saat dilimi UTC mi yoksa local mi? `kubectl describe cronjob/sgb-sync-delta` ile `Last Schedule Time` bak. v1.27+ ise `spec.timeZone` set edilebilir.
- **Pod `CrashLoopBackOff`**: `kubectl logs <pod>` ile incele. Tipik sebep: SGB API'ye erişim yok veya PVC'de yer kalmadı.
- **404 dönüyor**: full sync henüz bitmemiş. `kubectl exec deploy/sgb-serve -- ls -la /data/docs` ile dosyaları kontrol et.
- **Deployment `0/1 ready` Recreate'te takıldı**: PVC RWO ise CronJob pod'u ile Deployment pod'u aynı node'da olmalı. Multi-node cluster'da node affinity ekle veya RWX PVC kullan.

## Helm chart?

Şimdilik plain YAML. İhtiyaç olursa Helm chart eklenebilir; mevcut manifestler kustomize ile yeterince esnek.
