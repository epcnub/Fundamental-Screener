"""
screener.py  –  Screener.in fundamental data fetcher
Scrapes the consolidated view for each stock and returns a dict of raw metrics.
Falls back gracefully if a field is missing.
"""
 
import re
import time
import requests
from bs4 import BeautifulSoup
from typing import Optional
 
 
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.screener.in/",
}
 
_session: Optional[requests.Session] = None
 
 
def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(HEADERS)
        # Warm up session / grab cookies
        try:
            _session.get("https://www.screener.in/", timeout=10)
        except Exception:
            pass
    return _session
 
 
def _parse_number(text: str) -> Optional[float]:
    """Convert strings like '12,345.67', '45.3%', '2.1x' → float."""
    if not text:
        return None
    text = text.strip().replace(",", "").replace("%", "").replace("x", "").replace("₹", "")
    # Handle values like '1,234 Cr' — drop unit suffix
    text = re.split(r"\s+", text)[0]
    try:
        return float(text)
    except ValueError:
        return None
 
 
def _extract_top_ratios(soup: BeautifulSoup) -> dict:
    """Extract the top-ratios bar (Market Cap, P/E, Book Value, etc.)."""
    data = {}
    for li in soup.select("#top-ratios li"):
        name_el = li.select_one(".name")
        val_el  = li.select_one(".value, .number")
        if not name_el or not val_el:
            continue
        key = name_el.get_text(strip=True).lower().replace(" ", "_").replace("/", "_").replace(".", "")
        val = _parse_number(val_el.get_text(strip=True))
        data[key] = val
    return data
 
 
