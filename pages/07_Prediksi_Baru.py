import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_all, load_rfm, load_riwayat
from utils.helpers import warna_prob, label_prob, get_pic, get_faktor, get_aksi, parse_tgl, kpi_card
from utils.model import predict_churn_proba, predict_manual_churn
from utils.config import THRESHOLD_CHURN_PROB, BACKUP_DIR
from utils.audit import log_action
from auth.authenticator import get_username, is_viewer

model, scaler, meta = load_all()
rfm_df = load_rfm()
riwayat_df = load_riwayat()

st.markdown('<div class="hero-title">🔮 Prediksi Data Baru</div>', unsafe_allow_html=True)
st.caption("Upload data transaksi donatur terbaru untuk mendapatkan prediksi churn secara otomatis")

if model is None or scaler is None or meta is None:
    st.error("⚠ Jalankan `train_model.py` terlebih dahulu.")
    st.stop()

tab_up, tab_manual = st.tabs(["📁 Upload File CSV", "✏ Cek Donatur Manual"])

# ── Upload CSV ──
with tab_up:
    with st.expander("📋 Format data yang perlu diupload", expanded=True):
        st.markdown("""
Upload file **CSV** dengan kolom-kolom berikut (nama kolom harus persis sama, huruf besar/kecil sesuai):

| Kolom | Tipe Data | Contoh Isi | Wajib |
|---|---|---|---|
| `ID Donatur` | Teks | DAD-01234 | ✅ |
| `Donasi Tanggal` | Tanggal, format **`DD Bulan YYYY`** (nama bulan Bahasa Indonesia) | 15 Januari 2026 | ✅ |
| `Nominal` | Angka, boleh berformat `Rp 100,000` atau angka polos | Rp 150,000 | ✅ |
| `Program` | Teks — nama program donasi | Becare Food | ✅ |
| `Cara Bayar` | Teks — metode pembayaran | Transfer | ✅ |

**Catatan penting:**
- Setiap **baris** mewakili **satu transaksi donasi**. Satu donatur boleh muncul di banyak baris jika berdonasi lebih dari sekali.
- File harus punya 1 baris judul kosong/keterangan di paling atas (baris pertama dilewati saat dibaca), sama seperti format database transaksi OUF asli.
- Format file: **CSV (.csv)**, dipisahkan dengan koma.
        """)
        template_csv = (
            "Keterangan: Template Prediksi Baru\n"
            "ID Donatur,Donasi Tanggal,Nominal,Program,Cara Bayar\n"
            "DAD-99999,15 Januari 2026,150000,Becare Food,Transfer\n"
            "DAD-99998,03 Februari 2026,\"Rp 200,000\",Wakaf Sumur,QRIS\n"
        )
        st.download_button(
            "⬇ Download template CSV", template_csv,
            "template_prediksi_baru.csv", "text/csv"
        )

    uploaded = st.file_uploader("Upload file CSV", type=["csv"], label_visibility="collapsed")
    if uploaded:
        with st.spinner("🔄 Memproses data dan menjalankan prediksi..."):
            try:
                df_new = pd.read_csv(uploaded, skiprows=1)
                df_new.drop(columns=["Unnamed: 0","No"], errors="ignore", inplace=True)
                df_new.columns = df_new.columns.str.strip()

                # ── Validasi skema kolom wajib ──────────────────
                REQUIRED_COLS = {"ID Donatur", "Donasi Tanggal", "Nominal", "Program", "Cara Bayar"}
                missing_cols = REQUIRED_COLS - set(df_new.columns)
                if missing_cols:
                    st.error(f"❌ Kolom wajib tidak ditemukan: **{', '.join(sorted(missing_cols))}**")
                    st.info("Pastikan nama kolom persis sama (huruf besar/kecil sesuai template).")
                    st.stop()

                df_new["Nominal"] = (
                    df_new["Nominal"].astype(str)
                    .str.replace("Rp","",regex=False)
                    .str.replace(",","",regex=False)
                    .str.strip()
                )
                df_new["Nominal"] = pd.to_numeric(df_new["Nominal"], errors="coerce")
                df_new["Tanggal"] = df_new["Donasi Tanggal"].apply(parse_tgl)

                # ── Validasi per baris ──────────────────────────
                row_errors = []
                for i, r in df_new.iterrows():
                    baris = i + 3  # +1 index, +1 header, +1 skiprows
                    if pd.isna(r.get("ID Donatur")) or str(r.get("ID Donatur", "")).strip() == "":
                        row_errors.append(f"Baris {baris}: ID Donatur kosong")
                    if pd.isna(r.get("Nominal")) or (not pd.isna(r.get("Nominal")) and r["Nominal"] <= 0):
                        row_errors.append(f"Baris {baris}: Nominal tidak valid")
                    if pd.isna(r.get("Tanggal")):
                        row_errors.append(f"Baris {baris}: Tanggal tidak dapat diparsing ('{r.get('Donasi Tanggal', '')}')")

                if row_errors:
                    st.error(f"❌ Ditemukan **{len(row_errors)} kesalahan** pada data:")
                    for err in row_errors[:20]:
                        st.caption(f"  • {err}")
                    if len(row_errors) > 20:
                        st.caption(f"  ... dan {len(row_errors) - 20} kesalahan lainnya")
                    st.stop()

                df_new.dropna(subset=["ID Donatur","Nominal","Tanggal"], inplace=True)
                df_new = df_new[df_new["Nominal"] > 0]

                CUT   = df_new["Tanggal"].max()
                rfm_n = df_new.groupby("ID Donatur").agg(
                    recency      = ("Tanggal",    lambda x: (CUT - x.max()).days),
                    frequency    = ("Tanggal",    "count"),
                    monetary     = ("Nominal",    "sum"),
                    program      = ("Program",    lambda x: x.mode()[0] if len(x) > 0 else "-"),
                    last_date    = ("Tanggal",    "max"),
                    last_nominal = ("Nominal",    "last"),
                    cara_bayar   = ("Cara Bayar", lambda x: x.mode()[0] if len(x) > 0 else "-"),
                ).reset_index()
                rfm_n["monetary_log"] = np.log1p(rfm_n["monetary"])

                FITUR = meta["fitur"]
                rfm_n["prob_churn"] = predict_churn_proba(model, scaler, FITUR, rfm_n)
                rfm_n["churn"]      = (rfm_n["prob_churn"] >= THRESHOLD_CHURN_PROB).astype(int)
                rfm_n["segmen"]     = rfm_n["churn"].map({1:"Berpotensi Churn", 0:"Tidak Churn"})
                rfm_n["prediksi"]   = rfm_n["churn"]
                rfm_n["cluster"]    = -1   # tidak dicluster ulang
                rfm_n["PIC"]        = rfm_n["prob_churn"].apply(
                    lambda p: "Tim Retensi" if p>=THRESHOLD_CHURN_PROB else "Manajer Program"
                )
                rfm_n["last_date"]  = pd.to_datetime(rfm_n["last_date"])
                st.session_state["rfm_baru"] = rfm_n
                log_action(get_username(), "UPLOAD_CSV", f"{total_n} donatur dari file upload")

            except Exception as e:
                st.error(f"❌ Gagal memproses: {e}")
                st.stop()

    # ── Tampilkan hasil jika sudah ada di session ──────────────
    if "rfm_baru" in st.session_state:
        rfm_n   = st.session_state["rfm_baru"]
        total_n = len(rfm_n)
        ch_n    = (rfm_n["prob_churn"] >= THRESHOLD_CHURN_PROB).sum()

        st.success(f"✅ **{total_n:,} donatur** berhasil dianalisis")
        st.markdown("<br>", unsafe_allow_html=True)

        # ── KPI (biner: Churn vs Tidak Churn) ──────────────────
        k1,k2,k3 = st.columns(3)
        kpi_card(k1,"merah","⚠","Berpotensi Churn",      f"{ch_n:,}",         f"{ch_n/total_n:.1%} dari total")
        kpi_card(k2,"hijau","✅","Tidak Churn",           f"{total_n-ch_n:,}", f"{(total_n-ch_n)/total_n:.1%} dari total")
        kpi_card(k3,"biru", "👥","Total Donatur",         f"{total_n:,}",      "dalam file ini")

        # ── Histogram ──────────────────────────────────────────
        st.markdown('<br><div class="sec">📊 Sebaran Probabilitas Churn</div>', unsafe_allow_html=True)
        fig_h = px.histogram(
            rfm_n, x="prob_churn", nbins=30, color="segmen",
            color_discrete_map={"Berpotensi Churn":"#e74c3c","Tidak Churn":"#27ae60"},
            labels={"prob_churn":"Probabilitas Churn","segmen":"Status"},
            barmode="overlay", opacity=.8
        )
        fig_h.add_vline(x=.5, line_dash="dash", line_color="#888", annotation_text="Batas 50%")
        fig_h.update_layout(height=220, margin=dict(t=5,b=30),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_h, use_container_width=True)

        # ── Gabungkan ke database utama ────────────────────────
        st.markdown('<div class="sec">🔗 Gabungkan ke Database Utama</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">Donatur dari file ini akan bisa dilihat di semua menu (Daftar, Detail, Rekomendasi, dll)</div>', unsafe_allow_html=True)

        col_gb1, col_gb2 = st.columns([3,1])
        with col_gb1:
            if rfm_df is not None:
                ids_lama = set(rfm_df["ID Donatur"].tolist())
                ids_baru = set(rfm_n["ID Donatur"].tolist())
                overlap  = ids_lama & ids_baru
                hanya_baru = ids_baru - ids_lama
                st.info(
                    f"📋 **{len(ids_baru):,}** donatur dalam file baru · "
                    f"**{len(hanya_baru):,}** donatur baru (belum ada di database) · "
                    f"**{len(overlap):,}** donatur sudah ada (akan diperbarui)"
                )
            else:
                st.warning("⚠ Database utama (rfm_hasil.csv) belum ada — semua donatur akan ditambahkan sebagai baru.")

        with col_gb2:
            gabung = st.button("🔗 Gabungkan Sekarang", type="primary", use_container_width=True)

        if gabung:
            if is_viewer():
                st.error("🚫 Anda tidak memiliki akses untuk menggabungkan data (role: Viewer).")
            else:
                try:
                    import shutil, os
                    from datetime import datetime as _dt

                    # Backup otomatis sebelum overwrite
                    if os.path.exists("rfm_hasil.csv"):
                        os.makedirs(BACKUP_DIR, exist_ok=True)
                        backup_name = f"rfm_hasil_backup_{_dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        shutil.copy("rfm_hasil.csv", os.path.join(BACKUP_DIR, backup_name))
                        st.caption(f"💾 Backup disimpan: `{BACKUP_DIR}/{backup_name}`")

                    if rfm_df is not None:
                        # Gabungkan: donatur yang sudah ada akan digantikan versi baru
                        rfm_gabung = pd.concat([rfm_df, rfm_n], ignore_index=True)
                        rfm_gabung = rfm_gabung.drop_duplicates(subset=["ID Donatur"], keep="last")
                    else:
                        rfm_gabung = rfm_n.copy()

                    rfm_gabung.to_csv("rfm_hasil.csv", index=False)
                    log_action(get_username(), "GABUNG_DATABASE",
                               f"{len(rfm_gabung)} donatur total setelah penggabungan")
                    st.success(
                        f"✅ Berhasil! Database sekarang berisi **{len(rfm_gabung):,} donatur**. "
                        "Silakan pindah ke menu lain untuk melihat semua donatur."
                    )
                    st.cache_data.clear()   # paksa reload rfm_hasil.csv
                    st.info("💡 Klik menu lain di sidebar untuk melihat data yang sudah diperbarui.")
                except Exception as e:
                    st.error(f"❌ Gagal menggabungkan: {e}")

        st.markdown("---")

        # ── Tabel hasil + detail per donatur ───────────────────
        st.markdown('<div class="sec">📋 Hasil Prediksi per Donatur</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">Klik baris donatur untuk melihat detail lengkap, faktor risiko, dan rekomendasi tindakan</div>', unsafe_allow_html=True)

        dn = rfm_n.sort_values("prob_churn", ascending=False).copy()
        dn["Prob. Churn"]     = (dn["prob_churn"]*100).round(1).astype(str)+"%"
        dn["Terakhir Donasi"] = dn["recency"].astype(int).astype(str)+" hari lalu"
        dn["Total Donasi"]    = dn["monetary"].apply(lambda x: f"Rp {x:,.0f}")
        dn["Status"]          = dn["segmen"]

        # Selectbox pilih donatur dari tabel
        all_ids_baru = dn["ID Donatur"].tolist()
        pilih_baru   = st.selectbox(
            "Pilih donatur untuk melihat detail lengkap:",
            all_ids_baru,
            format_func=lambda x: f"{x}  —  {dn.loc[dn['ID Donatur']==x,'Prob. Churn'].values[0]}  {dn.loc[dn['ID Donatur']==x,'Status'].values[0]}"
        )

        st.dataframe(
            dn[["ID Donatur","Prob. Churn","Status","Terakhir Donasi","Total Donasi","program","PIC"]].rename(
                columns={"program":"Program"}),
            use_container_width=True, height=320, hide_index=True,
        )

        csv_out = rfm_n.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download hasil prediksi (CSV)", csv_out, "hasil_prediksi_baru.csv", "text/csv")

        # ── Detail donatur terpilih ─────────────────────────────
        st.markdown("---")
        row_b  = dn[dn["ID Donatur"] == pilih_baru].iloc[0]
        prob_b = row_b["prob_churn"]
        pct_b  = prob_b * 100
        lbl_b  = label_prob(prob_b)
        warna_b = warna_prob(prob_b)
        pic_b, urg_b = get_pic(prob_b)
        faktor_b     = get_faktor(row_b)
        aksi_b       = get_aksi(row_b)

        st.markdown(f"## 🔍 Detail — {pilih_baru}")

        hb1, hb2, hb3, hb4 = st.columns([2.5, 1.5, 1, 1])
        with hb1:
            badge_cls = "badge-churn" if prob_b >= THRESHOLD_CHURN_PROB else "badge-ok"
            st.markdown(f"**Program:** {row_b.get('program','-')} · **Cara Bayar:** {row_b.get('cara_bayar','-')}")
            st.markdown(f'<span class="{badge_cls}">{lbl_b}</span>', unsafe_allow_html=True)
            st.caption(f"Terakhir donasi: {pd.to_datetime(row_b['last_date']).strftime('%d %b %Y')}")
        with hb2:
            fig_gb = go.Figure(go.Indicator(
                mode="gauge+number", value=round(pct_b,1),
                number={"suffix":"%","font":{"size":30,"color":warna_b}},
                gauge={
                    "axis":{"range":[0,100]}, "bar":{"color":warna_b},
                    "steps":[
                        {"range":[0,50],  "color":"rgba(39,174,96,0.1)"},
                        {"range":[50,80], "color":"rgba(243,156,18,0.1)"},
                        {"range":[80,100],"color":"rgba(231,76,60,0.1)"},
                    ],
                    "threshold":{"line":{"color":"#555","width":2},"thickness":.75,"value":50}
                },
                title={"text":"Probabilitas Churn","font":{"size":12}}
            ))
            fig_gb.update_layout(height=190, margin=dict(t=30,b=0,l=5,r=5), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_gb, use_container_width=True)
        with hb3:
            st.metric("Terakhir donasi",  f"{int(row_b['recency'])} hari lalu")
            st.metric("Frekuensi donasi", f"{int(row_b['frequency'])}× total")
        with hb4:
            st.metric("Total donasi",     f"Rp {row_b['monetary']:,.0f}")
            st.metric("Nominal terakhir", f"Rp {row_b['last_nominal']:,.0f}")

        st.markdown("---")

        tb1, tb2, tb3 = st.tabs(["🔎 Mengapa Diprediksi Begini?", "✅ Apa yang Harus Dilakukan?", "👤 Siapa yang Menangani?"])

        with tb1:
            judul_alasan_b = (
                "Alasan donatur ini diprediksi **berpotensi churn**:"
                if prob_b >= THRESHOLD_CHURN_PROB else
                "Alasan donatur ini diprediksi **tidak churn** (masih aktif):"
            )
            st.markdown(f"**{judul_alasan_b}**")
            for f in faktor_b:
                st.markdown(f'<div class="faktor">{f}</div>', unsafe_allow_html=True)

            st.markdown("<br>**Posisi di antara semua donatur (file ini):**", unsafe_allow_html=True)
            fig_pos = px.histogram(
                rfm_n, x="prob_churn", nbins=30, color="segmen",
                color_discrete_map={"Berpotensi Churn":"#e74c3c","Tidak Churn":"#27ae60"},
                opacity=.7, labels={"prob_churn":"Probabilitas Churn","segmen":"Status"}
            )
            fig_pos.add_vline(x=prob_b, line_color="#333", line_width=3,
                              annotation_text=f"← {pilih_baru} ({pct_b:.0f}%)",
                              annotation_font_color="#333", annotation_position="top right")
            fig_pos.update_layout(height=200, margin=dict(t=5,b=30,l=5,r=5),
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  legend=dict(orientation="h", y=-.45))
            st.plotly_chart(fig_pos, use_container_width=True)

        with tb2:
            st.markdown("**6 tindakan yang dapat dilakukan tim yayasan:**")
            st.caption("🔴 = Segera lakukan · ⚪ = Tindakan pendukung")
            for i, (pr, txt) in enumerate(aksi_b, 1):
                cls  = "aksi-p" if pr else "aksi-n"
                ikon = "🔴" if pr else "⚪"
                st.markdown(f'<div class="{cls}">{ikon} <b>{i}.</b> {txt}</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if prob_b >= THRESHOLD_CHURN_PROB:
                st.warning("⚠ **SEGERA** — Hubungi donatur ini, jadwalkan pendekatan sebelum terlambat")
            else:
                st.success("✓ **PANTAU RUTIN** — Donatur masih aktif, pertahankan relasi")

        with tb3:
            st.markdown("**Tim yang bertanggung jawab:**")
            st.markdown(f"""
            <div class="pic-box">
                <div style="font-size:17px;font-weight:700;margin-bottom:4px;">{pic_b}</div>
                <div style="font-size:13px;opacity:0.7;">⏰ {urg_b}</div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame({
                "Status":      ["Berpotensi Churn","Tidak Churn"],
                "Tim PIC":     ["Tim Retensi","Manajer Program"],
                "Batas Waktu": ["3 hari kerja","Bulanan"],
            }), use_container_width=True, hide_index=True)

# ── Input manual ──
with tab_manual:
    st.markdown("**Masukkan data donatur secara manual untuk dicek risiko churn-nya:**")
    st.caption(
        "Isi tiga nilai RFM di bawah ini (Recency, Frequency, Monetary) berdasarkan riwayat donasi donatur yang ingin dicek."
    )
    mc1,mc2,mc3 = st.columns(3)
    with mc1:
        inp_rec = st.number_input("Sudah berapa hari tidak berdonasi?",
            min_value=0, max_value=3650, value=180, step=1,
            help="Hitung dari tanggal donasi terakhir hingga hari ini")
    with mc2:
        inp_frq = st.number_input("Total berapa kali pernah berdonasi?",
            min_value=1, max_value=500, value=3, step=1)
    with mc3:
        inp_mon = st.number_input("Total donasi selama ini (Rp)",
            min_value=0, max_value=100_000_000, value=250_000, step=50_000)

    if st.button("🔮 Cek Risiko Churn", type="primary"):
        FITUR    = meta["fitur"]
        inp_prob = predict_manual_churn(model, scaler, FITUR, inp_rec, inp_frq, inp_mon)
        inp_pct  = inp_prob * 100
        inp_warna = warna_prob(inp_prob)
        inp_lbl   = label_prob(inp_prob)
        inp_pic, inp_urg = get_pic(inp_prob)

        st.markdown("---")
        r1,r2,r3 = st.columns([1.5,1,1])
        with r1:
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number", value=round(inp_pct,1),
                number={"suffix":"%","font":{"size":34,"color":inp_warna}},
                gauge={
                    "axis":{"range":[0,100]}, "bar":{"color":inp_warna},
                    "steps":[
                        {"range":[0,50], "color":"#eafaf1"},
                        {"range":[50,80],"color":"#fef9e7"},
                        {"range":[80,100],"color":"#fdedec"},
                    ],
                    "threshold":{"line":{"color":"#555","width":2},"thickness":.75,"value":50}
                },
                title={"text":"Probabilitas Churn","font":{"size":13}}
            ))
            fig_g.update_layout(height=220, margin=dict(t=30,b=0,l=10,r=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_g, use_container_width=True)
        with r2:
            st.metric("Probabilitas Churn", f"{inp_pct:.1f}%")
            st.metric("Status",              inp_lbl)
            st.metric("Tim PIC",             inp_pic)
        with r3:
            st.metric("Tidak donasi selama", f"{inp_rec} hari")
            st.metric("Total donasi",        f"{inp_frq}× ({inp_frq} kali)")
            st.metric("Nilai donasi",        f"Rp {inp_mon:,.0f}")

        st.markdown("**Tindakan yang disarankan:**")
        dummy = {"prob_churn":inp_prob, "churn": int(inp_prob>=THRESHOLD_CHURN_PROB),
                 "recency":inp_rec, "frequency":inp_frq, "monetary":inp_mon, "program":"-"}
        for pr,txt in get_aksi(dummy):
            cls  = "aksi-p" if pr else "aksi-n"
            ikon = "🔴" if pr else "⚪"
            st.markdown(f'<div class="{cls}">{ikon} {txt}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if inp_prob >= THRESHOLD_CHURN_PROB:
            st.warning(f"⚠ Berpotensi churn — segera tindak lanjut ({inp_pic})")
        else:
            st.success(f"✓ Tidak churn — pantau rutin ({inp_pic})")
