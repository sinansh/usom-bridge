# Self-hosted GitLab kurulumu

Bu rehber, projeyi kurumun kendi GitLab sunucusuna klonlayıp tamamen offline (internet'ten bağımsız raw URL ile) çalıştırmanızı sağlar.

## Önkoşullar

- Self-hosted GitLab CE/EE (12.0+)
- En az bir GitLab Runner (shell veya docker executor). Full sync 6-10 saat sürebileceği için runner'ın `timeout` ayarı yeterli olmalı (`/etc/gitlab-runner/config.toml` içinde `timeout = 36000` gibi).
- Runner'ın SGB API'sine (`https://www.siberguvenlik.gov.tr`) çıkışı olmalı. Kurumsal proxy varsa `HTTPS_PROXY` env değişkeni runner config'ine eklenmeli.

## 1. Repo'yu klonla

```bash
git clone https://github.com/bilsectr/sgb-api-bridge.git
cd sgb-api-bridge
git remote set-url origin https://gitlab.kurum.local/<group>/sgb-api-bridge.git
git push -u origin main
```

## 2. Project Access Token oluştur

CI'nin commit/push yapabilmesi için bir token gerekiyor:

1. Proje → **Settings** → **Access Tokens** → **Add new token**
2. Name: `sgb-api-bridge-ci`
3. Role: `Maintainer`
4. Scopes: `write_repository`, `api`
5. Token'ı kopyala (bir daha gösterilmez).

## 3. CI/CD variable ekle

1. Proje → **Settings** → **CI/CD** → **Variables** → **Add variable**
2. Key: `GIT_PUSH_TOKEN`
3. Value: (yukarıda kopyaladığın token)
4. **Mask variable**: ✓
5. **Protect variable**: ✓ (sadece protected branch'lerden erişilebilir; default branch protected olmalı)

## 4. Pipeline Schedule'ları ekle

Proje → **Build** → **Pipeline schedules** → **New schedule**

**Delta (saatlik):**
- Description: `SGB delta sync`
- Interval Pattern: `23 * * * *`
- Target Branch: `main`
- Variables: `SYNC_MODE` = `delta`

**Full (haftalık):**
- Description: `SGB full sync`
- Interval Pattern: `0 3 * * 0`
- Target Branch: `main`
- Variables: `SYNC_MODE` = `full`

## 5. İlk full sync'i manuel tetikle

İki yöntem:

**A) UI'dan:** Build → Pipeline schedules → Full sync'in yanındaki "Play" butonuna bas.

**B) CLI ile:** Build → Pipelines → **Run pipeline** → branch `main` → variable `SYNC_MODE=full` → Run.

İlk full sync ~5-10 saat sürer. Runner timeout'a takılırsa son aşamada otomatik yeni pipeline tetiklenir (zincir devam eder). 1-2 zincir sonra `docs/*.txt` dosyaları dolu olur.

## 6. Repo görünürlüğü ve feed URL'leri

FortiGate gibi cihazlar dosyaları **anonim** olarak çekecek. Repo'yu uygun görünürlüğe getir:

- **Public** (internet'e açık): feed'ler herkese açık, hiçbir auth gerekmez
- **Internal** (sadece logged-in GitLab kullanıcıları): cihaz token koyamayacağı için çalışmaz; **Pages opsiyonunu kullan** (aşağıda)
- **Private**: yalnızca takım üyeleri; cihaz çekemez. **Pages opsiyonunu kullan**.

### Public/Internal+Network-restricted senaryosu — raw URL

Feed'lere bu URL'lerden eriş:

```
https://gitlab.kurum.local/<group>/sgb-api-bridge/-/raw/main/docs/domain-list.txt
https://gitlab.kurum.local/<group>/sgb-api-bridge/-/raw/main/docs/ip-list.txt
https://gitlab.kurum.local/<group>/sgb-api-bridge/-/raw/main/docs/url-list.txt
https://gitlab.kurum.local/<group>/sgb-api-bridge/-/raw/main/docs/ip6-list.txt
https://gitlab.kurum.local/<group>/sgb-api-bridge/-/raw/main/docs/ip6net-list.txt
```

### Private repo senaryosu — GitLab Pages

`.gitlab-ci.yml` dosyasındaki `pages` job'unu yorumdan çıkar, tekrar push et. Pages'i kullanmak için:

1. Admin: GitLab Pages özelliğinin aktif olduğunu doğrula
2. Proje → Settings → Pages → "Access Control" → **kapalı** (anonim erişim)
3. Feed URL'leri:
   ```
   https://<group>.<pages-domain>/sgb-api-bridge/domain-list.txt
   ```

## 7. FortiGate konfigürasyonu (örnek)

```
config system external-resource
    edit "SGB-Domain"
        set type domain
        set resource "https://gitlab.kurum.local/<group>/sgb-api-bridge/-/raw/main/docs/domain-list.txt"
        set refresh-rate 60
    next
    edit "SGB-IP"
        set type address
        set resource "https://gitlab.kurum.local/<group>/sgb-api-bridge/-/raw/main/docs/ip-list.txt"
        set refresh-rate 60
    next
end
```

## Sorun giderme

- **`HATA: GIT_PUSH_TOKEN tanimli degil`**: 3. adımı atladın.
- **`remote: HTTP Basic: Access denied`**: Token'ın scope'unda `write_repository` yok ya da süresi dolmuş. Yeniden oluştur.
- **Pipeline başladı ama hiçbir şey değişmiyor**: SGB API'ye erişim yok. Runner'ın `curl https://www.siberguvenlik.gov.tr/api/address/index?type=ip` ile çıkıp çıkamadığını kontrol et.
- **Runner timeout'a takılıyor ama otomatik tetiklenmiyor**: `GIT_PUSH_TOKEN`'a `api` scope'u verilmemiş. Token'ı güncelle.
- **stats.json'da `last_update_utc` 48 saatten eski**: healthcheck adımı fail edecek. Pipeline tarihine bak, hangi job'ta takılındı incele.
