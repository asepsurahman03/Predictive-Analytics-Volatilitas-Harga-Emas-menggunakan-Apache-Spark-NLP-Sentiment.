# RINGKASAN LENGKAP PENELITIAN — Untuk Referensi AI & Pencarian Jurnal/Prosiding

> ⚠️ **Catatan (November 2026):** ringkasan ini berasal dari versi awal penelitian. Angka di dalamnya (mis. AUC-ROC 93,83%, 288 artikel, skor 5V) sudah tidak berlaku. Hasil terbaru yang bebas *look-ahead leakage*: AUC-ROC 80,35%, recall kelas volatil 29,78%, MCC 0,38, dan 292 artikel. Rinciannya ada di `README.md` dan `output/*.json`.

> **Dokumen ini berisi deskripsi lengkap penelitian saya untuk dikirim ke AI lain.**
> Tujuan: Mendapatkan rekomendasi jurnal/prosiding Scopus yang paling cocok.

---

## 🎓 Identitas Penelitian

| | |
|---|---|
| **Program Studi** | S2 Magister Informatika |
| **Universitas** | Nusa Putra University |
| **Mata Kuliah** | Big Data Analytics |
| **Target Publikasi** | Prosiding / Jurnal Internasional Terindeks **Scopus** |

---

## 📌 Judul Penelitian

**"Predictive Analytics of Gold Price Volatility Using Apache Spark: Integrating Multi-Instrument Intraday Data and Global News Sentiment Analysis"**

*(Analisis Prediktif Volatilitas Harga Emas Menggunakan Apache Spark: Integrasi Data Intraday Multi-Instrumen dan Analisis Sentimen Berita Global)*

---

## 🔍 Latar Belakang & Motivasi

Emas (Gold / XAU) merupakan aset safe-haven yang volatilitasnya dipengaruhi oleh banyak faktor makroekonomi, geopolitik, dan sentimen pasar global. Prediksi volatilitas harga emas memiliki nilai strategis tinggi bagi investor, manajer risiko, dan pengambil kebijakan ekonomi.

Penelitian sebelumnya umumnya menggunakan:
- Hanya data harga harian (Daily) → kurang granular
- Satu instrumen saja (misalnya hanya Gold Futures) → tidak komprehensif
- Analisis statistik konvensional → tidak skalabel untuk Big Data

**Celah penelitian (Research Gap):**
1. Belum ada penelitian yang menggabungkan **data intraday multi-instrumen** emas (Futures + beberapa ETF) dalam satu pipeline Big Data terpadu
2. Analisis sentimen berita belum diintegrasikan secara langsung ke dalam model prediksi volatilitas harga emas menggunakan ekosistem Hadoop-Spark

---

## 🎯 Tujuan Penelitian

1. Membangun pipeline Big Data end-to-end menggunakan ekosistem Hadoop (HDFS, Hive, HBase) dan Apache Spark
2. Mengumpulkan dan memproses data multi-instrumen emas dalam granularitas per jam (hourly)
3. Mengintegrasikan analisis sentimen berita keuangan global (NLP) dengan data harga
4. Melatih dan mengevaluasi model Machine Learning (Random Forest - Spark MLlib) untuk memprediksi volatilitas harga emas
5. Membuktikan penerapan konsep 5V Big Data (Volume, Velocity, Variety, Veracity, Value) dalam konteks finansial

---

## 📐 Metodologi

### Arsitektur Sistem (Big Data Pipeline)

```
[Yahoo Finance API]  →  Hourly CSV  →  Local File System (HDFS-compatible)  →  Apache Hive
                                                                                (15 partisi: ticker × tahun)
                                                                                       ↓
[NewsAPI]            →  JSON        →  Local File System (HDFS-compatible)  →  Apache HBase
                                                                                (NoSQL: row key = date+id)
                                                                                       ↓
                                                                        [Apache Spark PySpark 4.2.0]
                                                                           ├── NLP Sentiment (VADER)
                                                                           ├── Feature Engineering
                                                                           ├── Spark MLlib Pipeline
                                                                           └── Random Forest Classifier
                                                                                       ↓
                                                                           Model Evaluation + Charts
```

