"""
🧪 Mode Sandbox — Data Contoh Terpisah dari Produksi
Halaman ini memungkinkan user mencoba fitur prediksi dan analisis
tanpa memengaruhi database asli.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_all
from utils.helpers import warna_prob, label_prob, get_pic, get_faktor, get_aksi, kpi_card
from utils.model import predict_churn_proba
from utils.config import THRESHOLD_CHURN_PROB

model, scaler, meta = load_all()

st.markdown('<div class="hero-title">🧪 Mode Sandbox</div>', unsafe_allow_html=True)
st.caption("Coba fitur prediksi dengan data contoh — tidak memengaruhi database produksi")

st.warning("🧪 **MODE SANDBOX** — Semua data dan hasil di halaman ini bersifat simulasi dan TIDAK disimpan ke database asli.")

if model is None or scaler is None or meta is None:
    st.error("⚠ Jalankan `train_model.py` terlebih dahulu.")
    st.stop()

# ── Data contoh (dummy) ──────────────────────────────────────
SAMPLE_DATA = pd.DataFrame([
    {"ID Donatur": "SANDBOX-001", "recency": 10,  "frequency": 15, "monetary": 2500000,  "program": "Becare Food",       "cara_bayar": "Transfer",  "last_nominal": 200000, "last_date": "2026-08-15"},
    {"ID Donatur": "SANDBOX-002", "recency": 45,  "frequency": 8,  "monetary": 1200000,  "program": "Wakaf Sumur",       "cara_bayar": "QRIS",      "last_nominal": 150000, "last_date": "2026-07-20"},
    {"ID Donatur": "SANDBOX-003", "recency": 90,  "frequency": 3,  "monetary": 450000,   "program": "Qurban Nusantara",  "cara_bayar": "Transfer",  "last_nominal": 100000, "last_date": "2026-06-01"},
    {"ID Donatur": "SANDBOX-004", "recency": 200, "frequency": 2,  "monetary": 200000,   "program": "Becare Food",       "cara_bayar": "E-Wallet",  "last_nominal": 100000, "last_date": "2026-02-15"},
    {"ID Donatur": "SANDBOX-005", "recency": 400, "frequency": 1,  "monetary": 50000,    "program": "Zakat Fitrah",      "cara_bayar": "Transfer",  "last_nominal": 50000,  "last_date": "2025-07-01"},
    {"ID Donatur": "SANDBOX-006", "recency": 5,   "frequency": 25, "monetary": 5000000,  "program": "Wakaf Produktif",   "cara_bayar": "Auto-Debit", "last_nominal": 500000, "last_date": "2026-09-05"},
    {"ID Donatur": "SANDBOX-007", "recency": 75,  "frequency": 4,  "monetary": 800000,   "program": "Becare Education",  "cara_bayar": "Transfer",  "last_nominal": 200000, "last_date": "2026-06-25"},
    {"ID Donatur": "SANDBOX-008", "recency": 150, "frequency": 2,  "monetary": 300000,   "program": "Qurban Nusantara",  "cara_bayar": "QRIS",      "last_nominal": 150000, "last_date": "2026-04-10"},
])

SAMPLE_DATA["monetary_log"] = np.log1p(SAMPLE_DATA["monetary"])
SAMPLE_DATA["last_date"] = pd.to_datetime(SAMPLE_DATA["last_date"])

# Prediksi
FITUR = meta["fitur"]
SAMPLE_DATA["prob_churn"] = predict_churn_proba(model, scaler, FITUR, SAMPLE_DATA)
SAMPLE_DATA["churn"] = (SAMPLE_DATA["prob_churn"] >= THRESHOLD_CHURN_PROB).astype(int)
SAMPLE_DATA["segmen"] = SAMPLE_DATA["churn"].map({1: "Berpotensi Churn", 0: "Tidak Churn"})

total = len(SAMPLE_DATA)
ch_n = SAMPLE_DATA["churn"].sum()

# ── KPI ──────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
kpi_card(k1, "merah", "⚠", "Berpotensi Churn", f"{ch_n}", f"{ch_n/total:.0%} dari {total} donatur contoh")
kpi_card(k2, "hijau", "✅", "Tidak Churn", f"{total-ch_n}", f"{(total-ch_n)/total:.0%} dari {total} donatur contoh")
kpi_card(k3, "abu", "🧪", "Mode Sandbox", "AKTIF", "Data contoh, bukan data asli")

st.markdown("<br>", unsafe_allow_html=True)

# ── Histogram ────────────────────────────────────────────────
st.markdown('<div class="sec">📊 Sebaran Probabilitas Churn (Data Contoh)</div>', unsafe_allow_html=True)
fig_h = px.histogram(
    SAMPLE_DATA, x="prob_churn", nbins=15, color="segmen",
    color_discrete_map={"Berpotensi Churn": "#e74c3c", "Tidak Churn": "#27ae60"},
    labels={"prob_churn": "Probabilitas Churn", "segmen": "Status"},
    barmode="overlay", opacity=.8
)
fig_h.add_vline(x=THRESHOLD_CHURN_PROB, line_dash="dash", line_color="#888",
                annotation_text=f"Batas {THRESHOLD_CHURN_PROB:.0%}")
fig_h.update_layout(height=250, margin=dict(t=5, b=30),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_h, use_container_width=True)

# ── Tabel ────────────────────────────────────────────────────
st.markdown('<div class="sec">📋 Daftar Donatur Contoh</div>', unsafe_allow_html=True)
disp = SAMPLE_DATA.copy()
disp["Prob. Churn"] = (disp["prob_churn"] * 100).round(1).astype(str) + "%"
disp["Status"] = disp["segmen"]
disp["Terakhir Donasi"] = disp["recency"].astype(str) + " hari lalu"
disp["Total Donasi"] = disp["monetary"].apply(lambda x: f"Rp {x:,.0f}")
disp["PIC"] = disp["prob_churn"].apply(
    lambda p: "Tim Retensi" if p >= THRESHOLD_CHURN_PROB else "Manajer Program"
)

st.dataframe(
    disp[["ID Donatur", "Prob. Churn", "Status", "Terakhir Donasi",
          "Total Donasi", "program", "PIC"]].rename(columns={"program": "Program"}),
    use_container_width=True, hide_index=True, height=350,
)

# ── Detail per donatur ───────────────────────────────────────
st.markdown('<div class="sec">🔍 Detail Donatur Contoh</div>', unsafe_allow_html=True)
pilih = st.selectbox(
    "Pilih donatur contoh:",
    SAMPLE_DATA["ID Donatur"].tolist(),
    format_func=lambda x: f"{x} — {disp.loc[disp['ID Donatur']==x, 'Prob. Churn'].values[0]} {disp.loc[disp['ID Donatur']==x, 'Status'].values[0]}"
)

row = SAMPLE_DATA[SAMPLE_DATA["ID Donatur"] == pilih].iloc[0]
prob = row["prob_churn"]
pct = prob * 100
lbl = label_prob(prob)
warna = warna_prob(prob)
pic, urg = get_pic(prob)
faktor = get_faktor(row)
aksi = get_aksi(row)

h1, h2, h3 = st.columns([2, 1.5, 1])
with h1:
    badge_cls = "badge-churn" if prob >= THRESHOLD_CHURN_PROB else "badge-ok"
    st.markdown(f"**{pilih}** · Program: {row['program']}")
    st.markdown(f'<span class="{badge_cls}">{lbl}</span>', unsafe_allow_html=True)
with h2:
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number", value=round(pct, 1),
        number={"suffix": "%", "font": {"size": 28, "color": warna}},
        gauge={
            "axis": {"range": [0, 100]}, "bar": {"color": warna},
            "steps": [
                {"range": [0, 50], "color": "rgba(39,174,96,0.1)"},
                {"range": [50, 80], "color": "rgba(243,156,18,0.1)"},
                {"range": [80, 100], "color": "rgba(231,76,60,0.1)"},
            ],
            "threshold": {"line": {"color": "#555", "width": 2}, "thickness": .75, "value": THRESHOLD_CHURN_PROB * 100}
        },
        title={"text": "Probabilitas Churn", "font": {"size": 11}}
    ))
    fig_g.update_layout(height=180, margin=dict(t=25, b=0, l=5, r=5), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_g, use_container_width=True)
with h3:
    st.metric("Recency", f"{int(row['recency'])} hari")
    st.metric("Frequency", f"{int(row['frequency'])}×")
    st.metric("Monetary", f"Rp {row['monetary']:,.0f}")

st.markdown("---")

# Faktor & Aksi
fb1, fb2 = st.columns(2)
with fb1:
    st.markdown("**🔎 Faktor Risiko:**")
    for f in faktor:
        st.markdown(f'<div class="faktor">{f}</div>', unsafe_allow_html=True)
with fb2:
    st.markdown("**✅ Rekomendasi Tindakan:**")
    for i, (pr, txt) in enumerate(aksi, 1):
        cls = "aksi-p" if pr else "aksi-n"
        ikon = "🔴" if pr else "⚪"
        st.markdown(f'<div class="{cls}">{ikon} <b>{i}.</b> {txt}</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info(
    "💡 **Ini adalah data simulasi.** Untuk menganalisis data donatur asli, "
    "gunakan menu **Beranda**, **Daftar Donatur**, atau **Prediksi Baru**."
)
