"""
=============================================================================
TRAIN MODEL — One Ummah Foundation
Prediksi Churn Donatur | XGBoost + K-Means RFM + SMOTE + GridSearchCV
=============================================================================
Mahasiswa : Naufal Rafif (10522112)
Program   : Sistem Informasi — FTIK UNIKOM
Yayasan   : One Ummah Foundation, Bandung

Fokus: Klasifikasi BINER → Churn (1) vs Tidak Churn (0)
Pipeline CRISP-DM:
  [1] Load Data
  [2] Cleaning & Parsing
  [3] Feature Engineering RFM
  [4] K-Means Clustering (Elbow + Silhouette)
  [5] Labeling berbasis Cluster
  [6] Min-Max Scaling
  [7] Train-Test Split 80:20
  [8] SMOTE hanya pada data latih
  [9] XGBoost + GridSearchCV 5-fold
 [10] Evaluasi & Simpan Artefak
 [11] Generate Gambar untuk Dashboard (EDA, Cluster, Confusion Matrix, ROC, dll)
=============================================================================
Jalankan: python train_model.py
=============================================================================
"""

import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report, confusion_matrix, roc_curve
)
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
FILE_PATH = "Database Filantropi OUF - Transaksi WA.csv"
IMG_DIR = "."

print("=" * 60)
print("  TRAIN MODEL — ONE UMMAH FOUNDATION")
print("  Prediksi Churn Donatur | CRISP-DM Pipeline")
print("=" * 60)

# ── [1] LOAD ──────────────────────────────────────────────────
print("\n[1/11] Load data...")
df_raw = pd.read_csv(FILE_PATH, skiprows=1)
df_raw.drop(columns=["Unnamed: 0","No"], inplace=True, errors="ignore")
df_raw.columns = df_raw.columns.str.strip()
print(f"  Baris awal: {len(df_raw):,}")

# ── [2] CLEANING ──────────────────────────────────────────────
print("[2/11] Cleaning & parsing...")
df = df_raw.copy()
df["Nominal"] = (
    df["Nominal"].astype(str)
    .str.replace("Rp","",regex=False)
    .str.replace(",","",regex=False)
    .str.strip()
)
df["Nominal"] = pd.to_numeric(df["Nominal"], errors="coerce")

BULAN = {
    "Januari":"January","Februari":"February","Maret":"March",
    "April":"April","Mei":"May","Juni":"June","Juli":"July",
    "Agustus":"August","September":"September",
    "Oktober":"October","November":"November","Desember":"December",
}
def parse_tanggal(t):
    t = str(t).strip()
    for a,b in BULAN.items(): t = t.replace(a,b)
    try: return pd.to_datetime(t, dayfirst=True)
    except:
        try: return pd.to_datetime("1 "+t, dayfirst=True)
        except: return pd.NaT

df["Tanggal"] = df["Donasi Tanggal"].apply(parse_tanggal)
df.dropna(subset=["ID Donatur","Nominal","Tanggal"], inplace=True)
df = df[df["Nominal"] > 0]
df.drop_duplicates(subset=["ID Donatur","Tanggal","Nominal"], inplace=True)
Q1,Q3 = df["Nominal"].quantile(.25), df["Nominal"].quantile(.75)
df = df[df["Nominal"] <= Q3 + 1.5*(Q3-Q1)]
print(f"  Data bersih: {len(df):,} transaksi | {df['ID Donatur'].nunique():,} donatur unik")

# ── [3] RFM ───────────────────────────────────────────────────
print("[3/11] Feature engineering RFM...")
CUTOFF = df["Tanggal"].max()
rfm = df.groupby("ID Donatur").agg(
    recency      = ("Tanggal",   lambda x: (CUTOFF-x.max()).days),
    frequency    = ("Tanggal",   "count"),
    monetary     = ("Nominal",   "sum"),
    last_date    = ("Tanggal",   "max"),
    last_nominal = ("Nominal",   "last"),
    program      = ("Program",   lambda x: x.mode()[0] if len(x)>0 else "-"),
    cara_bayar   = ("Cara Bayar",lambda x: x.mode()[0] if len(x)>0 else "-"),
).reset_index()
rfm["monetary_log"] = np.log1p(rfm["monetary"])
print(f"  Donatur RFM: {len(rfm):,}")

