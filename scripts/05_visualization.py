"""
Script 05: Visualisasi Hasil Penelitian — Light Mode / Academic Style
=======================================================================
Gaya: White background, Times New Roman, warna akademis (cocok untuk paper IEEE)
Input  : data/processed/merged_dataset.csv, output/model_evaluation.json
Output : output/charts/*.png (siap cetak di paper)
"""

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import seaborn as sns
import json, os, warnings
warnings.filterwarnings("ignore")

# ============================================================
# SETUP: Academic Light Mode — Times New Roman
# ============================================================
matplotlib.rcParams.update({
    # Canvas
    "figure.dpi":           150,
    "figure.facecolor":     "white",
    "figure.edgecolor":     "white",
    # Axes
    "axes.facecolor":       "#F8F9FA",
    "axes.edgecolor":       "#333333",
    "axes.linewidth":       0.8,
    "axes.labelcolor":      "#1a1a1a",
    "axes.labelsize":       10,
    "axes.titlesize":       11,
    "axes.titleweight":     "bold",
    "axes.titlecolor":      "#1a1a1a",
    "axes.spines.top":      False,
    "axes.spines.right":    False,
    # Ticks
    "xtick.color":          "#333333",
    "ytick.color":          "#333333",
    "xtick.labelsize":      9,
    "ytick.labelsize":      9,
    # Grid
    "grid.color":           "#DDDDDD",
    "grid.linestyle":       "--",
    "grid.linewidth":       0.5,
    "grid.alpha":           0.8,
    # Font — Times New Roman
    "font.family":          "serif",
    "font.serif":           ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size":            10,
    "text.color":           "#1a1a1a",
    # Legend
    "legend.framealpha":    0.9,
    "legend.edgecolor":     "#CCCCCC",
    "legend.fontsize":      9,
    # Lines
    "lines.linewidth":      1.5,
    "lines.antialiased":    True,
    # Save
    "savefig.bbox":         "tight",
    "savefig.dpi":          200,
    "savefig.facecolor":    "white",
})

# Academic color palette
C_GOLD   = "#B8860B"   # Dark goldenrod
C_BLUE   = "#1F77B4"   # Matplotlib blue
C_RED    = "#D62728"   # Matplotlib red
C_GREEN  = "#2CA02C"   # Matplotlib green
C_ORANGE = "#FF7F0E"   # Matplotlib orange
C_PURPLE = "#9467BD"   # Matplotlib purple
C_GRAY   = "#7F7F7F"

# ============================================================
# PATHS
# ============================================================
BASE   = os.path.dirname(os.path.abspath(__file__))
ROOT   = os.path.join(BASE, "..")
DATA   = os.path.join(ROOT, "data", "processed")
CHARTS = os.path.join(ROOT, "output", "charts")
EVAL   = os.path.join(ROOT, "output", "model_evaluation.json")
os.makedirs(CHARTS, exist_ok=True)

# ============================================================
# LOAD DATA
# ============================================================
print("[INFO] Memuat dataset...")
df = pd.read_csv(os.path.join(DATA, "merged_dataset.csv"), parse_dates=["trade_date"])
df = df.sort_values("trade_date").reset_index(drop=True)
print(f"[OK] Dataset: {len(df):,} baris, dari {df['trade_date'].min().date()} s.d. {df['trade_date'].max().date()}")

# Filter satu instrumen utama untuk plot tren
df_gc = df[df["instrument_name"] == "Gold Futures (COMEX)"].copy()

# Load evaluasi model
with open(EVAL) as f:
    eval_res = json.load(f)

# ============================================================
# CHART 1 — Tren Harga Emas + Sentimen (Academic Style)
# ============================================================
print("\n[INFO] Membuat Chart 1: Tren Harga Emas...")

# Agregasi harian untuk plot bersih
daily = df_gc.groupby("trade_date").agg(
    close_price   = ("close_price", "last"),
    avg_sentiment = ("avg_sentiment", "mean"),
    is_volatile   = ("is_volatile", "max"),
    pct_change    = ("pct_change", "mean")
).reset_index()

fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True,
                          gridspec_kw={"height_ratios": [3, 1, 1]})
fig.suptitle("Fig. 2.  Gold Futures (GC=F): Price Dynamics and News Sentiment\n"
             "Hourly Data, August 2024 – July 2026",
             fontsize=11, fontweight="bold", y=0.98)
fig.subplots_adjust(hspace=0.08)

# --- Panel 1: Harga Emas ---
ax1 = axes[0]
ax1.plot(daily["trade_date"], daily["close_price"], color=C_GOLD,
         lw=1.5, label="Daily Close Price (USD/oz)")
