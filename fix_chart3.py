"""
fix_chart3.py
=============
Regenerasi chart3_model_evaluation.png dengan perbaikan:
1. Fig. 4(a): nilai metrik dari JSON (Precision 80.66%, F1 79.22%)
2. Fig. 4(b): ranking fitur dari JSON (trade_hour rank 1: 41.06%)
3. Anotasi "Novel finding" dipindahkan agar tidak terpotong di tepi kanan
4. Tanpa suptitle (judul dari caption IEEE); anotasi trade_hour mengikuti uji confounding:
   importance trade_hour terutama berasal dari batas sesi ETF (paper Section IV-D)
"""

import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
matplotlib.use("Agg")

BASE   = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(BASE, "output", "charts")
EVAL   = os.path.join(BASE, "output", "model_evaluation.json")

with open(EVAL, encoding="utf-8") as f:
    eval_res = json.load(f)

# ── Academic Style ─────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "figure.dpi":        150,
    "figure.facecolor":  "white",
    "figure.edgecolor":  "white",
    "axes.facecolor":    "#F8F9FA",
    "axes.edgecolor":    "#333333",
    "axes.linewidth":    0.8,
    "axes.labelcolor":   "#1a1a1a",
    "axes.labelsize":    10,
    "axes.titlesize":    11,
    "axes.titleweight":  "bold",
    "axes.titlecolor":   "#1a1a1a",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "xtick.color":       "#333333",
    "ytick.color":       "#333333",
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "grid.color":        "#DDDDDD",
    "grid.linestyle":    "--",
    "grid.linewidth":    0.5,
    "grid.alpha":        0.8,
    "font.family":       "serif",
    "font.serif":        ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size":         10,
    "text.color":        "#1a1a1a",
    "legend.framealpha": 0.9,
    "legend.edgecolor":  "#CCCCCC",
    "legend.fontsize":   9,
    "lines.linewidth":   1.5,
    "savefig.bbox":      "tight",
    "savefig.dpi":       200,
    "savefig.facecolor": "white",
})

C_GOLD   = "#B8860B"
C_BLUE   = "#1F77B4"
C_RED    = "#D62728"
C_GREEN  = "#2CA02C"
C_PURPLE = "#9467BD"

# ── Data from JSON ─────────────────────────────────────────────────────────
METRIC_KEYS   = ["Accuracy", "F1-Score", "Precision", "Recall", "AUC-ROC"]
metrics       = {k: eval_res[k] for k in METRIC_KEYS if k in eval_res}
feat_data     = eval_res.get("feature_importance", {})

metric_labels = list(metrics.keys())
metric_vals   = list(metrics.values())

# Top-10 features sorted
top10 = sorted(feat_data.items(), key=lambda x: -x[1])[:10]
fn    = [x[0] for x in top10][::-1]   # bottom-up for barh
fv    = [x[1] for x in top10][::-1]

print("=== Metrics to plot ===")
for k, v in metrics.items():
    print(f"  {k}: {v:.4f}  ({v*100:.2f}%)")

print("\n=== Feature Importance Top-10 ===")
for feat, imp in top10:
    print(f"  {feat}: {imp:.4f}  ({imp*100:.2f}%)")

# ── Plot ───────────────────────────────────────────────────────────────────
# Judul figure diberikan oleh caption IEEE di paper (tanpa suptitle)
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

# ── Panel (a): Performance Metrics ────────────────────────────────────────
ax = axes[0]
colors_m = [C_GOLD, C_GREEN, C_BLUE, C_PURPLE, C_RED]
bars = ax.barh(metric_labels, metric_vals,
               color=colors_m[:len(metric_labels)],
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

auc_val = eval_res.get("AUC-ROC", 0.8035)
ax.axvline(auc_val, color=C_RED, ls="--", lw=1, alpha=0.7,
           label=f"AUC-ROC = {auc_val:.4f}")
ax.legend(fontsize=9)

# ── Panel (b): Feature Importance ─────────────────────────────────────────
ax2 = axes[1]

# Color: highlight trade_hour (rank 1 novel finding) and price_range
def bar_color(f):
    if "trade_hour" in f:
        return C_RED       # Novel finding — highlight
    if "price_range" in f:
        return C_PURPLE    # rank 3
    return C_BLUE

colors_f = [bar_color(f) for f in fn]
bars2 = ax2.barh(fn, fv, color=colors_f, alpha=0.82,
                 height=0.55, edgecolor="white", linewidth=0.5)
ax2.set_xlabel("Importance Score", fontsize=10)
ax2.set_title("(b) Top-10 Feature Importance", fontsize=10, fontweight="bold")
ax2.set_facecolor("#F8F9FA")

# Value labels
for bar, val in zip(bars2, fv):
    ax2.text(val + 0.002, bar.get_y() + bar.get_height() / 2,
             f"{val:.3f}", va="center", fontsize=8.5)
ax2.grid(True, axis="x", alpha=0.5)
ax2.set_axisbelow(True)

# Determine x-limit based on max value to avoid clipping
max_fv = max(fv) if fv else 0.45
ax2.set_xlim(0, max_fv * 1.55)   # generous right margin for annotation

# ── FIX: "Novel finding" annotation placed LEFT of bar (inside plot) ───────
trade_hour_idx = None
for i, f in enumerate(fn):
    if f == "trade_hour":
        trade_hour_idx = i
        break

if trade_hour_idx is not None:
    bar_val = fv[trade_hour_idx]
    bar_y   = trade_hour_idx  # barh y-index = index in reversed list

    # Place text to the LEFT of the bar so it never clips the right edge
    annotation_x = bar_val * 1.15  # area kosong di kanan bar volatility_7h/price_range
    annotation_y = bar_y - 1.0

    ax2.annotate(
        "Top predictor: mainly\nETF session boundary",
        xy=(bar_val, bar_y),
        xytext=(annotation_x, annotation_y),
        fontsize=8, color=C_RED, fontweight="bold",
        ha="center", va="top",
        arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.2),
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                  edgecolor=C_RED, alpha=0.9)
    )

# Legend for colors
legend_patches = [
    mpatches.Patch(color=C_RED,    alpha=0.82, label="trade_hour (rank 1; mainly session boundary)"),
    mpatches.Patch(color=C_PURPLE, alpha=0.82, label="price_range (rank 3)"),
    mpatches.Patch(color=C_BLUE,   alpha=0.82, label="Other features"),
]
ax2.legend(handles=legend_patches, fontsize=7.5, loc="lower right")

plt.tight_layout()
out_path = os.path.join(CHARTS, "chart3_model_evaluation.png")
plt.savefig(out_path)
plt.close()
print(f"\n[OK] chart3_model_evaluation.png saved -> {out_path}")
