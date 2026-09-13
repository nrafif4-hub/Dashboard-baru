"""
Konfigurasi umum aplikasi — nama-nama file artefak model & data,
threshold churn, dan parameter yang bisa diubah admin.
"""

import json
import os

# ── Artefak model (dihasilkan oleh train_model.py) ──────────────
MODEL_FILE = "model_churn_xgboost.pkl"
SCALER_FILE = "scaler_minmax.pkl"
METADATA_FILE = "model_metadata.pkl"

# ── Sumber data utama ─────────────────────────────────────────
RFM_FILE = "rfm_hasil.csv"

# Beberapa kemungkinan nama file database transaksi (spasi / underscore)
TRANSAKSI_FILE_CANDIDATES = [
    "Database Filantropi OUF - Transaksi WA.csv",
    "Database_Filantropi_OUF_-_Transaksi_WA.csv",
    "database filantropi ouf - transaksi wa.csv",
]

# ── Threshold churn (default, bisa di-override via config_table.json) ──
_DEFAULT_THRESHOLD_CHURN_HARI = 60       # Recency >= X hari → label churn (training)
_DEFAULT_THRESHOLD_CHURN_PROB = 0.5      # Probabilitas >= X → prediksi churn (dashboard)

# ── Config table (admin-editable JSON) ───────────────────────
CONFIG_TABLE_FILE = "config_table.json"

def _load_config_table():
    """Baca config_table.json jika ada, kembalikan dict kosong jika tidak."""
    if os.path.exists(CONFIG_TABLE_FILE):
        try:
            with open(CONFIG_TABLE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def _save_config_table(data: dict):
    """Simpan config_table.json."""
    with open(CONFIG_TABLE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_threshold_churn_hari() -> int:
    """Threshold recency (hari) untuk labeling churn saat training."""
    ct = _load_config_table()
    return int(ct.get("THRESHOLD_CHURN_HARI", _DEFAULT_THRESHOLD_CHURN_HARI))

def get_threshold_churn_prob() -> float:
    """Threshold probabilitas untuk klasifikasi churn di dashboard."""
    ct = _load_config_table()
    return float(ct.get("THRESHOLD_CHURN_PROB", _DEFAULT_THRESHOLD_CHURN_PROB))

# Shortcut — dipakai oleh helpers.py dan semua halaman
THRESHOLD_CHURN_HARI = get_threshold_churn_hari()
THRESHOLD_CHURN_PROB = get_threshold_churn_prob()

# ── Info aplikasi (dipakai di sidebar) ───────────────────────
APP_TITLE = "DSS Churn Donatur · One Ummah Foundation"
APP_ICON = "🕌"
APP_VERSION_CAPTION = "DSS Prediksi Churn Naufal Rafif Sistem Informasi UNIKOM"

# ── Direktori ────────────────────────────────────────────────
BACKUP_DIR = "backups"
MODELS_DIR = "models"
AUDIT_LOG_FILE = "audit_log.csv"