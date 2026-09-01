<div align="center">

# 🌟 Predictive Analytics of Gold Price Volatility Using Apache Spark
### *Integrating Multi-Instrument Intraday Data and Global News Sentiment Analysis*

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-4.2.0-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![PySpark MLlib](https://img.shields.io/badge/MLlib-Random%20Forest-FF6F00?style=for-the-badge&logo=spark&logoColor=white)](https://spark.apache.org/mllib/)
[![NLP Sentiment](https://img.shields.io/badge/NLP-VADER%20Sentiment-4B8BBE?style=for-the-badge&logo=natural-language-processing&logoColor=white)](https://github.com/cjhutto/vaderSentiment)
[![Target Scopus](https://img.shields.io/badge/Target-Scopus%20Indexed%20Proceeding-007396?style=for-the-badge&logo=scopus&logoColor=white)](https://www.scopus.com/)
[![Open In Colab](https://img.shields.io/badge/Google%20Colab-Ready-F9AB00?style=for-the-badge&logo=googlecolab&logoColor=white)](https://colab.research.google.com/)

<p align="center">
  <b>🎓 Tesis/Penelitian S2 Magister Informatika — Nusa Putra University</b><br>
  <i>Bidang Keahlian: Big Data Analytics, FinTech & Machine Learning</i>
</p>

---

</div>

## 📌 Ringkasan Eksekutif (Executive Summary)

Penelitian ini mengimplementasikan **arsitektur pipeline Big Data end-to-end** untuk memprediksi volatilitas harga emas (*Gold / XAU*) secara *intraday* (granularitas per jam). Penelitian ini menjembatani kesenjangan riset sebelumnya dengan mengintegrasikan **data harga multi-instrumen (Futures + 4 ETF emas)** bersama **analisis sentimen berita keuangan global (NLP)** menggunakan ekosistem terdistribusi **Hadoop (HDFS, Hive, HBase)** dan **Apache Spark (PySpark MLlib)**.

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 BIG DATA INGESTION                     │
                  │   Yahoo Finance API (Hourly)  +  NewsAPI Global Feed   │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │               DISTRIBUTED STORAGE LAYER                │
                  │  Structured (Hive: 15 partitions) + Unstructured (HBase)│
                  └──────────────────────────┬─────────────────────────────┘
                                             │
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │         APACHE SPARK DISTRIBUTED COMPUTING             │
                  │      PySpark 4.2.0 | VADER NLP | Feature Pipelines     │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │        PREDICTIVE MODELING & VISUAL ANALYTICS          │
                  │  Spark MLlib Random Forest | AUC: 93.83% | 5V Radar    │
                  └────────────────────────────────────────────────────────┘
```

---

## 🏆 Kinerja Model & Hasil Utama (Key Results)

Model prediktif dilatih menggunakan **Random Forest Classifier (Spark MLlib)** dengan evaluasi *chronological split* (80/20) untuk menghindari *look-ahead data leakage*.

### 📊 Metrik Evaluasi

| Metrik | Skor | Keterangan |
|:---|:---:|:---|
| **⭐ AUC-ROC** | **`93.83%`** | Kemampuan diskriminasi kelas volatilitas luar biasa tinggi |
| **🎯 Accuracy** | **`88.28%`** | Ketepatan klasifikasi total kondisi pasar |
| **⚖️ F1-Score** | **`88.12%`** | Keseimbangan presisi dan sensitivitas model |
| **🔍 Precision**| **`88.02%`** | Ketepatan saat mendeteksi lonjakan volatilitas |
| **📡 Recall**   | **`88.28%`** | Rasio deteksi lonjakan volatilitas aktual |

### 🔍 Top-5 Fitur Paling Berpengaruh (Feature Importance)
1. 🥇 **`price_range` (32.85%)** — Rentang fluktuasi harga (*High - Low*) per jam.
2. 🥈 **`trade_hour` (22.14%)** — **Pola Intraday**; jam pembukaan sesi London & New York memberikan dampak lonjakan volatilitas terbesar.
3. 🥉 **`volatility_7h` (21.68%)** — Momentum deviasi standar pergerakan harga 7 jam ke belakang.
4. 🔹 **`ma_7h` (3.76%)** — *Moving Average* jangka pendek.
5. 🔹 **`ma_24h` (3.43%)** — *Moving Average* tren harian.

---

## 🔬 Bukti Implementasi 5V Big Data

| Pilar 5V | Implementasi Riil dalam Repositori | Rating |
|:---|:---|:---:|
| **Volume** | **24.955** baris data *hourly* 2 tahun, **15 partisi Hive**, 288 dokumen HBase | **90%** |
| **Velocity** | Data per jam (23 jam/hari), ingestion otomatis, siap *streaming batch* | **80%** |
| **Variety** | Heterogen: CSV Terstruktur (Hive) + JSON Semi-Terstruktur (HBase) + Teks Bebas (NLP) | **90%** |
| **Veracity** | Validasi Yahoo Finance COMEX + verifikasi NewsAPI global, pembersihan missing values | **85%** |
| **Value** | Model klasifikasi volatilitas berakurasi tinggi untuk mitigasi risiko investasi | **88%** |

---

## 📈 Galeri Visualisasi Penelitian (High-Res Charts)

Visualisasi grafik diproduksi dengan resolusi tinggi (300 DPI) dalam format publikasi:

| Chart | Deskripsi |
|:---:|:---|
| ![Tren & Sentimen](output/charts/chart1_gold_trend_sentiment.png) | **Chart 1: Tren Fluktuasi Harga Multi-Instrumen & Distribusi Sentimen Berita Global** |
| ![Korelasi Sentimen](output/charts/chart2_sentiment_volatility.png) | **Chart 2: Analisis Sentimen VADER vs Volatilitas Harga Emas** |
| ![Evaluasi Model](output/charts/chart3_model_evaluation.png) | **Chart 3: Dashboard Kinerja Model Spark MLlib & Feature Importance** |
| ![Radar 5V](output/charts/chart4_5v_bigdata.png) | **Chart 4: Radar Assessment 5V Big Data Architecture** |
| ![Arsitektur Pipeline](output/charts/chart5_architecture.png) | **Chart 5: Diagram Alir Pipeline Terdistribusi End-to-End** |

---

## 📦 Dataset Multi-Instrumen

Dataset terstruktur mencakup 5 instrumen emas global (periode Agustus 2024 – Juli 2026):

| Simbol Ticker | Nama Instrumen | Granularitas | Baris Data |
|:---:|:---|:---:|:---:|
| **`GC=F`** | Gold Futures COMEX (Primary) | 1 Jam (23h/hari) | 11.275 |
| **`GLD`** | SPDR Gold Shares ETF | 1 Jam | 3.420 |
| **`IAU`** | iShares Gold Trust ETF (BlackRock) | 1 Jam | 3.420 |
| **`GDX`** | VanEck Gold Miners ETF | 1 Jam | 3.420 |
| **`GDXJ`** | VanEck Junior Gold Miners ETF | 1 Jam | 3.420 |
| **TOTAL** | **Multi-Instrument Time-Series** | **Hourly** | **24.955** |

---

## 📂 Struktur Repositori

```bash
├── Artikel/                     # Naskah ilmiah (Word / LaTeX template publikasi)
├── data/
│   ├── raw/                     # Data mentah: gold_price_raw.csv & news_raw.json
│   └── processed/               # Data terstruktur hasil Hive & HBase
├── output/
│   ├── charts/                  # 5 Grafik visualisasi resolusi tinggi (PNG)
│   └── model_evaluation.json    # Log metrik evaluasi model (JSON)
├── scripts/
│   ├── 01_collect_gold_price.py # Scraping multi-instrument Yahoo Finance -> Hive
│   ├── 02_collect_news.py       # Scraping berita pasar global -> HBase format
│   ├── 03_sentiment_analysis.py # VADER NLP Sentiment scoring & data fusion
│   ├── 04_spark_ml_analysis.py  # Spark MLlib Feature Pipeline & Random Forest
│   └── 05_visualization.py      # Generator 5 grafik analisis publikasi
├── COLAB_NOTEBOOK.py            # Standalone pipeline siap Google Colab
├── gold_price_research.ipynb    # Jupyter Notebook interaktif
├── PANDUAN_GOOGLE_COLAB.md      # Panduan eksekusi di Cloud Google Colab
├── RINGKASAN_PENELITIAN_UNTUK_AI.md # Ringkasan riset lengkap
├── requirements.txt             # Dependensi Python
└── README.md                    # Dokumentasi utama proyek
```

---

## ⚡ Panduan Menjalankan (Quick Start)

### 1. Kloning Repositori
```bash
git clone https://github.com/asepsurahman03/Predictive-Analytics-Volatilitas-Harga-Emas-menggunakan-Apache-Spark-NLP-Sentiment..git
cd Predictive-Analytics-Volatilitas-Harga-Emas-menggunakan-Apache-Spark-NLP-Sentiment.
```

### 2. Pasang Dependensi
```bash
pip install -r requirements.txt
```

### 3. Eksekusi Pipeline Otomatis
```bash
# Jalankan seluruh modul secara sekuensial
python scripts/01_collect_gold_price.py
python scripts/02_collect_news.py
python scripts/03_sentiment_analysis.py
python scripts/04_spark_ml_analysis.py
python scripts/05_visualization.py
```

> 💡 **Ingin menjalankan di Google Colab?** Buka [PANDUAN_GOOGLE_COLAB.md](PANDUAN_GOOGLE_COLAB.md) untuk langkah *1-click run* gratis di GPU/CPU cloud!

---

## 🛠️ Stack Teknologi

* **Big Data Distributed Engine**: [Apache Spark 4.2.0](https://spark.apache.org/) (PySpark)
* **Data Storage / Warehousing**: HDFS (Compatible Lake), Apache Hive Schema, Apache HBase JSON
* **Machine Learning**: Spark MLlib (`VectorAssembler`, `StandardScaler`, `RandomForestClassifier`)
* **Natural Language Processing**: VADER Sentiment Analysis (`vaderSentiment`)
* **Data Retrieval**: `yfinance`, `NewsAPI`, `requests`
* **Visualisasi Ilmiah**: `matplotlib`, `seaborn`

---

## ✍️ Sitasi & Peneliti

Jika penelitian atau kode ini bermanfaat bagi studi Anda, silakan rujuk:

```bibtex
@mastersthesis{asepsurahman2026goldvolatility,
  author       = {Asep Surahman},
  title        = {Predictive Analytics of Gold Price Volatility Using Apache Spark: Integrating Multi-Instrument Intraday Data and Global News Sentiment Analysis},
  school       = {Magister Informatika, Universitas Nusa Putra},
  year         = {2026},
  note         = {Big Data Analytics Research}
}
```

<div align="center">
  <sub>Dibuat untuk memenuhi tugas & publikasi <b>Magister Teknik Informatika - Universitas Nusa Putra</b>.</sub>
</div>
