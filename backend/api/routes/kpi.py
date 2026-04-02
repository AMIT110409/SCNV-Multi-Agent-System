"""
KPI API routes — serves Allocation Efficiency, Productive Trends,
Sub-optimal Customer metrics, and available countries list.
All data is sourced from synthetic JSON files in data/synthetic/gap_extended/.
"""

from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
import os
import json
from collections import defaultdict
from datetime import datetime

router = APIRouter()

# ── Data Loading ────────────────────────────────────────────────────────────────
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/synthetic/gap_extended"))

def _load_json(filename: str) -> list:
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Cache data on module load
_stos = _load_json("incoming_stos_extended.json")
_customer_orders = _load_json("customer_orders.json")
_plants = _load_json("plant_country_master.json")


# ── GET /countries ──────────────────────────────────────────────────────────────
@router.get("/countries")
async def get_countries():
    """Return distinct country codes from plant master + customer orders."""
    country_set = set()
    for p in _plants:
        cc = p.get("LAND1")
        if cc:
            country_set.add(cc)
    for o in _customer_orders:
        cc = o.get("country_code")
        if cc:
            country_set.add(cc)
    for s in _stos:
        cc = s.get("COUNTRY_CODE")
        if cc:
            country_set.add(cc)

    return {"countries": sorted(country_set)}


# ── GET /allocation-efficiency ──────────────────────────────────────────────────
@router.get("/allocation-efficiency")
async def get_allocation_efficiency(country: Optional[str] = Query(None)):
    """
    Allocation Efficiency KPI for a given country (or all).
    Returns: efficiency_pct, unproductive_transfer_ratio, optimal_allocation_ratio
    """
    orders = _customer_orders
    stos = _stos

    if country:
        orders = [o for o in _customer_orders if o.get("country_code") == country]
        stos = [s for s in _stos if s.get("COUNTRY_CODE") == country]

    # Allocation efficiency from customer_orders
    total_orders = len(orders)
    optimal_count = sum(1 for o in orders if o.get("is_optimal_allocation"))
    avg_score = 0.0
    if total_orders > 0:
        avg_score = sum(o.get("allocation_efficiency_score", 0) for o in orders) / total_orders
        optimal_ratio = (optimal_count / total_orders) * 100
    else:
        optimal_ratio = 0.0

    # Unproductive transfer ratio from STOs
    total_vol = sum(s.get("VOLUME_HL", 0) for s in stos)
    productive_vol = sum(
        s.get("VOLUME_HL", 0) for s in stos
        if s.get("movement_type") == "641" and s.get("is_pre_goods_issue")
    )
    unproductive_vol = total_vol - productive_vol
    unproductive_ratio = (unproductive_vol / total_vol * 100) if total_vol > 0 else 0.0

    return {
        "country": country or "ALL",
        "total_orders": total_orders,
        "optimal_orders": optimal_count,
        "allocation_efficiency_pct": round(avg_score * 100, 1),
        "unproductive_transfer_ratio": round(unproductive_ratio, 1),
        "optimal_allocation_ratio": round(optimal_ratio, 1),
        "total_volume_hl": round(total_vol, 1),
        "productive_volume_hl": round(productive_vol, 1),
    }


# ── GET /productive-trend ──────────────────────────────────────────────────────
@router.get("/productive-trend")
async def get_productive_trend(country: Optional[str] = Query(None)):
    """
    Monthly productive vs unproductive volume for the bar chart.
    """
    stos = _stos
    if country:
        stos = [s for s in _stos if s.get("COUNTRY_CODE") == country]

    monthly: Dict[str, Dict[str, float]] = defaultdict(lambda: {"productive": 0.0, "unproductive": 0.0})

    for s in stos:
        vol = s.get("VOLUME_HL", 0)
        date_str = s.get("creation_date", "")
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            month_key = dt.strftime("%Y-%m")
        except Exception:
            month_key = "Unknown"

        is_productive = s.get("movement_type") == "641" and s.get("is_pre_goods_issue")
        if is_productive:
            monthly[month_key]["productive"] += vol
        else:
            monthly[month_key]["unproductive"] += vol

    trend = []
    for month in sorted(monthly.keys()):
        trend.append({
            "month": month,
            "productive": round(monthly[month]["productive"], 1),
            "unproductive": round(monthly[month]["unproductive"], 1),
        })

    return {"country": country or "ALL", "trend": trend}


# ── GET /suboptimal-customers ───────────────────────────────────────────────────
@router.get("/suboptimal-customers")
async def get_suboptimal_customers(country: Optional[str] = Query(None)):
    """
    Sub-optimal customer allocation percentage per country (or all).
    """
    orders = _customer_orders
    if country:
        orders = [o for o in _customer_orders if o.get("country_code") == country]

    total = len(orders)
    suboptimal = sum(1 for o in orders if not o.get("is_optimal_allocation"))
    pct = (suboptimal / total * 100) if total > 0 else 0.0

    # If no country filter, also return per-country breakdown
    breakdown = []
    if not country:
        by_country: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "suboptimal": 0})
        for o in _customer_orders:
            cc = o.get("country_code", "Unknown")
            by_country[cc]["total"] += 1
            if not o.get("is_optimal_allocation"):
                by_country[cc]["suboptimal"] += 1
        for cc in sorted(by_country.keys()):
            d = by_country[cc]
            breakdown.append({
                "country": cc,
                "total_orders": d["total"],
                "suboptimal_orders": d["suboptimal"],
                "suboptimal_pct": round(d["suboptimal"] / d["total"] * 100, 1) if d["total"] > 0 else 0.0
            })

    return {
        "country": country or "ALL",
        "total_orders": total,
        "suboptimal_orders": suboptimal,
        "suboptimal_pct": round(pct, 1),
        "breakdown": breakdown,
    }