ax1.fill_between(daily["trade_date"], daily["close_price"],
                 daily["close_price"].min() * 0.99,
                 alpha=0.12, color=C_GOLD)
vol_days = daily[daily["is_volatile"] == 1]
ax1.scatter(vol_days["trade_date"], vol_days["close_price"],
            color=C_RED, s=6, alpha=0.5, label="Next-Hour Volatile (t+1 label)", zorder=5)
ax1.set_ylabel("Close Price (USD/oz)", fontsize=10)
ax1.legend(loc="upper left", fontsize=9)
ax1.grid(True)
ax1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
    lambda x, _: f"${x:,.0f}"))

# --- Panel 2: Daily Return ---
ax2 = axes[1]
colors_ret = [C_GREEN if r >= 0 else C_RED for r in daily["pct_change"]]
ax2.bar(daily["trade_date"], daily["pct_change"],
        color=colors_ret, alpha=0.75, width=0.5)
ax2.axhline(0, color="#333333", lw=0.7, ls="-")
ax2.set_ylabel("Avg Hourly\nReturn (%)", fontsize=9)
ax2.grid(True)

# --- Panel 3: Sentimen ---
ax3 = axes[2]
colors_sent = [C_GREEN if s > 0 else (C_RED if s < 0 else C_GRAY)
               for s in daily["avg_sentiment"]]
ax3.bar(daily["trade_date"], daily["avg_sentiment"],
        color=colors_sent, alpha=0.75, width=0.5)
ax3.axhline(0, color="#333333", lw=0.7, ls="-")
ax3.set_ylabel("News Sentiment\n(VADER)", fontsize=9)
ax3.set_xlabel("Date", fontsize=10)
ax3.grid(True)
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

for ax in axes:
    ax.set_facecolor("#F8F9FA")

plt.savefig(os.path.join(CHARTS, "chart1_gold_trend_sentiment.png"))
plt.close()
print(f"[OK] chart1_gold_trend_sentiment.png")

# ============================================================
# CHART 2 — Distribusi Sentimen vs Volatilitas + Korelasi
# ============================================================
print("\n[INFO] Membuat Chart 2: Distribusi Sentimen vs Volatilitas...")

# Judul figure diberikan oleh caption IEEE di paper (tanpa suptitle)
fig, axes = plt.subplots(1, 2, figsize=(11, 5))

# --- Panel kiri: Violin + Box ---
ax = axes[0]
df["Volatility"] = df["is_volatile"].map({0: "Stable", 1: "Volatile"})
palette = {"Stable": C_BLUE, "Volatile": C_RED}
sns.violinplot(data=df, x="Volatility", y="avg_sentiment",
               palette=palette, ax=ax, inner="box",
               order=["Stable", "Volatile"])
ax.set_title("(a) VADER Sentiment by Volatility Class", fontsize=10, fontweight="bold")
ax.set_xlabel("Volatility Class", fontsize=10)
ax.set_ylabel("VADER Compound Score", fontsize=10)
ax.set_facecolor("#F8F9FA")
ax.grid(True, axis="y")

# n-count di label sumbu-x agar tidak tertimpa garis violin
counts = df["Volatility"].value_counts()
ax.set_xticks([0, 1])
ax.set_xticklabels([f"{c}\n(n={counts[c]:,})" for c in ["Stable", "Volatile"]])

# --- Panel kanan: Correlation Heatmap ---
ax2 = axes[1]
corr_cols = ["close_price", "pct_change", "avg_sentiment",
             "price_range", "trade_hour", "volatility_7h", "is_volatile"]
corr_cols = [c for c in corr_cols if c in df.columns]
cm = df[corr_cols].corr()
nice_labels = {
    "close_price": "Close Price",
    "pct_change":  "Pct Change",
    "avg_sentiment": "Sentiment",
    "price_range": "Price Range",
    "trade_hour":  "Trade Hour",
    "volatility_7h": "Vol. 7h",
    "is_volatile": "Is Volatile"
}
cm.index   = [nice_labels.get(c, c) for c in cm.index]
cm.columns = [nice_labels.get(c, c) for c in cm.columns]

mask = np.zeros_like(cm, dtype=bool)
mask[np.triu_indices_from(mask, k=1)] = True
sns.heatmap(cm, ax=ax2, annot=True, fmt=".2f", cmap="RdYlGn",
            linewidths=0.5, annot_kws={"size": 8},
            vmin=-1, vmax=1, square=True,
            cbar_kws={"shrink": 0.8, "label": "Pearson r"})