# ── [4] K-MEANS ───────────────────────────────────────────────
print("[4/11] K-Means Clustering...")
sc_km   = StandardScaler()
rfm_sc  = sc_km.fit_transform(rfm[["recency","frequency","monetary_log"]])

K_RANGE = range(2,9)
sil_ls, ine_ls = [], []
for k in K_RANGE:
    km  = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    lbl = km.fit_predict(rfm_sc)
    sil_ls.append(silhouette_score(rfm_sc, lbl))
    ine_ls.append(km.inertia_)

best_k = list(K_RANGE)[np.argmax(sil_ls)]
print(f"  K optimal: {best_k} (Silhouette={max(sil_ls):.4f})")

km_final  = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=10)
rfm["cluster"] = km_final.fit_predict(rfm_sc)

cp = rfm.groupby("cluster").agg(
    recency_mean   = ("recency",   "mean"),
    frequency_mean = ("frequency", "mean"),
    monetary_mean  = ("monetary",  "mean"),
    jumlah         = ("ID Donatur","count"),
).round(2)

# ── [5] LABELING — BINER: Churn vs Tidak Churn ───────────────
#     Label sekarang berdasarkan THRESHOLD RECENCY, bukan cluster K-Means.
#     K-Means tetap dipertahankan untuk segmentasi visual (profil cluster),
#     tapi TIDAK dipakai untuk menentukan label churn.
print("[5/11] Data labeling (Churn vs Tidak Churn)...")

# Baca threshold dari config (default: 60 hari)
from utils.config import get_threshold_churn_hari
THRESHOLD_CHURN_HARI = get_threshold_churn_hari()

rfm["churn"]  = (rfm["recency"] >= THRESHOLD_CHURN_HARI).astype(int)
rfm["segmen"] = rfm["churn"].map({1: "Berpotensi Churn", 0: "Tidak Churn"})

# Profil cluster tetap dihitung untuk visualisasi di Evaluasi Model
cp["churn_score"] = (
      cp["recency_mean"].rank(ascending=True)
    - cp["frequency_mean"].rank(ascending=True)
    - cp["monetary_mean"].rank(ascending=True)
)
churn_cluster = int(cp["churn_score"].idxmax())

n_churn = rfm["churn"].sum()
print(f"  Threshold churn : Recency >= {THRESHOLD_CHURN_HARI} hari")
print(f"  Churn (1)       : {n_churn:,} ({n_churn/len(rfm)*100:.1f}%)")
print(f"  Tidak Churn (0) : {len(rfm)-n_churn:,} ({(len(rfm)-n_churn)/len(rfm)*100:.1f}%)")

# ── [6] SCALING ───────────────────────────────────────────────
print("[6/11] Min-Max Scaling...")
FITUR  = ["recency","frequency","monetary_log"]
scaler = MinMaxScaler()
X      = pd.DataFrame(scaler.fit_transform(rfm[FITUR]), columns=FITUR)
y      = rfm["churn"]

# ── [7] SPLIT ─────────────────────────────────────────────────
print("[7/11] Train-test split 80:20 (stratified)...")
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=.2, random_state=RANDOM_STATE, stratify=y
)
print(f"  Latih: {len(X_tr):,} | Uji: {len(X_te):,}")

# ── [8] SMOTE ─────────────────────────────────────────────────
print("[8/11] SMOTE pada data latih...")
sm = SMOTE(random_state=RANDOM_STATE)
X_tr_sm, y_tr_sm = sm.fit_resample(X_tr, y_tr)
print(f"  Sebelum: {len(y_tr):,} | Setelah: {len(y_tr_sm):,}")

# ── [9] XGBOOST + GRIDSEARCHCV ────────────────────────────────
print("[9/11] XGBoost + GridSearchCV 5-fold...")
param_grid = {
    "n_estimators"    : [100,200,300],
    "max_depth"       : [3,5,7],
    "learning_rate"   : [0.01,0.1,0.3],
    "subsample"       : [0.7,0.8,1.0],
    "colsample_bytree": [0.7,0.8,1.0],
}
cv  = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
gs  = GridSearchCV(
    XGBClassifier(eval_metric="logloss", random_state=RANDOM_STATE, verbosity=0),
    param_grid, scoring="f1", cv=cv, n_jobs=-1, verbose=0
)
gs.fit(X_tr_sm, y_tr_sm)
model       = gs.best_estimator_
best_params = gs.best_params_

