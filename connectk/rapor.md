# Connect-K Arena — Yapay Zekâ Ödev Raporu

**Varyant Bilgisi:** `(R=7, C=8, K=4, V=0, d=8)`  
- **Satır Sayısı ($R$):** $5 + (8 \bmod 3) = 7$  
- **Sütun Sayısı ($C$):** $6 + ((8 \operatorname{div} 3) \bmod 3) = 8$  
- **Kazanma Taşı ($K$):** $4 + ((8 \operatorname{div} 9) \bmod 2) = 4$  
- **Kural Varyasyonu ($V$):** $(8 \operatorname{div} 18) \bmod 4 = 0$ (Standart Connect-4 kuralları; kod ayrıca $V \in \{1, 2, 3\}$ varyasyonlarını da desteklemektedir)

---

## Aşama 0: Oyun Modeli ve Perft Analizi

Oyun durumu Python `dataclass(frozen=True)` ve iç içe `tuple` yapısıyla değişmez (immutable) olarak tasarlanmıştır. Bu sayede arama ağacındaki dallanmalar birbirinin tahtasını bozmaz. Kazanma kontrolü tüm tahtayı taramak yerine yalnızca son bırakılan taşın bulunduğu `(r0, c0)` koordinatının yatay, dikey ve iki çapraz ekseninde yapılır.

- **Boş Tahta Perft ($n=1..5$):** $R=7, C=8, K=4$ tahtasında ilk 6 hamlede oyun bitmeyeceği için yaprak düğüm sayıları teorik $C^n$ değerleriyle ($8, 64, 512, 4096, 32768$) birebir örtüşmüştür (`results/stage0_perft.csv`).
- **Yarı Dolu Orta Oyun Konumu:** 12 hamle oynanmış yarı dolu konumda bazı dallar erken kazanma ile terminal duruma ulaştığından düğüm sayıları $C^n$'in altında kalmıştır ($n=4$ için $2822$, $n=5$ için $20011$ düğüm; $0.12372\text{ sn}$).

---

## Aşama 1: Derinlik Sınırlı Minimax ve Etkin Dallanma Çarpanı

`MinimaxAgent` sınıfında terminal testi derinlik kontrolünden önce çalıştırılmış, beraberlik durumlarında deterministik davranış için merkeze en yakın sütun (`3, 4, 2, 5, 1, 6, 0, 7`) tercih edilmiştir.

- **Etkin Dallanma Çarpanı ($b_{\text{etkin}} = \text{Düğüm}^{1/d}$):** Boş tahtada derinlik $d=2$ için düğüm sayısı $1 + 8 + 64 = 73$ ve $b_{\text{etkin}} = 73^{0.5} \approx 8.544$ olarak ölçülmüştür. Derinlik arttıkça ($d=4, 6$) kök ve ara düğümlerin toplam içindeki payı azaldığından $b_{\text{etkin}}$ değeri sütun sayısı olan $C = 8.0$'a yaklaşmaktadır (`results/stage1_minimax.csv`).

---

## Aşama 2: Alpha-Beta Budaması ve Hamle Sıralaması

`seed=8` ile üretilen 50 rastgele orta oyun konumunda derinlik $6$ seviyesinde düz Minimax ile $\alpha$-$\beta$ budamasının kök değerleri **50/50 konumda birebir eşit** çıkmıştır (`results/stage2_summary.csv` ve `results/stage2_nodes.png`).

- **Sıralama Karşılaştırması:**
  - `a_siralamasiz`: Doğal sütun sırası (`0..7`). En geç budama yapan yöntemdir.
  - `b_merkez`: Merkez sütunlara öncelik vererek ortalama düğüm sayısını belirgin biçimde düşürmüştür.
  - `c_taktiksel`: Önce 1 hamlede kazandıran ve rakibi engelleyen hamleleri, ardından merkez sütunları inceleyerek en yüksek budama kazancını sağlamıştır.
- **Kuramsal Sınır ve Sıralama Maliyeti:** Kuramsal en iyi durum olan $O(b^{m/2}) \approx 8^3 = 512$ düğüme en çok taktiksel sıralama yaklaşmıştır. En az budama, tüm hamlelerin eşit değerli (`0.0`) olduğu ve zorlayıcı taktik tehdit bulunmayan dengeli konumlarda gerçekleşmektedir.

---

