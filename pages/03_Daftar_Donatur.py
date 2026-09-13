import streamlit as st

from utils.data_loader import load_rfm
from utils.helpers import kpi_card
from utils.config import THRESHOLD_CHURN_PROB

rfm_df = load_rfm()

st.markdown('<div class="hero-title">📋 Daftar & Segmentasi Donatur</div>', unsafe_allow_html=True)

if rfm_df is None:
    st.error("⚠ Jalankan `train_model.py` terlebih dahulu.")
    st.stop()

total = len(rfm_df)
ch_n  = rfm_df["churn"].sum()

k1,k2,k3 = st.columns(3)
kpi_card(k1,"merah","⚠","Berpotensi Churn", f"{ch_n:,}", f"{ch_n/total:.1%} dari total")
kpi_card(k2,"hijau","✅","Tidak Churn", f"{total-ch_n:,}", f"{(total-ch_n)/total:.1%} dari total")
kpi_card(k3,"biru","👥","Total Donatur", f"{total:,}", "seluruh donatur teranalisis")

st.markdown("<br>", unsafe_allow_html=True)

# ── Top 10 per segmen (hasil segmentasi RFM + K-Means) ───────
st.markdown('<div class="sec">🏆 Top 10 Donatur per Segmen</div>', unsafe_allow_html=True)
st.markdown('<div class="sec-sub">Donatur dengan nominal donasi tertinggi pada masing-masing segmen hasil clustering</div>', unsafe_allow_html=True)

tc1, tc2 = st.columns(2)
with tc1:
    st.markdown("**🔴 Berpotensi Churn — nominal tertinggi**")
    top10_churn = rfm_df[rfm_df["churn"]==1].nlargest(10, "monetary")[
        ["ID Donatur","monetary","prob_churn","recency","frequency"]
    ].copy()
    top10_churn["Total Donasi"] = top10_churn["monetary"].apply(lambda x: f"Rp {x:,.0f}")
    top10_churn["Prob. Churn"]  = (top10_churn["prob_churn"]*100).round(1).astype(str)+"%"
    st.dataframe(
        top10_churn[["ID Donatur","Total Donasi","Prob. Churn"]],
        hide_index=True, use_container_width=True, height=320
    )
with tc2:
    st.markdown("**🟢 Tidak Churn — nominal tertinggi**")
    top10_ok = rfm_df[rfm_df["churn"]==0].nlargest(10, "monetary")[
        ["ID Donatur","monetary","prob_churn","recency","frequency"]
    ].copy()
    top10_ok["Total Donasi"] = top10_ok["monetary"].apply(lambda x: f"Rp {x:,.0f}")
    top10_ok["Prob. Churn"]  = (top10_ok["prob_churn"]*100).round(1).astype(str)+"%"
    st.dataframe(
        top10_ok[["ID Donatur","Total Donasi","Prob. Churn"]],
        hide_index=True, use_container_width=True, height=320
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="sec">📋 Daftar Lengkap Donatur</div>', unsafe_allow_html=True)

# Filter sederhana — biner sesuai fokus penelitian (Churn vs Tidak Churn saja)
f1,f2,f3 = st.columns(3)
with f1:
    f_status = st.selectbox("Tampilkan", ["Semua","Berpotensi Churn saja","Tidak Churn saja"])
with f2:
    f_urut = st.selectbox("Urutkan", ["Prob. churn tertinggi","Paling lama tidak donasi","Total donasi terbesar","ID Donatur A-Z"])
with f3:
    f_cari = st.text_input("Cari ID Donatur", placeholder="DAD-00001", label_visibility="collapsed")

df = rfm_df.copy()
if f_status == "Berpotensi Churn saja": df = df[df["churn"]==1]
elif f_status == "Tidak Churn saja":     df = df[df["churn"]==0]
if f_cari: df = df[df["ID Donatur"].str.contains(f_cari, case=False, na=False)]

sort_map = {
    "Prob. churn tertinggi":    ("prob_churn", False),
    "Paling lama tidak donasi": ("recency",    False),
    "Total donasi terbesar":    ("monetary",   False),
    "ID Donatur A-Z":           ("ID Donatur", True),
}
sc, sa = sort_map[f_urut]
df = df.sort_values(sc, ascending=sa)

st.caption(f"Menampilkan **{len(df):,}** dari **{len(rfm_df):,}** donatur")

disp = df[["ID Donatur","prob_churn","segmen","recency",
           "frequency","monetary","program","last_date"]].copy()
disp["Prob. Churn"]       = (disp["prob_churn"]*100).round(1).astype(str)+"%"
disp["Status"]            = disp["segmen"]
disp["Terakhir Donasi"]   = disp["recency"].astype(int).astype(str)+" hari lalu"
disp["Jumlah Donasi"]     = disp["frequency"].astype(int).astype(str)+"x"
disp["Total Donasi"]      = disp["monetary"].apply(lambda x: f"Rp {x:,.0f}")
disp["Tanggal Terakhir"]  = disp["last_date"].dt.strftime("%d %b %Y")
disp["PIC"] = disp["prob_churn"].apply(lambda p: "Tim Retensi" if p>=THRESHOLD_CHURN_PROB else "Manajer Program")

# ── Pagination ───────────────────────────────────────────────
PAGE_SIZE = 50
total_pages = max(1, (len(disp) + PAGE_SIZE - 1) // PAGE_SIZE)
pg_col1, pg_col2, pg_col3 = st.columns([1, 2, 1])
with pg_col2:
    page_num = st.number_input(
        f"Halaman (1–{total_pages})", min_value=1, max_value=total_pages, value=1,
        label_visibility="collapsed"
    )
st.caption(f"Halaman **{page_num}** dari **{total_pages}** ({PAGE_SIZE} donatur per halaman)")

start_idx = (page_num - 1) * PAGE_SIZE
end_idx = min(start_idx + PAGE_SIZE, len(disp))
disp_page = disp.iloc[start_idx:end_idx]

st.dataframe(
    disp_page[["ID Donatur","Prob. Churn","Status","Terakhir Donasi",
          "Jumlah Donasi","Total Donasi","program","PIC"]].rename(
              columns={"program":"Program Terakhir"}),
    use_container_width=True, height=500, hide_index=True,
)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇ Download daftar ini (CSV)", csv, "daftar_donatur_churn.csv", "text/csv")
