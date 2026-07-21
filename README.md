# Nifty 50 Fundamental Stock Screener

A fully automated CLI tool that scrapes **Screener.in** for Nifty 50 stocks,
runs each stock through a 14-criterion fundamental analysis engine,
assigns a score out of 100, a letter grade, and surfaces red flags.

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Usage

### Screen all 50 Nifty stocks
```bash
python main.py
```

### Show only top 10 by score
```bash
python main.py --top 10
```

### Detailed breakdown for specific stocks
```bash
python main.py --detail INFY TCS RELIANCE
```

### Export full results to CSV (saved in ./output/)
```bash
python main.py --export
```

### Show only red flag report (skip summary table)
```bash
python main.py --flags-only
```

### Screen a custom set of symbols
```bash
python main.py --symbols INFY TCS HDFCBANK ICICIBANK
```

### Adjust request delay (be polite to Screener.in!)
```bash
python main.py --delay 2.0
```

---

## How Scoring Works

Each stock is evaluated across **5 pillars** (100 points total):

| Pillar         | Max Pts | Key Metrics                          |
|----------------|---------|--------------------------------------|
| Profitability  | 25      | ROE, ROCE, Net Margin, OPM           |
| Growth         | 20      | Revenue CAGR (3Y), Profit CAGR (3Y)  |
| Valuation      | 20      | P/E Ratio, P/B Ratio                 |
| Debt Health    | 20      | D/E Ratio, Interest Coverage         |
| Quality        | 15      | CFO/PAT, Promoter Holding, Pledging  |
| Trend (bonus)  | 5       | Consistent 3Y profit growth          |

### Grading
| Grade | Score Range | Meaning                   |
|-------|-------------|---------------------------|
| A     | 75–100      | Excellent fundamentals    |
| B     | 60–74       | Good fundamentals         |
| C     | 45–59       | Average / mixed signals   |
| D     | 30–44       | Weak fundamentals         |
| F     | 0–29        | Poor — avoid              |

### Red Flags
Red flags are **hard warnings** independent of score.  
A stock can score well but still carry red flags (e.g. high PE + great ROCE).  
Red flags include:
- ROE < 10%
- ROCE < 10%  
- Net margin negative (loss-making)
- D/E ratio > 2
- Interest coverage < 1.5x
- Negative operating cash flow
- Promoter holding < 20%
- Promoter pledging > 30%
- Loss-making year in past 3 years
- Negative revenue/profit CAGR

---

## Output Files

CSV exports are saved in `./output/nifty50_screener_YYYYMMDD_HHMM.csv`  
with columns: rank, symbol, company, score, grade, all metrics, red flags.

---

## Data Source

All fundamental data is scraped from **[Screener.in](https://www.screener.in)**
(consolidated view). Screener.in is a free, publicly accessible platform.

**Please be respectful:** the default delay between requests is 1.5 seconds.  
Do not reduce this significantly or run multiple parallel processes.

---

## Project Structure

```
stock_screener/
├── main.py          # CLI entry point
├── screener.py      # Screener.in scraper + data parser
├── criteria.py      # 14 scoring criteria + red flag logic
├── universe.py      # Nifty 50 symbol list
├── report.py        # Rich CLI tables + CSV export
├── requirements.txt
└── README.md
```

---

## Extending

### Add a new criterion
In `criteria.py`, define a function `c_your_metric(data: dict) -> CriterionResult`
and add it to the `ALL_CRITERIA` list. The scoring engine picks it up automatically.

### Change the universe
Edit `universe.py` or use `--symbols` at runtime to screen any NSE-listed stock
available on Screener.in.

### Add more data fields
In `screener.py`, extend `_extract_table_row()` calls or add new `_extract_*`
functions. All new fields are available in `data` dict passed to criterion functions.