## Aşama 3: Değerlendirme Fonksiyonu ve Ağırlık Ayarı

`Evaluator` sınıfı başlangıçta tahtadaki tüm geçerli $K$'lık pencereleri önceden hesaplar ve her durum için 6 öznitelik çıkarır:
1. $f_1$: MAX için $K-1$ taş + 1 boş içeren tehdit penceresi sayısı
2. $f_2$: MIN için $K-1$ taş + 1 boş içeren tehdit penceresi sayısı
3. $f_3$: MAX için $K-2$ taş + 2 boş içeren gelişim penceresi sayısı
4. $f_4$: MIN için $K-2$ taş + 2 boş içeren gelişim penceresi sayısı
5. $f_5$: Merkez sütun (`3` ve `4`) kontrol farkı
6. $f_6$ (Varyant / Yerçekimi Özniteliği): Standart tahtada yerçekimiyle doğrudan erişilebilir (altı dolu) anında tamamlanabilir tehdit farkı; $V=1$ Silindirde sarmalı pencere tehditleri, $V=3$ Engelli tahtada engel komşuluğundaki tehditlerdir. Bu öznitelik "havada asılı" sahte tehditlerle bir sonraki hamlede gerçekten doldurulabilir tehditleri ayırt etmek için eklenmiştir.

Sonuç $\tanh(\text{skor} / 35.0)$ ile $(-1, +1)$ aralığına sıkıştırılmıştır. Derinlik 5'te 3 ağırlık vektörü (`W1_varsayilan`, `W2_agresif`, `W3_savunmaci`) arasında oynanan turnuva sonuçları `results/stage3_weights.csv` dosyasında kayıtlıdır.

---

## Aşama 4: Zaman Sınırlı Arama, Zobrist Tablosu ve Ufuk Etkisi

- **İteratif Derinleşme ve Süre Kontrolü:** Hamle başına `1.0` saniye sınırını aşmamak için `60 ms` güvenlik payı bırakılmış, her 1000 düğümde bir `time.perf_counter()` kontrolü yapılmıştır. Süre dolduğunda yarım kalan derinlik `SearchTimeout` ile iptal edilerek yalnızca son tamamlanan derinliğin hamlesi döndürülmüştür; çünkü kısmi aramada yalnızca ilk bakılan hamle incelendiğinden diğer dalların daha iyi olup olmadığı bilinemez.
- **Yer Değiştirme Tablosu (TT):** 64-bit Zobrist hash (`EXACT`, `LOWER`, `UPPER` bayrakları ve sıra bilgisi dahil) ile aynı konuma farklı hamle sıralarıyla ulaşıldığında tekrar hesaplama önlenmiş, 1 saniyede ulaşılan ortalama derinlik artmıştır (`results/stage4_depth_summary.csv`).
- **Ufuk Etkisi:** Derinlik sınırında rakibin 1 hamlede kazanma tehdidi (`_has_immediate_threat`) tespit edildiğinde arama derinliği `+1` uzatılarak sığ derinlikte tehdidi öteleme hatası giderilmiştir (`results/stage4_horizon.csv`).

---

## Aşama 5: Turnuva Protokolü ve Yenilgi Analizi

`agent.py`, `--R`, `--C`, `--K`, `--V`, `--seed` parametrelerini alarak `MOVES` ve `QUIT` komutlarını standart girdi/çıktı üzerinden `flush=True` ile yürütür.

- **Kendi Kendine / Provalarda Tespit Edilen Hata Analizi:**
  - **Hata Hamlesi:** Orta oyunda dikey ve yatay çifte tehdit (çatal) kurulan konumlarda (`[3, 1, 4, 2, 0, 1, 5, 2]`) sığ derinlikte merkez kontrolüne aşırı ağırlık verilmesi rakibin 2 hamle sonraki çatalını geç fark etmeye yol açmıştır.
  - **Kök Neden:** Aşama 3 özniteliklerinde tekil $K-1$ tehditleri sayılırken aynı sütunun ardışık iki satırında üst üste oluşan çifte tehditlere ekstra çarpan verilmemesi ve sabit derinlik ufku.
  - **Sonraki Sürüm İyileştirmesi:** Aynı sütunda ardışık iki boş kareyi tehdit eden "çifte tehdit" (double-threat) özniteliği eklemek ve TT boyutunu sabitleyerek daha derin iterasyonlara ulaşmak.