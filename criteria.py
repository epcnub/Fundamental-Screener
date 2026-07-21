"""
criteria.py  –  Fundamental scoring engine
Each criterion returns (points_earned, max_points, red_flags: list[str])
Final score is summed and normalised to 100.
"""
 
from typing import Optional
from dataclasses import dataclass, field
 
 
@dataclass
class CriterionResult:
    name:       str
    pillar:     str
    points:     float
    max_points: float
    passed:     bool
    red_flag:   Optional[str] = None  # Non-None means this is a hard disqualifier flag
    note:       str = ""
 
 
def _safe(val, default=None):
    """Return val if it is a real number, else default."""
    if val is None:
        return default
    try:
        f = float(val)
        return default if (f != f) else f   # NaN check
    except (TypeError, ValueError):
        return default
 
 
# ─────────────────────────────────────────────────────────────
# PILLAR 1 – PROFITABILITY  (max 25 pts)
# ─────────────────────────────────────────────────────────────
 
def c_roe(data: dict) -> CriterionResult:
    roe = _safe(data.get("roe"))
    if roe is None:
        return CriterionResult("ROE", "Profitability", 0, 7, False, note="Data unavailable")
    if roe >= 20:
        pts, note = 7, f"ROE {roe:.1f}% ≥ 25% — excellent"
    elif roe >= 15:
        pts, note = 5, f"ROE {roe:.1f}% ≥ 15% — good"
    elif roe >= 10:
        pts, note = 2, f"ROE {roe:.1f}% 10–15% — average"
    else:
        pts, note = 0, f"ROE {roe:.1f}% < 10% — weak"
    flag = "ROE below 10% — poor capital efficiency" if roe < 10 else None
    return CriterionResult("ROE", "Profitability", pts, 7, pts > 0, flag, note)
 
 
def c_roce(data: dict) -> CriterionResult:
    roce = _safe(data.get("roce"))
    if roce is None:
        return CriterionResult("ROCE", "Profitability", 0, 8, False, note="Data unavailable")
    if roce >= 20:
        pts, note = 8, f"ROCE {roce:.1f}% ≥ 20% — excellent"
    elif roce >= 15:
        pts, note = 5, f"ROCE {roce:.1f}% ≥ 15% — good"
    elif roce >= 10:
        pts, note = 2, f"ROCE {roce:.1f}% 10–15% — average"
    else:
        pts, note = 0, f"ROCE {roce:.1f}% < 10% — poor"
    flag = "ROCE below 10% — capital being destroyed" if roce < 10 else None
    return CriterionResult("ROCE", "Profitability", pts, 8, pts > 0, flag, note)
 
 
def c_net_margin(data: dict) -> CriterionResult:
    nm = _safe(data.get("net_margin_pct"))
    if nm is None:
        return CriterionResult("Net Margin", "Profitability", 0, 5, False, note="Data unavailable")
    if nm >= 15:
        pts, note = 5, f"Net margin {nm:.1f}% ≥ 15% — strong"
    elif nm >= 8:
        pts, note = 3, f"Net margin {nm:.1f}% 8–15% — decent"
    elif nm >= 3:
        pts, note = 1, f"Net margin {nm:.1f}% 3–8% — thin"
    else:
        pts, note = 0, f"Net margin {nm:.1f}% < 3% — very thin"
    flag = "Net margin below 0% — loss-making" if nm < 0 else None
    return CriterionResult("Net Margin", "Profitability", pts, 5, pts > 0, flag, note)
 
 
def c_opm(data: dict) -> CriterionResult:
    opm = _safe(data.get("opm_pct"))
    if opm is None:
        return CriterionResult("Operating Margin", "Profitability", 0, 5, False, note="Data unavailable")
    if opm >= 20:
        pts, note = 5, f"OPM {opm:.1f}% ≥ 20% — excellent"
    elif opm >= 12:
        pts, note = 3, f"OPM {opm:.1f}% 12–20% — good"
    elif opm >= 5:
        pts, note = 1, f"OPM {opm:.1f}% 5–12% — average"
    else:
        pts, note = 0, f"OPM {opm:.1f}% < 5% — very low"
    flag = "Operating margin below 0% — operating losses" if opm < 0 else None
    return CriterionResult("Operating Margin", "Profitability", pts, 5, pts > 0, flag, note)
 
 
