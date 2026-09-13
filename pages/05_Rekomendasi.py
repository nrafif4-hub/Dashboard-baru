import streamlit as st
import pandas as pd


st.markdown('<div class="hero-title">💡 Rekomendasi untuk Tim Yayasan</div>', unsafe_allow_html=True)
st.caption("Panduan praktis menangani donatur berpotensi churn")

st.markdown('<div class="sec">📋 Tabel Prioritas Tindakan per Status Donatur</div>', unsafe_allow_html=True)
st.dataframe(pd.DataFrame([
    {"Status":"🔴 Berpotensi Churn","Tindakan Utama":"Hubungi donatur secara personal, tanyakan kendala yang dihadapi, dan kirimkan laporan dampak donasi","Kanal":"WhatsApp / Telepon","PIC":"Tim Retensi","Waktu":"3 hari kerja"},
    {"Status":"🟢 Tidak Churn",     "Tindakan Utama":"Sampaikan apresiasi, tawarkan program donasi rutin, dan jadikan donatur ambassador","Kanal":"Semua kanal","PIC":"Manajer Program","Waktu":"Bulanan"},
]), use_container_width=True, hide_index=True)

st.markdown('<div class="sec">🛠️ 6 Tindakan Retensi Donatur</div>', unsafe_allow_html=True)
reko_items = [
    ("📱", "1. Hubungi Secara Personal",
     "Sebutkan nama donatur dan program yang pernah didukungnya. "
     "Pesan yang terasa personal jauh lebih efektif daripada pesan siaran (broadcast) massal."),
    ("🏆", "2. Sampaikan Apresiasi",
     "Akui kontribusi donatur secara spesifik — sebutkan berapa orang yang "
     "terbantu dari donasinya. Donatur yang merasa dihargai cenderung tetap loyal."),
    ("🤝", "3. Tanyakan Kendala",
     "Buka komunikasi dua arah. Tanyakan apakah ada hambatan yang membuat mereka "
     "tidak lagi berdonasi, baik dari sisi teknis, finansial, maupun kepercayaan."),
    ("📊", "4. Kirim Laporan Dampak Donasi",
     "Kirimkan cerita nyata tentang dampak donasi mereka, misalnya foto penerima manfaat, "
     "jumlah yang terbantu, dan kontribusi spesifik donatur tersebut."),
    ("📅", "5. Manfaatkan Momen Musiman",
     "Gunakan momen Ramadan, Idul Adha, akhir tahun, atau kejadian kemanusiaan "
     "sebagai kesempatan mengajak donatur kembali berdonasi."),
    ("🔄", "6. Ganti Kanal Komunikasi",
     "Jika pesan WhatsApp tidak direspons dalam 14 hari, coba hubungi lewat telepon "
     "atau email. Catat kanal mana yang paling efektif untuk tiap donatur."),
]
r1c1,r1c2,r1c3 = st.columns(3)
r2c1,r2c2,r2c3 = st.columns(3)
for col, (icon, title, body) in zip([r1c1,r1c2,r1c3,r2c1,r2c2,r2c3], reko_items):
    with col:
        st.markdown(f"""
        <div class="reko-card">
            <div class="reko-card-icon">{icon}</div>
            <div class="reko-card-title">{title}</div>
            <div class="reko-card-body">{body}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="sec">💎 Prinsip Dasar Menjaga Loyalitas Donatur</div>', unsafe_allow_html=True)
t1,t2,t3,t4 = st.tabs(["🤲 Kepercayaan","👥 Relasi","🔍 Transparansi","💎 Loyalitas"])

with t1:
    st.markdown("""
**Donatur bukan sekadar sumber dana — mereka adalah mitra kemanusiaan.**

Kepercayaan dibangun dengan:
- Menunjukkan bahwa yayasan peduli dan mengenal setiap donaturnya secara personal
- Membuktikan bahwa setiap rupiah dikelola dengan amanah dan berdampak nyata
- Melakukan pendekatan **sebelum** donatur pergi, bukan setelah donasi menurun
    """)
with t2:
    st.markdown("""
**Relasi yang tulus lebih kuat daripada sekadar kampanye donasi.**

Cara membangun relasi berbasis data:
1. Hubungi donatur pada momen personal — misalnya hari ulang tahun donasi pertama mereka
2. Catat program favorit dan kanal komunikasi yang paling responsif untuk tiap donatur
3. Libatkan donatur loyal sebagai duta (ambassador) yayasan
4. Segmentasi donatur memungkinkan pendekatan yang berbeda untuk tiap kelompok
    """)
with t3:
    st.markdown("""
**Transparansi adalah keunggulan utama One Ummah Foundation.**

Laporan dampak yang baik harus:
- **Personal** — sebutkan nama donatur dan program spesifik yang mereka dukung
- **Konkret** — bukan *"membantu banyak orang"*, melainkan *"23 keluarga di Cianjur mendapat sembako"*
- **Tepat waktu** — dikirim paling lambat 2 minggu setelah kampanye selesai
- **Mudah dibagikan** — agar donatur dapat menyebarkan dampaknya di media sosial
    """)
with t4:
    st.markdown("""
**Program penghargaan untuk mempertahankan donatur aktif:**

| Level | Syarat | Apresiasi |
|---|---|---|
| 🥉 Pendukung | 1–5 kali donasi | Buletin dampak bulanan |
| 🥈 Setia | 6–20 kali donasi | Laporan dampak personal + undangan acara |
| 🥇 Utama | 21+ kali donasi | Akses eksklusif + peran duta (ambassador) |
| 💎 Wakaf | Total > Rp 10 juta | Program wakaf jariyah + dedikasi khusus |
    """)
