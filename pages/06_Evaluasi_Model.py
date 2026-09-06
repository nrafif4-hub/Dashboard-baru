import streamlit as st
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import confusion_matrix, roc_curve, roc_auc_score

from utils.data_loader import load_all, load_rfm
from utils.helpers import kpi_card
from utils.model import predict_churn_proba

model, scaler, meta = load_all()
rfm_df = load_rfm()

st.markdown("# 🔬 Evaluasi Model")
st.caption("Hasil pengujian model XGBoost pada data uji yang terpisah dari data latih")

if meta is None:
    st.error("⚠ Jalankan `train_model.py` terlebih dahulu.")
    st.stop()

m = meta["metrics"]

c1,c2,c3,c4,c5 = st.columns(5)
kpi_card(c1,"hijau","🎯","Akurasi", f"{m['acc']:.2%}", "Proporsi prediksi yang benar")
kpi_card(c2,"biru", "🔬","Precision", f"{m['prec']:.2%}", "Ketepatan prediksi churn")
kpi_card(c3,"biru", "🔍","Recall", f"{m['rec']:.2%}", "Kemampuan deteksi donatur churn")
kpi_card(c4,"hijau","⚖️","F1-Score", f"{m['f1']:.2%}", "Keseimbangan Precision & Recall")
kpi_card(c5,"hijau","📈","AUC-ROC", f"{m['auc']:.2%}", "Kemampuan membedakan Churn vs Tidak")

st.markdown("<br>", unsafe_allow_html=True)

e1,e2 = st.columns(2)

with e1:
    st.markdown('<div class="sec">🧮 Confusion Matrix</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Hasil prediksi vs kenyataan</div>', unsafe_allow_html=True)
    TP=m["TP"]; FN=m["FN"]; FP=m["FP"]; TN=m["TN"]
    fig_cm = px.imshow(
        [[TN,FP],[FN,TP]], text_auto=True,
        labels=dict(x="Hasil Prediksi Model",y="Kondisi Sebenarnya"),
        x=["Tidak Churn","Churn"], y=["Tidak Churn","Churn"],
        color_continuous_scale="Blues",
    )
    fig_cm.update_layout(height=280, margin=dict(t=10,b=10), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_cm, use_container_width=True)
    st.caption(
        f"✅ Benar: {TP+TN:,} prediksi · ❌ Salah: {FP+FN:,} prediksi\n"
        f"FN={FN} = donatur churn yang tidak terdeteksi (paling merugikan)"
    )

with e2:
    st.markdown('<div class="sec">📉 ROC Curve</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Seberapa baik model memisahkan dua kelas</div>', unsafe_allow_html=True)
    if rfm_df is not None and model is not None and scaler is not None:
        FITUR = meta["fitur"]
        y_prob = predict_churn_proba(model, scaler, FITUR, rfm_df)
        fpr,tpr,_ = roc_curve(rfm_df["churn"], y_prob)
        auc_v = roc_auc_score(rfm_df["churn"], y_prob)
        fig_roc = go.Figure()
        fig_roc.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines",
            line=dict(color="#e74c3c",width=2.5), name=f"Model (AUC={auc_v:.4f})"))
        fig_roc.add_trace(go.Scatter(x=[0,1],y=[0,1],mode="lines",
            line=dict(color="#bdc3c7",dash="dash"), name="Tebak acak"))
        fig_roc.update_layout(
            xaxis_title="False Positive Rate", yaxis_title="True Positive Rate",
            height=280, margin=dict(t=10,b=30), paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", legend=dict(font_size=11)
        )
        st.plotly_chart(fig_roc, use_container_width=True)
        st.caption("Semakin mendekati pojok kiri atas = model semakin baik. AUC=1.0 = sempurna")

e3,e4 = st.columns(2)
with e3:
    st.markdown('<div class="sec">🧩 Fitur Mana yang Paling Penting?</div>', unsafe_allow_html=True)
    if model is not None:
        fi = pd.DataFrame({
            "Fitur": ["Recency (kapan terakhir donasi)","Frequency (seberapa sering donasi)","Monetary (total nilai donasi)"],
            "Skor Kepentingan": model.feature_importances_
        }).sort_values("Skor Kepentingan")
        fig_fi = go.Figure(go.Bar(
            x=fi["Skor Kepentingan"], y=fi["Fitur"], orientation="h",
            marker_color=["#aed6f1","#2980b9","#1a5276"],
            text=[f"{v:.4f}" for v in fi["Skor Kepentingan"]], textposition="outside"
        ))
        fig_fi.update_layout(height=220, xaxis_title="Tingkat Kepentingan",
            margin=dict(t=5,b=20,l=10,r=70), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_fi, use_container_width=True)