# ─────────────────────────────────────────────────────────────
# PILLAR 2 – GROWTH  (max 20 pts)
# ─────────────────────────────────────────────────────────────
 
def c_revenue_growth(data: dict) -> CriterionResult:
    cagr = _safe(data.get("revenue_cagr_3y"))
    if cagr is None:
        return CriterionResult("Revenue CAGR (3Y)", "Growth", 0, 10, False, note="Data unavailable")
    if cagr >= 20:
        pts, note = 10, f"Revenue CAGR {cagr:.1f}% ≥ 20% — high growth"
    elif cagr >= 12:
        pts, note = 7,  f"Revenue CAGR {cagr:.1f}% 12–20% — healthy"
    elif cagr >= 5:
        pts, note = 4,  f"Revenue CAGR {cagr:.1f}% 5–12% — moderate"
    else:
        pts, note = 0,  f"Revenue CAGR {cagr:.1f}% < 5% — stagnant"
    flag = "Revenue CAGR negative — business shrinking" if cagr < 0 else None
    return CriterionResult("Revenue CAGR (3Y)", "Growth", pts, 10, pts > 0, flag, note)
 
 
def c_profit_growth(data: dict) -> CriterionResult:
    cagr = _safe(data.get("profit_cagr_3y"))
    if cagr is None:
        return CriterionResult("Profit CAGR (3Y)", "Growth", 0, 10, False, note="Data unavailable")
    if cagr >= 20:
        pts, note = 10, f"Profit CAGR {cagr:.1f}% ≥ 20% — compounding fast"
    elif cagr >= 12:
        pts, note = 7,  f"Profit CAGR {cagr:.1f}% 12–20% — solid"
    elif cagr >= 5:
        pts, note = 4,  f"Profit CAGR {cagr:.1f}% 5–12% — moderate"
    else:
        pts, note = 0,  f"Profit CAGR {cagr:.1f}% < 5% — weak"
    flag = "Profit CAGR negative — earnings declining" if cagr < 0 else None
    return CriterionResult("Profit CAGR (3Y)", "Growth", pts, 10, pts > 0, flag, note)
 
 
# ─────────────────────────────────────────────────────────────
# PILLAR 3 – VALUATION  (max 20 pts)
# ─────────────────────────────────────────────────────────────
 
def c_pe_ratio(data: dict) -> CriterionResult:
    pe = _safe(data.get("pe_ratio"))
    if pe is None:
        return CriterionResult("P/E Ratio", "Valuation", 0, 10, False, note="Data unavailable")
    if pe <= 0:
        return CriterionResult("P/E Ratio", "Valuation", 0, 10, False,
                               red_flag="Negative P/E — company is loss-making",
                               note=f"P/E {pe:.1f} — loss-making")
    if pe <= 15:
        pts, note = 10, f"P/E {pe:.1f} ≤ 15 — cheap"
    elif pe <= 25:
        pts, note = 7,  f"P/E {pe:.1f} 15–25 — fair"
    elif pe <= 40:
        pts, note = 4,  f"P/E {pe:.1f} 25–40 — slightly expensive"
    else:
        pts, note = 1,  f"P/E {pe:.1f} > 40 — expensive"
    flag = f"P/E > 60 ({pe:.0f}) — highly overvalued" if pe > 60 else None
    return CriterionResult("P/E Ratio", "Valuation", pts, 10, True, flag, note)
 
 
def c_pb_ratio(data: dict) -> CriterionResult:
    pb = _safe(data.get("pb_ratio"))
    if pb is None:
        return CriterionResult("P/B Ratio", "Valuation", 0, 10, False, note="Data unavailable")
    if pb <= 1:
        pts, note = 10, f"P/B {pb:.1f} ≤ 1 — trading below book"
    elif pb <= 3:
        pts, note = 7,  f"P/B {pb:.1f} 1–3 — reasonable"
    elif pb <= 6:
        pts, note = 4,  f"P/B {pb:.1f} 3–6 — premium"
    else:
        pts, note = 1,  f"P/B {pb:.1f} > 6 — high premium"
    flag = f"P/B > 10 ({pb:.1f}) — extremely expensive vs book" if pb > 10 else None
    return CriterionResult("P/B Ratio", "Valuation", pts, 10, True, flag, note)
 
 