ax2.set_title("(b) Pearson Correlation Matrix", fontsize=10, fontweight="bold")
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha="right", fontsize=8)
ax2.set_yticklabels(ax2.get_yticklabels(), rotation=0, fontsize=8)

plt.tight_layout()
plt.savefig(os.path.join(CHARTS, "chart2_sentiment_volatility.png"))
plt.close()
print(f"[OK] chart2_sentiment_volatility.png")

# ============================================================
# CHART 3 — Model Evaluation Dashboard
# ============================================================
print("\n[INFO] Membuat Chart 3: Model Evaluation Dashboard...")

# Only keep the 5 core float metrics (exclude experiment_note, n_train, etc.)
METRIC_KEYS = ["Accuracy", "F1-Score", "Precision", "Recall", "AUC-ROC"]
metrics    = {k: v for k, v in eval_res.items() if k in METRIC_KEYS}
feat_data  = eval_res.get("feature_importance", {})
metric_labels = list(metrics.keys())
metric_vals   = list(metrics.values())

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Fig. 4.  Random Forest Classifier Evaluation — Apache Spark MLlib 4.2.0\n"
             "[Leakage-Free: Features at t → Predicts Volatility at t+1]",
             fontsize=11, fontweight="bold")

# --- Panel kiri: Metrik Bar Chart ---
ax = axes[0]
colors_m = [C_GOLD, C_GREEN, C_BLUE, C_PURPLE, C_RED]
bars = ax.barh(metric_labels, metric_vals, color=colors_m[:len(metric_labels)],
               alpha=0.85, height=0.55, edgecolor="white", linewidth=0.5)
ax.set_xlim(0, 1.12)
ax.set_xlabel("Score", fontsize=10)
ax.set_title("(a) Performance Metrics", fontsize=10, fontweight="bold")
ax.set_facecolor("#F8F9FA")
for bar, val in zip(bars, metric_vals):
    ax.text(val + 0.01, bar.get_y() + bar.get_height() / 2,
            f"{val:.4f}", va="center", ha="left", fontsize=10,
            fontweight="bold", color="#1a1a1a")
ax.grid(True, axis="x", alpha=0.5)
ax.set_axisbelow(True)

# Highlight AUC-ROC dynamically from JSON
auc_val = eval_res.get("AUC-ROC", 0.9383)
ax.axvline(auc_val, color=C_RED, ls="--", lw=1, alpha=0.7, label=f"AUC-ROC = {auc_val:.4f}")
ax.legend(fontsize=9)

# --- Panel kanan: Feature Importance ---
ax2 = axes[1]
if feat_data:
    top10 = sorted(feat_data.items(), key=lambda x: -x[1])[:10]
    fn = [x[0] for x in top10][::-1]
    fv = [x[1] for x in top10][::-1]
    def _bar_color(f):
        if "trade_hour" in f: return C_RED
        if "price_range" in f: return C_PURPLE
        return C_BLUE
    colors_f = [_bar_color(f) for f in fn]
    bars2 = ax2.barh(fn, fv, color=colors_f, alpha=0.82,
                     height=0.55, edgecolor="white", linewidth=0.5)
    ax2.set_xlabel("Importance Score", fontsize=10)
    ax2.set_title("(b) Top-10 Feature Importance", fontsize=10, fontweight="bold")
    ax2.set_facecolor("#F8F9FA")
    for bar, val in zip(bars2, fv):
        ax2.text(val + 0.002, bar.get_y() + bar.get_height() / 2,
                 f"{val:.3f}", va="center", fontsize=8.5)
    ax2.grid(True, axis="x", alpha=0.5)
    ax2.set_axisbelow(True)
    # Ensure right margin wide enough; annotation placed INSIDE (left of bar) to avoid clipping
    max_fv = max(fv) if fv else 0.45
    ax2.set_xlim(0, max_fv * 1.55)
    for i, f in enumerate(fn):
        if f == "trade_hour":
            ax2.annotate(
                "Novel finding\n(Intraday Seasonality)",
                xy=(fv[i], i),
                xytext=(fv[i] * 0.5, i - 0.8),
                fontsize=8, color=C_RED, fontweight="bold",
                ha="center", va="top",
                arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.2),
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                          edgecolor=C_RED, alpha=0.9)
            )
            break

plt.tight_layout()
plt.savefig(os.path.join(CHARTS, "chart3_model_evaluation.png"))
plt.close()
print(f"[OK] chart3_model_evaluation.png")

# ============================================================
# CHART 4 — 5V Big Data Radar Chart (Light Mode)
# ============================================================
print("\n[INFO] Membuat Chart 4: 5V Big Data Radar Chart...")