> **Catatan Deployment**: Pipeline dijalankan menggunakan Apache Spark 4.2.0 dalam
> konfigurasi *single-node local deployment* yang merupakan pendekatan umum dalam
> penelitian akademis. Struktur partisi Hive (ticker × tahun) dan skema row-key HBase
> diterapkan secara konsisten dengan standar ekosistem Hadoop.

### Teknologi yang Digunakan

| Komponen | Teknologi | Versi |
|----------|-----------|-------|
| Bahasa Pemrograman | Python | 3.14 |
| Big Data Engine | Apache Spark (PySpark) | 4.2.0 |
| Runtime Java | Microsoft OpenJDK (Hotspot) | 17.0.19 |
| Data Warehouse (Structured) | Apache Hive — partisi CSV (ticker × tahun) | — |
| NoSQL Database (Unstructured) | Apache HBase — row-key JSON (date+article_id) | — |
| Distributed File System | HDFS-compatible local filesystem | — |
| ML Library | Spark MLlib | 4.2.0 |
| NLP Sentiment | VADER (vaderSentiment) | 3.3.2 |
| Data Collection | yfinance, requests | — |
| Visualisasi | Matplotlib, Seaborn | — |
| OS | Windows 11 | — |

---

## 📦 Dataset

### Data Terstruktur — Harga Emas Multi-Instrumen (Hourly)

| Instrumen | Kode | Deskripsi | Jumlah Baris |
|-----------|------|-----------|-------------|
| Gold Futures COMEX | GC=F | Kontrak berjangka emas (trading 23 jam/hari) | 11.275 |
| SPDR Gold Shares ETF | GLD | ETF emas terbesar di dunia | 3.420 |
| iShares Gold Trust ETF | IAU | ETF emas BlackRock | 3.420 |
| VanEck Gold Miners ETF | GDX | ETF perusahaan tambang emas | 3.420 |
| Junior Gold Miners ETF | GDXJ | ETF perusahaan tambang emas kecil | 3.420 |
| **TOTAL** | | | **24.955 baris** |

- **Periode**: Agustus 2024 – Juli 2026 (~2 tahun)
- **Granularitas**: Per jam (hourly, interval 1h)
- **Kolom**: trade_datetime, open, high, low, close, volume, pct_change, price_range, is_volatile, trade_hour, month, day_of_week
- **Sumber**: Yahoo Finance API (via `yfinance`)
- **Penyimpanan**: 15 partisi Hive (ticker × tahun)

### Data Tidak Terstruktur — Berita Keuangan Global

| Parameter | Nilai |
|-----------|-------|
| Total Artikel | 288 artikel |
| Keyword Pencarian | "gold price", "inflation rate", "interest rate", "gold market", "XAU USD" |
| Periode | 30 hari terakhir (NewsAPI free tier) |
| Format | JSON (simulasi HBase) |
| Sumber | NewsAPI (newsapi.org) |
| Analisis Sentimen | VADER (Positive: 160, Negative: 77, Neutral: 51) |

---

## ⚙️ Feature Engineering

Fitur yang digunakan dalam model ML (17 fitur total):

