# Yapay Zekâ Kullanım Tutanağı (PROMPTLAR.md)

**Öğrenci Numarası Son İki Hanesi (d):** 08  
**Oyun Varyantı:** (R=7, C=8, K=4, V=0, d=8)  
**GitHub Deposu:** https://github.com/mervee-yldzz/connectk-arena

## Kullanım Özeti

1. **Proje İskeleti ve Varyant Hesabı**
   - **İstek:** Öğrenci numarası son iki hanesi `08` için `(R, C, K, V, d)` parametrelerinin hesaplanması ve Git deposu klasör yapısının kurulması.
   - **Kullanılan Kısım:** Parametre formüllerinin doğrulanması (`R=7, C=8, K=4, V=0`) ve `.gitignore` ile klasör hiyerarşisinin oluşturulması.

2. **Aşama 0 — Oyun Modeli (`game.py`) ve Birim Testler (`tests/test_game.py`)**
   - **İstek:** Değişmez (`frozen=True` dataclass) durum temsili, 4 varyasyon kuralı (Standart, Silindir, Misère, Engelli) ve `perft` fonksiyonunun tasarımı.
   - **Kullanılan Kısım:** `ConnectKGame` sınıfı, son konan taş etrafında 4 eksenli kazanma kontrolü ve 11 birim test senaryosu.

3. **Aşama 1 & Aşama 2 — Minimax ve Alpha-Beta Budaması (`search.py`)**
   - **İstek:** Derinlik sınırlı Minimax, etkin dallanma çarpanı ölçümü, $\alpha$-$\beta$ kesme koşulları ve 3 farklı hamle sıralaması (`none`, `center`, `tactical`).
   - **Kullanılan Kısım:** `MinimaxAgent`, `AlphaBetaAgent` ve 50 rastgele konum üzerinde doğrulama testleri.

4. **Aşama 3 — Değerlendirme Fonksiyonu (`evaluate.py`)**
   - **İstek:** Önceden hesaplanmış $K$-uzunluklu pencereler, tehdit öznitelikleri, merkez kontrolü ve `[-1, +1]` `tanh` sıkıştırması.
   - **Kullanılan Kısım:** `Evaluator` sınıfı, 6 öznitelikli doğrusal kombinasyon ve ağırlık turnuvası deney düzeneği.

5. **Aşama 4 & Aşama 5 — Zaman Sınırlı Arama ve Turnuva Arayüzü (`search.py`, `agent.py`)**
   - **İstek:** 1.0 saniye sınırı altında iteratif derinleşme, 64-bit Zobrist anahtarlı Yer Değiştirme Tablosu (TT), acil tehdit derinlik uzatması ve komut satırı `MOVES`/`QUIT` protokolü.
   - **Kullanılan Kısım:** `TimedAlphaBetaAgent` ve `agent.py` standart girdi/çıktı arayüzü.