labels  = ["Volume", "Velocity", "Variety", "Veracity", "Value"]
scores  = [0.90, 0.80, 0.90, 0.85, 0.88]
N       = len(labels)
angles  = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]
scores_plot = scores + scores[:1]

descriptions = [
    "24,955 hourly rows; 15 Hive partitions",
    "1h interval data; 23h/day (GC=F)",
    "CSV + JSON + NLP (Hive, HBase, VADER)",
    "Yahoo Finance + NewsAPI; dedup",
    f"AUC-ROC {eval_res['AUC-ROC']*100:.2f}%; next-hour volatility",
]
colors_5v = [C_BLUE, C_GREEN, C_ORANGE, C_PURPLE, C_GOLD]

# Ukuran ringkas untuk satu kolom IEEE (judul dari caption paper)
fig = plt.figure(figsize=(7.2, 3.3))

# Radar
ax_r = fig.add_subplot(121, polar=True)
ax_r.set_facecolor("#F8F9FA")
ax_r.plot(angles, scores_plot, color=C_BLUE, lw=2, zorder=5)
ax_r.fill(angles, scores_plot, color=C_BLUE, alpha=0.20)

# Reference circles
for level in [0.25, 0.5, 0.75, 1.0]:
    ax_r.plot(angles, [level] * (N + 1), color="#CCCCCC", lw=0.5, ls="--", zorder=1)

ax_r.set_xticks(angles[:-1])
ax_r.set_xticklabels(labels, fontsize=12, fontweight="bold", color="#1a1a1a")
ax_r.set_yticks([0.25, 0.5, 0.75, 1.0])
ax_r.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=9, color="#555555")
ax_r.set_ylim(0, 1.0)
ax_r.set_rlabel_position(108)
ax_r.tick_params(axis="x", pad=8)
ax_r.set_title("(a) 5V score", fontsize=12, fontweight="bold", pad=14)

# Score dots
for angle, score, color in zip(angles[:-1], scores, colors_5v):
    ax_r.scatter(angle, score, color=color, s=50, zorder=6)

# Detail panel: label, skor, bar, deskripsi
ax_d = fig.add_subplot(122)
ax_d.set_xlim(0, 1); ax_d.set_ylim(0, 1)
ax_d.axis("off")
ax_d.set_title("(b) Per-dimension score", fontsize=12, fontweight="bold")

for i, (lbl, sc, dsc, col) in enumerate(zip(labels, scores, descriptions, colors_5v)):
    y = 0.90 - i * 0.20
    ax_d.text(0.0, y + 0.05, lbl, color=col, fontsize=12, fontweight="bold", va="center")
    ax_d.text(1.0, y + 0.05, f"{sc*100:.0f}%", color=col, fontsize=12,
              fontweight="bold", ha="right", va="center")
    ax_d.add_patch(mpatches.Rectangle((0.0, y - 0.015), 1.0, 0.035,
                                       facecolor="#E8E8E8", edgecolor="none"))
    ax_d.add_patch(mpatches.Rectangle((0.0, y - 0.015), sc, 0.035,
                                       facecolor=col, edgecolor="none", alpha=0.85))
    ax_d.text(0.0, y - 0.06, dsc, color="#333333", fontsize=9, va="center")

plt.tight_layout()
plt.savefig(os.path.join(CHARTS, "chart4_5v_bigdata.png"), dpi=300)
plt.close()
print(f"[OK] chart4_5v_bigdata.png")

# ============================================================
# CHART 5 — Arsitektur Pipeline (Light Mode)
# ============================================================
print("\n[INFO] Membuat Chart 5: Arsitektur Pipeline Big Data...")

fig, ax = plt.subplots(figsize=(13, 7))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
ax.set_xlim(0, 14); ax.set_ylim(0, 7.5)
ax.axis("off")
ax.set_title("Fig. 1.  Big Data Pipeline Architecture for Gold Price Volatility Analytics",
             fontsize=11, fontweight="bold", pad=12, color="#1a1a1a")

def draw_box(ax, x, y, w, h, title, items, color, icon=""):
    """Draw a light-mode box with border."""
    rect = mpatches.FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.15",
                                    facecolor=color + "22",
                                    edgecolor=color,
                                    linewidth=2.0)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h - 0.32,
            f"{icon} {title}",
            ha="center", va="center", fontsize=9.5, fontweight="bold",
            color=color, fontfamily="Times New Roman")
    ax.axhline(y=y + h - 0.52, xmin=(x) / 14, xmax=(x + w) / 14,
               color=color, lw=0.7, alpha=0.5)
    for i, item in enumerate(items):
        if item:
            ax.text(x + w / 2, y + h - 0.78 - i * 0.42,
                    item, ha="center", va="center",
                    fontsize=8.5, color="#333333", fontfamily="Times New Roman")

