"""
07_robustness.py
================
Eksperimen robustness untuk menjawab catatan dosen (v11):
  1. Target sadar-sesi (session-aware): buang transisi t -> t+1 yang bukan jam berurutan
     (penutupan sesi ETF ke pembukaan esok hari, jeda harian GC=F, akhir pekan, libur).
  2. Expanding-window walk-forward (5 fold) dengan embargo 1 hari, plus tuning maxDepth
     di dalam training window (4 fold) -> mean ± SD.
  3. Ketidakseimbangan kelas: RF dengan class weight (weightCol) dan tuning threshold
     pada slice validasi kronologis (20% terakhir training).
  4. Sensitivitas threshold volatilitas theta (0.3, 0.5, 0.7) dan ablasi price_range.
  5. Perbandingan algoritma (RF, GBT, LR, aturan historis) + uji statistik:
     DeLong (AUC berpasangan), McNemar, bootstrap 95% CI.
  6. Benchmark Spark: waktu training RF vs jumlah core (local[1..8]) dan ukuran data.

Input : data/processed/merged_dataset.csv (keluaran 04_spark_ml_analysis.py)
Output: output/robustness.json
"""

import os, sys, json, time
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (accuracy_score, roc_auc_score, matthews_corrcoef,
                             balanced_accuracy_score, recall_score, precision_score, f1_score)

from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import (RandomForestClassifier, GBTClassifier,
                                       LogisticRegression)
from pyspark.ml.functions import vector_to_array

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(BASE, "output", "robustness.json")

FEATURES = [
    "open_price", "high_price", "low_price", "close_price",
    "price_range", "pct_change",
    "trade_hour", "month", "day_of_week",
    "avg_sentiment", "total_articles", "positive_count", "negative_count",
    "prev_close", "prev_sentiment", "ma_7h", "ma_24h", "volatility_7h"
]
TEMPORAL = ["trade_hour", "month", "day_of_week"]
GC = "Gold Futures (COMEX)"


def log(*a):
    print(*a, flush=True)


# ── Data ────────────────────────────────────────────────────────────────────
df = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_dataset.csv"))
df["dt"] = pd.to_datetime(df["trade_datetime"])
df = df.sort_values(["instrument_name", "dt"]).reset_index(drop=True)
g = df.groupby("instrument_name")
df["next_dt"] = g["dt"].shift(-1)
df["next_pct"] = g["pct_change"].shift(-1)
df["gap_h"] = (df["next_dt"] - df["dt"]).dt.total_seconds() / 3600
# Batas sesi: bar t+1 bukan jam berikutnya (atau tidak diketahui untuk baris terakhir)
df["boundary"] = ~(df["gap_h"] == 1.0)
for th in (0.3, 0.5, 0.7):
    df[f"y_{th}"] = (df["next_pct"].abs() > th).astype(float)
    df.loc[df["next_pct"].isna(), f"y_{th}"] = np.nan
df["y"] = df["is_volatile_next"].astype(float)

# Urutan & split kronologis yang sama dengan 04/06 (80:20)
df = df.sort_values(["trade_date", "trade_hour"], kind="stable").reset_index(drop=True)
df["row"] = np.arange(len(df))
cut = int(len(df) * 0.8)
df["is_test"] = df["row"] >= cut
log(f"rows {len(df):,} | train {cut:,} | test {len(df)-cut:,} | boundary {df['boundary'].mean():.3f}")

