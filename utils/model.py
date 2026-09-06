"""
Fungsi-fungsi terkait model XGBoost / scaler / preprocessing input / SHAP.
"""

import numpy as np
import pandas as pd


def predict_churn_proba(model, scaler, fitur, df):
    """Scaling + prediksi probabilitas churn untuk sebuah DataFrame RFM.

    Pola ini identik dengan:
        X_all = pd.DataFrame(scaler.transform(df[FITUR]), columns=FITUR)
        y_prob = model.predict_proba(X_all)[:,1]
    """
    X = pd.DataFrame(scaler.transform(df[fitur]), columns=fitur)
    return model.predict_proba(X)[:, 1]


def predict_manual_churn(model, scaler, fitur, recency, frequency, monetary):
    """Prediksi probabilitas churn dari input manual (Recency, Frequency, Monetary)."""
    inp_df = pd.DataFrame([[recency, frequency, np.log1p(monetary)]], columns=fitur)
    inp_sc = pd.DataFrame(scaler.transform(inp_df), columns=fitur)
    return float(model.predict_proba(inp_sc)[0, 1])


def get_shap_reasons(model, scaler, fitur, row, top_n=1):
    """Hitung kontribusi SHAP per fitur untuk SATU donatur.

    Mengembalikan (top_fitur, semua_kontribusi):
      - top_fitur: list [(nama_fitur, nilai_shap), ...] diurutkan dari
        kontribusi ABSOLUT terbesar ke terkecil, dipotong sebanyak top_n.
      - semua_kontribusi: dict {nama_fitur: nilai_shap} untuk seluruh fitur.

    Nilai SHAP positif = mendorong prediksi ke arah CHURN (1).
    Nilai SHAP negatif = mendorong prediksi ke arah TIDAK CHURN (0).

    Dipakai sebagai dasar rekomendasi tindakan otomatis per donatur
    (lihat utils/helpers.py -> get_aksi_shap) dan sebagai penjelasan
    per-donatur di halaman Detail Donatur.
    """
    import shap

    x_row = pd.DataFrame([[row[f] for f in fitur]], columns=fitur)
    x_scaled = pd.DataFrame(scaler.transform(x_row), columns=fitur)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(x_scaled)

    # Beberapa versi shap mengembalikan list per-kelas untuk klasifikasi biner
    if isinstance(shap_values, list):
        shap_values = shap_values[1]  # kelas churn (1)

    kontribusi = dict(zip(fitur, shap_values[0]))
    urutan = sorted(kontribusi.items(), key=lambda x: abs(x[1]), reverse=True)
    return urutan[:top_n], kontribusi