def draw_arrow(ax, x1, y1, x2, y2, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="#555555",
                                lw=1.5, mutation_scale=14))
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.15, label, ha="center", fontsize=8,
                color="#555555", fontfamily="Times New Roman",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                           edgecolor="#CCCCCC", alpha=0.9))

# ---- Boxes ----
# Layer 1 — Data Sources
draw_box(ax, 0.3,  4.8, 3.0, 2.4, "Data Sources",
         ["Yahoo Finance API", "(GC=F, GLD, IAU, GDX, GDXJ)",
          "NewsAPI", "(Financial News Articles)"],
         C_BLUE, "\u2601")

# Layer 2 — Storage
draw_box(ax, 4.5,  5.6, 2.5, 1.5, "Hive Table",
         ["15 Partitions", "(ticker \u00d7 year)", "CSV Format"],
         C_GREEN, "\U0001f5c4")
draw_box(ax, 4.5,  3.8, 2.5, 1.5, "HBase Schema",
         ["288 JSON records", "Row-key: date_id", "NoSQL Format"],
         C_ORANGE, "\U0001f4cb")

# Layer 3 — Spark
draw_box(ax, 8.0,  3.8, 3.5, 3.5, "Apache Spark 4.2.0",
         ["Java 17 Runtime",
          "Spark SQL JOIN",
          "Window Functions",
          "Feature Engineering",
          "Spark MLlib Pipeline"],
         C_RED, "\u26a1")

# Layer 4 — Output
draw_box(ax, 12.0, 5.2, 1.7, 2.0, "Model",
         ["RF Classifier", "B=100 trees", "depth=8"],
         C_PURPLE, "\U0001f916")
draw_box(ax, 12.0, 2.8, 1.7, 2.0, "Results",
         [f"AUC-ROC {eval_res.get('AUC-ROC', 0.9383)*100:.2f}%",
          f"Acc. {eval_res.get('Accuracy', 0.8828)*100:.2f}%",
          "5 Charts"],
         C_GOLD, "\U0001f4ca")

# Subbox — NLP
draw_box(ax, 0.3, 2.2, 3.0, 2.0, "NLP Processing",
         ["VADER Sentiment", "Compound Score", "Daily Aggregation"],
         C_PURPLE, "\U0001f4dd")

# ---- Arrows ----
draw_arrow(ax, 3.3, 6.3, 4.5, 6.3, "Hourly CSV")
draw_arrow(ax, 3.3, 5.0, 4.5, 4.6, "JSON")
draw_arrow(ax, 3.3, 3.2, 4.5, 4.4, "News Text")
draw_arrow(ax, 7.0, 6.3, 8.0, 5.8, "Hive read")
draw_arrow(ax, 7.0, 4.5, 8.0, 5.2, "JOIN")
draw_arrow(ax, 11.5, 5.8, 12.0, 6.0, "Pipeline.fit()")
draw_arrow(ax, 11.5, 4.8, 12.0, 3.8, "Evaluate")

# Labels Layer
for label, xpos in [("Layer 1: Ingestion", 1.8),
                     ("Layer 2: Storage (Hive + HBase)", 5.75),
                     ("Layer 3: Processing (Spark)", 9.75),
                     ("Layer 4: Output", 12.85)]:
    ax.text(xpos, 1.6, label, ha="center", fontsize=8.5, color="#555555",
            fontfamily="Times New Roman", fontstyle="italic")

# HDFS bar at bottom
ax.add_patch(mpatches.FancyBboxPatch((0.2, 0.2), 13.6, 0.9,
                                      boxstyle="round,pad=0.1",
                                      facecolor="#E8F4FD", edgecolor=C_BLUE, lw=1.5))
ax.text(7.0, 0.65, "\U0001f4be  HDFS-Compatible Local Filesystem  |  "
        "5V: Volume \u2713  Velocity \u2713  Variety \u2713  Veracity \u2713  Value \u2713",
        ha="center", va="center", fontsize=9, color=C_BLUE,
        fontweight="bold", fontfamily="Times New Roman")

plt.tight_layout()
plt.savefig(os.path.join(CHARTS, "chart5_architecture.png"))
plt.close()
print(f"[OK] chart5_architecture.png")

# ============================================================
print("\n" + "=" * 55)
print("  [SELESAI] Semua 5 chart light mode berhasil dibuat!")
print(f"  -> {CHARTS}")
print("=" * 55)