def _extract_table_row(soup: BeautifulSoup, section_id: str, row_label: str) -> list:
    """
    From a table section, extract a row by its label and return all year values.
    Returns list of floats (most recent last).
    """
    section = soup.select_one(f"#{section_id}")
    if not section:
        return []
    table = section.find("table")
    if not table:
        return []
    for tr in table.select("tbody tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        label = cells[0].get_text(strip=True).lower()
        if row_label.lower() in label:
            return [_parse_number(c.get_text(strip=True)) for c in cells[1:]]
    return []
 
 
def _growth_rate(values: list, years: int = 3) -> Optional[float]:
    """
    Calculate CAGR over `years` from a list of annual values.
    Uses last (years+1) values so we have start and end points.
    """
    vals = [v for v in values if v is not None and v > 0]
    if len(vals) < years + 1:
        return None
    start = vals[-(years + 1)]
    end   = vals[-1]
    if start <= 0:
        return None
    return ((end / start) ** (1 / years) - 1) * 100  # percentage
 
 
def fetch_fundamentals(ticker_screener: str, delay: float = 1.5) -> dict:
    """
    Fetch fundamental data for a stock from Screener.in.
 
    Args:
        ticker_screener: Screener.in symbol (e.g. 'INFY', 'RELIANCE')
        delay: polite delay in seconds between requests
 
    Returns:
        dict with all parsed metrics, None for unavailable fields.
    """
    time.sleep(delay)
    session = _get_session()
 
    url = f"https://www.screener.in/company/{ticker_screener}/consolidated/"
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [!] Failed to fetch {ticker_screener}: {e}")
        return {"symbol": ticker_screener, "fetch_error": True}
 
    soup = BeautifulSoup(resp.text, "html.parser")
 
    # ── Top ratios bar ────────────────────────────────────────────────────────
    ratios = _extract_top_ratios(soup)
 
    # ── Income statement rows ─────────────────────────────────────────────────
    revenue_vals  = _extract_table_row(soup, "profit-loss", "sales")
    profit_vals   = _extract_table_row(soup, "profit-loss", "net profit")
    opm_vals      = _extract_table_row(soup, "profit-loss", "opm")       # Operating margin %
    interest_vals = _extract_table_row(soup, "profit-loss", "interest")
    ebit_vals     = _extract_table_row(soup, "profit-loss", "operating profit")
 
    # ── Balance sheet rows ────────────────────────────────────────────────────
    equity_vals   = _extract_table_row(soup, "balance-sheet", "equity capital")
    reserves_vals = _extract_table_row(soup, "balance-sheet", "reserves")
    debt_vals     = _extract_table_row(soup, "balance-sheet", "borrowings")
 
    # ── Cash flow rows ────────────────────────────────────────────────────────
    cfo_vals      = _extract_table_row(soup, "cash-flow", "cash from operating")
 
    # ── Shareholding ─────────────────────────────────────────────────────────
    promoter_holding = None
    pledged_pct      = None
    sh_section = soup.select_one("#shareholding")
    if sh_section:
        # Promoter % – look for the most recent quarter value
        for tr in sh_section.select("table tbody tr"):
            cells = tr.find_all("td")
            if cells and "promoter" in cells[0].get_text(strip=True).lower():
                vals = [_parse_number(c.get_text(strip=True)) for c in cells[1:]]
                vals = [v for v in vals if v is not None]
                promoter_holding = vals[-1] if vals else None
        # Pledged % – separate small table on screener
        for tr in sh_section.select("table tbody tr"):
            cells = tr.find_all("td")
            if cells and "pledged" in cells[0].get_text(strip=True).lower():
                vals = [_parse_number(c.get_text(strip=True)) for c in cells[1:]]
                vals = [v for v in vals if v is not None]
                pledged_pct = vals[-1] if vals else None
 
    # ── Derived metrics ───────────────────────────────────────────────────────
    latest_revenue  = revenue_vals[-1]  if revenue_vals  else None
    latest_profit   = profit_vals[-1]   if profit_vals   else None
    latest_opm      = opm_vals[-1]      if opm_vals      else None
    latest_cfo      = cfo_vals[-1]      if cfo_vals      else None
    latest_ebit     = ebit_vals[-1]     if ebit_vals     else None
    latest_interest = interest_vals[-1] if interest_vals else None
    latest_debt     = debt_vals[-1]     if debt_vals     else None
 
    # Net worth = equity capital + reserves
    net_worth = None
    if equity_vals and reserves_vals:
        e = equity_vals[-1]
        r = reserves_vals[-1]
        if e is not None and r is not None:
            net_worth = e + r
 
    # Debt-to-Equity
    de_ratio = None
    if latest_debt is not None and net_worth and net_worth > 0:
        de_ratio = latest_debt / net_worth
 
    # Interest Coverage = EBIT / Interest
    interest_coverage = None
    if latest_ebit is not None and latest_interest and latest_interest > 0:
        interest_coverage = latest_ebit / latest_interest
 
    # CFO / PAT quality ratio
    cfo_pat_ratio = None
    if latest_cfo is not None and latest_profit and latest_profit != 0:
        cfo_pat_ratio = latest_cfo / latest_profit
 
    return {
        "symbol": ticker_screener,
        "fetch_error": False,
 
        # --- Valuation (from top ratios) ---
        "pe_ratio":        ratios.get("stock_p_e"),
        "pb_ratio":        ratios.get("price_to_book_value") or ratios.get("book_value"),
        "ev_ebitda":       None,  # not directly on screener top bar; can be derived
        "market_cap_cr":   ratios.get("market_cap"),
        "dividend_yield":  ratios.get("dividend_yield"),
        "face_value":      ratios.get("face_value"),
 
        # --- Profitability ---
        "roe":             ratios.get("return_on_equity") or ratios.get("roe"),
        "roce":            ratios.get("roce"),
        "net_margin_pct":  (latest_profit / latest_revenue * 100)
                           if latest_profit is not None and latest_revenue else None,
        "opm_pct":         latest_opm,
 
        # --- Growth ---
        "revenue_cagr_3y":  _growth_rate(revenue_vals, 3),
        "profit_cagr_3y":   _growth_rate(profit_vals,  3),
 
        # --- Debt health ---
        "de_ratio":            de_ratio,
        "interest_coverage":   interest_coverage,
        "total_debt_cr":        latest_debt,
 
        # --- Cash flow quality ---
        "cfo_cr":          latest_cfo,
        "cfo_pat_ratio":   cfo_pat_ratio,
 
        # --- Shareholding ---
        "promoter_holding_pct": promoter_holding,
        "pledged_pct":          pledged_pct,
 
        # --- Raw arrays (useful for trend checks) ---
        "_revenue_vals":   revenue_vals,
        "_profit_vals":    profit_vals,
        "_cfo_vals":       cfo_vals,
        "_debt_vals":      debt_vals,
    }
 