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
#from auth.authenticator import check_login, get_user_role, get_user_name, show_logout_button, can_access_page

# ── KONFIGURASI ───────────────────────────────────────────────
st.set_page_config(
    page_title="DSS Churn Donatur · One Ummah Foundation",
    page_icon="🕌", layout="wide",
    initial_sidebar_state="expanded",
)

# ── AUTENTIKASI ───────────────────────────────────────────────
#if not check_login():
 #   st.stop()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Base ── */
html, body, [class*="css"] { font-family:'Inter',sans-serif; }

/* ── Keyframes ── */
@keyframes fadeInUp {
    from { opacity:0; transform:translateY(18px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes shimmer {
    0%   { background-position:-200% 0; }
    100% { background-position:200% 0; }
}
@keyframes pulse-glow {
    0%, 100% { box-shadow:0 0 4px rgba(231,76,60,0.2); }
    50%      { box-shadow:0 0 14px rgba(231,76,60,0.45); }
}
@keyframes gradient-shift {
    0%   { background-position:0% 50%; }
    50%  { background-position:100% 50%; }
    100% { background-position:0% 50%; }
}

/* ── Custom Scrollbar ── */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(34,139,59,0.3); border-radius:10px; }
::-webkit-scrollbar-thumb:hover { background:rgba(34,139,59,0.5); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1a0e 0%, #0f2614 40%, #0b1c10 100%) !important;
    border-right: 1px solid rgba(34,139,59,0.15);
}
[data-testid="stSidebar"]::before {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background:linear-gradient(90deg, #228B3B, #2daa4a, #F5C518);
    z-index:10;
}
[data-testid="stSidebar"] * { color:#d0e8d4 !important; }
[data-testid="stSidebar"] .stRadio label {
    padding:8px 12px; border-radius:10px; transition:all .25s ease;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background:rgba(34,139,59,0.12);
}
.sidebar-brand {
    text-align:center; padding:10px 0 6px;
}
.sidebar-brand h2 {
    background:linear-gradient(135deg, #4dc96a, #2daa4a, #F5C518);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    font-size:22px; font-weight:800; margin-bottom:2px;
}
.sidebar-tagline {
    font-size:13px; font-weight:600; letter-spacing:.04em;
    background:linear-gradient(90deg, #2daa4a, #F5C518);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.sidebar-divider {
    height:1px; margin:12px 0;
    background:linear-gradient(90deg, transparent, rgba(34,139,59,0.35), transparent);
}
.sidebar-perf-title {
    font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.06em;
    color:#4dc96a !important; margin-bottom:6px;
}
.sidebar-version {
    text-align:center; font-size:11px; opacity:0.45;
    padding:4px 12px; border-radius:20px;
    background:rgba(34,139,59,0.08);
    border:1px solid rgba(34,139,59,0.12);
    display:inline-block;
}

/* ── KPI Cards ── */
.kpi {
    background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.07));
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    border-radius:16px; padding:20px 22px;
    border:1px solid rgba(34,139,59,0.12);
    position:relative; overflow:hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06), inset 0 1px 0 rgba(255,255,255,0.05);
    transition: all .3s cubic-bezier(.4,0,.2,1);
    margin-bottom:10px;
    animation: fadeInUp .5s ease both;
}
.kpi:hover {
    box-shadow: 0 8px 25px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.08);
    transform: translateY(-4px);
    border-color: rgba(34,139,59,0.3);
}
.kpi::before {
    content:''; position:absolute; top:0; left:0; right:0; height:4px;
    background-size:200% 200%; animation: gradient-shift 3s ease infinite;
}
.kpi.merah::before { background:linear-gradient(90deg, #e74c3c, #ff6b6b, #e74c3c); background-size:200% 200%; animation: gradient-shift 3s ease infinite; }
.kpi.hijau::before { background:linear-gradient(90deg, #228B3B, #2daa4a, #228B3B); background-size:200% 200%; animation: gradient-shift 3s ease infinite; }
.kpi.biru::before  { background:linear-gradient(90deg, #2980b9, #3498db, #2980b9); background-size:200% 200%; animation: gradient-shift 3s ease infinite; }
.kpi.abu::before   { background:linear-gradient(90deg, #8e9aaf, #b0bec5, #8e9aaf); background-size:200% 200%; animation: gradient-shift 3s ease infinite; }
.kpi.emas::before  { background:linear-gradient(90deg, #F5C518, #fad84a, #F5C518); background-size:200% 200%; animation: gradient-shift 3s ease infinite; }
.kpi .kpi-icon-watermark {
    position:absolute; top:50%; right:12px; transform:translateY(-50%);
    font-size:42px; opacity:0.08; pointer-events:none;
}
.kpi-lbl {
    font-size:11.5px; color:#7a9e82; margin-bottom:8px; font-weight:700;
    text-transform:uppercase; letter-spacing:.06em;
}
.kpi-val { font-size:30px; font-weight:800; color:inherit; line-height:1.05; }
.kpi-sub { font-size:11.5px; opacity:0.55; margin-top:6px; font-weight:500; }

/* ── Badges ── */
.badge-churn {
    background:rgba(231,76,60,0.12); color:#ff6b6b;
    padding:5px 14px; border-radius:20px; font-size:12px; font-weight:700;
    display:inline-block; border:1px solid rgba(231,76,60,0.2);
    animation: pulse-glow 2.5s ease-in-out infinite;
}
.badge-ok {
    background:rgba(34,139,59,0.12); color:#4dc96a;
    padding:5px 14px; border-radius:20px; font-size:12px; font-weight:700;
    display:inline-block; border:1px solid rgba(34,139,59,0.2);
}
.badge-emas {
    background:rgba(245,197,24,0.12); color:#F5C518;
    padding:5px 14px; border-radius:20px; font-size:12px; font-weight:700;
    display:inline-block; border:1px solid rgba(245,197,24,0.2);
}

/* ── Section header ── */
.sec {
    font-size:15px; font-weight:700; color:inherit;
    margin:1.4rem 0 .6rem; padding-bottom:8px;
    border-bottom:2px solid transparent;
    border-image:linear-gradient(90deg, #228B3B, #F5C518, transparent) 1;
    display:flex; align-items:center; gap:8px;
}
.sec-sub { font-size:12px; opacity:0.5; margin-top:-6px; margin-bottom:.7rem; font-weight:500; }

/* ── Card panel ── */
.card {
    background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.08));
    backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
    border-radius:16px; padding:20px 22px;
    border:1px solid rgba(34,139,59,0.12);
    box-shadow:0 2px 8px rgba(0,0,0,.04);
    transition: all .3s ease;
}
.card:hover {
    box-shadow:0 6px 20px rgba(0,0,0,.1);
    transform:translateY(-2px);
    border-color:rgba(34,139,59,0.25);
}

/* ── Action items ── */
.aksi-p {
    padding:12px 16px; border-radius:10px; margin-bottom:8px;
    font-size:13.5px; background:rgba(231,76,60,0.08);
    border-left:4px solid; border-image:linear-gradient(180deg, #e74c3c, #ff6b6b) 1;
    color:inherit; transition:all .2s ease;
}
.aksi-p:hover { background:rgba(231,76,60,0.14); transform:translateX(4px); }
.aksi-n {
    padding:12px 16px; border-radius:10px; margin-bottom:8px;
    font-size:13.5px; background:rgba(34,139,59,0.08);
    border-left:4px solid; border-image:linear-gradient(180deg, #228B3B, #2daa4a) 1;
    color:inherit; transition:all .2s ease;
}
.aksi-n:hover { background:rgba(34,139,59,0.14); transform:translateX(4px); }
.faktor {
    padding:12px 16px; background:rgba(245,197,24,0.08);
    border-left:4px solid; border-image:linear-gradient(180deg, #F5C518, #fad84a) 1;
    border-radius:10px; margin-bottom:7px; font-size:13.5px;
    color:inherit; transition:all .2s ease;
}
.faktor:hover { background:rgba(245,197,24,0.14); transform:translateX(4px); }
.pic-box {
    background:linear-gradient(135deg, rgba(34,139,59,0.08), rgba(245,197,24,0.06));
    border:1px solid rgba(34,139,59,0.2);
    border-radius:14px; padding:18px 22px;
    transition:all .3s ease;
}
.pic-box:hover { border-color:rgba(34,139,59,0.35); box-shadow:0 4px 16px rgba(34,139,59,0.1); }

/* ── Riwayat donasi timeline ── */
.riwayat-item {
    display:flex; align-items:center; justify-content:space-between;
    padding:11px 16px; border-radius:10px;
    background:linear-gradient(135deg, rgba(128,128,128,0.05), rgba(128,128,128,0.08));
    border:1px solid rgba(128,128,128,0.12);
    margin-bottom:7px; font-size:13px;
    transition:all .2s ease;
}
.riwayat-item:hover {
    background:linear-gradient(135deg, rgba(34,139,59,0.06), rgba(245,197,24,0.04));
    border-color:rgba(34,139,59,0.2);
    transform:translateX(3px);
}
.riwayat-tgl  { font-weight:700; color:inherit; min-width:100px; }
.riwayat-prog { opacity:0.65; flex:1; padding:0 12px; }
.riwayat-nom  { font-weight:700; color:#2daa4a; }

/* ── Hero header ── */
.hero-title {
    font-size:28px; font-weight:800; line-height:1.2; margin-bottom:6px;
    background:linear-gradient(135deg, #228B3B, #2daa4a, #F5C518);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.hero-sub {
    font-size:14.5px; opacity:0.7; line-height:1.6; max-width:700px;
}

/* ── Podium cards ── */
.podium-1 {
    background:linear-gradient(135deg, rgba(245,197,24,0.1), rgba(245,197,24,0.06));
    border:1px solid rgba(245,197,24,0.25); border-radius:16px; padding:20px;
    transition:all .3s ease; position:relative; overflow:hidden;
}
.podium-1::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg, #F5C518, #fad84a); }
.podium-1:hover { transform:translateY(-3px); box-shadow:0 8px 24px rgba(245,197,24,0.15); }
.podium-2 {
    background:linear-gradient(135deg, rgba(189,195,199,0.1), rgba(149,165,166,0.08));
    border:1px solid rgba(189,195,199,0.25); border-radius:16px; padding:20px;
    transition:all .3s ease; position:relative; overflow:hidden;
}
.podium-2::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg, #bdc3c7, #95a5a6); }
.podium-2:hover { transform:translateY(-3px); box-shadow:0 8px 24px rgba(189,195,199,0.15); }
.podium-3 {
    background:linear-gradient(135deg, rgba(205,127,50,0.1), rgba(176,108,43,0.08));
    border:1px solid rgba(205,127,50,0.25); border-radius:16px; padding:20px;
    transition:all .3s ease; position:relative; overflow:hidden;
}
.podium-3::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg, #cd7f32, #b06c2b); }
.podium-3:hover { transform:translateY(-3px); box-shadow:0 8px 24px rgba(205,127,50,0.15); }

/* ── Rekomendasi action cards ── */
.reko-card {
    background:linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.07));
    backdrop-filter:blur(8px); border-radius:14px; padding:20px;
    border:1px solid rgba(34,139,59,0.12);
    transition:all .3s ease; height:100%;
}
.reko-card:hover {
    transform:translateY(-4px);
    box-shadow:0 8px 24px rgba(0,0,0,0.1);
    border-color:rgba(34,139,59,0.3);
}
.reko-card-icon {
    font-size:28px; margin-bottom:10px;
    width:52px; height:52px; border-radius:14px;
    display:flex; align-items:center; justify-content:center;
    background:linear-gradient(135deg, rgba(34,139,59,0.12), rgba(245,197,24,0.08));
}
.reko-card-title { font-size:14px; font-weight:700; margin-bottom:8px; }
.reko-card-body { font-size:13px; opacity:0.7; line-height:1.55; }

/* ── Tabel header ── */
.tbl-header {
    background:linear-gradient(135deg, rgba(34,139,59,0.08), rgba(245,197,24,0.04));
    border-radius:10px; padding:10px 14px; margin-bottom:4px;
    border:1px solid rgba(34,139,59,0.12);
}
.tbl-header b { font-size:12.5px; text-transform:uppercase; letter-spacing:.04em; }
.tbl-row {
    padding:9px 14px; border-radius:8px; margin-bottom:3px;
    transition:all .2s ease; border:1px solid transparent;
}
.tbl-row:hover {
    background:rgba(34,139,59,0.04); border-color:rgba(34,139,59,0.1);
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:2px solid rgba(128,128,128,0.1); }
.stTabs [data-baseweb="tab"] {
    font-weight:600; font-size:13px; border-radius:8px 8px 0 0;
    padding:8px 16px; transition:all .2s ease;
}
.stTabs [data-baseweb="tab"]:hover { background:rgba(34,139,59,0.06); }
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    border-bottom:2px solid #228B3B;
}

/* ── Misc ── */
footer { visibility:hidden; }
[data-testid="stMetricValue"] { font-size:20px; }
hr { margin:0.8rem 0; opacity:0.15; }

/* ── Streamlit buttons ── */
.stButton > button {
    border-radius:10px; font-weight:600; font-size:13px;
    transition:all .25s ease; border:1px solid rgba(128,128,128,0.2);
}
.stButton > button:hover {
    transform:translateY(-1px); box-shadow:0 4px 12px rgba(0,0,0,0.1);
}
.stButton > button[kind="primary"] {
    background:linear-gradient(135deg, #228B3B, #2daa4a) !important;
    border:none; color:#fff !important;
}
.stButton > button[kind="primary"]:hover {
    background:linear-gradient(135deg, #1a7a35, #228B3B) !important;
    box-shadow:0 4px 16px rgba(34,139,59,0.35);
}

/* ── Expander ── */
.streamlit-expanderHeader {
    font-weight:600; font-size:13.5px;
    border-radius:10px;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius:12px; overflow:hidden;
    border:1px solid rgba(34,139,59,0.12);
}
</style>
""", unsafe_allow_html=True)


# ── DAFTAR HALAMAN ──────────────────────────────────────────
all_pages = [
    ("Beranda",         "pages/01_Beranda.py",         "🏠", True),
    ("Top Donatur",     "pages/02_Top_Donatur.py",     "🏆", False),
    ("Daftar Donatur",  "pages/03_Daftar_Donatur.py",  "📋", False),
    ("Detail Donatur",  "pages/04_Detail_Donatur.py",  "🔍", False),
    ("Rekomendasi",     "pages/05_Rekomendasi.py",     "💡", False),
    ("Prediksi Baru",   "pages/07_Prediksi_Baru.py",   "🔮", False),
    ("Sandbox",         "pages/08_Sandbox.py",          "🧪", False),
]

pages = []
for title, path, icon, is_default in all_pages:
    if can_access_page(title):
        try:
            pages.append(st.Page(path, title=title, icon=icon, default=is_default))
        except Exception:
            pass

# ── SIDEBAR ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h2>🕌 One Ummah Foundation</h2>
        <div class="sidebar-tagline">#HelpWithAction</div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Dakwah · Ekonomi · Sosial · Pendidikan · Kemanusiaan")
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    #show_logout_button()

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    pg = st.navigation(pages)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;"><span class="sidebar-version">{APP_VERSION_CAPTION}</span></div>', unsafe_allow_html=True)

pg.run()
