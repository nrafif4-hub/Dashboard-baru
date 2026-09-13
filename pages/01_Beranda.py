import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_all, load_rfm, load_riwayat
from utils.helpers import kpi_card, goto_detail, format_rupiah_ringkas
from utils.config import THRESHOLD_CHURN_PROB

model, scaler, meta = load_all()
rfm_df = load_rfm()
riwayat_df = load_riwayat()

st.markdown("""
<div class="hero-title">🏠 Beranda</div>
<div class="hero-sub">
    Selamat datang di <b>Sistem Pendukung Keputusan Prediksi Churn Donatur</b>
    One Ummah Foundation. Sistem ini membantu tim yayasan mengetahui
    <b>donatur mana yang berpotensi berhenti berdonasi</b>, sehingga bisa
    segera ditindak lanjuti sebelum terlambat.
</div>
""", unsafe_allow_html=True)

if rfm_df is None or meta is None:
    st.error("⚠ Jalankan `train_model.py` terlebih dahulu.")
    st.stop()

total   = len(rfm_df)
ch_n    = rfm_df["churn"].sum()
ok_n    = total - ch_n

# ── 3 KPI utama (biner: Churn vs Tidak Churn) ────────────
k1,k2,k3 = st.columns(3)
kpi_card(k1,"merah","⚠️","Berpotensi Churn", f"{ch_n/total:.1%}", f"{ch_n:,} donatur perlu perhatian")
kpi_card(k2,"hijau","✅","Tidak Churn / Aktif", f"{ok_n/total:.1%}", f"{ok_n:,} donatur masih aktif")
kpi_card(k3,"biru","👥","Total Donatur Dianalisis", f"{total:,}", f"dari {meta['n_transaksi']:,} transaksi")

# ── Tooltip inline ────────────────────────────────────────
with st.popover("ℹ️ Apa arti angka-angka ini?"):
    st.markdown(f"""
**Berpotensi Churn ({ch_n/total:.0%})** — Donatur yang diprediksi akan berhenti berdonasi berdasarkan pola historis mereka.

**Tidak Churn ({ok_n/total:.0%})** — Donatur yang masih aktif dan kemungkinan kecil akan berhenti.

**Threshold saat ini:** Probabilitas ≥ {THRESHOLD_CHURN_PROB:.0%} → Berpotensi Churn
    """)

st.markdown("<br>", unsafe_allow_html=True)

# ── Baris chart ──────────────────────────────────────────
c1, c2 = st.columns([1, 1.8])

