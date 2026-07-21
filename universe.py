"""
universe.py  –  Stock universe loader
Fetches all ~2000 NSE-listed EQ stocks live from NSE's official free CSV API.
Falls back to Nifty 50 hardcoded list if the fetch fails.
"""

import csv
import io
import requests

NSE_CSV_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.nseindia.com/",
}

# Hardcoded Nifty 50 fallback
NIFTY_50_FALLBACK = [
    {"name": "Adani Enterprises",    "screener": "ADANIENT"},
    {"name": "Adani Ports",          "screener": "ADANIPORTS"},
    {"name": "Apollo Hospitals",     "screener": "APOLLOHOSP"},
    {"name": "Asian Paints",         "screener": "ASIANPAINT"},
    {"name": "Axis Bank",            "screener": "AXISBANK"},
    {"name": "Bajaj Auto",           "screener": "BAJAJ-AUTO"},
    {"name": "Bajaj Finance",        "screener": "BAJFINANCE"},
    {"name": "Bajaj Finserv",        "screener": "BAJAJFINSV"},
    {"name": "BPCL",                 "screener": "BPCL"},
    {"name": "Bharti Airtel",        "screener": "BHARTIARTL"},
    {"name": "Britannia",            "screener": "BRITANNIA"},
    {"name": "Cipla",                "screener": "CIPLA"},
    {"name": "Coal India",           "screener": "COALINDIA"},
    {"name": "Divi's Labs",          "screener": "DIVISLAB"},
    {"name": "Dr Reddy's",           "screener": "DRREDDY"},
    {"name": "Eicher Motors",        "screener": "EICHERMOT"},
    {"name": "Grasim Industries",    "screener": "GRASIM"},
    {"name": "HCL Technologies",     "screener": "HCLTECH"},
    {"name": "HDFC Bank",            "screener": "HDFCBANK"},
    {"name": "HDFC Life Insurance",  "screener": "HDFCLIFE"},
    {"name": "Hero MotoCorp",        "screener": "HEROMOTOCO"},
    {"name": "Hindalco",             "screener": "HINDALCO"},
    {"name": "Hindustan Unilever",   "screener": "HINDUNILVR"},
    {"name": "ICICI Bank",           "screener": "ICICIBANK"},
    {"name": "ITC",                  "screener": "ITC"},
    {"name": "IndusInd Bank",        "screener": "INDUSINDBK"},
    {"name": "Infosys",              "screener": "INFY"},
    {"name": "JSW Steel",            "screener": "JSWSTEEL"},
    {"name": "Kotak Mahindra Bank",  "screener": "KOTAKBANK"},
    {"name": "LTIMindtree",          "screener": "LTIM"},
    {"name": "Larsen & Toubro",      "screener": "LT"},
    {"name": "M&M",                  "screener": "M&M"},
    {"name": "Maruti Suzuki",        "screener": "MARUTI"},
    {"name": "NTPC",                 "screener": "NTPC"},
    {"name": "Nestle India",         "screener": "NESTLEIND"},
    {"name": "ONGC",                 "screener": "ONGC"},
    {"name": "Power Grid",           "screener": "POWERGRID"},
    {"name": "Reliance Industries",  "screener": "RELIANCE"},
    {"name": "SBI Life Insurance",   "screener": "SBILIFE"},
    {"name": "SBI",                  "screener": "SBIN"},
    {"name": "Shriram Finance",      "screener": "SHRIRAMFIN"},
    {"name": "Sun Pharma",           "screener": "SUNPHARMA"},
    {"name": "TCS",                  "screener": "TCS"},
    {"name": "Tata Consumer",        "screener": "TATACONSUM"},
    {"name": "Tata Motors",          "screener": "TATAMOTORS"},
    {"name": "Tata Steel",           "screener": "TATASTEEL"},
    {"name": "Tech Mahindra",        "screener": "TECHM"},
    {"name": "Titan Company",        "screener": "TITAN"},
    {"name": "UltraTech Cement",     "screener": "ULTRACEMCO"},
    {"name": "Wipro",                "screener": "WIPRO"},
]


def fetch_all_nse_stocks() -> list[dict]:
    """
    Fetch all EQ-series NSE stocks from NSE's official CSV.
    Returns list of {"name": ..., "screener": ...} dicts.
    Falls back to Nifty 50 if fetch fails.
    """
    try:
        print("Fetching stock universe from NSE...")
        r = requests.get(NSE_CSV_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()

        reader = csv.DictReader(io.StringIO(r.text))
        stocks = []
        for row in reader:
            # Column names may have leading spaces — strip all keys and values
            row = {k.strip(): v.strip() for k, v in row.items()}
            series = row.get("SERIES", "")
            symbol = row.get("SYMBOL", "")
            name   = row.get("NAME OF COMPANY", "")
            if series == "EQ" and symbol:
                stocks.append({"name": name, "screener": symbol})

        print(f"✔ Loaded {len(stocks)} NSE EQ stocks.")
        return stocks

    except Exception as e:
        print(f"[!] Could not fetch NSE stock list ({e}). Falling back to Nifty 50.")
        return NIFTY_50_FALLBACK


# Cache so we don't fetch multiple times per run
_universe_cache: list[dict] | None = None


def get_universe() -> list[dict]:
    global _universe_cache
    if _universe_cache is None:
        _universe_cache = fetch_all_nse_stocks()
    return _universe_cache


def get_screener_symbols() -> list[str]:
    return [s["screener"] for s in get_universe()]


def get_name_map() -> dict[str, str]:
    return {s["screener"]: s["name"] for s in get_universe()}