spark = SparkSession.builder.master("local[*]") \
    .config("spark.ui.enabled", "false") \
    .config("spark.driver.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

cols = FEATURES + ["row", "y", "y_0.3", "y_0.5", "y_0.7", "boundary", "is_test", "instrument_name"]
sdf_all = spark.createDataFrame(df[cols].rename(columns={"y_0.3": "y_03", "y_0.5": "y_05", "y_0.7": "y_07"}))
sdf_all = sdf_all.cache()
sdf_all.count()


def pipe(est, feats):
    return Pipeline(stages=[VectorAssembler(inputCols=feats, outputCol="raw"),
                            StandardScaler(inputCol="raw", outputCol="features", withMean=True),
                            est])


def rf(label="y", depth=8, weight=None):
    kw = dict(labelCol=label, featuresCol="features", numTrees=100, maxDepth=depth, seed=42)
    if weight:
        kw["weightCol"] = weight
    return RandomForestClassifier(**kw)


def fit_score(est, feats, train, test, label="y"):
    """Latih pada Spark DF train, kembalikan (y, p1, model) dari test, urut berdasarkan row."""
    model = pipe(est, feats).fit(train)
    out = model.transform(test).select("row", label, vector_to_array("probability")[1].alias("p1")) \
        .toPandas().sort_values("row")
    return out[label].values.astype(int), out["p1"].values, model


def metrics(y, p, thr=0.5):
    pred = (p > thr).astype(int)
    return {
        "AUC": round(float(roc_auc_score(y, p)), 4) if len(np.unique(p)) > 1 else 0.5,
        "Accuracy": round(float(accuracy_score(y, pred)), 4),
        "Precision1": round(float(precision_score(y, pred, zero_division=0)), 4),
        "Recall1": round(float(recall_score(y, pred, zero_division=0)), 4),
        "F1_1": round(float(f1_score(y, pred, zero_division=0)), 4),
        "BalAcc": round(float(balanced_accuracy_score(y, pred)), 4),
        "MCC": round(float(matthews_corrcoef(y, pred)), 4),
        "n": int(len(y)), "pos_rate": round(float(np.mean(y)), 4),
    }


def importances(model, feats, k=5):
    imp = model.stages[-1].featureImportances.toArray()
    return {f: round(float(v), 4) for f, v in sorted(zip(feats, imp), key=lambda x: -x[1])[:k]}


# ── DeLong (Sun & Xu, 2014) ─────────────────────────────────────────────────
def _midrank(x):
    j = np.argsort(x)
    z = x[j]
    n = len(x)
    t = np.zeros(n)
    i = 0
    while i < n:
        a = i
        while a < n and z[a] == z[i]:
            a += 1
        t[i:a] = 0.5 * (i + a - 1)
        i = a
    out = np.empty(n)
    out[j] = t + 1
    return out


def delong(y, p_a, p_b):
    """Uji DeLong dua sisi untuk selisih AUC dua model pada sampel yang sama."""
    order = np.argsort(-y, kind="stable")
    y = y[order]
    preds = np.vstack([p_a[order], p_b[order]])
    m = int(y.sum())
    n = len(y) - m
    k = preds.shape[0]
    tx = np.array([_midrank(r[:m]) for r in preds])
    ty = np.array([_midrank(r[m:]) for r in preds])
    tz = np.array([_midrank(r) for r in preds])
    aucs = tz[:, :m].sum(axis=1) / m / n - (m + 1.0) / 2.0 / n
    v01 = (tz[:, :m] - tx) / n
    v10 = 1.0 - (tz[:, m:] - ty) / m
    cov = np.cov(v01) / m + np.cov(v10) / n
    diff = aucs[0] - aucs[1]
    var = cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]
    z = diff / np.sqrt(var)
    return {"AUC_a": round(float(aucs[0]), 4), "AUC_b": round(float(aucs[1]), 4),
            "diff": round(float(diff), 4), "z": round(float(z), 3),
            "p": float(2 * stats.norm.sf(abs(z)))}


def mcnemar(y, pred_a, pred_b):
    a_ok, b_ok = pred_a == y, pred_b == y
    b = int(np.sum(a_ok & ~b_ok))
    c = int(np.sum(~a_ok & b_ok))
    chi2 = (abs(b - c) - 1) ** 2 / (b + c) if b + c else 0.0
    return {"a_only_correct": b, "b_only_correct": c, "chi2": round(chi2, 3),
            "p": float(stats.chi2.sf(chi2, 1))}


R = {}
train_all = sdf_all.filter("NOT is_test")
test_all = sdf_all.filter("is_test")
y_test = df.loc[df["is_test"], "y"].values.astype(int)

