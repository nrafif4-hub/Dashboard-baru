"""
Scheduled Retraining Script — One Ummah Foundation
Dijalankan via cron/Airflow/Prefect untuk retrain otomatis.

Contoh crontab:
    0 2 * * 1  cd /path/to/project && python scripts/retrain_cron.py

Pipeline:
    1. Jalankan train_model.py
    2. Bandingkan metrik model baru vs model lama
    3. Jika metrik OK → swap model (simpan ke folder models/vN/)
    4. Jika metrik turun → rollback, kirim notifikasi
"""

import os
import sys
import shutil
import joblib
import subprocess
from datetime import datetime

# Tambahkan project root ke path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from utils.config import MODELS_DIR, METADATA_FILE
from scripts.validate_model import should_swap, load_metrics


def get_next_version():
    """Tentukan versi model berikutnya (v1, v2, dst.)."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    existing = [d for d in os.listdir(MODELS_DIR) if d.startswith("v") and d[1:].isdigit()]
    if not existing:
        return 1
    return max(int(d[1:]) for d in existing) + 1


def backup_current_model(version):
    """Simpan model saat ini ke folder versioning."""
    version_dir = os.path.join(MODELS_DIR, f"v{version}")
    os.makedirs(version_dir, exist_ok=True)

    artifacts = [
        "model_churn_xgboost.pkl",
        "scaler_minmax.pkl",
        "scaler_kmeans.pkl",
        "kmeans_model.pkl",
        "model_metadata.pkl",
    ]
    for f in artifacts:
        if os.path.exists(f):
            shutil.copy2(f, os.path.join(version_dir, f))

    return version_dir


def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"  SCHEDULED RETRAIN — {timestamp}")
    print(f"{'='*60}")

    # 1. Ambil metrik model lama (sebelum retrain)
    old_metrics = load_metrics()
    if old_metrics:
        print(f"\n[INFO] Metrik model lama:")
        for k, v in old_metrics.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")

    # 2. Backup model lama
    version = get_next_version()
    if old_metrics:
        backup_dir = backup_current_model(version - 1 if version > 1 else 1)
        print(f"[INFO] Model lama di-backup ke: {backup_dir}")

    # 3. Jalankan retrain
    print(f"\n[INFO] Menjalankan train_model.py...")
    result = subprocess.run(
        [sys.executable, "train_model.py"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"[ERROR] Retrain gagal!\n{result.stderr}")
        sys.exit(1)

    # 4. Bandingkan metrik
    new_metrics = load_metrics()
    if old_metrics and new_metrics:
        swap, reasons = should_swap(old_metrics, new_metrics)
        print(f"\n[INFO] Hasil validasi model baru:")
        for r in reasons:
            print(f"  {r}")

        if not swap:
            print(f"\n[WARNING] Model baru TIDAK lebih baik — rollback ke model lama")
            # Restore model lama dari backup
            old_version_dir = os.path.join(MODELS_DIR, f"v{version - 1 if version > 1 else 1}")
            if os.path.exists(old_version_dir):
                for f in os.listdir(old_version_dir):
                    shutil.copy2(os.path.join(old_version_dir, f), f)
                print("[INFO] Rollback berhasil.")
            sys.exit(1)

    # 5. Simpan model baru ke versioning
    new_version_dir = backup_current_model(version)
    print(f"\n[OK] Model baru disimpan ke: {new_version_dir}")

    # 6. Log
    from utils.audit import log_action
    log_action("cron_retrain", "RETRAIN",
               f"Model v{version} — auto retrain berhasil")

    print(f"\n{'='*60}")
    print(f"  RETRAIN SELESAI — Model v{version}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
