"""
Script 02: Pengumpulan Data Berita Ekonomi (Data Tidak Terstruktur)
===================================================================
Sumber  : NewsAPI (newsapi.org) - Gratis untuk riset
Target  : Berita bertopik harga emas, inflasi, dan ekonomi global
Output  : data/raw/news_raw.json (simulasi HBase input)
          data/processed/hbase_table_news/ (simulasi HBase - row key = tanggal+id)

CATATAN : Daftar API key gratis di https://newsapi.org/register
          Ganti NEWS_API_KEY di bawah dengan key Anda.
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta

# ============================================================
# KONFIGURASI
# ============================================================
NEWS_API_KEY  = "YOUR_NEWSAPI_KEY_HERE"  # Daftar gratis di https://newsapi.org/register
OUTPUT_RAW    = os.path.join("..", "data", "raw", "news_raw.json")
OUTPUT_HBASE  = os.path.join("..", "data", "processed", "hbase_table_news")
YEARS_HISTORY = 1   # NewsAPI free tier hanya 1 bulan ke belakang, 1 tahun untuk paid
KEYWORDS      = ["gold price", "inflation rate", "interest rate", "gold market", "XAU USD"]
PAGE_SIZE     = 100

os.makedirs(OUTPUT_HBASE, exist_ok=True)

# ============================================================
# FUNGSI SCRAPING
# ============================================================
def fetch_news(keyword: str, from_date: str, to_date: str) -> list:
    """Ambil berita dari NewsAPI berdasarkan keyword dan rentang tanggal."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q":        keyword,
        "from":     from_date,
        "to":       to_date,
        "language": "en",
        "sortBy":   "publishedAt",
        "pageSize": PAGE_SIZE,
        "apiKey":   NEWS_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    if resp.status_code == 200:
        return resp.json().get("articles", [])
    else:
        print(f"  [WARN] Gagal fetch '{keyword}': {resp.status_code} - {resp.text[:200]}")
        return []

# ============================================================
# MAIN: LOOP SEMUA KEYWORD
# ============================================================
all_articles = []
seen_urls    = set()  # Deduplikasi

end_dt   = datetime.today()
start_dt = end_dt - timedelta(days=30)  # Free API limit

for kw in KEYWORDS:
    print(f"[INFO] Mengambil berita untuk keyword: '{kw}'...")
    articles = fetch_news(
        keyword   = kw,
        from_date = start_dt.strftime("%Y-%m-%d"),
        to_date   = end_dt.strftime("%Y-%m-%d"),
    )
    for art in articles:
        url = art.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            # Susun record dengan format yang sesuai skema HBase
            record = {
                "row_key":      f"{art.get('publishedAt', '')[:10]}_{len(all_articles):05d}",
                "info:source":  art.get("source", {}).get("name", "Unknown"),
                "info:author":  art.get("author", "Unknown"),
                "info:title":   art.get("title", ""),
                "info:content": art.get("description", "") or art.get("content", "") or "",
                "info:date":    art.get("publishedAt", "")[:10],
                "info:url":     url,
                "meta:keyword": kw,
            }
            all_articles.append(record)
    print(f"  -> {len(articles)} artikel ditemukan, total unik sejauh ini: {len(all_articles)}")
    time.sleep(0.5)  # Hindari rate limit

# ============================================================
# SIMPAN: RAW JSON (Simulasi HDFS)
# ============================================================
with open(OUTPUT_RAW, "w", encoding="utf-8") as f:
    json.dump(all_articles, f, ensure_ascii=False, indent=2)
print(f"\n[OK] {len(all_articles)} artikel disimpan ke: {OUTPUT_RAW}")

# ============================================================
# SIMPAN: Per-file JSON (Simulasi HBase Row)
# ============================================================
for art in all_articles:
    row_key   = art["row_key"].replace(":", "-")
    date_part = art["info:date"] or "unknown"
    dir_path  = os.path.join(OUTPUT_HBASE, f"date={date_part}")
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, f"{row_key}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(art, f, ensure_ascii=False, indent=2)

print(f"[OK] Simulasi HBase disimpan di: {OUTPUT_HBASE}")
print("\n[SELESAI] Pengumpulan data berita berhasil!")
