"""
Fungsi-fungsi bantu (helpers) yang dipakai di berbagai halaman.
"""

import pandas as pd
import streamlit as st

from utils.config import THRESHOLD_CHURN_PROB


# ── HELPERS ───────────────────────────────────────────────────
def warna_prob(p):
    return "#e74c3c" if p >= THRESHOLD_CHURN_PROB else "#27ae60"

def label_prob(p):
    """Biner sesuai fokus penelitian: Churn vs Tidak Churn (tanpa tingkat Sangat Tinggi/Sedang/Rendah)."""
    return "Berpotensi Churn" if p >= THRESHOLD_CHURN_PROB else "Tidak Churn"

def get_pic(p):
    """Biner: Tim Retensi untuk berpotensi churn, Manajer Program untuk tidak churn."""
    if p >= THRESHOLD_CHURN_PROB:
        return "Tim Retensi", "Tindak lanjut segera (maks. 3 hari kerja)"
    return "Manajer Program", "Monitoring rutin bulanan"

def goto_detail(donor_id):
    """Simpan ID donatur terpilih ke session_state lalu pindah ke halaman Detail Donatur."""
    st.session_state["selected_donor"] = donor_id
    st.switch_page("pages/04_Detail_Donatur.py")

def get_faktor(row):
    """Alasan ditampilkan disesuaikan dengan status churn/tidak churn donatur ini."""
    is_churn = (row["churn"] == 1) if "churn" in row and pd.notna(row.get("churn")) else (row["prob_churn"] >= THRESHOLD_CHURN_PROB)
    f = []
    if is_churn:
        if row["recency"] > 365:
            f.append(f"⏱ Sudah {int(row['recency'])} hari tidak berdonasi (lebih dari 1 tahun)")
        elif row["recency"] > 180:
            f.append(f"⏱ Sudah {int(row['recency'])} hari tidak berdonasi (lebih dari 6 bulan)")
        elif row["recency"] > 60:
            f.append(f"⏱ Sudah {int(row['recency'])} hari tidak berdonasi")
        if row["frequency"] <= 2:
            f.append(f"📉 Frekuensi donasi sangat rendah — hanya {int(row['frequency'])} kali")
        elif row["frequency"] <= 5:
            f.append(f"📉 Frekuensi donasi rendah — {int(row['frequency'])} kali")
        if row["monetary"] < 300_000:
            f.append(f"💰 Total donasi kecil — Rp {row['monetary']:,.0f}")
        if not f:
            f.append("📊 Pola donasi menunjukkan potensi berhenti berdasarkan analisis data")
    else:
        f.append(
            f"✅ Pola donasi ({int(row['frequency'])}× dalam {int(row['recency'])} hari terakhir) "
            f"sesuai profil donatur aktif berdasarkan segmentasi RFM + K-Means"
        )
        if row["frequency"] <= 2 and row["recency"] > 365:
            f.append(
                "ℹ️ Donatur ini memang jarang berdonasi sejak awal (bukan penurunan aktivitas), "
                "sehingga tidak termasuk kelompok prioritas retensi berdasarkan profil clusternya"
            )
    return f

def get_aksi(row):
    """Rekomendasi tindakan berbasis aturan tetap (fixed-rule), dipakai sebagai fallback
    jika SHAP tidak tersedia (model/scaler belum di-load atau library shap belum terpasang)."""
    p    = row["prob_churn"]
    prog = row.get("program","-")
    if p >= THRESHOLD_CHURN_PROB:
        return [
            (True,  f'Hubungi langsung via WhatsApp — sebut nama & program "{prog}" yang pernah didukung'),
            (True,  'Tanyakan kabar dan kendala — apakah ada hal yang menghambat donasi?'),
            (True,  f'Kirim laporan dampak donasi program {prog} secara personal (foto + cerita)'),
            (True,  'Sampaikan apresiasi — sebutkan berapa orang yang sudah terbantu lewat kontribusinya'),
            (False, 'Masukkan ke campaign Ramadan / Idul Adha / momen kemanusiaan sebagai pintu kembali'),
            (False, 'Jika tidak merespons 14 hari → coba hubungi via telepon atau kanal lain'),
        ]
    else:
        return [
            (False, 'Kirim ucapan apresiasi — akui loyalitas dan kontribusi yang sudah diberikan'),
            (False, 'Informasikan program baru atau dampak terkini dari yayasan'),
            (False, 'Tawarkan program donasi rutin bulanan (auto-debit) agar lebih mudah'),
            (False, 'Ajak menjadi donatur ambassador — bagikan cerita kepada keluarga/teman'),
            (False, 'Informasikan program wakaf atau donasi jariyah jangka panjang'),
            (False, 'Pantau rutin — jika recency mulai di atas 90 hari segera hubungi'),
        ]

