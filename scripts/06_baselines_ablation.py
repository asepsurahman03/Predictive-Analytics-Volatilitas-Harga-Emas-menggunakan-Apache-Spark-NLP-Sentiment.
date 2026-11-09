"""
06_baselines_ablation.py
========================
Baseline dan ablation untuk prediksi volatilitas jam t+1 (Spark MLlib).
Memakai merged_dataset.csv (keluaran 04_spark_ml_analysis.py: fitur jam t, label is_volatile_next)
dengan split kronologis 80:20 yang sama.

Model:
  - Majority class (selalu non-volatile)
  - Historical-volatility rule: volatile jika volatility_7h > theta (0.5%)
  - Logistic Regression (Spark MLlib)
  - Random Forest (full, 18 fitur)            -> harus mereproduksi model_evaluation.json
  - RF tanpa fitur temporal (trade_hour, month, day_of_week)
  - RF tanpa fitur sentimen
  - RF GC=F-only (train & test hanya GC=F), dengan dan tanpa fitur temporal
  - RF ETF-only (GLD, IAU, GDX, GDXJ), dengan dan tanpa fitur temporal
    -> menguji apakah trade_hour hanya menangkap identitas instrumen

Output: output/baseline_ablation.json
"""

import os, sys, json
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, roc_auc_score, matthews_corrcoef,
                             balanced_accuracy_score, f1_score, recall_score)

from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier, LogisticRegression
from pyspark.ml.functions import vector_to_array

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

THETA = 0.5
LABEL = "is_volatile_next"
FEATURES = [
    "open_price", "high_price", "low_price", "close_price",
    "price_range", "pct_change",
    "trade_hour", "month", "day_of_week",
    "avg_sentiment", "total_articles", "positive_count", "negative_count",
    "prev_close", "prev_sentiment", "ma_7h", "ma_24h", "volatility_7h"
]
TEMPORAL  = ["trade_hour", "month", "day_of_week"]
SENTIMENT = ["avg_sentiment", "total_articles", "positive_count", "negative_count", "prev_sentiment"]

spark = SparkSession.builder.master("local[*]") \
    .config("spark.ui.enabled", "false") \
    .config("spark.driver.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

df = pd.read_csv(os.path.join(BASE, "data", "processed", "merged_dataset.csv"))
df = df.sort_values(["trade_date", "trade_hour"], kind="stable").reset_index(drop=True)
cutoff = int(len(df) * 0.8)
train_pd, test_pd = df.iloc[:cutoff], df.iloc[cutoff:]
print(f"Train {len(train_pd):,} | Test {len(test_pd):,} | test volatile {test_pd[LABEL].sum():,}")


def metrics(y, pred, score):
    return {
        "AUC-ROC":           round(float(roc_auc_score(y, score)), 4) if len(set(score)) > 1 else 0.5,
        "Accuracy":          round(float(accuracy_score(y, pred)), 4),
        "F1_weighted":       round(float(f1_score(y, pred, average="weighted")), 4),
        "Recall_volatile":   round(float(recall_score(y, pred, zero_division=0)), 4),
        "Balanced_Accuracy": round(float(balanced_accuracy_score(y, pred)), 4),
        "MCC":               round(float(matthews_corrcoef(y, pred)), 4),
    }


importances = {}


def fit_predict(estimator, feats, tr, te, name=None):
    assembler = VectorAssembler(inputCols=feats, outputCol="features_raw")
    scaler = StandardScaler(inputCol="features_raw", outputCol="features", withMean=True)
    model = Pipeline(stages=[assembler, scaler, estimator]).fit(spark.createDataFrame(tr))
    if name and hasattr(model.stages[-1], "featureImportances"):
        imp = sorted(zip(feats, model.stages[-1].featureImportances.toArray()), key=lambda x: -x[1])
        importances[name] = {k: round(float(v), 4) for k, v in imp[:5]}
    out = model.transform(spark.createDataFrame(te)) \
        .select(LABEL, "prediction", vector_to_array("probability")[1].alias("p1")).toPandas()
    return out[LABEL].values, out["prediction"].values.astype(int), out["p1"].values


def rf():
    return RandomForestClassifier(labelCol=LABEL, featuresCol="features",
                                  numTrees=100, maxDepth=8, seed=42)


results = {}
y_test = test_pd[LABEL].values

results["Majority class"] = metrics(y_test, np.zeros_like(y_test), np.zeros(len(y_test)))

vol = test_pd["volatility_7h"].values
results["Historical-volatility rule"] = metrics(y_test, (vol > THETA).astype(int), vol)

y, p, s = fit_predict(LogisticRegression(labelCol=LABEL, featuresCol="features", maxIter=100),
                      FEATURES, train_pd, test_pd)
results["Logistic Regression"] = metrics(y, p, s)

y, p, s = fit_predict(rf(), FEATURES, train_pd, test_pd)
results["RF (full, 18 features)"] = metrics(y, p, s)
full_pred = pd.DataFrame({"instrument": test_pd["instrument_name"].values, "y": y, "p": p, "s": s})

y, p, s = fit_predict(rf(), [f for f in FEATURES if f not in TEMPORAL], train_pd, test_pd)
results["RF w/o temporal"] = metrics(y, p, s)

y, p, s = fit_predict(rf(), [f for f in FEATURES if f not in SENTIMENT], train_pd, test_pd)
results["RF w/o sentiment"] = metrics(y, p, s)

# GC=F-only model vs. full model, keduanya dievaluasi pada baris test GC=F
gc = "Gold Futures (COMEX)"
tr_gc = train_pd[train_pd["instrument_name"] == gc]
te_gc = test_pd[test_pd["instrument_name"] == gc]
y, p, s = fit_predict(rf(), FEATURES, tr_gc, te_gc, name="RF GC=F-only")
results["RF GC=F-only (GC=F test rows)"] = metrics(y, p, s)
g = full_pred[full_pred["instrument"] == gc]
results["RF full (GC=F test rows)"] = metrics(g["y"].values, g["p"].values, g["s"].values)

# Uji confounding instrumen: apakah trade_hour tetap penting di dalam satu kelompok instrumen?
# (ETF hanya ~7 jam/hari jam bursa AS; GC=F ~23 jam/hari)
y, p, s = fit_predict(rf(), [f for f in FEATURES if f not in TEMPORAL], tr_gc, te_gc)
results["RF GC=F-only w/o temporal (GC=F test rows)"] = metrics(y, p, s)
tr_etf = train_pd[train_pd["instrument_name"] != gc]
te_etf = test_pd[test_pd["instrument_name"] != gc]
y, p, s = fit_predict(rf(), FEATURES, tr_etf, te_etf, name="RF ETF-only")
results["RF ETF-only (ETF test rows)"] = metrics(y, p, s)
y, p, s = fit_predict(rf(), [f for f in FEATURES if f not in TEMPORAL], tr_etf, te_etf)
results["RF ETF-only w/o temporal (ETF test rows)"] = metrics(y, p, s)
results["top5_importance"] = importances

per_instrument = {}
for inst, g in full_pred.groupby("instrument"):
    if g["y"].nunique() > 1:
        per_instrument[inst] = round(float(roc_auc_score(g["y"], g["s"])), 4)
results["per_instrument_AUC_full_model"] = per_instrument

for k, v in results.items():
    print(f"{k:<32} {v}")

with open(os.path.join(BASE, "output", "baseline_ablation.json"), "w") as f:
    json.dump(results, f, indent=2)
spark.stop()
