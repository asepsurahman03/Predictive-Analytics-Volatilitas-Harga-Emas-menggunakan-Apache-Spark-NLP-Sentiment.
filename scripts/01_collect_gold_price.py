"""
Script 01 (v2): Pengumpulan Data Multi-Instrumen Emas (Hourly)
=============================================================
Sumber   : Yahoo Finance via library `yfinance`
Instrumen: GC=F (Gold Futures), GLD (SPDR Gold ETF), IAU (iShares Gold ETF), GDX (Gold Miners ETF)
Interval : 1 Jam (Hourly) — Yahoo Finance menyediakan max 730 hari untuk interval ini
Target   : > 10.000 baris data terstruktur
Output   : data/raw/gold_price_raw.csv
           data/processed/hive_table_gold_price/ (simulasi Hive, partisi per ticker & tahun)
"""

import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# ============================================================
# KONFIGURASI
# ============================================================
OUTPUT_RAW   = os.path.join("..", "data", "raw", "gold_price_raw.csv")
OUTPUT_HIVE  = os.path.join("..", "data", "processed", "hive_table_gold_price")
INTERVAL     = "1h"       # Hourly — max 730 hari ke belakang
DAYS_BACK    = 720        # ~2 tahun

# Multi-instrumen: Gold Futures + ETF turunan emas
TICKERS = {
    "GC=F":  "Gold Futures (COMEX)",
    "GLD":   "SPDR Gold Shares ETF",
    "IAU":   "iShares Gold Trust ETF",
    "GDX":   "VanEck Gold Miners ETF",
    "GDXJ":  "Junior Gold Miners ETF",
}

END_DATE   = datetime.today().strftime("%Y-%m-%d")
START_DATE = (datetime.today() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")

os.makedirs(OUTPUT_HIVE, exist_ok=True)

# ============================================================
# DOWNLOAD MULTI-INSTRUMEN
# ============================================================
all_dfs = []

for ticker, desc in TICKERS.items():
    print(f"\n[INFO] Mengambil {desc} ({ticker}) [{START_DATE} s.d. {END_DATE}] interval={INTERVAL}...")
    try:
        raw = yf.download(ticker, start=START_DATE, end=END_DATE,
                          interval=INTERVAL, auto_adjust=True, progress=False)

        if raw.empty:
            print(f"  [WARN] Data kosong untuk {ticker}, skip.")
            continue

        df = raw.reset_index()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

        # Normalisasi nama kolom
        df.rename(columns={
            "Datetime": "trade_datetime",
            "Date":     "trade_datetime",
            "Open":     "open_price",
            "High":     "high_price",
            "Low":      "low_price",
            "Close":    "close_price",
            "Volume":   "volume"
        }, inplace=True)

        df.dropna(subset=["close_price"], inplace=True)

        # Tambah kolom identitas & kalkulasi
        df["ticker"]          = ticker
        df["instrument_name"] = desc
        df["trade_datetime"]  = pd.to_datetime(df["trade_datetime"])
        df["trade_date"]      = df["trade_datetime"].dt.strftime("%Y-%m-%d")
        df["trade_hour"]      = df["trade_datetime"].dt.hour
        df["year"]            = df["trade_datetime"].dt.year
        df["month"]           = df["trade_datetime"].dt.month
        df["day_of_week"]     = df["trade_datetime"].dt.dayofweek  # 0=Senin

        # Fitur teknikal
        df["price_range"]       = df["high_price"] - df["low_price"]
        df["pct_change"]        = df["close_price"].pct_change() * 100
        df["is_volatile"]       = (df["pct_change"].abs() > 0.5).astype(int)  # >0.5% per jam = volatile

        df.dropna(subset=["pct_change"], inplace=True)
        df["trade_datetime"] = df["trade_datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

        print(f"  [OK] {len(df)} baris dimuat.")
        all_dfs.append(df)

    except Exception as e:
        print(f"  [ERROR] Gagal download {ticker}: {e}")

# ============================================================
# GABUNGKAN SEMUA INSTRUMEN
# ============================================================
if not all_dfs:
    raise ValueError("[ERROR] Semua download gagal!")

merged = pd.concat(all_dfs, ignore_index=True)
merged = merged.sort_values(["ticker", "trade_datetime"]).reset_index(drop=True)

print(f"\n{'='*55}")
print(f"  TOTAL DATASET GABUNGAN: {len(merged):,} baris")
print(f"{'='*55}")
print(merged.groupby("ticker")[["close_price"]].count().rename(columns={"close_price": "jumlah_baris"}))

# ============================================================
# SIMPAN: RAW (Simulasi HDFS)
# ============================================================
merged.to_csv(OUTPUT_RAW, index=False)
print(f"\n[OK] Data RAW disimpan ke: {OUTPUT_RAW} ({len(merged):,} baris)")

# ============================================================
# SIMPAN: Hive Table (partisi per ticker × tahun)
# ============================================================
import shutil
if os.path.exists(OUTPUT_HIVE):
    shutil.rmtree(OUTPUT_HIVE)  # Reset partisi lama (dari data harian)

for (ticker, year), group in merged.groupby(["ticker", "year"]):
    part_path = os.path.join(OUTPUT_HIVE, f"ticker={ticker}", f"year={year}", "data.csv")
    os.makedirs(os.path.dirname(part_path), exist_ok=True)
    group.drop(columns=["ticker", "year"], errors="ignore").to_csv(part_path, index=False)
    print(f"  [OK] Hive {ticker}/year={year}: {len(group):,} baris")

print(f"\n[SELESAI] Total {len(merged):,} baris data multi-instrumen emas berhasil dikumpulkan!")
