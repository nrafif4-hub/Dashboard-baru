"""
Audit log — mencatat siapa mengubah data/model dan kapan.
Log disimpan ke file CSV agar mudah dibaca dan difilter.
"""

import os
import csv
from datetime import datetime

from utils.config import AUDIT_LOG_FILE


def log_action(username: str, action: str, detail: str = ""):
    """Catat aksi ke audit_log.csv.

    Parameters:
        username: Username yang melakukan aksi
        action: Jenis aksi (mis. "UPLOAD_CSV", "GABUNG_DATABASE", "RETRAIN", "UBAH_CONFIG")
        detail: Detail tambahan (mis. nama file, jumlah record, dll.)
    """
    file_exists = os.path.exists(AUDIT_LOG_FILE)

    with open(AUDIT_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "username", "action", "detail"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            username,
            action,
            detail,
        ])


def get_audit_log(limit: int = 100):
    """Baca audit log, kembalikan list of dict (terbaru di atas).

    Parameters:
        limit: Jumlah maksimum baris yang dikembalikan
    """
    if not os.path.exists(AUDIT_LOG_FILE):
        return []

    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Terbaru di atas
    rows.reverse()
    return rows[:limit]
