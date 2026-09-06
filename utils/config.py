"""
Konfigurasi umum aplikasi — nama-nama file artefak model & data.
Nilai-nilai ini SAMA PERSIS dengan yang dipakai app.py sebelum refactor;
tidak ada perilaku baru yang ditambahkan di sini.
"""

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

# ── Info aplikasi (dipakai di sidebar) ───────────────────────
APP_TITLE = "DSS Churn Donatur · One Ummah Foundation"
APP_ICON = "🕌"
APP_VERSION_CAPTION = "DSS Prediksi Churn Naufal Rafif Sistem Informasi UNIKOM"