| # | Fitur | Deskripsi |
|---|-------|-----------|
| 1 | `open_price` | Harga pembukaan per jam |
| 2 | `high_price` | Harga tertinggi per jam |
| 3 | `low_price` | Harga terendah per jam |
| 4 | `close_price` | Harga penutupan per jam |
| 5 | `price_range` | High - Low (rentang harga) |
| 6 | `trade_hour` | Jam trading (0-23) |
| 7 | `month` | Bulan (1-12) |
| 8 | `day_of_week` | Hari (0=Senin, 6=Minggu) |
| 9 | `avg_sentiment` | Rata-rata skor sentimen berita harian |
| 10 | `total_articles` | Jumlah artikel berita pada hari tersebut |
| 11 | `positive_count` | Jumlah artikel berita positif |
| 12 | `negative_count` | Jumlah artikel berita negatif |
| 13 | `prev_close` | Harga penutupan jam sebelumnya (lag-1) |
| 14 | `prev_sentiment` | Sentimen jam sebelumnya (lag-1) |
| 15 | `ma_7h` | Moving Average 7 jam |
| 16 | `ma_24h` | Moving Average 24 jam |
| 17 | `volatility_7h` | Standar deviasi pct_change 7 jam terakhir |

**Target Variable (Label):**
- `is_volatile` = 1 jika `|pct_change| > 0.5%` per jam, 0 jika stabil

---

## 🤖 Model Machine Learning

**Algoritma**: Random Forest Classifier (Spark MLlib)
- Jumlah pohon: 100
- Max depth: 8
- Pipeline: VectorAssembler → StandardScaler → RandomForestClassifier

**Split Data**:
- Train: 19.960 baris (80%)
- Test: 4.990 baris (20%)
- Metode: Chronological split (tidak random, untuk menghindari data leakage)

---

## 📊 Hasil Evaluasi Model

| Metrik | Nilai |
|--------|-------|
| **Accuracy** | **88.28%** |
| **F1-Score** | **88.12%** |
| **Precision** | **88.02%** |
| **Recall** | **88.28%** |
| **AUC-ROC** | **93.83%** ⭐ |

### Feature Importance (Top 5):

| Rank | Fitur | Importance | Insight |
|------|-------|-----------|---------|
| 1 | `price_range` | 32.85% | Rentang harga/jam = proksi volatilitas terkuat |
| 2 | `trade_hour` | 22.14% | **Pola intraday** — jam perdagangan berpengaruh signifikan |
| 3 | `volatility_7h` | 21.68% | Momentum volatilitas jangka pendek |
| 4 | `ma_7h` | 3.76% | Moving average jangka pendek |
| 5 | `ma_24h` | 3.43% | Moving average harian |

---

## 💡 Temuan Utama (Key Findings)

1. **Pola Intraday pada Volatilitas Emas**: Jam trading (`trade_hour`) merupakan fitur ke-2 terpenting dalam memprediksi volatilitas, mengindikasikan adanya pola waktu yang konsisten — emas cenderung lebih volatil pada jam-jam tertentu (misalnya pembukaan sesi London dan New York).

2. **Dominasi Fitur Teknikal**: Fitur berbasis harga (price_range, volatility_7h) jauh lebih prediktif dibanding fitur sentimen berita dalam granularitas per jam. Hal ini konsisten dengan teori *efficient market hypothesis* untuk pasar intraday.

3. **Keterbatasan Sentimen (Limitation)**: Fitur sentimen berita memiliki importance mendekati 0 karena NewsAPI free tier hanya menyediakan data 30 hari terakhir, sementara data harga mencakup 2 tahun. Ini menjadi *future work* yang eksplisit.

4. **Skalabilitas Big Data**: Pipeline berhasil memproses 24.955 data points menggunakan Spark MLlib dengan AUC-ROC 93.83%, membuktikan efektivitas arsitektur Big Data untuk analisis pasar finansial.

---

## 🔬 Kontribusi Ilmiah (Scientific Contributions)

1. **Pipeline Big Data End-to-End** untuk analisis pasar emas yang mengintegrasikan HDFS, Hive, HBase, dan Spark dalam satu arsitektur terpadu
2. **Analisis Multi-Instrumen Intraday**: Pertama kali menggabungkan 5 instrumen emas (Futures + 4 ETF) dalam analisis Big Data hourly
3. **Bukti Pola Intraday**: Temuan empiris bahwa jam trading merupakan fitur prediktif signifikan untuk volatilitas emas
4. **Integrasi Data Heterogen**: Demonstrasi data fusion antara time-series keuangan (structured) dan teks berita (unstructured) dalam ekosistem Big Data

