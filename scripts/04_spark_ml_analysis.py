"""
Script 04: Analisis & Machine Learning dengan PySpark
=====================================================
Input   : data/processed/hive_table_gold_price/ (simulasi Hive)
          data/processed/daily_sentiment_score.csv (dari HBase via script 03)
Output  : data/processed/merged_dataset.csv
          output/models/rf_model/
          output/model_evaluation.json

Algoritma: Random Forest Classifier (Spark MLlib)
Target   : is_volatile_next (1 = jam BERIKUTNYA (t+1) volatile > 0.5%, 0 = stabil)
           *** PERBAIKAN LEAKAGE v2: prediksi t+1, bukan t ***
"""

import os, json, warnings
warnings.filterwarnings("ignore")

# ===========================================================
# SETUP PYSPARK (local mode - tidak butuh cluster Hadoop)
# ===========================================================
JAVA_HOME   = r"C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot"
PYTHON_EXE  = r"C:\Users\X1 YOGA\AppData\Local\Python\pythoncore-3.14-64\python.exe"
HADOOP_HOME = r"C:\hadoop"

os.environ["JAVA_HOME"]             = JAVA_HOME
os.environ["HADOOP_HOME"]           = HADOOP_HOME
os.environ["PYSPARK_PYTHON"]        = PYTHON_EXE
os.environ["PYSPARK_DRIVER_PYTHON"] = PYTHON_EXE

# Tambahkan Java bin dan Hadoop bin ke PATH
java_bin   = os.path.join(JAVA_HOME, "bin")
hadoop_bin = os.path.join(HADOOP_HOME, "bin")
for p in [java_bin, hadoop_bin]:
    if p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")

# Set SPARK_HOME otomatis dari lokasi pyspark package
import pyspark
spark_home = os.path.dirname(pyspark.__file__)
os.environ["SPARK_HOME"] = spark_home
print(f"[INFO] SPARK_HOME: {spark_home}")
print(f"[INFO] JAVA_HOME:  {JAVA_HOME}")

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier, GBTClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import pandas as pd