# ─────────────────────────────────────────────────────────────
# PILLAR 4 – DEBT HEALTH  (max 20 pts)
# ─────────────────────────────────────────────────────────────
 
def c_de_ratio(data: dict) -> CriterionResult:
    de = _safe(data.get("de_ratio"))
    if de is None:
        return CriterionResult("D/E Ratio", "Debt Health", 0, 10, False, note="Data unavailable")
    if de <= 0.1:
        pts, note = 10, f"D/E {de:.2f} — virtually debt-free"
    elif de <= 0.5:
        pts, note = 8,  f"D/E {de:.2f} — low debt"
    elif de <= 1.0:
        pts, note = 5,  f"D/E {de:.2f} — moderate debt"
    elif de <= 2.0:
        pts, note = 2,  f"D/E {de:.2f} — high debt"
    else:
        pts, note = 0,  f"D/E {de:.2f} — very high debt"
    flag = f"D/E ratio {de:.1f} > 2 — overleveraged" if de > 2 else None
    return CriterionResult("D/E Ratio", "Debt Health", pts, 10, pts > 0, flag, note)
 
 
def c_interest_coverage(data: dict) -> CriterionResult:
    ic = _safe(data.get("interest_coverage"))
    if ic is None:
        # Could be debt-free — treat as passing if D/E is also 0
        de = _safe(data.get("de_ratio"), 999)
        if de == 0 or de is None:
            return CriterionResult("Interest Coverage", "Debt Health", 10, 10, True,
                                   note="Likely debt-free — N/A")
        return CriterionResult("Interest Coverage", "Debt Health", 0, 10, False, note="Data unavailable")
    if ic >= 5:
        pts, note = 10, f"Interest coverage {ic:.1f}x ≥ 5x — very safe"
    elif ic >= 3:
        pts, note = 6,  f"Interest coverage {ic:.1f}x 3–5x — adequate"
    elif ic >= 1.5:
        pts, note = 3,  f"Interest coverage {ic:.1f}x 1.5–3x — thin"
    else:
        pts, note = 0,  f"Interest coverage {ic:.1f}x < 1.5x — danger zone"
    flag = f"Interest coverage {ic:.1f}x < 1.5 — debt repayment at risk" if ic < 1.5 else None
    return CriterionResult("Interest Coverage", "Debt Health", pts, 10, pts > 0, flag, note)
 
 
# ─────────────────────────────────────────────────────────────
# PILLAR 5 – QUALITY  (max 15 pts)
# ─────────────────────────────────────────────────────────────
 
def c_cfo_quality(data: dict) -> CriterionResult:
    cfo_pat = _safe(data.get("cfo_pat_ratio"))
    cfo     = _safe(data.get("cfo_cr"))
    if cfo_pat is None:
        return CriterionResult("CFO Quality (CFO/PAT)", "Quality", 0, 7, False, note="Data unavailable")
    if cfo_pat >= 1.0:
        pts, note = 7, f"CFO/PAT {cfo_pat:.2f} ≥ 1 — earnings backed by cash"
    elif cfo_pat >= 0.6:
        pts, note = 4, f"CFO/PAT {cfo_pat:.2f} 0.6–1 — reasonable"
    elif cfo_pat >= 0:
        pts, note = 1, f"CFO/PAT {cfo_pat:.2f} 0–0.6 — low quality earnings"
    else:
        pts, note = 0, f"CFO/PAT {cfo_pat:.2f} negative — profits not converting"
    flag = "Negative operating cash flow — earnings quality concern" if (cfo is not None and cfo < 0) else None
    return CriterionResult("CFO Quality (CFO/PAT)", "Quality", pts, 7, pts > 0, flag, note)
 
 
def c_promoter_holding(data: dict) -> CriterionResult:
    ph = _safe(data.get("promoter_holding_pct"))
    if ph is None:
        return CriterionResult("Promoter Holding", "Quality", 0, 5, False, note="Data unavailable")
    if ph >= 50:
        pts, note = 5, f"Promoter holding {ph:.1f}% ≥ 50% — strong conviction"
    elif ph >= 35:
        pts, note = 3, f"Promoter holding {ph:.1f}% 35–50% — decent"
    elif ph >= 20:
        pts, note = 1, f"Promoter holding {ph:.1f}% 20–35% — low"
    else:
        pts, note = 0, f"Promoter holding {ph:.1f}% < 20% — very low"
    flag = "Promoter holding < 20% — low skin in game" if ph < 20 else None
    return CriterionResult("Promoter Holding", "Quality", pts, 5, pts > 0, flag, note)
 
 
