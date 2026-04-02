"""
migrate_sap_so.py — Migration script to:
1. Create SAP SO tables (VBAK, VBAP, LIKP, LIPS) in Supabase
2. Generate SAP-format data from customer_orders.json
3. Populate all 4 tables with synthetic data

Usage: cd backend && python migrate_sap_so.py
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.append(os.path.dirname(__file__))
from database import engine, Base
from models.sap_so_tables import VBAK, VBAP, LIKP, LIPS
from sqlalchemy.orm import sessionmaker

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic', 'gap_extended')

# Sales Org -> Country mapping (SAP standard)
VKORG_MAP = {
    "GB": "GB11", "BE": "BE01", "DE": "DE01", "NL": "NL01", "FR": "FR01",
    "ES": "ES01", "IT": "IT01", "PL": "PL01", "SE": "SE01", "US": "US01",
    "CN": "CN01", "IN": "IN01", "SG": "SG01", "BR": "BR01", "MX": "MX01",
    "JP": "JP01", "AU": "AU01", "HK": "HK01", "TR": "TR01", "ZA": "ZA01",
}


def generate_delivery_number(so_number: str, idx: int) -> str:
    """Generate a SAP-style delivery document number."""
    base = int(so_number.lstrip("0") or "0") + 80000000 + idx
    return f"{base:010d}"


def migrate():
    print("=" * 60)
    print("  SCNV Agent — SAP SO Tables Migration (VBAK/VBAP/LIKP/LIPS)")
    print("=" * 60)

    # Drop and recreate tables
    print("\n[Step 1] Creating SAP SO tables...")
    for table in [LIPS.__table__, LIKP.__table__, VBAP.__table__, VBAK.__table__]:
        try:
            table.drop(engine, checkfirst=True)
        except Exception:
            pass
    Base.metadata.create_all(bind=engine, tables=[
        VBAK.__table__, VBAP.__table__, LIKP.__table__, LIPS.__table__
    ])
    print("[OK] Tables created: sap_vbak, sap_vbap, sap_likp, sap_lips")

    # Load source data
    orders_path = os.path.join(DATA_DIR, "customer_orders.json")
    if not os.path.exists(orders_path):
        print("Error: customer_orders.json not found")
        sys.exit(1)

    with open(orders_path, "r", encoding="utf-8") as f:
        orders = json.load(f)
    print(f"\n[Step 2] Processing {len(orders)} customer orders -> SAP format...")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    vbak_count = 0
    vbap_count = 0
    likp_count = 0
    lips_count = 0

    for i, order in enumerate(orders):
        so_number = order.get("so_number", f"00{45678900 + i}")
        country_code = order.get("country_code", "GB")
        vkorg = VKORG_MAP.get(country_code, "XX01")

        # Parse dates
        try:
            order_date = datetime.strptime(order["order_date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            order_date = datetime.now().date()

        try:
            planned_gi = datetime.strptime(order["planned_gi_date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            planned_gi = order_date + timedelta(days=3)

        # 1. VBAK — Sales Order Header
        vbak = VBAK(
            VBELN=so_number,
            KUNNR=order.get("customer_number", f"CUST{i:03d}"),
            VKORG=vkorg,
            ERDAT=order_date,
            AUART="ZOR",  # Standard order type
            NETWR=round(order.get("quantity_hl", 100) * 12.5, 2),  # Approximate net value
            WAERK="EUR",
        )
        db.add(vbak)
        vbak_count += 1

        # 2. VBAP — Sales Order Items
        vbap = VBAP(
            VBELN=so_number,
            POSNR=order.get("so_item", "000010"),
            MATNR=order.get("material_number", f"MAT{i:06d}"),
            WERKS=order.get("assigned_plant", "GB01"),
            KWMENG=order.get("quantity_hl", 100.0),
            MEINS="HL",
            LGNUM="",
        )
        db.add(vbap)
        vbap_count += 1

        # 3. LIKP — Delivery Header (one delivery per SO for simplicity)
        delivery_number = generate_delivery_number(so_number, i)
        shipping_point = order.get("assigned_plant", "GB01")

        likp = LIKP(
            VBELN=delivery_number,
            VBELN_SO=so_number,
            WADAT=planned_gi,
            VSTEL=shipping_point,
            KUNNR=order.get("customer_number", f"CUST{i:03d}"),
            INCO1="EXW",
        )
        db.add(likp)
        likp_count += 1

        # 4. LIPS — Delivery Items
        shipped_qty = order.get("quantity_hl", 100.0) * random.uniform(0.9, 1.0)
        lips = LIPS(
            VBELN=delivery_number,
            POSNR=order.get("so_item", "000010"),
            MATNR=order.get("material_number", f"MAT{i:06d}"),
            LFIMG=round(shipped_qty, 2),
            MEINS="HL",
            WERKS=order.get("assigned_plant", "GB01"),
        )
        db.add(lips)
        lips_count += 1

        if (i + 1) % 50 == 0:
            db.flush()
            print(f"  Processed {i + 1}/{len(orders)} orders...")

    db.commit()
    db.close()

    print(f"\n[OK] Migration complete!")
    print(f"  VBAK (SO Headers):    {vbak_count} records")
    print(f"  VBAP (SO Items):      {vbap_count} records")
    print(f"  LIKP (Deliveries):    {likp_count} records")
    print(f"  LIPS (Delivery Items): {lips_count} records")
    print("=" * 60)


if __name__ == "__main__":
    migrate()