# ── [10] EVALUASI & SIMPAN ────────────────────────────────────
print("[10/11] Evaluasi & simpan artefak...")
y_pred = model.predict(X_te)
y_prob = model.predict_proba(X_te)[:,1]
cm     = confusion_matrix(y_te, y_pred)

metrics = {
    "acc" : accuracy_score(y_te, y_pred),
    "prec": precision_score(y_te, y_pred, zero_division=0),
    "rec" : recall_score(y_te, y_pred, zero_division=0),
    "f1"  : f1_score(y_te, y_pred, zero_division=0),
    "auc" : roc_auc_score(y_te, y_prob),
    "TP"  : int(cm[1][1]), "FN": int(cm[1][0]),
    "FP"  : int(cm[0][1]), "TN": int(cm[0][0]),
}

# Simpan prediksi prob seluruh donatur
rfm["prob_churn"] = model.predict_proba(
    pd.DataFrame(scaler.transform(rfm[FITUR]), columns=FITUR)
)[:,1]
rfm["prediksi"] = (rfm["prob_churn"] >= .5).astype(int)
rfm["last_date"] = pd.to_datetime(rfm["last_date"])

joblib.dump(model,       "model_churn_xgboost.pkl")
joblib.dump(scaler,      "scaler_minmax.pkl")
joblib.dump(sc_km,       "scaler_kmeans.pkl")
joblib.dump(km_final,    "kmeans_model.pkl")
joblib.dump({
    "churn_cluster" : churn_cluster,
    "cluster_profile": cp,
    "best_k"        : best_k,
    "cutoff_date"   : CUTOFF,
    "cutoff_date_str": str(CUTOFF.date()),
    "sil_scores"    : list(zip(K_RANGE, sil_ls)),
    "inertia_scores": list(zip(K_RANGE, ine_ls)),
    "best_params"   : best_params,
    "metrics"       : metrics,
    "fitur"         : FITUR,
    "n_total"       : len(rfm),
    "n_churn"       : int(n_churn),
    "n_transaksi"   : len(df),
    "threshold_churn_hari": THRESHOLD_CHURN_HARI,
    "penurunan"     : "Rp 130.000.000 (Des 2025 – Feb 2026)",
}, "model_metadata.pkl")
rfm.to_csv("rfm_hasil.csv", index=False)

m = metrics
print(f"\n{'='*50}")
print(f"  Accuracy  : {m['acc']:.4f}")
print(f"  Precision : {m['prec']:.4f}")
print(f"  Recall    : {m['rec']:.4f}  <- prioritas")
print(f"  F1-Score  : {m['f1']:.4f}")
print(f"  AUC-ROC   : {m['auc']:.4f}")
print(f"  TP={m['TP']} FN={m['FN']} FP={m['FP']} TN={m['TN']}")
print(f"{'='*50}")

# ── [11] GENERATE GAMBAR ──────────────────────────────────────
print("\n[11/11] Generate gambar untuk dashboard...")
sns.set_style("whitegrid")

# 1) eda_rfm.png — Distribusi RFM per Kelas
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, col, title in zip(
    axes, ["recency","frequency","monetary_log"],
    ["Recency (hari)","Frequency (kali)","Monetary Log"]
):
    sns.histplot(data=rfm, x=col, hue="segmen", bins=30, ax=ax,
                 palette={"Berpotensi Churn":"#e74c3c","Tidak Churn":"#2ecc71"},
                 element="step", stat="density", common_norm=False)
    ax.set_title(title)
plt.suptitle("Distribusi RFM per Kelas Churn")
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/eda_rfm.png", dpi=150)
plt.close()
print("  [OK] eda_rfm.png")

