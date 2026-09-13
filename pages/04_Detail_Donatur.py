import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_all, load_rfm, load_riwayat
from utils.helpers import warna_prob, label_prob, get_pic, get_faktor, get_aksi_shap
from utils.config import THRESHOLD_CHURN_PROB

model, scaler, meta = load_all()
rfm_df = load_rfm()
riwayat_df = load_riwayat()

st.markdown('<div class="hero-title">🔍 Detail Donatur</div>', unsafe_allow_html=True)
st.caption("Lihat informasi lengkap, faktor risiko, riwayat donasi, dan rekomendasi tindakan untuk setiap donatur")

if rfm_df is None:
    st.error("⚠ Jalankan `train_model.py` terlebih dahulu.")
    st.stop()

all_ids = rfm_df.sort_values("prob_churn",ascending=False)["ID Donatur"].tolist()

# ── Donatur terpilih dari halaman lain (mis. tombol "Lihat Detail" di Beranda) ──
selected_from_other_page = st.session_state.pop("selected_donor", None)

c1,c2 = st.columns([3,1])
with c2:
    q = st.selectbox("",["Pilih manual","Risiko tertinggi","Terlama tidak donasi","Donatur terbesar"],
                     label_visibility="collapsed")
if selected_from_other_page and selected_from_other_page in all_ids:
    did_default = selected_from_other_page
elif q == "Risiko tertinggi":
    did_default = rfm_df.loc[rfm_df["prob_churn"].idxmax(),"ID Donatur"]
elif q == "Terlama tidak donasi":
    did_default = rfm_df.loc[rfm_df["recency"].idxmax(),"ID Donatur"]
elif q == "Donatur terbesar":
    did_default = rfm_df.loc[rfm_df["monetary"].idxmax(),"ID Donatur"]
else:
    did_default = rfm_df.sort_values("prob_churn",ascending=False)["ID Donatur"].iloc[0]

with c1:
    did = st.selectbox("Pilih ID Donatur", all_ids, index=all_ids.index(did_default), label_visibility="collapsed")

row  = rfm_df[rfm_df["ID Donatur"]==did].iloc[0]
prob = row["prob_churn"]
pct  = prob*100
warna = warna_prob(prob)
lbl   = label_prob(prob)
pic, pic_urg = get_pic(prob)
faktor = get_faktor(row)
aksi   = get_aksi_shap(row, model, scaler, meta["fitur"]) if meta else []

st.markdown("---")

# Header
h1,h2,h3,h4 = st.columns([2.5,1.5,1,1])
with h1:
    st.markdown(f"### {did}")
    st.markdown(f"Program: **{row.get('program','-')}** · Cara Bayar: **{row.get('cara_bayar','-')}**")
    badge_cls = "badge-churn" if prob>=THRESHOLD_CHURN_PROB else "badge-ok"
    st.markdown(f'<span class="{badge_cls}">{lbl}</span>', unsafe_allow_html=True)
    st.caption(f"Terakhir donasi: {pd.to_datetime(row['last_date']).strftime('%d %b %Y')}")
