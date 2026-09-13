"""
Fungsi-fungsi loading data & artefak model.
Dipindahkan dari app.py TANPA mengubah logika, hanya nama file
literal digantikan konstanta dari utils/config.py.
"""

import joblib
import pandas as pd
import streamlit as st

from utils.config import MODEL_FILE, SCALER_FILE, METADATA_FILE, RFM_FILE, TRANSAKSI_FILE_CANDIDATES


# ── LOAD ARTEFAK ──────────────────────────────────────────────
@st.cache_resource
def load_all():
    try:
        return (
            joblib.load(MODEL_FILE),
            joblib.load(SCALER_FILE),
            joblib.load(METADATA_FILE),
        )
    except FileNotFoundError:
        return None, None, None

@st.cache_data(ttl=300)  # 5 menit TTL
def load_rfm():
    try:
        df = pd.read_csv(RFM_FILE)
        df["last_date"] = pd.to_datetime(df["last_date"], format="mixed", dayfirst=False)
        return df
    except FileNotFoundError:
        return None

def _parse_tgl_riwayat(t):
    """Parser tanggal khusus riwayat — sama logikanya dengan parse_tgl di bawah,
    didefinisikan lebih awal supaya bisa dipakai oleh load_riwayat()."""
    _BULAN = {
        "Januari":"January","Februari":"February","Maret":"March",
        "April":"April","Mei":"May","Juni":"June","Juli":"July",
        "Agustus":"August","September":"September",
        "Oktober":"October","November":"November","Desember":"December",
    }
    t = str(t).strip()
    for a,b in _BULAN.items(): t = t.replace(a,b)
    try: return pd.to_datetime(t, dayfirst=True)
    except Exception:
        try: return pd.to_datetime("1 "+t, dayfirst=True)
        except Exception: return pd.NaT

@st.cache_data(ttl=300)  # 5 menit TTL
def load_riwayat():
    """Riwayat transaksi mentah per donatur (program & tanggal donasi).
    Dibaca langsung dari database transaksi asli (file CSV yang sama
    dipakai oleh train_model.py) — tidak perlu file riwayat terpisah.
    Mencoba beberapa kemungkinan nama file (spasi / underscore)."""
    kandidat_nama = TRANSAKSI_FILE_CANDIDATES

    df_raw = None
    for nama_file in kandidat_nama:
        try:
            df_raw = pd.read_csv(nama_file, skiprows=1)
            break
        except FileNotFoundError:
            continue

    if df_raw is None:
        return None

    try:
        df = df_raw.drop(columns=[c for c in df_raw.columns if "Unnamed" in c or c.strip()=="No"], errors="ignore")
        df.columns = df.columns.str.strip()

        df["Nominal"] = (
            df["Nominal"].astype(str)
            .str.replace("Rp","",regex=False)
            .str.replace(",","",regex=False)
            .str.strip()
        )
        df["Nominal"] = pd.to_numeric(df["Nominal"], errors="coerce")
        df["Tanggal"] = df["Donasi Tanggal"].apply(_parse_tgl_riwayat)
        df["Program"] = df["Program"].astype(str).str.strip()
        df["ID Donatur"] = df["ID Donatur"].astype(str).str.strip()

        df.dropna(subset=["ID Donatur","Nominal","Tanggal"], inplace=True)
        df = df[df["Nominal"] > 0]
        return df[["ID Donatur","Tanggal","Program","Nominal","Cara Bayar"]]
    except Exception:
        return None