# 2) cluster_evaluation.png — Elbow Method & Silhouette Score
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(list(K_RANGE), ine_ls, marker="o", color="#3498db")
axes[0].axvline(best_k, color="red", linestyle="--", alpha=0.6)
axes[0].set_xlabel("Jumlah Cluster (K)")
axes[0].set_ylabel("Inertia (WCSS)")
axes[0].set_title("Elbow Method")

axes[1].plot(list(K_RANGE), sil_ls, marker="o", color="#9b59b6")
axes[1].axvline(best_k, color="red", linestyle="--", alpha=0.6)
axes[1].set_xlabel("Jumlah Cluster (K)")
axes[1].set_ylabel("Silhouette Score")
axes[1].set_title(f"Silhouette Score (K optimal = {best_k})")
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/cluster_evaluation.png", dpi=150)
plt.close()
print("  [OK] cluster_evaluation.png")

# 3) cluster_profile.png — Profil Cluster Donatur
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
cp_plot = cp.reset_index()
for ax, col, title in zip(
    axes, ["recency_mean","frequency_mean","monetary_mean"],
    ["Recency Rata-rata (hari)","Frequency Rata-rata (kali)","Monetary Rata-rata (Rp)"]
):
    colors = ["#e74c3c" if c == churn_cluster else "#2ecc71" for c in cp_plot["cluster"]]
    ax.bar(cp_plot["cluster"].astype(str), cp_plot[col], color=colors)
    ax.set_title(title)
    ax.set_xlabel("Cluster")
plt.suptitle(f"Profil Cluster Donatur (Cluster {churn_cluster} = Berpotensi Churn)")
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/cluster_profile.png", dpi=150)
plt.close()
print("  [OK] cluster_profile.png")

# 4) confusion_matrix.png
fig, ax = plt.subplots(figsize=(5, 4))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["Tidak Churn","Churn"],
            yticklabels=["Tidak Churn","Churn"], ax=ax)
ax.set_xlabel("Prediksi")
ax.set_ylabel("Aktual")
ax.set_title("Confusion Matrix — Model XGBoost")
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/confusion_matrix.png", dpi=150)
plt.close()
print("  [OK] confusion_matrix.png")

# 5) roc_curve.png
fpr, tpr, _ = roc_curve(y_te, y_prob)
fig, ax = plt.subplots(figsize=(5.5, 4.5))
ax.plot(fpr, tpr, color="#e74c3c", label=f"AUC = {m['auc']:.4f}")
ax.plot([0,1],[0,1], linestyle="--", color="gray")
ax.set_xlabel("False Positive Rate")
ax.set_ylabel("True Positive Rate")
ax.set_title("ROC Curve — Model XGBoost")
ax.legend(loc="lower right")
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/roc_curve.png", dpi=150)
plt.close()
print("  [OK] roc_curve.png")

# 6) feature_importance.png
fi = pd.Series(model.feature_importances_, index=FITUR).sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(6, 4))
fi.plot(kind="barh", color="#3498db", ax=ax)
ax.set_xlabel("Feature Importance")
ax.set_title("Feature Importance — Model XGBoost")
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/feature_importance.png", dpi=150)
plt.close()
print("  [OK] feature_importance.png")

# 7) metrik_evaluasi.png — Ringkasan Metrik Evaluasi
fig, ax = plt.subplots(figsize=(7, 4))
metrik_nama = ["Accuracy","Precision","Recall","F1-Score","AUC-ROC"]
metrik_nilai = [m["acc"], m["prec"], m["rec"], m["f1"], m["auc"]]
bars = ax.bar(metrik_nama, metrik_nilai, color="#2ecc71")
ax.set_ylim(0, 1.1)
ax.axhline(0.8, color="red", linestyle="--", alpha=0.5, label="Target Minimum 80%")
for bar, val in zip(bars, metrik_nilai):
    ax.text(bar.get_x()+bar.get_width()/2, val+0.02, f"{val*100:.2f}%",
            ha="center", fontsize=9)
ax.set_title("Ringkasan Metrik Evaluasi Model XGBoost")
ax.legend()
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/metrik_evaluasi.png", dpi=150)
plt.close()
print("  [OK] metrik_evaluasi.png")

print("\nSemua 7 gambar berhasil dibuat di folder proyek.")
print("Selesai! Jalankan: streamlit run app.py")