def get_aksi_shap(row, model, scaler, fitur):
    """Rekomendasi tindakan OTOMATIS berbasis fitur SHAP dominan per donatur.

    Berbeda dengan get_aksi() (aturan tetap berdasarkan threshold probabilitas),
    fungsi ini menentukan tindakan berdasarkan fitur RFM mana yang paling besar
    kontribusinya (nilai SHAP) terhadap prediksi churn donatur SPESIFIK ini —
    sehingga rekomendasi bersifat personal, bukan generik per rentang probabilitas.

    Jika SHAP gagal dihitung (mis. library belum terpasang, atau model/scaler
    None), otomatis jatuh ke get_aksi() sebagai fallback.
    """
    p    = row["prob_churn"]
    prog = row.get("program", "-")

    if p < THRESHOLD_CHURN_PROB:
        return [
            (False, 'Kirim ucapan apresiasi — akui loyalitas dan kontribusi yang sudah diberikan'),
            (False, 'Tawarkan program donasi rutin bulanan (auto-debit) agar lebih mudah'),
            (False, 'Pantau rutin — jika recency mulai di atas 90 hari segera hubungi'),
        ]

    if model is None or scaler is None:
        return get_aksi(row)

    try:
        from utils.model import get_shap_reasons
        top_fitur, _ = get_shap_reasons(model, scaler, fitur, row, top_n=1)
        fitur_dominan = top_fitur[0][0]
    except Exception:
        return get_aksi(row)

    if fitur_dominan == "recency":
        return [
            (True, f'Sudah {int(row["recency"])} hari sejak donasi terakhir — ini faktor risiko utama menurut SHAP. Hubungi via WhatsApp segera'),
            (True, 'Tanyakan kabar dan kendala secara personal — apakah ada hal yang menghambat donasi?'),
            (True, 'Masukkan ke campaign musiman terdekat sebagai pintu kembali'),
            (False, f'Kirim laporan dampak donasi program {prog} secara personal (foto + cerita)'),
        ]
    elif fitur_dominan == "frequency":
        return [
            (True, f'Frekuensi donasi rendah ({int(row["frequency"])}× total) adalah faktor risiko utama menurut SHAP — tawarkan program donasi rutin bulanan'),
            (True, 'Ajak bergabung ke program auto-debit agar donasi lebih konsisten'),
            (False, f'Kirim update dampak program {prog} untuk menjaga keterlibatan'),
            (False, 'Sampaikan apresiasi atas kontribusi yang sudah diberikan'),
        ]
    elif fitur_dominan == "monetary_log":
        return [
            (True, f'Nominal donasi (Rp {row["monetary"]:,.0f}) adalah faktor risiko utama menurut SHAP — cek kemungkinan perubahan kapasitas memberi donatur'),
            (True, 'Tawarkan opsi nominal donasi lebih fleksibel/kecil agar tetap mudah berdonasi'),
            (False, 'Sampaikan apresiasi atas kontribusi yang sudah diberikan selama ini'),
            (False, 'Jika tidak merespons 14 hari → coba hubungi via telepon atau kanal lain'),
        ]
    else:
        return get_aksi(row)

BULAN = {
    "Januari":"January","Februari":"February","Maret":"March",
    "April":"April","Mei":"May","Juni":"June","Juli":"July",
    "Agustus":"August","September":"September",
    "Oktober":"October","November":"November","Desember":"December",
}
def parse_tgl(t):
    t = str(t).strip()
    for a,b in BULAN.items(): t = t.replace(a,b)
    try: return pd.to_datetime(t, dayfirst=True)
    except:
        try: return pd.to_datetime("1 "+t, dayfirst=True)
        except: return pd.NaT

def kpi_card(col, cls, ikon, lbl, val, sub):
    with col:
        st.markdown(f"""<div class="kpi {cls}">
            <div class="kpi-icon-watermark">{ikon}</div>
            <div class="kpi-lbl">{ikon} {lbl}</div>
            <div class="kpi-val">{val}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

def format_rupiah_ringkas(nilai):
    """Format angka Rupiah ke satuan Indonesia (Ribu/Juta/Miliar) — pengganti label 'M' (Million) berbahasa Inggris."""
    if nilai >= 1_000_000_000:
        return f"Rp {nilai/1_000_000_000:.2f} Miliar"
    if nilai >= 1_000_000:
        return f"Rp {nilai/1_000_000:.1f} Juta"
    if nilai >= 1_000:
        return f"Rp {nilai/1_000:.0f} Ribu"
    return f"Rp {nilai:,.0f}"