# ── 1. Holdout: algoritma ───────────────────────────────────────────────────
log("[1] holdout models")
t0 = time.time()
y, p_rf, m_rf = fit_score(rf(), FEATURES, train_all, test_all)
R["fit_seconds_rf_holdout"] = round(time.time() - t0, 1)
assert (y == y_test).all()
_, p_lr, _ = fit_score(LogisticRegression(labelCol="y", featuresCol="features", maxIter=100),
                       FEATURES, train_all, test_all)
_, p_gbt, _ = fit_score(GBTClassifier(labelCol="y", featuresCol="features", maxIter=100,
                                      maxDepth=5, seed=42), FEATURES, train_all, test_all)
_, p_nt, _ = fit_score(rf(), [f for f in FEATURES if f not in TEMPORAL], train_all, test_all)
_, p_npr, _ = fit_score(rf(), [f for f in FEATURES if f != "price_range"], train_all, test_all)
p_hist = df.loc[df["is_test"], "volatility_7h"].values
R["holdout"] = {
    "RF": metrics(y, p_rf), "GBT": metrics(y, p_gbt), "LR": metrics(y, p_lr),
    "HistRule": metrics(y, (p_hist > 0.5).astype(float)) | {"AUC": round(float(roc_auc_score(y, p_hist)), 4)},
    "RF_no_temporal": metrics(y, p_nt), "RF_no_price_range": metrics(y, p_npr),
}
R["holdout_importance_RF"] = importances(m_rf, FEATURES)
log(json.dumps(R["holdout"], indent=1))

# ── 2. Uji statistik ────────────────────────────────────────────────────────
log("[2] statistics")
R["delong"] = {
    "RF_vs_GBT": delong(y, p_rf, p_gbt), "RF_vs_LR": delong(y, p_rf, p_lr),
    "RF_vs_HistRule": delong(y, p_rf, p_hist), "RF_vs_RF_no_temporal": delong(y, p_rf, p_nt),
}
R["mcnemar"] = {
    "RF_vs_LR": mcnemar(y, (p_rf > 0.5).astype(int), (p_lr > 0.5).astype(int)),
    "RF_vs_GBT": mcnemar(y, (p_rf > 0.5).astype(int), (p_gbt > 0.5).astype(int)),
}
rng = np.random.default_rng(42)
boot = {"AUC": [], "MCC": [], "Recall1": []}
pred_rf = (p_rf > 0.5).astype(int)
for _ in range(1000):
    i = rng.integers(0, len(y), len(y))
    if y[i].min() == y[i].max():
        continue
    boot["AUC"].append(roc_auc_score(y[i], p_rf[i]))
    boot["MCC"].append(matthews_corrcoef(y[i], pred_rf[i]))
    boot["Recall1"].append(recall_score(y[i], pred_rf[i]))
R["bootstrap_ci95_RF"] = {k: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]
                          for k, v in boot.items()}
log(json.dumps({k: R[k] for k in ("delong", "mcnemar", "bootstrap_ci95_RF")}, indent=1))

# ── 3. Ketidakseimbangan kelas ──────────────────────────────────────────────
log("[3] imbalance")
pos = float(df.loc[~df["is_test"], "y"].mean())
w_pos, w_neg = 0.5 / pos, 0.5 / (1 - pos)
sdf_w = sdf_all.withColumn("w", (sdf_all["y"] * w_pos + (1 - sdf_all["y"]) * w_neg))
_, p_rfw, _ = fit_score(rf(weight="w"), FEATURES, sdf_w.filter("NOT is_test"), sdf_w.filter("is_test"))
R["holdout"]["RF_class_weighted"] = metrics(y, p_rfw)
# Tuning threshold pada slice validasi kronologis (20% terakhir training)
cut_val = int(cut * 0.8)
y_v, p_v, _ = fit_score(rf(), FEATURES, sdf_all.filter(f"row < {cut_val}"),
                        sdf_all.filter(f"row >= {cut_val} AND NOT is_test"))