with e4:
    st.markdown('<div class="sec">📐 Silhouette Score</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Menentukan jumlah cluster optimal</div>', unsafe_allow_html=True)
    sil = meta.get("sil_scores",[])
    k_ls = [s[0] for s in sil]; s_ls = [s[1] for s in sil]
    bk   = meta["best_k"]
    fig_sil = go.Figure(go.Bar(
        x=[f"K={k}" for k in k_ls], y=s_ls,
        marker_color=["#e74c3c" if k==bk else "#aed6f1" for k in k_ls],
        text=[f"{v:.3f}" for v in s_ls], textposition="outside"
    ))
    fig_sil.add_hline(y=max(s_ls), line_dash="dash", line_color="#e74c3c", annotation_text=f"K terbaik = {bk}")
    fig_sil.update_layout(height=220, yaxis_title="Silhouette Score", yaxis_range=[0, max(s_ls)*1.25],
        margin=dict(t=10,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_sil, use_container_width=True)
    st.caption(f"K={bk} dipilih karena menghasilkan Silhouette Score tertinggi ({max(s_ls):.4f})")

with st.expander("ℹ️ Penjelasan metrik untuk pengguna awam"):
    st.markdown("""
- **Akurasi** — dari 100 prediksi, berapa yang benar. Contoh: 99% = 99 dari 100 prediksi benar
- **Recall** — dari semua donatur yang benar-benar akan churn, berapa persen yang berhasil dideteksi. Ini metrik terpenting karena donatur yang tidak terdeteksi = potensi kehilangan donasi
- **Precision** — dari semua yang diprediksi churn, berapa persen yang benar-benar churn
- **F1-Score** — nilai gabungan Recall dan Precision
- **AUC-ROC** — kemampuan model membedakan donatur churn vs tidak churn. Nilai 1.0 = sempurna
    """)

# ── SHAP per Program (fitur pengaturan segmentasi berbasis SHAP) ──
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="sec">⚙️ Pengaturan Analisis SHAP per Program</div>', unsafe_allow_html=True)
st.markdown('<div class="sec-sub">Lihat kontribusi tiap fitur (Recency, Frequency, Monetary) terhadap prediksi churn, dipecah per program donasi</div>', unsafe_allow_html=True)

if rfm_df is not None and model is not None and scaler is not None and "program" in rfm_df.columns:
    daftar_program = ["Semua Program"] + sorted(rfm_df["program"].dropna().unique().tolist())
    pilih_prog = st.selectbox("Pilih program untuk analisis SHAP", daftar_program)

    if st.button("🔎 Jalankan Analisis SHAP", type="primary"):
        try:
            import shap
            import matplotlib.pyplot as plt

            FITUR = meta["fitur"]
            data_shap = rfm_df if pilih_prog == "Semua Program" else rfm_df[rfm_df["program"] == pilih_prog]

            if len(data_shap) < 5:
                st.warning("⚠ Data terlalu sedikit pada program ini untuk analisis SHAP (minimal 5 donatur).")
            else:
                with st.spinner("Menghitung SHAP values..."):
                    X_shap = pd.DataFrame(scaler.transform(data_shap[FITUR]), columns=FITUR)
                    explainer = shap.TreeExplainer(model)
                    shap_values = explainer.shap_values(X_shap)

                st.markdown(f"**Kontribusi fitur untuk program: {pilih_prog}** ({len(data_shap):,} donatur)")
                fig_shap, ax = plt.subplots(figsize=(7, 4))
                shap.summary_plot(shap_values, X_shap, plot_type="bar", show=False)
                st.pyplot(fig_shap)
                plt.close(fig_shap)

                st.caption(
                    "Semakin besar nilai SHAP suatu fitur, semakin besar pengaruh fitur tersebut "
                    "terhadap prediksi churn untuk donatur pada program ini."
                )
        except ImportError:
            st.error("Library `shap` belum terpasang. Jalankan `pip install shap` terlebih dahulu.")
        except Exception as e:
            st.error(f"❌ Gagal menjalankan analisis SHAP: {e}")
else:
    st.info("Data belum lengkap untuk menjalankan analisis SHAP per program.")

# ── Visualisasi dari train_model.py ──────────────────────────
png_files = {
    "eda_rfm.png":            ("📊 Exploratory Data Analysis (EDA) — Distribusi RFM per Kelas",
                               "Distribusi Recency, Frequency, Monetary, dan scatter plot antar fitur per kelas churn."),
    "cluster_evaluation.png": ("🔵 Evaluasi Cluster — Elbow Method & Silhouette Score",
                               "Elbow Method (Inertia) dan Silhouette Score untuk menentukan jumlah cluster K yang optimal."),
    "cluster_profile.png":    ("🗂 Profil Cluster Donatur",
                               "Rata-rata Recency, Frequency, dan Monetary tiap cluster. Cluster berwarna merah = cluster churn."),
    "confusion_matrix.png":   ("🧮 Confusion Matrix — Output dari train_model.py",
                               "TP, TN, FP, FN dari hasil pengujian model pada data uji (20%)."),
    "roc_curve.png":          ("📉 ROC Curve — Output dari train_model.py",
                               "Kurva ROC model XGBoost pada data uji, termasuk titik threshold optimal (Youden's J)."),
    "feature_importance.png": ("🧩 Feature Importance — Output dari train_model.py",
                               "Tingkat kepentingan setiap fitur RFM dalam menentukan prediksi churn."),
    "metrik_evaluasi.png":    ("📐 Ringkasan Metrik Evaluasi",
                               "Visualisasi bar chart kelima metrik evaluasi model: Accuracy, Precision, Recall, F1, AUC-ROC."),
}

tersedia = {f: v for f, v in png_files.items() if os.path.exists(f)}
tidak_ada = [f for f in png_files if not os.path.exists(f)]

if tersedia:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec">🖼 Visualisasi Hasil Training</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Gambar-gambar berikut dihasilkan otomatis oleh train_model.py</div>', unsafe_allow_html=True)

    for fname, (judul, keterangan) in png_files.items():
        if os.path.exists(fname):
            st.markdown(f"**{judul}**")
            st.caption(keterangan)
            st.image(fname, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

if tidak_ada:
    with st.expander(f"⚠ {len(tidak_ada)} gambar belum tersedia (klik untuk lihat)"):
        for f in tidak_ada:
            judul, _ = png_files[f]
            st.caption(f"❌ `{f}` — {judul}")
        st.info("Jalankan ulang `train_model.py` untuk menghasilkan semua gambar.")
