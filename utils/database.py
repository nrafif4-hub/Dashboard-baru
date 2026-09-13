"""
Database Abstraction Layer — One Ummah Foundation
Menyediakan interface untuk migrasi dari CSV ke database relasional.

Saat ini: masih menggunakan CSV sebagai backend (backward compatible).
Masa depan: tinggal ganti implementasi ke PostgreSQL/MySQL tanpa ubah kode halaman.

Penggunaan:
    from utils.database import get_db
    db = get_db()
    rfm = db.get_rfm_data()
    db.save_rfm_data(rfm_df)
"""

import os
import pandas as pd
from utils.config import RFM_FILE, TRANSAKSI_FILE_CANDIDATES


class CSVDatabase:
    """Backend CSV — implementasi default, backward compatible."""

    def get_rfm_data(self):
        """Baca data RFM dari CSV."""
        if not os.path.exists(RFM_FILE):
            return None
        df = pd.read_csv(RFM_FILE)
        df["last_date"] = pd.to_datetime(df["last_date"], format="mixed", dayfirst=False)
        return df

    def save_rfm_data(self, df: pd.DataFrame):
        """Simpan data RFM ke CSV."""
        df.to_csv(RFM_FILE, index=False)

    def get_transaksi_data(self):
        """Baca data transaksi dari CSV."""
        from utils.data_loader import load_riwayat
        return load_riwayat()

    def get_rfm_paginated(self, page: int = 1, page_size: int = 50,
                          sort_by: str = "prob_churn", ascending: bool = False,
                          filter_status: str = None, search_id: str = None):
        """Baca data RFM dengan pagination dan filter.

        Returns:
            (data: DataFrame, total_count: int, total_pages: int)
        """
        df = self.get_rfm_data()
        if df is None:
            return None, 0, 0

        # Filter
        if filter_status == "churn":
            df = df[df["churn"] == 1]
        elif filter_status == "tidak_churn":
            df = df[df["churn"] == 0]

        if search_id:
            df = df[df["ID Donatur"].str.contains(search_id, case=False, na=False)]

        total_count = len(df)
        total_pages = max(1, (total_count + page_size - 1) // page_size)

        # Sort
        df = df.sort_values(sort_by, ascending=ascending)

        # Paginate
        start = (page - 1) * page_size
        end = min(start + page_size, total_count)
        data = df.iloc[start:end]

        return data, total_count, total_pages


class PostgreSQLDatabase:
    """Backend PostgreSQL — untuk migrasi skala besar.

    TODO: Implementasi lengkap setelah setup PostgreSQL:
        - Connection pooling via SQLAlchemy
        - Migration scripts (Alembic)
        - Query optimization dengan indexing
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # from sqlalchemy import create_engine
        # self.engine = create_engine(connection_string, pool_size=5)

    def get_rfm_data(self):
        raise NotImplementedError("PostgreSQL backend belum diimplementasi")

    def save_rfm_data(self, df: pd.DataFrame):
        raise NotImplementedError("PostgreSQL backend belum diimplementasi")


# ── Factory ──────────────────────────────────────────────────
_DB_BACKEND = os.environ.get("OUF_DB_BACKEND", "csv")
_DB_CONNECTION = os.environ.get("OUF_DB_CONNECTION", "")


def get_db():
    """Kembalikan database backend yang aktif.

    Set environment variable OUF_DB_BACKEND="postgresql" dan
    OUF_DB_CONNECTION="postgresql://..." untuk beralih ke PostgreSQL.
    """
    if _DB_BACKEND == "postgresql" and _DB_CONNECTION:
        return PostgreSQLDatabase(_DB_CONNECTION)
    return CSVDatabase()