grid = np.round(np.arange(0.05, 0.95, 0.01), 2)
f1s = [f1_score(y_v, (p_v > t).astype(int), zero_division=0) for t in grid]
thr = float(grid[int(np.argmax(f1s))])
R["tuned_threshold"] = thr
R["holdout"]["RF_tuned_threshold"] = metrics(y, p_rf, thr)
log("threshold", thr, R["holdout"]["RF_tuned_threshold"], R["holdout"]["RF_class_weighted"])

# ── 4. Target sadar-sesi ────────────────────────────────────────────────────
log("[4] session-aware")
sa = sdf_all.filter("NOT boundary")
ys, ps, m_sa = fit_score(rf(), FEATURES, sa.filter("NOT is_test"), sa.filter("is_test"))
_, ps_nt, _ = fit_score(rf(), [f for f in FEATURES if f not in TEMPORAL], sa.filter("NOT is_test"), sa.filter("is_test"))
R["session_aware"] = {"RF": metrics(ys, ps), "RF_no_temporal": metrics(ys, ps_nt),
                      "importance_RF": importances(m_sa, FEATURES),
                      "delong_RF_vs_no_temporal": delong(ys, ps, ps_nt),
                      "boundary_share": round(float(df["boundary"].mean()), 4),
                      "vol_rate_boundary": round(float(df.loc[df["boundary"], "y"].mean()), 4),
                      "vol_rate_within": round(float(df.loc[~df["boundary"], "y"].mean()), 4)}
te_sa = df[(~df["boundary"]) & df["is_test"]].sort_values("row")
for name, mask in (("GC=F", te_sa["instrument_name"] == GC), ("ETF", te_sa["instrument_name"] != GC)):
    mk = mask.values
    R["session_aware"][f"RF_{name}"] = metrics(ys[mk], ps[mk])
    R["session_aware"][f"RF_no_temporal_{name}"] = metrics(ys[mk], ps_nt[mk])
# Bagian batas sesi pada test holdout model utama
te = df[df["is_test"]].sort_values("row")
bd = te["boundary"].values
R["holdout_by_boundary"] = {"boundary": metrics(y[bd], p_rf[bd]), "within_session": metrics(y[~bd], p_rf[~bd])}
log(json.dumps(R["session_aware"], indent=1))

# ── 5. Sensitivitas theta ───────────────────────────────────────────────────
log("[5] theta")
R["theta"] = {}
for th, col in ((0.3, "y_03"), (0.5, "y_05"), (0.7, "y_07")):
    s = sdf_all.filter(f"NOT isnan({col})")  # NaN pandas menjadi NaN Spark, bukan NULL
    yt, pt, _ = fit_score(rf(label=col), FEATURES, s.filter("NOT is_test"), s.filter("is_test"), label=col)
    R["theta"][str(th)] = metrics(yt, pt) | {"pos_rate_all": round(float(df[f"y_{th}"].mean()), 4)}
log(json.dumps(R["theta"], indent=1))

# ── 6. Walk-forward expanding window (5 fold, embargo 1 hari) ──────────────
log("[6] walk-forward")
blocks = np.array_split(np.arange(len(df)), 6)
wf = {k: [] for k in ("RF", "GBT", "LR", "HistRule")}
folds = []
for k in range(1, 6):
    te_idx = blocks[k]
    t_start = df.loc[te_idx[0], "dt"]
    tr_mask = (df["row"] < te_idx[0]) & (df["dt"] < t_start - pd.Timedelta(days=1))
    tr_max = int(df.loc[tr_mask, "row"].max())
    tr = sdf_all.filter(f"row <= {tr_max}")
    ts = sdf_all.filter(f"row >= {te_idx[0]} AND row <= {te_idx[-1]}")
    yk, pk, _ = fit_score(rf(), FEATURES, tr, ts)
    _, pg, _ = fit_score(GBTClassifier(labelCol="y", featuresCol="features", maxIter=100, maxDepth=5, seed=42),
                         FEATURES, tr, ts)
    _, pl, _ = fit_score(LogisticRegression(labelCol="y", featuresCol="features", maxIter=100), FEATURES, tr, ts)
    ph = df.loc[te_idx, "volatility_7h"].values
    wf["RF"].append(metrics(yk, pk)); wf["GBT"].append(metrics(yk, pg)); wf["LR"].append(metrics(yk, pl))
    wf["HistRule"].append(metrics(yk, (ph > 0.5).astype(float)) | {"AUC": round(float(roc_auc_score(yk, ph)), 4)})
    folds.append({"fold": k, "train_rows": int(tr_mask.sum()), "test_rows": int(len(te_idx)),
                  "test_start": str(t_start), "test_end": str(df.loc[te_idx[-1], "dt"])})
    log("fold", k, wf["RF"][-1]["AUC"], wf["GBT"][-1]["AUC"], wf["LR"][-1]["AUC"])
