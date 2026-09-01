# 🏆 Gold Price Predictive Analytics — Big Data Research

> **Penelitian S2 Magister Informatika** | Nusa Putra University  
> **Mata Kuliah**: Big Data Analytics  
> **Target Publikasi**: International Proceeding (Scopus Indexed)

---

## 📌 Judul Penelitian
**"Predictive Analytics of Gold Price Volatility Using Apache Spark: Integrating Macroeconomic Indicators and Global News Sentiment Analysis"**

---

## 🏗️ Arsitektur Sistem

```
[Yahoo Finance API]  →  CSV  →  HDFS/local  →  Apache Hive (Structured)
                                                        ↓
[NewsAPI]            →  JSON →  HDFS/local  →  Apache HBase (Unstructured)
                                                        ↓
                                            [Apache Spark (PySpark)]
                                             NLP Sentiment + MLlib RF
                                                        ↓
                                             Evaluation & Visualization
                                                        ↓
                                              📄 Scopus Paper
```

---

## 📂 Struktur Proyek

```
gold-research/
├── scripts/
│   ├── 01_collect_gold_price.py    # Scraping XAU/USD → Hive table
│   ├── 02_collect_news.py          # Scraping berita → HBase format
│   ├── 03_sentiment_analysis.py    # NLP: VADER + FinBERT
│   ├── 04_spark_ml_analysis.py     # PySpark MLlib (Random Forest)
│   └── 05_visualization.py         # Chart publikasi (dark mode)
├── data/
│   ├── raw/                        # Data mentah (HDFS simulation)
│   └── processed/                  # Data hasil preprocessing
│       ├── hive_table_gold_price/  # Partisi Hive (per tahun)
│       └── hbase_table_news/       # Simulasi HBase (per tanggal)
├── output/
│   ├── charts/                     # Grafik siap paper
│   └── models/                     # Spark ML model tersimpan
├── requirements.txt
└── README.md
```

---

## ⚡ Cara Menjalankan

### 1. Setup Environment (sudah dilakukan otomatis)
```powershell
pip install -r requirements.txt
```

### 2. Jalankan Pipeline Secara Berurutan
```powershell
# Set lokasi Python
$PYTHON = "C:\Users\X1 YOGA\AppData\Local\Python\pythoncore-3.14-64\python.exe"

# Step 1: Kumpulkan data harga emas
cd scripts
& $PYTHON 01_collect_gold_price.py

# Step 2: Kumpulkan berita (ganti API key di script dulu!)
& $PYTHON 02_collect_news.py

# Step 3: Analisis sentimen
& $PYTHON 03_sentiment_analysis.py

# Step 4: PySpark ML
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-11.0.31.11-hotspot"
& $PYTHON 04_spark_ml_analysis.py

# Step 5: Buat visualisasi
& $PYTHON 05_visualization.py
```

---

## 📋 Teknologi yang Digunakan

| Komponen         | Teknologi                        | Fungsi                                |
|------------------|----------------------------------|---------------------------------------|
| Data Terstruktur | Apache Hive (simulasi)           | Penyimpanan historis harga emas       |
| Data Unstructured| Apache HBase (simulasi)          | Penyimpanan teks berita (NoSQL)       |
| Distributed FS   | HDFS (simulasi lokal)            | Penyimpanan data lake                 |
| Pemrosesan       | Apache Spark (PySpark)           | In-memory distributed computing      |
| ML               | Spark MLlib (Random Forest)      | Prediksi volatilitas harga emas       |
| NLP              | FinBERT + VADER                  | Analisis sentimen teks berita         |
| Visualisasi      | Matplotlib + Seaborn             | Chart premium siap publikasi          |

---

## 🔑 Konfigurasi Penting

1. **NewsAPI Key**: Daftar gratis di https://newsapi.org/register  
   Ganti `"GANTI_DENGAN_API_KEY_ANDA"` di `scripts/02_collect_news.py`

2. **JAVA_HOME**: Sudah terinstall di  
   `C:\Program Files\Microsoft\jdk-11.0.31.11-hotspot`

---

## 📊 Output yang Diharapkan

| Output                           | Keterangan                                   |
|----------------------------------|----------------------------------------------|
| `data/raw/gold_price_raw.csv`    | Data harga emas 5 tahun                      |
| `data/raw/news_raw.json`         | Artikel berita ekonomi (JSON)                |
| `data/processed/merged_dataset.csv` | Dataset gabungan siap analisis            |
| `output/model_evaluation.json`   | Accuracy, F1, AUC-ROC model                  |
| `output/charts/chart1_*.png`     | Chart tren harga emas + sentimen             |
| `output/charts/chart2_*.png`     | Distribusi sentimen vs volatilitas           |
| `output/charts/chart3_*.png`     | Dashboard evaluasi model ML                  |