with c1:
    st.markdown('<div class="sec">🥧 Perbandingan Donatur</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Proporsi donatur berpotensi churn vs aktif</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Pie(
        labels=["Berpotensi Churn","Tidak Churn"],
        values=[ch_n, ok_n],
        hole=.68,
        marker_colors=["#e74c3c","#27ae60"],
        textinfo="percent",
        textfont_size=13,
        pull=[0.05, 0],
        hovertemplate="<b>%{label}</b><br>%{value:,} donatur (%{percent})<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>{ch_n/total:.0%}</b><br><span style='font-size:11px;color:#888'>Churn</span>",
        x=.5, y=.5, font_size=20, showarrow=False, font_color="#e74c3c"
    )
    fig.update_layout(
        showlegend=True, height=300,
        legend=dict(orientation="h", y=-.1, font_size=12),
        margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown('<div class="sec">📊 Sebaran Probabilitas Churn</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Semakin ke kanan = semakin tinggi risiko berhenti berdonasi</div>', unsafe_allow_html=True)
    fig = px.histogram(
        rfm_df, x="prob_churn", nbins=30,
        color="segmen",
        color_discrete_map={"Berpotensi Churn":"#e74c3c","Tidak Churn":"#27ae60"},
        labels={"prob_churn":"Probabilitas Churn","count":"Jumlah Donatur","segmen":"Status"},
        barmode="overlay", opacity=.8,
    )
    fig.add_vline(x=.5, line_dash="dash", line_color="#555",
                  annotation_text="Batas 50%", annotation_font_color="#555",
                  annotation_position="top right")
    fig.update_layout(
        height=300, margin=dict(t=10,b=30,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        bargap=.05, legend=dict(orientation="h", y=-.25, font_size=12),
        xaxis_title="Probabilitas Churn", yaxis_title="Jumlah Donatur",
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Tren donasi bulanan (jika riwayat ada) ────────────────
if riwayat_df is not None:
    st.markdown('<div class="sec">📈 Tren Donasi Bulanan</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Total nominal donasi yang diterima per bulan</div>', unsafe_allow_html=True)
    tren = riwayat_df.copy()
    tren["Bulan"] = tren["Tanggal"].dt.to_period("M").astype(str)
    tren_agg = tren.groupby("Bulan").agg(
        total=("Nominal","sum"), jml=("Nominal","count")
    ).reset_index().sort_values("Bulan")
    tren_agg["total_label"] = tren_agg["total"].apply(format_rupiah_ringkas)
    fig_tr = go.Figure()
    fig_tr.add_trace(go.Bar(
        x=tren_agg["Bulan"], y=tren_agg["total"],
        marker_color="#2980b9", name="Total Donasi (Rp)",
        customdata=tren_agg["total_label"],
        hovertemplate="<b>%{x}</b><br>%{customdata}<extra></extra>"
    ))
    fig_tr.update_layout(
        height=260, margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Total Donasi (Rp)", xaxis_title="",
        yaxis=dict(tickformat=",.0f", tickprefix="Rp "),
    )
    st.plotly_chart(fig_tr, use_container_width=True)

# ── Tabel prioritas ──────────────────────────────────────
st.markdown('<div class="sec">⚠ 10 Donatur yang Paling Perlu Segera Dihubungi</div>', unsafe_allow_html=True)
st.markdown('<div class="sec-sub">Diurutkan berdasarkan probabilitas churn tertinggi — klik "Lihat Detail" untuk membuka profil lengkap</div>', unsafe_allow_html=True)

top10 = rfm_df.nlargest(10, "prob_churn")[[
    "ID Donatur","prob_churn","recency","frequency","monetary","program"
]].copy()
top10["Prob. Churn"]  = (top10["prob_churn"]*100).round(1).astype(str) + "%"
top10["Sejak Donasi"] = top10["recency"].astype(int).astype(str) + " hari lalu"
top10["Total Donasi"] = top10["monetary"].apply(lambda x: f"Rp {x:,.0f}")
top10["PIC"] = top10["prob_churn"].apply(lambda p: "Tim Retensi" if p>=THRESHOLD_CHURN_PROB else "Manajer Program")

st.markdown('<div class="tbl-header">', unsafe_allow_html=True)
hdr = st.columns([1.3, 1, 1.1, 1.2, 1.3, 1.1, 1])
for c, t in zip(hdr, ["ID Donatur","Prob. Churn","Sejak Donasi","Total Donasi","Program","PIC",""]):
    c.markdown(f"**{t}**")
st.markdown('</div>', unsafe_allow_html=True)

for _, r in top10.iterrows():
    st.markdown('<div class="tbl-row">', unsafe_allow_html=True)
    row_cols = st.columns([1.3, 1, 1.1, 1.2, 1.3, 1.1, 1])
    row_cols[0].markdown(r["ID Donatur"])
    row_cols[1].markdown(f'<span class="badge-churn">{r["Prob. Churn"]}</span>' if float(r["Prob. Churn"].replace("%","")) >= 50 else r["Prob. Churn"], unsafe_allow_html=True)
    row_cols[2].markdown(r["Sejak Donasi"])
    row_cols[3].markdown(r["Total Donasi"])
    row_cols[4].markdown(r["program"])
    row_cols[5].markdown(r["PIC"])
    with row_cols[6]:
        if st.button("Lihat Detail →", key=f"btn_beranda_{r['ID Donatur']}"):
            goto_detail(r["ID Donatur"])
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
with st.expander("ℹ️ Cara membaca dashboard ini"):
    st.markdown("""
- **Berpotensi Churn** = donatur yang diprediksi akan berhenti berdonasi berdasarkan pola historis
- **Tidak Churn** = donatur yang masih aktif dan kemungkinan kecil akan berhenti
- **Probabilitas Churn** = angka 0–100% yang menunjukkan seberapa besar risiko seorang donatur berhenti. Semakin tinggi = semakin perlu segera dihubungi
- **Tim Retensi** = menangani donatur berpotensi churn (probabilitas ≥ 50%)
- **Manajer Program** = memantau donatur yang masih aktif (tidak churn)
    """)
