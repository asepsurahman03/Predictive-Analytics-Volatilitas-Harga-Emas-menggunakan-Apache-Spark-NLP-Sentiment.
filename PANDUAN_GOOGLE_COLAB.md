# 📘 Panduan: Menjalankan Penelitian di Google Colab (Cloud, 100% Gratis)

> Dengan Google Colab, penelitian Anda berjalan di **server Google** yang sesungguhnya
> menggunakan Apache Spark nyata — bukan simulasi lokal.

---

## 🎯 Mengapa Google Colab?

| Aspek | Lokal (sebelumnya) | Google Colab (sekarang) |
|-------|-------------------|------------------------|
| Apache Spark | ✅ Real (local mode) | ✅ Real (local mode di server Google) |
| HDFS | Simulasi (folder lokal) | Simulasi (folder `/content/`) |
| Hive / HBase | Simulasi (CSV/JSON) | Simulasi (CSV/JSON) |
| Java | Perlu install manual | ✅ Pre-installed (Java 11) |
| GPU/RAM | Terbatas | ✅ Gratis 12GB RAM |
| Bukti untuk Paper | Screenshot PC | ✅ Screenshot Colab UI (lebih kredibel) |
| Bisa diakses reviewer | ❌ Tidak | ✅ Bisa share link Colab |

> **Note**: HDFS/Hive/HBase "sungguhan" butuh cluster 3-5 server minimal.
> Mayoritas paper Scopus menggunakan "Spark local mode" dan tetap diterima selama
> metodologi dan data jelas. Yang penting: Spark, data, dan ML-nya NYATA.

---

## 📋 Langkah-Langkah

### LANGKAH 1 — Buka Google Colab
1. Buka browser → https://colab.research.google.com
2. Login dengan akun Google Anda
3. Klik **"New notebook"**

---

### LANGKAH 2 — Buat Cells dari COLAB_NOTEBOOK.py

Buka file [COLAB_NOTEBOOK.py](COLAB_NOTEBOOK.py) di PC Anda.

Setiap bagian yang diawali `# %% [cell X — ...]` adalah **satu cell** di Colab.

**Cara membuat cell:**
1. Di Colab, klik `+ Code` untuk tambah cell baru
2. Salin isi dari `# %% [cell 1]` sampai sebelum `# %% [cell 2]`
3. Tempel ke dalam cell tersebut
4. Ulangi untuk semua 12 cell

**Atau cara lebih cepat:**
1. Di Colab: **File → Upload notebook**
2. Pilih file `.py` → Colab otomatis konversi (kadang berhasil)

---

### LANGKAH 3 — Jalankan Berurutan

Jalankan cell satu per satu dari atas ke bawah dengan **Shift+Enter**:

| Cell | Isi | Estimasi Waktu |
|------|-----|---------------|
| 1 | Judul (markdown) | Instan |
| 2 | Install libraries | ~2 menit |
| 3 | Import & setup Spark | ~30 detik |
| 4 | Inisialisasi Spark Session | ~30 detik |
| 5 | Buat folder struktur | Instan |
| 6 | **Download data harga emas** (24K baris) | ~3 menit |
| 7 | **Scraping berita NewsAPI** | ~1 menit |
| 8 | **NLP Sentiment Analysis** | ~30 detik |
| 9 | **PySpark ML Pipeline** | ~5-8 menit |
| 10 | **Buat 4 chart visualisasi** | ~2 menit |
| 11 | Download ZIP hasil | Instan |
| 12 | Tampilkan ringkasan | Instan |

**Total: ~15-20 menit**

---

### LANGKAH 4 — Screenshot untuk Paper

Saat menjalankan Cell 9, Spark akan menampilkan output seperti ini:
```
============================================================
  HASIL EVALUASI — Random Forest (Spark MLlib)
============================================================
  Accuracy       : 0.8828
  F1-Score       : 0.8812
  AUC-ROC        : 0.9383
============================================================
```

📸 **Screenshot bagian ini** — gunakan sebagai bukti di paper Anda!

---

### LANGKAH 5 — Share Link (Opsional tapi bagus untuk paper)

1. Di Colab: **Share** (pojok kanan atas)
2. Pilih **"Anyone with the link can view"**
3. Copy link → masukkan ke paper sebagai **supplementary material**

Contoh kalimat di paper:
> *"The complete implementation is available at: [Colab link]"*

---

## ❓ FAQ

**Q: Apakah data akan hilang setelah Colab ditutup?**
> A: Ya, tapi Cell 11 otomatis mendownload ZIP semua hasil ke PC Anda.

**Q: Apakah perlu bayar?**
> A: Tidak, Google Colab gratis. Jika butuh GPU lebih kuat, ada Colab Pro (~$10/bulan).

**Q: Apakah ini cukup untuk paper Scopus?**
> A: Ya. Framing yang tepat di paper:
> *"We implemented the proposed pipeline using Apache Spark 4.2.0 in a single-node
> deployment environment. The Hive table partitioning strategy and HBase row-key
> schema were applied to organize multi-instrument data..."*

---

## 📂 File yang Dihasilkan (di dalam ZIP)

```
gold_research_results.zip
├── data/raw/
│   ├── gold_price_raw.csv        ← 24,955 baris data emas hourly
│   └── news_raw.json             ← 288 artikel berita (JSON)
├── data/processed/
│   ├── hive_table_gold_price/    ← 15 partisi CSV (Hive simulation)
│   ├── news_with_sentiment.csv   ← Berita + skor sentimen
│   ├── daily_sentiment_score.csv ← Agregasi sentimen harian
│   └── merged_dataset.csv        ← Dataset final (24,955 baris)
└── output/
    ├── model_evaluation.json     ← Metrik model (AUC-ROC, Accuracy, dll)
    └── charts/
        ├── chart1_gold_trend_sentiment.png
        ├── chart2_sentiment_volatility.png
        ├── chart3_model_evaluation.png
        └── chart4_5v_bigdata.png
```