# ===========================================================
# INISIALISASI SPARK SESSION
# ===========================================================
print("[INFO] Memulai Spark Session (local mode) -- LEAKAGE-FREE t+1 prediction...")
spark = SparkSession.builder \
    .appName("GoldPricePrediction") \
    .master("local[*]") \
    .config("spark.sql.warehouse.dir", "../data/spark-warehouse") \
    .config("spark.driver.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print(f"[OK] Spark Version: {spark.version}")

# ===========================================================
# LOAD DATA HARGA EMAS (Simulasi Hive - baca semua partisi via Pandas dulu)
# ===========================================================
print("\n[INFO] Memuat data harga emas dari Hive (partisi per tahun)...")
import glob as glob_mod
hive_path = os.path.abspath(os.path.join("..", "data", "processed", "hive_table_gold_price"))
csv_files  = glob_mod.glob(os.path.join(hive_path, "**", "*.csv"), recursive=True)
gold_pandas = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
gold_pandas["trade_date"] = pd.to_datetime(gold_pandas["trade_date"]).dt.strftime("%Y-%m-%d")
gold_pandas = gold_pandas.sort_values(["instrument_name", "trade_date", "trade_hour"]).reset_index(drop=True)
gold_df = spark.createDataFrame(gold_pandas)
gold_df = gold_df.withColumn("trade_date",  F.to_date("trade_date", "yyyy-MM-dd"))
gold_df = gold_df.withColumn("close_price", gold_df["close_price"].cast(DoubleType()))
gold_df = gold_df.withColumn("pct_change",  gold_df["pct_change"].cast(DoubleType()))
gold_df = gold_df.withColumn("price_range", gold_df["price_range"].cast(DoubleType()))
gold_df = gold_df.withColumn("trade_hour",  gold_df["trade_hour"].cast(IntegerType()))
gold_df = gold_df.withColumn("month",       gold_df["month"].cast(IntegerType()))
gold_df = gold_df.withColumn("day_of_week", gold_df["day_of_week"].cast(IntegerType()))
gold_df = gold_df.withColumn("is_volatile", gold_df["is_volatile"].cast(IntegerType()))
print(f"[OK] {gold_df.count():,} baris data dimuat dari {len(csv_files)} partisi Hive.")
print(gold_df.groupBy("instrument_name").count().show())

# ===========================================================
# LOAD DATA SENTIMEN (Simulasi HBase output)
# ===========================================================
print("\n[INFO] Memuat skor sentimen harian (dari HBase)...")
sent_path = os.path.abspath(os.path.join("..", "data", "processed", "daily_sentiment_score.csv"))
sent_pandas = pd.read_csv(sent_path)
sent_df = spark.createDataFrame(sent_pandas)
sent_df = sent_df.withColumn("trade_date", F.to_date("trade_date", "yyyy-MM-dd"))
print(f"[OK] {sent_df.count()} hari data sentimen dimuat.")

# ===========================================================
# JOIN DATASET (Spark SQL equivalent)
# ===========================================================
print("\n[INFO] Menggabungkan dataset (JOIN berdasarkan trade_date)...")
merged = gold_df.join(sent_df, on="trade_date", how="left")
merged = merged.fillna({
    "avg_sentiment":  0.0,
    "total_articles": 0,
    "positive_count": 0,
    "negative_count": 0,
    "neutral_count":  0
})
merged.createOrReplaceTempView("gold_sentiment")
print(f"[OK] Dataset gabungan: {merged.count()} baris, {len(merged.columns)} kolom.")

# Tampilkan statistik deskriptif (untuk paper)
print("\n[INFO] Statistik Deskriptif:")
merged.describe(["close_price", "pct_change", "avg_sentiment", "price_range"]).show()

# ===========================================================
# FEATURE ENGINEERING + LABEL t+1 (FIX LEAKAGE)
# ===========================================================
print("\n[INFO] Feature Engineering + pembuatan label t+1 (fix leakage)...")
from pyspark.sql.window import Window

# Window per instrumen, diurutkan berdasarkan datetime
w = Window.partitionBy("instrument_name").orderBy("trade_date", "trade_hour")
merged = merged \
    .withColumn("prev_close",     F.lag("close_price", 1).over(w)) \
    .withColumn("prev_sentiment", F.lag("avg_sentiment", 1).over(w)) \
    .withColumn("ma_7h",          F.avg("close_price").over(w.rowsBetween(-6, 0))) \
    .withColumn("ma_24h",         F.avg("close_price").over(w.rowsBetween(-23, 0))) \
    .withColumn("volatility_7h",  F.stddev("pct_change").over(w.rowsBetween(-6, 0)))

# *** KUNCI FIX LEAKAGE: buat label t+1 menggunakan lead() ***
# is_volatile_next = apakah JAM BERIKUTNYA (t+1) akan volatile?
# Semua fitur di atas berasal dari jam t (sudah terjadi) -> tidak leaky
merged = merged.withColumn(
    "is_volatile_next",
    F.lead("is_volatile", 1).over(w).cast(IntegerType())
)

# Hapus baris tanpa label t+1 (baris terakhir setiap instrumen)
# dan baris tanpa lag features (baris pertama setiap instrumen)
merged = merged.dropna(subset=["is_volatile_next", "prev_close", "volatility_7h"])
print(f"[OK] Dataset setelah fix leakage: {merged.count():,} baris")
print("[NOTE] Label: is_volatile_next = volatilitas jam t+1")

# Semua fitur berasal dari jam t (sudah terjadi saat prediksi dibuat)
# -> tidak ada leakage terhadap label is_volatile_next (jam t+1)
FEATURES = [
    "open_price", "high_price", "low_price", "close_price",
    "price_range", "pct_change",   # return & range jam t (sudah terjadi)
    "trade_hour", "month", "day_of_week",
    "avg_sentiment", "total_articles", "positive_count", "negative_count",
    "prev_close", "prev_sentiment", "ma_7h", "ma_24h", "volatility_7h"
]
LABEL = "is_volatile_next"   # <- TARGET: volatilitas JAM t+1

# ===========================================================
# PIPELINE ML (VectorAssembler → Scaler → RandomForest)
# ===========================================================
assembler = VectorAssembler(inputCols=FEATURES, outputCol="features_raw")
scaler    = StandardScaler(inputCol="features_raw", outputCol="features", withMean=True)
rf        = RandomForestClassifier(
    labelCol    = LABEL,
    featuresCol = "features",
    numTrees    = 100,
    maxDepth    = 8,
    seed        = 42
)
pipeline = Pipeline(stages=[assembler, scaler, rf])

# Simpan merged dataset (dengan label baru)
merged_pd = merged.toPandas()
merged_pd.to_csv(os.path.join("..", "data", "processed", "merged_dataset.csv"), index=False)
print(f"[OK] merged_dataset.csv disimpan ({len(merged_pd):,} baris)")

# ===========================================================
# TRAIN / TEST SPLIT (80:20, chronological — tidak random)
# ===========================================================
print("\n[INFO] Split data Train 80% / Test 20% (chronological)...")
total  = merged.count()
cutoff = int(total * 0.8)
sorted_data = merged.orderBy("trade_date", "trade_hour")
train_df = spark.createDataFrame(sorted_data.toPandas().iloc[:cutoff])
test_df  = spark.createDataFrame(sorted_data.toPandas().iloc[cutoff:])
print(f"[OK] Train: {train_df.count():,} | Test: {test_df.count():,}")
print(f"[NOTE] Chronological split -- mencegah future leakage pada split level")

# ===========================================================
# TRAINING MODEL
# ===========================================================
print("\n[INFO] Melatih Random Forest Classifier...")
model = pipeline.fit(train_df)

# ===========================================================
# EVALUASI MODEL
# ===========================================================
print("\n[INFO] Mengevaluasi model...")
predictions = model.transform(test_df)

# Evaluasi multi-metrik
evaluators = {
    "Accuracy":  MulticlassClassificationEvaluator(labelCol=LABEL, metricName="accuracy"),
    "F1-Score":  MulticlassClassificationEvaluator(labelCol=LABEL, metricName="f1"),
    "Precision": MulticlassClassificationEvaluator(labelCol=LABEL, metricName="weightedPrecision"),
    "Recall":    MulticlassClassificationEvaluator(labelCol=LABEL, metricName="weightedRecall"),
    "AUC-ROC":   BinaryClassificationEvaluator(labelCol=LABEL, metricName="areaUnderROC"),
}

results = {}
print("\n" + "="*58)
print("  HASIL EVALUASI MODEL (Random Forest -- PREDIKSI t+1)")
print("  [Leakage-Free: fitur jam t -> label jam t+1]")
print("="*58)
for metric, evaluator in evaluators.items():
    val = evaluator.evaluate(predictions)
    results[metric] = round(val, 4)
    print(f"  {metric:<15}: {val:.4f}  ({val*100:.2f}%)")
print("="*58)

# Feature Importance
rf_model = model.stages[-1]
feat_importance = sorted(zip(FEATURES, rf_model.featureImportances), key=lambda x: -x[1])
results["feature_importance"] = {k: round(float(v), 4) for k, v in feat_importance}
results["experiment_note"] = "Leakage-free: label = is_volatile at t+1 (lead=1)"
results["n_train"] = int(train_df.count())
results["n_test"]  = int(test_df.count())
results["n_features"] = len(FEATURES)

print("\n  Top 5 Fitur Terpenting (prediksi t+1):")
for feat, imp in feat_importance[:5]:
    print(f"    {feat:<25} : {imp:.4f}  ({imp*100:.2f}%)")

# Simpan hasil evaluasi
eval_path = os.path.abspath(os.path.join("..", "output", "model_evaluation.json"))
with open(eval_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\n[OK] Hasil evaluasi disimpan ke: {eval_path}")

# Simpan model
model_path = os.path.abspath(os.path.join("..", "output", "models", "rf_model"))
model.write().overwrite().save(model_path)
print(f"[OK] Model disimpan ke: {model_path}")

spark.stop()
print("\n[SELESAI] Pipeline PySpark ML berhasil!")
