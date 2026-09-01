"""
Script 03: Analisis Sentimen Berita (NLP - FinBERT / VADER)
===========================================================
Input   : data/raw/news_raw.json
Output  : data/processed/news_with_sentiment.csv
Metode  : 
  - VADER (cepat, berbasis lexicon) untuk validasi
  - FinBERT (akurat, transformer-based untuk teks keuangan)
  
Sentimen: POSITIVE (+1), NEGATIVE (-1), NEUTRAL (0)
Kolom Daily Aggregation: skor sentimen harian rata-rata
"""

import json
import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# KONFIGURASI
# ============================================================
INPUT_NEWS     = os.path.join("..", "data", "raw", "news_raw.json")
OUTPUT_SENT    = os.path.join("..", "data", "processed", "news_with_sentiment.csv")
OUTPUT_DAILY   = os.path.join("..", "data", "processed", "daily_sentiment_score.csv")

# ============================================================
# LOAD DATA BERITA
# ============================================================
print("[INFO] Memuat data berita...")
with open(INPUT_NEWS, "r", encoding="utf-8") as f:
    articles = json.load(f)

df = pd.DataFrame(articles)
df = df[df["info:content"].str.strip() != ""].reset_index(drop=True)
print(f"[INFO] Total {len(df)} artikel dimuat.")

# ============================================================
# METODE 1: VADER Sentiment (cepat, tidak butuh GPU)
# ============================================================
print("\n[INFO] Menjalankan VADER Sentiment Analysis...")
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # pip install vaderSentiment

vader = SentimentIntensityAnalyzer()

def vader_sentiment(text: str) -> tuple:
    if not text or len(text.strip()) < 5:
        return 0.0, "NEUTRAL"
    scores = vader.polarity_scores(str(text))
    compound = scores["compound"]
    label = "POSITIVE" if compound >= 0.05 else ("NEGATIVE" if compound <= -0.05 else "NEUTRAL")
    return round(compound, 4), label

df[["vader_score", "vader_label"]] = df["info:content"].apply(
    lambda x: pd.Series(vader_sentiment(x))
)
print(f"[OK] VADER selesai.")
print(df["vader_label"].value_counts())

# ============================================================
# METODE 2: FinBERT (lebih akurat untuk teks finansial)
# ============================================================
print("\n[INFO] Menjalankan FinBERT Sentiment Analysis (model ProsusAI/finbert)...")
try:
    from transformers import pipeline
    finbert = pipeline(
        "text-classification",
        model="ProsusAI/finbert",
        truncation=True,
        max_length=512
    )

    LABEL_MAP = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}

    def finbert_sentiment(text: str) -> tuple:
        if not text or len(text.strip()) < 10:
            return 0.0, "neutral"
        try:
            result = finbert(text[:512])[0]
            label  = result["label"].lower()
            score  = result["score"] * LABEL_MAP.get(label, 0)
            return round(score, 4), label.upper()
        except Exception:
            return 0.0, "NEUTRAL"

    print("[INFO] Memproses FinBERT batch... (harap sabar, bisa beberapa menit)")
    finbert_results = df["info:content"].apply(finbert_sentiment)
    df[["finbert_score", "finbert_label"]] = pd.DataFrame(
        finbert_results.tolist(), index=df.index
    )
    print("[OK] FinBERT selesai.")
    print(df["finbert_label"].value_counts())

    # Gunakan FinBERT sebagai skor utama
    df["sentiment_score"] = df["finbert_score"]
    df["sentiment_label"] = df["finbert_label"]

except Exception as e:
    print(f"[WARN] FinBERT gagal ({e}). Menggunakan VADER sebagai fallback.")
    df["sentiment_score"] = df["vader_score"]
    df["sentiment_label"] = df["vader_label"]

# ============================================================
# AGREGASI HARIAN (untuk digabung dengan data harga emas)
# ============================================================
df["trade_date"] = pd.to_datetime(df["info:date"]).dt.strftime("%Y-%m-%d")

daily = df.groupby("trade_date").agg(
    avg_sentiment    = ("sentiment_score", "mean"),
    total_articles   = ("sentiment_score", "count"),
    positive_count   = ("sentiment_label", lambda x: (x == "POSITIVE").sum()),
    negative_count   = ("sentiment_label", lambda x: (x == "NEGATIVE").sum()),
    neutral_count    = ("sentiment_label", lambda x: (x == "NEUTRAL").sum()),
).reset_index()

daily["avg_sentiment"] = daily["avg_sentiment"].round(4)

# ============================================================
# SIMPAN OUTPUT
# ============================================================
df_out = df[["row_key", "info:date", "info:title", "info:source",
             "sentiment_score", "sentiment_label", "vader_score"]].copy()
df_out.to_csv(OUTPUT_SENT, index=False)
print(f"\n[OK] Detail sentimen disimpan ke: {OUTPUT_SENT}")

daily.to_csv(OUTPUT_DAILY, index=False)
print(f"[OK] Skor sentimen harian disimpan ke: {OUTPUT_DAILY}")
print("\n[SELESAI] Analisis sentimen berhasil!")
print(daily.tail(10))
