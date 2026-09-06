import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_rfm, load_riwayat
from utils.helpers import kpi_card

rfm_df = load_rfm()
riwayat_df = load_riwayat()

st.markdown("# 🏆 Top 10 Donatur Terbesar")
st.caption("Donatur dengan kontribusi nominal tertinggi — dapat difilter per periode waktu")

if rfm_df is None:
    st.error("⚠ Jalankan `train_model.py` terlebih dahulu.")
    st.stop()

# ── Filter periode waktu (segmentasi waktu, mis. Januari 2021) ──
periode_aktif = "Semua Waktu"
if riwayat_df is not None:
    riwayat_df = riwayat_df.copy()
    riwayat_df["Bulan"] = riwayat_df["Tanggal"].dt.to_period("M").astype(str)
    daftar_bulan = ["Semua Waktu"] + sorted(riwayat_df["Bulan"].unique().tolist())
    periode_aktif = st.selectbox("📅 Pilih Periode Waktu", daftar_bulan)

if riwayat_df is not None and periode_aktif != "Semua Waktu":
    donasi_periode = (
        riwayat_df[riwayat_df["Bulan"] == periode_aktif]
        .groupby("ID Donatur")["Nominal"].sum()
        .reset_index()
        .rename(columns={"Nominal": "monetary_periode"})
    )
    top10_donasi = (
        rfm_df.merge(donasi_periode, on="ID Donatur")
        .nlargest(10, "monetary_periode")
        .reset_index(drop=True)
    )
    top10_donasi["monetary"] = top10_donasi["monetary_periode"]
    total_donasi = donasi_periode["monetary_periode"].sum()
    st.caption(f"Menampilkan Top 10 donatur khusus periode **{periode_aktif}**")
else:
    total_donasi = rfm_df["monetary"].sum()
    top10_donasi = rfm_df.nlargest(10, "monetary").reset_index(drop=True)

if len(top10_donasi) == 0:
    st.warning("Tidak ada data donasi pada periode yang dipilih.")
    st.stop()

# KPI ringkas
k1,k2,k3 = st.columns(3)
kpi_card(k1,"emas","💎","Total Donasi Top 10", f"Rp {top10_donasi['monetary'].sum():,.0f}",
         f"{top10_donasi['monetary'].sum()/total_donasi:.1%} dari total donasi periode ini")
kpi_card(k2,"biru","👑","Donatur Teratas", top10_donasi.iloc[0]["ID Donatur"],
         f"Rp {top10_donasi.iloc[0]['monetary']:,.0f}")
kpi_card(k3,"hijau","📦","Total Donasi Periode Ini", f"Rp {total_donasi:,.0f}",
         f"periode: {periode_aktif}")

st.markdown("<br>", unsafe_allow_html=True)

c1, c2 = st.columns([1.6, 1])