---

## 📋 5V Big Data Assessment

| V | Implementasi dalam Penelitian | Skor |
|---|-------------------------------|------|
| **Volume** | 24.955 baris data hourly, 15 partisi Hive, 288 JSON HBase | 90% |
| **Velocity** | Data per jam (23h/hari untuk GC=F), pipeline otomatis, near real-time capable | 80% |
| **Variety** | CSV terstruktur (Hive) + JSON semi-terstruktur (HBase) + teks bebas (NLP) | 90% |
| **Veracity** | Sumber resmi Yahoo Finance (COMEX) + NewsAPI, cleaning & deduplication | 85% |
| **Value** | AUC-ROC 93.83%, prediksi volatilitas untuk keputusan investasi emas | 88% |

---

## 📁 Struktur File Proyek

```
gold-research/
├── scripts/
│   ├── 01_collect_gold_price.py    # Scraping XAU multi-instrumen (hourly) → Hive
│   ├── 02_collect_news.py          # Scraping berita NewsAPI → HBase (JSON)
│   ├── 03_sentiment_analysis.py    # NLP: VADER sentiment analysis
│   ├── 04_spark_ml_analysis.py     # PySpark MLlib: Feature Eng + Random Forest
│   └── 05_visualization.py         # 5 chart premium siap publikasi
├── data/
│   ├── raw/
│   │   ├── gold_price_raw.csv      # 24.955 baris data mentah
│   │   └── news_raw.json           # 288 artikel berita (JSON)
│   └── processed/
│       ├── hive_table_gold_price/  # 15 partisi CSV (ticker × tahun)
│       ├── hbase_table_news/       # Simulasi HBase (JSON per tanggal)
│       ├── news_with_sentiment.csv # Data berita + skor sentimen
│       ├── daily_sentiment_score.csv # Agregasi sentimen harian
│       └── merged_dataset.csv      # Dataset gabungan (24.955 baris)
├── output/
│   ├── charts/
│   │   ├── chart1_gold_trend_sentiment.png   # Tren harga + sentimen
│   │   ├── chart2_sentiment_volatility.png   # Distribusi + korelasi
│   │   ├── chart3_model_evaluation.png       # Dashboard evaluasi ML
│   │   ├── chart4_5v_bigdata.png             # Radar 5V Big Data
│   │   └── chart5_architecture.png           # Arsitektur pipeline
│   ├── models/rf_model/            # Model Spark MLlib tersimpan
│   └── model_evaluation.json       # Metrik evaluasi (JSON)
└── requirements.txt
```

---

## ❓ Pertanyaan untuk AI / Rekomendasi yang Dibutuhkan

Tolong rekomendasikan **5-10 prosiding atau jurnal internasional terindeks Scopus** yang paling cocok untuk penelitian ini, dengan mempertimbangkan:

1. **Topik**: Big Data, Machine Learning, Analisis Pasar Keuangan, Prediksi Harga Komoditas
2. **Teknologi**: Apache Spark, Hadoop Ecosystem, NLP, Random Forest
3. **Level**: Cocok untuk mahasiswa S2 / peneliti early-career
4. **Format**: Prosiding (Conference Proceedings) **lebih diutamakan** daripada jurnal biasa, karena lebih cepat proses reviewnya
5. **Scope**: Informatika, Computer Science, Data Science, Financial Technology (FinTech)
6. **Impact**: Terindeks Scopus Q1-Q4, atau minimal terindeks IEEE Xplore / SpringerLink / ACM Digital Library

Untuk setiap rekomendasi, tolong sertakan:
- Nama lengkap prosiding/jurnal
- Link website / URL submission
- Deadline submission terdekat (jika diketahui)
- Impact Factor / CiteScore / Quartile Scopus
- Alasan mengapa cocok dengan penelitian ini
- Estimasi biaya publikasi (APC / gratis)