def c_pledging(data: dict) -> CriterionResult:
    pledged = _safe(data.get("pledged_pct"), 0.0)
    if pledged <= 0:
        return CriterionResult("Pledging", "Quality", 3, 3, True, note="No pledging — clean")
    elif pledged <= 10:
        return CriterionResult("Pledging", "Quality", 2, 3, True, note=f"Pledging {pledged:.1f}% — minor")
    elif pledged <= 30:
        return CriterionResult("Pledging", "Quality", 1, 3, True,
                               red_flag=f"Promoter pledging {pledged:.1f}% > 10% — watch carefully",
                               note=f"Pledging {pledged:.1f}% — moderate risk")
    else:
        return CriterionResult("Pledging", "Quality", 0, 3, False,
                               red_flag=f"Promoter pledging {pledged:.1f}% > 30% — HIGH RISK",
                               note=f"Pledging {pledged:.1f}% — high risk")
 
 
# ─────────────────────────────────────────────────────────────
# TREND CHECKS  (bonus / penalty — max ±5 pts)
# ─────────────────────────────────────────────────────────────
 
def c_profit_trend(data: dict) -> CriterionResult:
    """Reward consistent profit growth, penalise erratic/declining trend."""
    vals = [v for v in data.get("_profit_vals", []) if v is not None]
    if len(vals) < 3:
        return CriterionResult("Profit Trend (3Y)", "Quality", 0, 5, False, note="Insufficient data")
 
    recent = vals[-3:]
    increasing = all(recent[i] < recent[i+1] for i in range(len(recent)-1))
    any_negative = any(v < 0 for v in recent)
 
    if increasing and not any_negative:
        pts, note = 5, "Profit growing consistently last 3 years"
        flag = None
    elif any_negative:
        pts, note = 0, "Losses reported in last 3 years"
        flag = "Loss-making year in past 3 years — earnings instability"
    else:
        pts, note = 2, "Profit growth inconsistent"
        flag = None
    return CriterionResult("Profit Trend (3Y)", "Quality", pts, 5, pts > 0, flag, note)
 
 
# ─────────────────────────────────────────────────────────────
# MASTER SCORER
# ─────────────────────────────────────────────────────────────
 
ALL_CRITERIA = [
    c_roe, c_roce, c_net_margin, c_opm,            # Profitability  25 pts
    c_revenue_growth, c_profit_growth,             # Growth         20 pts
    c_pe_ratio, c_pb_ratio,                        # Valuation      20 pts
    c_de_ratio, c_interest_coverage,               # Debt Health    20 pts
    c_cfo_quality, c_promoter_holding, c_pledging, # Quality        15 pts
    c_profit_trend,                                # Trend           5 pts
]
# Total max = 100 pts
 
 
def score_stock(data: dict) -> dict:
    """
    Run all criteria on a stock's fundamental data dict.
    Returns a result dict with score, grade, red_flags, and breakdown.
    """
    if data.get("fetch_error"):
        return {
            "symbol":     data["symbol"],
            "score":      None,
            "grade":      "N/A",
            "red_flags":  ["Could not fetch data from Screener.in"],
            "breakdown":  [],
            "fetch_error": True,
        }
 
    results   = [fn(data) for fn in ALL_CRITERIA]
    total_pts = sum(r.points     for r in results)
    max_pts   = sum(r.max_points for r in results)
    score     = round((total_pts / max_pts) * 100, 1) if max_pts else 0
 
    red_flags = [r.red_flag for r in results if r.red_flag]
 
    if score >= 75:
        grade = "A"
    elif score >= 60:
        grade = "B"
    elif score >= 45:
        grade = "C"
    elif score >= 30:
        grade = "D"
    else:
        grade = "F"
 
    return {
        "symbol":     data["symbol"],
        "score":      score,
        "grade":      grade,
        "red_flags":  red_flags,
        "breakdown":  results,
        "fetch_error": False,
    }