with h2:
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number", value=round(pct,1),
        number={"suffix":"%","font":{"size":32,"color":warna}},
        gauge={
            "axis":{"range":[0,100],"tickwidth":1},
            "bar":{"color":warna},
            "steps":[
                {"range":[0,50], "color":"#eafaf1"},
                {"range":[50,80],"color":"#fef9e7"},
                {"range":[80,100],"color":"#fdedec"},
            ],
            "threshold":{"line":{"color":"#555","width":2},"thickness":.75,"value":50}
        },
        title={"text":"Probabilitas Churn","font":{"size":12}}
    ))
    fig_g.update_layout(height=200, margin=dict(t=30,b=0,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_g, use_container_width=True)
with h3:
    st.metric("Terakhir donasi",   f"{int(row['recency'])} hari lalu")
    st.metric("Frekuensi donasi",  f"{int(row['frequency'])}× total")
with h4:
    st.metric("Total donasi",      f"Rp {row['monetary']:,.0f}")
    st.metric("Nominal terakhir",  f"Rp {row['last_nominal']:,.0f}")

st.markdown("---")

t1,t2,t3,t4,t5 = st.tabs([
    "🔎 Mengapa Diprediksi Begini?",
    "✅ Apa yang Harus Dilakukan?",
    "👤 Siapa yang Menangani?",
    "🗂️ Riwayat Donasi",
    "📜 Ringkasan Keputusan",
])

# Tab 1 — Faktor (disesuaikan dengan status churn/tidak churn + kontribusi SHAP)
with t1:
    judul_alasan = (
        "Alasan donatur ini diprediksi **berpotensi churn**:"
        if prob >= THRESHOLD_CHURN_PROB else
        "Alasan donatur ini diprediksi **tidak churn** (masih aktif):"
    )
    st.markdown(f"**{judul_alasan}**")
    for f in faktor:
        st.markdown(f'<div class="faktor">{f}</div>', unsafe_allow_html=True)

    # ── Kontribusi SHAP per donatur (dasar keputusan otomatis tab "Apa yang Harus Dilakukan?") ──
    if model is not None and scaler is not None and meta is not None:
        try:
            from utils.model import get_shap_reasons
            top_fitur, semua_kontribusi = get_shap_reasons(model, scaler, meta["fitur"], row, top_n=3)
            st.markdown("<br>**Kontribusi SHAP terhadap prediksi donatur ini:**", unsafe_allow_html=True)
            st.caption("Dasar kuantitatif yang menentukan rekomendasi tindakan otomatis pada tab berikutnya")
            nama_fitur = {
                "recency": "Recency (kapan terakhir donasi)",
                "frequency": "Frequency (seberapa sering donasi)",
                "monetary_log": "Monetary (total nilai donasi)",
            }
            for f, v in top_fitur:
                arah = "mendorong ke arah CHURN" if v > 0 else "mendorong ke arah TIDAK CHURN"
                st.markdown(
                    f'<div class="faktor">🔹 {nama_fitur.get(f,f)}: {arah} (nilai SHAP: {v:.3f})</div>',
                    unsafe_allow_html=True
                )
        except ImportError:
            st.caption("ℹ️ Library `shap` belum terpasang — jalankan `pip install shap` untuk mengaktifkan analisis kontribusi fitur per donatur.")
        except Exception as e:
            st.caption(f"ℹ️ SHAP belum dapat dihitung untuk donatur ini: {e}")

    st.markdown("<br>**Dibandingkan rata-rata donatur lain:**", unsafe_allow_html=True)
    if meta:
        cp  = meta["cluster_profile"]
        cluster_id = int(row["cluster"])
        m1,m2,m3 = st.columns(3)
        if cluster_id in cp.index:
            # Donatur dari database utama — ada data cluster
            cr = cp.loc[cluster_id]
            m1.metric("Terakhir donasi", f"{int(row['recency'])} hari",
                      delta=f"{int(row['recency']-cr['recency_mean'])} hari dari rata-rata", delta_color="inverse")
            m2.metric("Frekuensi donasi", f"{int(row['frequency'])}×",
                      delta=f"{row['frequency']-cr['frequency_mean']:.1f}× dari rata-rata")
            m3.metric("Total donasi", f"Rp {row['monetary']:,.0f}",
                      delta=f"Rp {row['monetary']-cr['monetary_mean']:,.0f} dari rata-rata")
        else:
            # Donatur dari Prediksi Baru (cluster=-1) — bandingkan dengan rata-rata global
            avg_rec = cp["recency_mean"].mean()
            avg_frq = cp["frequency_mean"].mean()
            avg_mon = cp["monetary_mean"].mean()
            m1.metric("Terakhir donasi", f"{int(row['recency'])} hari",
                      delta=f"{int(row['recency']-avg_rec)} hari dari rata-rata global", delta_color="inverse")
            m2.metric("Frekuensi donasi", f"{int(row['frequency'])}×",
                      delta=f"{row['frequency']-avg_frq:.1f}× dari rata-rata global")
            m3.metric("Total donasi", f"Rp {row['monetary']:,.0f}",
                      delta=f"Rp {row['monetary']-avg_mon:,.0f} dari rata-rata global")
            st.caption("ℹ️ Donatur ini berasal dari Prediksi Baru — perbandingan menggunakan rata-rata global semua cluster.")

    st.markdown("<br>**Posisi donatur ini di antara semua donatur:**", unsafe_allow_html=True)
    fig_h = px.histogram(rfm_df, x="prob_churn", nbins=30, color="segmen",
                         color_discrete_map={"Berpotensi Churn":"#e74c3c","Tidak Churn":"#27ae60"},
                         opacity=.7, labels={"prob_churn":"Probabilitas Churn","segmen":"Status"})
    fig_h.add_vline(x=prob, line_color="#333", line_width=3,
                    annotation_text=f"← {did} ({pct:.0f}%)",
                    annotation_font_color="#333", annotation_position="top right")
    fig_h.update_layout(height=210, margin=dict(t=5,b=30,l=5,r=5),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        legend=dict(orientation="h", y=-.4))
    st.plotly_chart(fig_h, use_container_width=True)

# Tab 2 — Aksi (rekomendasi otomatis berbasis SHAP)
with t2:
    st.markdown("**Tindakan yang direkomendasikan sistem:**")
    st.caption("🔴 = Segera lakukan · ⚪ = Tindakan pendukung · Dipilih otomatis berdasarkan fitur SHAP paling dominan pada donatur ini")
    for i,(pr,txt) in enumerate(aksi, 1):
        cls  = "aksi-p" if pr else "aksi-n"
        ikon = "🔴" if pr else "⚪"
        st.markdown(f'<div class="{cls}">{ikon} <b>{i}.</b> {txt}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if prob >= THRESHOLD_CHURN_PROB:
        st.warning("⚠ **SEGERA** — Hubungi donatur ini, jadwalkan pendekatan sebelum terlambat")
    else:
        st.success("✓ **PANTAU RUTIN** — Donatur masih aktif, pertahankan relasi")

# Tab 3 — PIC (biner)
with t3:
    st.markdown("**Tim yang bertanggung jawab untuk donatur ini:**")
    st.markdown(f"""
    <div class="pic-box">
        <div style="font-size:17px;font-weight:700;margin-bottom:4px;">{pic}</div>
        <div style="font-size:13px;color:#555;">⏰ {pic_urg}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>**Pembagian tugas tim berdasarkan status:**", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "Status":         ["Berpotensi Churn","Tidak Churn"],
        "Tim PIC":        ["Tim Retensi","Manajer Program"],
        "Tindakan Utama": ["Hubungi segera personal","Monitoring & apresiasi"],
        "Kanal":          ["WhatsApp / Telepon","Semua kanal"],
        "Batas Waktu":    ["3 hari kerja","Bulanan"],
    }), use_container_width=True, hide_index=True)

# Tab 4 — Riwayat Donasi
with t4:
    st.markdown(f"**Seluruh riwayat program dan tanggal donasi — {did}:**")
    if riwayat_df is not None:
        riw = riwayat_df[riwayat_df["ID Donatur"] == did].sort_values("Tanggal", ascending=False)
        if len(riw) == 0:
            st.info("Belum ada data riwayat detail untuk donatur ini.")
        else:
            st.caption(f"Total **{len(riw)} transaksi** tercatat")

            ring_prog = riw.groupby("Program").agg(
                total=("Nominal","sum"), jml=("Nominal","count")
            ).reset_index().sort_values("total", ascending=False)

            rc1, rc2 = st.columns([1, 1.4])
            with rc1:
                st.markdown("**Distribusi per program:**")
                fig_pr = go.Figure(go.Pie(
                    labels=ring_prog["Program"], values=ring_prog["total"],
                    hole=.55, textinfo="label+percent",
                    marker_colors=px.colors.qualitative.Set2,
                ))
                fig_pr.update_layout(height=260, margin=dict(t=10,b=10,l=10,r=10),
                                     paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
                st.plotly_chart(fig_pr, use_container_width=True)

            with rc2:
                st.markdown("**Daftar transaksi (terbaru → terlama):**")
                for _, r in riw.iterrows():
                    st.markdown(f"""
                    <div class="riwayat-item">
                        <span class="riwayat-tgl">📅 {r['Tanggal'].strftime('%d %b %Y')}</span>
                        <span class="riwayat-prog">📦 {r['Program']}</span>
                        <span class="riwayat-nom">Rp {r['Nominal']:,.0f}</span>
                    </div>""", unsafe_allow_html=True)
    else:
        st.warning("⚠ File database transaksi (Database Filantropi OUF - Transaksi WA.csv) tidak ditemukan di folder ini. Rincian detail per transaksi tidak dapat ditampilkan.")
        st.caption("Pastikan file CSV transaksi asli berada di folder yang sama dengan dashboard_churn.py")

# Tab 5 — Ringkasan
with t5:
    st.markdown(f"""
### Ringkasan Keputusan — {did}

| Informasi | Detail |
|---|---|
| **ID Donatur** | {did} |
| **Probabilitas Churn** | **{pct:.1f}%** |
| **Status** | {lbl} |
| **Terakhir Donasi** | {int(row['recency'])} hari lalu ({pd.to_datetime(row['last_date']).strftime('%d %b %Y')}) |
| **Total Frekuensi** | {int(row['frequency'])}× transaksi |
| **Total Donasi** | Rp {row['monetary']:,.0f} |
| **Program Terakhir** | {row.get('program','-')} |
| **Cara Bayar** | {row.get('cara_bayar','-')} |
| **Tim PIC** | {pic} |
| **Tenggat Tindakan** | {pic_urg} |
| **Aksi Pertama (berbasis SHAP)** | {aksi[0][1] if aksi else '-'} |
    """)
    st.markdown("---")
    if prob >= THRESHOLD_CHURN_PROB:
        st.warning(
            f"**KEPUTUSAN SISTEM:** Donatur **{did}** berpotensi berhenti berdonasi "
            f"(probabilitas {pct:.0f}%). Lakukan pendekatan oleh **{pic}** — {pic_urg.lower()}."
        )
    else:
        st.success(
            f"**KEPUTUSAN SISTEM:** Donatur **{did}** masih aktif "
            f"(probabilitas churn hanya {pct:.0f}%). "
            f"Pertahankan relasi dan pantau secara rutin oleh **{pic}**."
        )
