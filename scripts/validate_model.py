"""
Validasi Model Baru vs Model Lama — One Ummah Foundation
Memastikan model baru hanya dipakai jika metriknya tidak turun drastis.

Aturan swap:
  - F1-Score tidak turun > 5%
  - Recall tidak turun > 10%  (prioritas: jangan sampai miss churn)
  - AUC-ROC tidak turun > 3%
"""

import os
import sys
import joblib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.config import METADATA_FILE

# Batas toleransi penurunan (dalam poin, bukan persen)
MAX_F1_DROP = 0.05
MAX_RECALL_DROP = 0.10
MAX_AUC_DROP = 0.03


def load_metrics(metadata_file=None):
    """Baca metrik evaluasi dari model_metadata.pkl."""
    path = metadata_file or METADATA_FILE
    if not os.path.exists(path):
        return None
    try:
        meta = joblib.load(path)
        return meta.get("metrics", None)
    except Exception:
        return None


def should_swap(old_metrics: dict, new_metrics: dict):
    """Bandingkan metrik model lama vs baru.

    Returns:
        (should_swap: bool, reasons: list[str])
    """
    reasons = []
    should = True

    # F1-Score
    f1_drop = old_metrics["f1"] - new_metrics["f1"]
    if f1_drop > MAX_F1_DROP:
        reasons.append(f"❌ F1-Score turun {f1_drop:.4f} (maks {MAX_F1_DROP}): "
                       f"{old_metrics['f1']:.4f} → {new_metrics['f1']:.4f}")
        should = False
    else:
        reasons.append(f"✅ F1-Score: {old_metrics['f1']:.4f} → {new_metrics['f1']:.4f} "
                       f"(delta: {-f1_drop:+.4f})")

    # Recall (prioritas tinggi)
    rec_drop = old_metrics["rec"] - new_metrics["rec"]
    if rec_drop > MAX_RECALL_DROP:
        reasons.append(f"❌ Recall turun {rec_drop:.4f} (maks {MAX_RECALL_DROP}): "
                       f"{old_metrics['rec']:.4f} → {new_metrics['rec']:.4f}")
        should = False
    else:
        reasons.append(f"✅ Recall: {old_metrics['rec']:.4f} → {new_metrics['rec']:.4f} "
                       f"(delta: {-rec_drop:+.4f})")

    # AUC-ROC
    auc_drop = old_metrics["auc"] - new_metrics["auc"]
    if auc_drop > MAX_AUC_DROP:
        reasons.append(f"❌ AUC-ROC turun {auc_drop:.4f} (maks {MAX_AUC_DROP}): "
                       f"{old_metrics['auc']:.4f} → {new_metrics['auc']:.4f}")
        should = False
    else:
        reasons.append(f"✅ AUC-ROC: {old_metrics['auc']:.4f} → {new_metrics['auc']:.4f} "
                       f"(delta: {-auc_drop:+.4f})")

    # Accuracy & Precision (info saja, tidak memblokir)
    reasons.append(f"ℹ️ Accuracy: {old_metrics['acc']:.4f} → {new_metrics['acc']:.4f}")
    reasons.append(f"ℹ️ Precision: {old_metrics['prec']:.4f} → {new_metrics['prec']:.4f}")

    return should, reasons


if __name__ == "__main__":
    metrics = load_metrics()
    if metrics:
        print("Metrik model saat ini:")
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")
    else:
        print("Model metadata belum tersedia.")
