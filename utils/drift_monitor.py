"""
Data Drift Monitor — One Ummah Foundation
Deteksi apakah distribusi data baru menyimpang jauh dari data training.

Menggunakan PSI (Population Stability Index):
  PSI < 0.1  → Tidak ada perubahan signifikan
  PSI 0.1–0.2 → Perlu monitoring
  PSI > 0.2  → Distribusi berubah signifikan, perlu retrain
"""

import numpy as np
import pandas as pd


def _psi_bucket(expected, actual, buckets=10):
    """Hitung PSI antara dua distribusi numerik."""
    # Buat bin dari distribusi expected
    breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
    breakpoints = np.unique(breakpoints)  # Hapus duplikat

    if len(breakpoints) < 2:
        return 0.0

    # Hitung proporsi di tiap bin
    expected_counts = np.histogram(expected, bins=breakpoints)[0]
    actual_counts = np.histogram(actual, bins=breakpoints)[0]

    # Hindari pembagian dengan nol
    expected_pct = (expected_counts + 1) / (expected_counts.sum() + len(expected_counts))
    actual_pct = (actual_counts + 1) / (actual_counts.sum() + len(actual_counts))

    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(psi)


def check_drift(train_df: pd.DataFrame, new_df: pd.DataFrame,
                features=None, threshold=0.2):
    """Cek data drift antara data training dan data baru.

    Parameters:
        train_df: DataFrame data training (RFM)
        new_df: DataFrame data baru
        features: List fitur yang dicek (default: recency, frequency, monetary)
        threshold: Batas PSI untuk flagging (default: 0.2)

    Returns:
        dict dengan hasil per fitur:
        {
            "recency": {"psi": 0.05, "status": "OK", "message": "..."},
            ...
            "overall_drift": False,
            "recommendation": "..."
        }
    """
    if features is None:
        features = ["recency", "frequency", "monetary"]

    results = {}
    any_drift = False

    for feat in features:
        if feat not in train_df.columns or feat not in new_df.columns:
            results[feat] = {
                "psi": None,
                "status": "SKIP",
                "message": f"Kolom '{feat}' tidak ditemukan"
            }
            continue

        train_vals = train_df[feat].dropna().values
        new_vals = new_df[feat].dropna().values

        if len(train_vals) < 10 or len(new_vals) < 10:
            results[feat] = {
                "psi": None,
                "status": "SKIP",
                "message": f"Data terlalu sedikit untuk analisis ({len(train_vals)}/{len(new_vals)} baris)"
            }
            continue

        psi = _psi_bucket(train_vals, new_vals)

        if psi > threshold:
            status = "DRIFT"
            message = f"⚠ Distribusi berubah signifikan (PSI={psi:.4f} > {threshold})"
            any_drift = True
        elif psi > threshold / 2:
            status = "MONITOR"
            message = f"⚡ Perlu monitoring (PSI={psi:.4f})"
        else:
            status = "OK"
            message = f"✅ Stabil (PSI={psi:.4f})"

        results[feat] = {
            "psi": round(psi, 4),
            "status": status,
            "message": message
        }

    results["overall_drift"] = any_drift
    if any_drift:
        results["recommendation"] = (
            "🔴 Distribusi data baru berbeda signifikan dari data training. "
            "Disarankan retrain model agar prediksi tetap akurat."
        )
    else:
        results["recommendation"] = (
            "🟢 Distribusi data masih konsisten dengan data training. "
            "Model masih bisa digunakan."
        )

    return results


def format_drift_report(results: dict) -> str:
    """Format hasil drift check menjadi teks yang mudah dibaca."""
    lines = ["📊 Laporan Data Drift", "=" * 40]

    for key, val in results.items():
        if key in ("overall_drift", "recommendation"):
            continue
        if isinstance(val, dict):
            lines.append(f"  {key}: {val['message']}")

    lines.append("")
    lines.append(results.get("recommendation", ""))
    return "\n".join(lines)