R["walk_forward"] = {"folds": folds, "per_fold": wf,
                     "summary": {m: {k: [round(float(np.mean([f[k] for f in v])), 4),
                                         round(float(np.std([f[k] for f in v], ddof=1)), 4)]
                                     for k in ("AUC", "MCC", "Recall1", "BalAcc")}
                                 for m, v in wf.items()}}
rf_auc = [f["AUC"] for f in wf["RF"]]
R["walk_forward"]["wilcoxon_RF_vs_LR_AUC"] = float(stats.wilcoxon(rf_auc, [f["AUC"] for f in wf["LR"]]).pvalue)
R["walk_forward"]["wilcoxon_RF_vs_GBT_AUC"] = float(stats.wilcoxon(rf_auc, [f["AUC"] for f in wf["GBT"]]).pvalue)
log(json.dumps(R["walk_forward"]["summary"], indent=1))

# ── 7. Tuning maxDepth di dalam training (expanding 4 fold) ─────────────────
log("[7] depth tuning")
tb = np.array_split(np.arange(cut), 5)
R["depth_tuning"] = {}
for depth in (4, 6, 8, 10):
    aucs = []
    for k in range(1, 5):
        yk, pk, _ = fit_score(rf(depth=depth), FEATURES, sdf_all.filter(f"row < {tb[k][0]}"),
                              sdf_all.filter(f"row >= {tb[k][0]} AND row <= {tb[k][-1]}"))
        aucs.append(roc_auc_score(yk, pk))
    R["depth_tuning"][str(depth)] = [round(float(np.mean(aucs)), 4), round(float(np.std(aucs, ddof=1)), 4)]
    log("depth", depth, R["depth_tuning"][str(depth)])

with open(OUT, "w") as f:
    json.dump(R, f, indent=2)
train_pd = df.loc[~df["is_test"], FEATURES + ["y"]].copy()
spark.stop()

# ── 8. Benchmark Spark: core dan ukuran data ────────────────────────────────
log("[8] benchmark")
bench = {"cpu": "Intel Core i7-10610U (4 cores / 8 threads), 16 GB RAM", "cores": {}, "data_fraction": {}}


def time_fit(master, frac):
    sp = SparkSession.builder.master(master).config("spark.ui.enabled", "false") \
        .config("spark.driver.memory", "4g").getOrCreate()
    sp.sparkContext.setLogLevel("ERROR")
    n = int(len(train_pd) * frac)
    s = sp.createDataFrame(train_pd.iloc[:n]).repartition(8).cache()
    s.count()
    pipe(rf(), FEATURES).fit(s)  # warm-up
    ts = []
    for _ in range(2):
        t0 = time.time()
        pipe(rf(), FEATURES).fit(s)
        ts.append(time.time() - t0)
    sp.stop()
    return round(min(ts), 2)


for c in (1, 2, 4, 8):
    bench["cores"][str(c)] = time_fit(f"local[{c}]", 1.0)
    log("cores", c, bench["cores"][str(c)])
for fr in (0.25, 0.5, 1.0):
    bench["data_fraction"][str(fr)] = time_fit("local[8]", fr)
    log("frac", fr, bench["data_fraction"][str(fr)])
R["benchmark_rf_fit_seconds"] = bench

with open(OUT, "w") as f:
    json.dump(R, f, indent=2)
log("[OK] saved", OUT)
