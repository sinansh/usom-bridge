# Güvenlik Politikası

## Desteklenen sürümler

Bu proje sürekli güncel tutulan bir tehdit beslemesi köprüsüdür. Güvenlik düzeltmeleri yalnızca `main` dalı üzerinde yapılır; eski commit'ler veya fork'lar için geriye dönük yama yayınlanmaz.

| Bileşen | Destek |
|---|---|
| `main` (en güncel commit) | ✅ |
| GitHub Pages üzerinden yayınlanan feed dosyaları | ✅ |
| `sgb-taxii.bilsec.tr` TAXII 2.1 servisi | ✅ |
| Eski commit'ler / fork'lar | ❌ |

## Güvenlik açığı bildirme

Bir güvenlik açığı bulduğunuzu düşünüyorsanız **lütfen GitHub Issues üzerinden public olarak açmayın.**

Bildirim için tercih edilen kanallar:

1. **GitHub private vulnerability reporting** — [Security → Report a vulnerability](https://github.com/bilsectr/sgb-api-bridge/security/advisories/new)

Bildiriminizde lütfen şunları içerin:

- Etkilenen bileşen (feed dosyaları, TAXII worker, sync script'leri, Docker/K8s manifest'leri, dokümantasyon)
- Yeniden üretim adımları veya PoC
- Etki değerlendirmesi (gizlilik / bütünlük / erişilebilirlik)
- Varsa önerilen düzeltme

## Yanıt süresi

| Aşama | Hedef süre |
|---|---|
| İlk yanıt (alındı bilgisi) | 3 iş günü |
| İlk değerlendirme | 7 iş günü |
| Düzeltme veya hafifletme planı | 30 gün (kritik açıklar için daha kısa) |
| Public disclosure | Düzeltme yayınlandıktan sonra, bildirenle koordineli |

## Kapsam

**Kapsam içi:**

- Bu repo'daki sync, dönüştürme ve TAXII script'leri
- `cloudflare/taxii-worker/` altındaki Cloudflare Worker kodu
- Docker / Kubernetes manifest ve nginx konfigürasyonları
- GitHub Pages üzerinden servis edilen feed üretim mantığı
- CI/CD pipeline'larındaki güvenlik sorunları (secret sızıntısı, supply chain vb.)

**Kapsam dışı:**

- Yukarı kaynak SGB API'sindeki (`siberguvenlik.gov.tr`) güvenlik sorunları — bunlar doğrudan SGB'ye bildirilmelidir
- Feed içeriğindeki kayıtların doğruluğu / güncelliği (besleme bütünüyle SGB tarafından sağlanır)
- Bilinçli olarak public ve anonim sunulan servislere yapılan rate-limit veya DoS testleri
- Üçüncü taraf SIEM/TIP ürünlerindeki entegrasyon sorunları

## Güvenlik tasarım kararları

- TAXII servisi **anonim ve kimlik doğrulamasız** sunulur; istemci credential'ı saklanmaz.
- Sync süreçleri yalnızca SGB tarafından yayınlanan veriyi okur; kullanıcı girdisi kabul etmez.
- Feed dosyaları statik olarak yayınlanır; çalışma zamanı sunucu mantığı içermez.
- Repo'da hiçbir secret tutulmaz; CI gizli değerleri GitHub Actions secret'larında saklanır.

## Teşekkür

Sorumlu bildirimde bulunan araştırmacılar, kabul etmeleri halinde release notlarında ve `SECURITY.md` "Acknowledgements" bölümünde anılır.