with c1:
    st.markdown('<div class="sec">📊 Peringkat Top 10 Donatur</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">Berdasarkan total nominal donasi — {periode_aktif}</div>', unsafe_allow_html=True)
    td = top10_donasi.copy().sort_values("monetary")
    fig_top = go.Figure(go.Bar(
        x=td["monetary"], y=td["ID Donatur"],
        orientation="h",
        marker_color=["#f1c40f" if i==len(td)-1 else "#f39c12" if i>=len(td)-3 else "#85c1e9"
                      for i in range(len(td))],
        text=[f"Rp {v:,.0f}" for v in td["monetary"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Rp %{x:,.0f}<extra></extra>"
    ))
    fig_top.update_layout(
        height=420, margin=dict(t=10,b=10,l=10,r=110),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Total Donasi (Rp)", yaxis_title="",
    )
    st.plotly_chart(fig_top, use_container_width=True)

with c2:
    st.markdown('<div class="sec">🏅 Podium 3 Teratas</div>', unsafe_allow_html=True)
    medali = ["🥇","🥈","🥉"]
    for i in range(min(3, len(top10_donasi))):
        r = top10_donasi.iloc[i]
        st.markdown(f"""
        <div class="card" style="margin-bottom:10px;">
            <div style="font-size:22px;">{medali[i]} <b>{r['ID Donatur']}</b></div>
            <div style="font-size:20px;font-weight:800;color:#1a1a2e;margin-top:4px;">Rp {r['monetary']:,.0f}</div>
            <div style="font-size:12.5px;color:#8a93a3;margin-top:4px;">
                {int(r['frequency'])}× donasi · Program: {r.get('program','-')}
            </div>
            <div style="margin-top:8px;">
                <span class="{'badge-churn' if r['prob_churn']>=.5 else 'badge-ok'}">
                    {'⚠ Berpotensi Churn' if r['prob_churn']>=.5 else '✅ Tidak Churn'}
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

# ── Tabel detail top 10 ──────────────────────────────────
st.markdown('<div class="sec">📋 Detail Top 10 Donatur</div>', unsafe_allow_html=True)
disp = top10_donasi.copy()
disp.index = disp.index + 1
disp["Peringkat"]     = disp.index
disp["Total Donasi"]  = disp["monetary"].apply(lambda x: f"Rp {x:,.0f}")
disp["Frekuensi"]     = disp["frequency"].astype(int).astype(str) + "x"
disp["Terakhir Donasi"] = disp["recency"].astype(int).astype(str) + " hari lalu"
disp["Status"] = disp["prob_churn"].apply(lambda p: "⚠ Berpotensi Churn" if p>=.5 else "✅ Tidak Churn")

st.dataframe(
    disp[["Peringkat","ID Donatur","Total Donasi","Frekuensi","Terakhir Donasi","program","Status"]].rename(
        columns={"program":"Program Terakhir"}),
    use_container_width=True, height=420, hide_index=True,
)

# ── Rincian riwayat donasi per program & tanggal ─────────
st.markdown('<div class="sec">🗂️ Rincian Riwayat Donasi per Donatur</div>', unsafe_allow_html=True)
st.markdown('<div class="sec-sub">Pilih salah satu Top 10 donatur untuk melihat seluruh riwayat program dan tanggal donasinya</div>', unsafe_allow_html=True)

pilih_id = st.selectbox("Pilih Donatur", top10_donasi["ID Donatur"].tolist())

if riwayat_df is not None:
    riw = riwayat_df[riwayat_df["ID Donatur"] == pilih_id].sort_values("Tanggal", ascending=False)
    if len(riw) == 0:
        st.info("Belum ada data riwayat detail untuk donatur ini.")
    else:
        st.caption(f"Total **{len(riw)} transaksi** ditemukan untuk **{pilih_id}**")

        # Ringkasan per program
        ring_prog = riw.groupby("Program").agg(
            total=("Nominal","sum"), jml=("Nominal","count")
        ).reset_index().sort_values("total", ascending=False)

        cc1, cc2 = st.columns([1, 1.3])
        with cc1:
            st.markdown("**Distribusi donasi per program:**")
            fig_pr = go.Figure(go.Pie(
                labels=ring_prog["Program"], values=ring_prog["total"],
                hole=.55, textinfo="label+percent",
                marker_colors=px.colors.qualitative.Set2,
            ))
            fig_pr.update_layout(height=280, margin=dict(t=10,b=10,l=10,r=10),
                                 paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig_pr, use_container_width=True)

        with cc2:
            st.markdown("**Riwayat transaksi (tanggal & program):**")
            for _, r in riw.iterrows():
                st.markdown(f"""
                <div class="riwayat-item">
                    <span class="riwayat-tgl">📅 {r['Tanggal'].strftime('%d %b %Y')}</span>
                    <span class="riwayat-prog">📦 {r['Program']}</span>
                    <span class="riwayat-nom">Rp {r['Nominal']:,.0f}</span>
                </div>""", unsafe_allow_html=True)
else:
    st.warning("⚠ File database transaksi (Database Filantropi OUF - Transaksi WA.csv) tidak ditemukan di folder ini. Rincian detail per transaksi tidak dapat ditampilkan — hanya ringkasan RFM yang tersedia.")
    st.caption("Pastikan file CSV transaksi asli berada di folder yang sama dengan dashboard_churn.py")
