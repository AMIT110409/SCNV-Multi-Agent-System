"""
sap_so_tables.py — SQLAlchemy ORM models for SAP Sales Order tables.

Mirrors the SAP S/4HANA tables:
  VBAK  — Sales Order Header
  VBAP  — Sales Order Items
  LIKP  — Delivery Header
  LIPS  — Delivery Items

These tables are wired alongside the existing STO tables (EKKO/EKPO/MSEG).
"""

from sqlalchemy import Column, Integer, String, Float, Date, Boolean
from database import Base


class VBAK(Base):
    """SAP Sales Order Header (VBAK)"""
    __tablename__ = "sap_vbak"

    id = Column(Integer, primary_key=True, index=True)
    VBELN = Column(String(20), unique=True, index=True, comment="Sales Order Number")
    KUNNR = Column(String(20), index=True, comment="Customer Number")
    VKORG = Column(String(10), comment="Sales Organization (maps to country)")
    ERDAT = Column(Date, comment="SO Creation Date")
    AUART = Column(String(10), comment="Sales Document Type")
    NETWR = Column(Float, comment="Net Value of Order")
    WAERK = Column(String(5), comment="Currency")


class VBAP(Base):
    """SAP Sales Order Items (VBAP)"""
    __tablename__ = "sap_vbap"

    id = Column(Integer, primary_key=True, index=True)
    VBELN = Column(String(20), index=True, comment="Sales Order Number (FK to VBAK)")
    POSNR = Column(String(10), comment="Line Item Number")
    MATNR = Column(String(40), index=True, comment="Material / SKU Number")
    WERKS = Column(String(10), comment="Delivering Plant Code")
    KWMENG = Column(Float, comment="Order Quantity (HL/cases)")
    MEINS = Column(String(5), comment="Unit of Measure")
    LGNUM = Column(String(10), comment="Warehouse Number (DC identification)")


class LIKP(Base):
    """SAP Delivery Header (LIKP)"""
    __tablename__ = "sap_likp"

    id = Column(Integer, primary_key=True, index=True)
    VBELN = Column(String(20), unique=True, index=True, comment="Delivery Document Number")
    VBELN_SO = Column(String(20), index=True, comment="Reference Sales Order Number")
    WADAT = Column(Date, comment="Planned Goods Issue Date")
    VSTEL = Column(String(10), comment="Shipping Point (maps to plant/DC)")
    KUNNR = Column(String(20), index=True, comment="Ship-to Customer")
    INCO1 = Column(String(5), comment="Incoterms")


class LIPS(Base):
    """SAP Delivery Items (LIPS)"""
    __tablename__ = "sap_lips"

    id = Column(Integer, primary_key=True, index=True)
    VBELN = Column(String(20), index=True, comment="Delivery Document Number (FK to LIKP)")
    POSNR = Column(String(10), comment="Delivery Item Number")
    MATNR = Column(String(40), index=True, comment="Material / SKU Number")
    LFIMG = Column(Float, comment="Actual Shipped Quantity")
    MEINS = Column(String(5), comment="Unit of Measure")
    WERKS = Column(String(10), comment="Supplying Plant")
