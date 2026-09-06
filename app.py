"""
DSS Prediksi Churn Donatur — One Ummah Foundation
Naufal Rafif (10522112) | Sistem Informasi FTIK UNIKOM
Fokus: Churn vs Tidak Churn | Streamlit

app.py adalah file utama yang RINGAN — hanya menangani:
konfigurasi Streamlit, CSS global, sidebar/navigasi, info performa
model, dan routing ke halaman. Seluruh fitur ada di folder pages/.
"""

import warnings
import streamlit as st

warnings.filterwarnings("ignore")

from utils.config import APP_VERSION_CAPTION
from utils.data_loader import load_all

# ── KONFIGURASI ───────────────────────────────────────────────
st.set_page_config(
    page_title="DSS Churn Donatur · One Ummah Foundation",
    page_icon="🕌", layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family:'Inter',sans-serif; }

[data-testid="stSidebar"] { background:#15172b; }
[data-testid="stSidebar"] * { color:#e8e8ef !important; }
[data-testid="stSidebar"] .stRadio label { padding:6px 4px; border-radius:8px; }

/* ── KPI Cards ── */
.kpi { background:transparent; border-radius:14px; padding:18px 20px;
       border:1px solid rgba(128,128,128,0.25); position:relative; overflow:hidden;
       box-shadow:0 1px 3px rgba(0,0,0,.06); transition:.2s; margin-bottom:10px; }
.kpi:hover { box-shadow:0 6px 16px rgba(0,0,0,.12); transform:translateY(-2px); }
.kpi::before { content:''; position:absolute; top:0; left:0; right:0; height:4px; }
.kpi.merah::before { background:#e74c3c; }
.kpi.hijau::before { background:#27ae60; }
.kpi.biru::before  { background:#2980b9; }
.kpi.abu::before   { background:#8e9aaf; }
.kpi.emas::before  { background:#f39c12; }
.kpi-lbl { font-size:12.5px; color:#8a93a3; margin-bottom:6px; font-weight:600;
           text-transform:uppercase; letter-spacing:.03em; }
.kpi-val { font-size:28px; font-weight:800; color:inherit; line-height:1.1; }
.kpi-sub { font-size:12px; opacity:0.6; margin-top:5px; }

/* ── Badges ── */
.badge-churn { background:rgba(192,57,43,0.15); color:#e74c3c; padding:4px 12px;
               border-radius:20px; font-size:12.5px; font-weight:700; display:inline-block; }
.badge-ok    { background:rgba(30,132,73,0.15); color:#27ae60; padding:4px 12px;
               border-radius:20px; font-size:12.5px; font-weight:700; display:inline-block; }
.badge-emas  { background:rgba(185,119,14,0.15); color:#f39c12; padding:4px 12px;
               border-radius:20px; font-size:12.5px; font-weight:700; display:inline-block; }

/* ── Section header ── */
.sec { font-size:15px; font-weight:700; color:inherit;
       margin:1.4rem 0 .6rem; padding-bottom:6px;
       border-bottom:2px solid rgba(128,128,128,0.2); display:flex; align-items:center; gap:6px; }
.sec-sub { font-size:12.5px; opacity:0.55; margin-top:-6px; margin-bottom:.6rem; }

/* ── Card panel ── */
.card { background:transparent; border-radius:14px; padding:18px 20px;
        border:1px solid rgba(128,128,128,0.25); box-shadow:0 1px 3px rgba(0,0,0,.04); }

/* ── Action items ── */
.aksi-p { padding:10px 14px; border-radius:8px; margin-bottom:7px;
          font-size:13.5px; background:rgba(231,76,60,0.1); border-left:4px solid #e74c3c;
          color:inherit; }
.aksi-n { padding:10px 14px; border-radius:8px; margin-bottom:7px;
          font-size:13.5px; background:rgba(39,174,96,0.1); border-left:4px solid #27ae60;
          color:inherit; }
.faktor { padding:10px 14px; background:rgba(243,156,18,0.1);
          border-left:4px solid #f39c12; border-radius:8px;
          margin-bottom:6px; font-size:13.5px; color:inherit; }
.pic-box { background:rgba(41,128,185,0.1); border:1px solid rgba(41,128,185,0.2);
           border-radius:12px; padding:16px 20px; }

/* ── Riwayat donasi timeline ── */
.riwayat-item { display:flex; align-items:center; justify-content:space-between;
                padding:10px 14px; border-radius:8px; background:rgba(128,128,128,0.07);
                border:1px solid rgba(128,128,128,0.15); margin-bottom:6px; font-size:13px; }
.riwayat-tgl  { font-weight:700; color:inherit; min-width:90px; }
.riwayat-prog { opacity:0.7; flex:1; padding:0 10px; }
.riwayat-nom  { font-weight:700; color:#27ae60; }

/* ── Misc ── */
.stTabs [data-baseweb="tab-list"] { gap:4px; }
.stTabs [data-baseweb="tab"] { font-weight:600; font-size:13.5px; }
footer { visibility:hidden; }
[data-testid="stMetricValue"] { font-size:20px; }
hr { margin:0.8rem 0; }
</style>
""", unsafe_allow_html=True)


# ── DAFTAR HALAMAN (routing) ────────────────────────────────────
pages = [
    st.Page("pages/01_Beranda.py",         title="Beranda",         icon="🏠", default=True),
    st.Page("pages/02_Top_Donatur.py",     title="Top Donatur",     icon="🏆"),
    st.Page("pages/03_Daftar_Donatur.py",  title="Daftar Donatur",  icon="📋"),
    st.Page("pages/04_Detail_Donatur.py",  title="Detail Donatur",  icon="🔍"),
    st.Page("pages/05_Rekomendasi.py",     title="Rekomendasi",     icon="💡"),
    st.Page("pages/06_Evaluasi_Model.py",  title="Evaluasi Model",  icon="🔬"),
    st.Page("pages/07_Prediksi_Baru.py",   title="Prediksi Baru",   icon="🔮"),
]

# ── SIDEBAR: branding, menu navigasi, & performa model ──────────
with st.sidebar:
    st.markdown("## 🕌 One Ummah Foundation")
    st.markdown("**#HelpWithAction**")
    st.caption("Dakwah · Ekonomi · Sosial\nPendidikan · Kemanusiaan")
    st.markdown("---")

    pg = st.navigation(pages)

    st.markdown("---")
    _, _, meta = load_all()
    if meta:
        m = meta["metrics"]
        st.markdown("**📊 Performa Model**")
        c1, c2 = st.columns(2)
        c1.metric("Akurasi",  f"{m['acc']:.1%}")
        c2.metric("F1-Score", f"{m['f1']:.1%}")
        c1.metric("Recall",   f"{m['rec']:.1%}")
        c2.metric("AUC-ROC",  f"{m['auc']:.1%}")
    st.markdown("---")
    st.caption(APP_VERSION_CAPTION)

pg.run()