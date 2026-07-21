"""
app.py  –  Flask web UI for the Nifty stock screener
Run:  python app.py
Then open:  http://stockscreener.in
"""

import sys
import os
import json
from pathlib import Path
from flask import Flask, render_template, jsonify, request

sys.path.insert(0, str(Path(__file__).parent))

from screener import fetch_fundamentals
from criteria import score_stock
from universe import get_screener_symbols, get_name_map
from report   import export_csv

app = Flask(__name__)
@app.route("/")
def home():
    return "Hello"

# In-memory cache so re-visiting the page doesn't re-fetch
_cache: dict = {}   # { "results": [...], "data_map": {...} }


def _run_screener(symbols: list[str]) -> tuple[list, dict]:
    name_map    = get_name_map()
    all_data    = {}
    all_results = []

    for sym in symbols:
        print(f"  Fetching {sym}...")
        data   = fetch_fundamentals(sym, delay=1.2)
        result = score_stock(data)
        all_data[sym] = data
        all_results.append(result)

    return all_results, all_data


def _result_to_dict(result: dict, data: dict, name_map: dict, rank: int) -> dict:
    def fmt(v):
        if v is None:
            return "—"
        if isinstance(v, float):
            return round(v, 2)
        return v

    return {
        "rank":                rank,
        "symbol":              result["symbol"],
        "company":             name_map.get(result["symbol"], ""),
        "score":               fmt(result.get("score")),
        "grade":               result.get("grade", "N/A"),
        "red_flags":           result.get("red_flags", []),
        "fetch_error":         result.get("fetch_error", False),

        # Metrics
        "pe_ratio":            fmt(data.get("pe_ratio")),
        "pb_ratio":            fmt(data.get("pb_ratio")),
        "roe":                 fmt(data.get("roe")),
        "roce":                fmt(data.get("roce")),
        "net_margin_pct":      fmt(data.get("net_margin_pct")),
        "opm_pct":             fmt(data.get("opm_pct")),
        "revenue_cagr_3y":     fmt(data.get("revenue_cagr_3y")),
        "profit_cagr_3y":      fmt(data.get("profit_cagr_3y")),
        "de_ratio":            fmt(data.get("de_ratio")),
        "interest_coverage":   fmt(data.get("interest_coverage")),
        "cfo_pat_ratio":       fmt(data.get("cfo_pat_ratio")),
        "promoter_holding_pct":fmt(data.get("promoter_holding_pct")),
        "pledged_pct":         fmt(data.get("pledged_pct")),
        "market_cap_cr":       fmt(data.get("market_cap_cr")),

        # Breakdown by pillar for detail modal
        "breakdown": [
            {
                "pillar":      c.pillar,
                "name":        c.name,
                "points":      c.points,
                "max_points":  c.max_points,
                "passed":      c.passed,
                "note":        c.note,
                "red_flag":    c.red_flag,
            }
            for c in result.get("breakdown", [])
        ],
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
def api_run():
    """Start a screener run. Body: { "symbols": ["INFY", ...] } or empty for full universe."""
    global _cache
    body    = request.get_json(silent=True) or {}
    symbols = body.get("symbols") or get_screener_symbols()

    print(f"\n[Screener] Running on {len(symbols)} stocks...")
    results, data_map = _run_screener(symbols)

    name_map = get_name_map()
    ranked   = sorted(
        [r for r in results if not r.get("fetch_error")],
        key=lambda x: -(x.get("score") or 0)
    )
    errors = [r for r in results if r.get("fetch_error")]

    rows = []
    for rank, result in enumerate(ranked + errors, 1):
        d = data_map.get(result["symbol"], {})
        rows.append(_result_to_dict(result, d, name_map, rank))

    _cache = {"rows": rows, "data_map": data_map, "results": results}

    # Stats
    scored = [r for r in results if r.get("score") is not None]
    stats  = {}
    if scored:
        scores = [r["score"] for r in scored]
        stats = {
            "total":   len(results),
            "avg":     round(sum(scores) / len(scores), 1),
            "best":    max(scored, key=lambda x: x["score"])["symbol"],
            "worst":   min(scored, key=lambda x: x["score"])["symbol"],
            "grade_counts": {
                g: sum(1 for r in scored if r.get("grade") == g)
                for g in ["A", "B", "C", "D", "F"]
            },
            "flagged": sum(1 for r in results if r.get("red_flags")),
        }

    return jsonify({"rows": rows, "stats": stats})


@app.route("/api/report")
def api_report():
    """Return cached results (or empty if not run yet)."""
    if not _cache:
        return jsonify({"rows": [], "stats": {}})
    return jsonify({"rows": _cache.get("rows", []), "stats": {}})


@app.route("/api/export")
def api_export():
    """Export cached results to CSV and return file path."""
    if not _cache:
        return jsonify({"error": "No data yet. Run the screener first."}), 400
    name_map = get_name_map()
    path = export_csv(
        _cache["results"], _cache["data_map"],
        name_map, output_dir="output"
    )
    return jsonify({"path": path, "filename": os.path.basename(path)})


if __name__ == "__main__":
    print("\n  Stock Screener UI  →  http://localhost:5000\n")
    app.run(debug=True, port=5000)