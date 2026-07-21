"""
report.py  –  Pretty CLI output + CSV export for the screener results
"""

import csv
import os
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text


console = Console()

GRADE_COLOR = {
    "A": "bold green",
    "B": "green",
    "C": "yellow",
    "D": "red",
    "F": "bold red",
    "N/A": "dim",
}

PILLAR_ORDER = ["Profitability", "Growth", "Valuation", "Debt Health", "Quality"]


def _grade_style(grade: str) -> str:
    return GRADE_COLOR.get(grade, "white")


def print_summary_table(scored_stocks: list[dict], name_map: dict = None):
    """Print ranked summary table of all stocks."""
    name_map = name_map or {}

    # Sort: fetch errors last, then by score descending
    ranked = sorted(
        scored_stocks,
        key=lambda x: (x.get("fetch_error", False), -(x.get("score") or 0))
    )

    table = Table(
        title=f"[bold]Nifty 50 — Fundamental Screener[/bold]  [dim]{datetime.now().strftime('%d %b %Y')}[/dim]",
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold white on dark_blue",
        expand=False,
    )

    table.add_column("#",          style="dim",        width=3,  justify="right")
    table.add_column("Symbol",     style="bold white", width=13)
    table.add_column("Company",    style="white",      width=22)
    table.add_column("Score /100", justify="right",    width=10)
    table.add_column("Grade",      justify="center",   width=7)
    table.add_column("Red Flags",  width=40, no_wrap=False)

    for rank, stock in enumerate(ranked, 1):
        sym    = stock["symbol"]
        name   = name_map.get(sym, "")
        score  = stock.get("score")
        grade  = stock.get("grade", "N/A")
        flags  = stock.get("red_flags", [])

        score_str = f"{score:.1f}" if score is not None else "—"
        flags_str = "; ".join(flags[:2]) if flags else "[dim]None[/dim]"
        if len(flags) > 2:
            flags_str += f" [dim](+{len(flags)-2} more)[/dim]"

        grade_markup = f"[{_grade_style(grade)}]{grade}[/]"
        table.add_row(
            str(rank),
            f"[cyan]{sym}[/cyan]",
            name,
            score_str,
            grade_markup,
            flags_str,
        )

    console.print()
    console.print(table)
    console.print()


def print_stock_detail(result: dict, data: dict, name_map: dict = None):
    """Print a detailed breakdown for a single stock."""
    name_map = name_map or {}
    sym   = result["symbol"]
    name  = name_map.get(sym, sym)
    score = result.get("score")
    grade = result.get("grade", "N/A")

    header = Text()
    header.append(f"{name}  ", style="bold white")
    header.append(f"({sym})", style="dim")
    header.append(f"   Score: {score:.1f}/100" if score else "   Score: N/A", style="bold")
    header.append(f"   Grade: {grade}", style=_grade_style(grade) + " bold")

    console.print(Panel(header, border_style="blue"))

    # Pillar breakdown
    breakdown = result.get("breakdown", [])
    by_pillar = {}
    for cr in breakdown:
        by_pillar.setdefault(cr.pillar, []).append(cr)

    for pillar in PILLAR_ORDER:
        crs = by_pillar.get(pillar, [])
        if not crs:
            continue
        pillar_pts = sum(c.points for c in crs)
        pillar_max = sum(c.max_points for c in crs)
        console.print(f"\n[bold underline]{pillar}[/]  [dim]{pillar_pts:.0f}/{pillar_max:.0f} pts[/dim]")
        for c in crs:
            tick = "[green]✔[/]" if c.passed else "[red]✘[/]"
            pts  = f"[dim]{c.points:.0f}/{c.max_points:.0f}[/dim]"
            note_style = "red" if c.red_flag else "white"
            console.print(f"  {tick} {c.name:<26} {pts}  [{note_style}]{c.note}[/]")

    # Red flags
    flags = result.get("red_flags", [])
    if flags:
        console.print(f"\n[bold red]⚠  Red Flags ({len(flags)})[/bold red]")
        for f in flags:
            console.print(f"   [red]▸ {f}[/red]")
    else:
        console.print("\n[green]✔  No red flags[/green]")

    console.print()


def print_red_flag_report(scored_stocks: list[dict], name_map: dict = None):
    """Print stocks with red flags, grouped by severity."""
    name_map = name_map or {}

    flagged = [s for s in scored_stocks if s.get("red_flags")]
    if not flagged:
        console.print("[green]✔  No red flags across any Nifty 50 stock.[/green]")
        return

    flagged_sorted = sorted(flagged, key=lambda x: -len(x.get("red_flags", [])))

    table = Table(
        title="[bold red]⚠  Red Flag Report[/bold red]",
        box=box.ROUNDED,
        header_style="bold white on red",
        expand=False,
    )
    table.add_column("Symbol",    style="bold cyan",  width=13)
    table.add_column("Grade",     justify="center",    width=7)
    table.add_column("# Flags",   justify="center",    width=8)
    table.add_column("Red Flags", width=55, no_wrap=False)

    for stock in flagged_sorted:
        sym   = stock["symbol"]
        grade = stock.get("grade", "N/A")
        flags = stock.get("red_flags", [])
        table.add_row(
            sym,
            f"[{_grade_style(grade)}]{grade}[/]",
            str(len(flags)),
            "\n".join(f"▸ {f}" for f in flags),
        )

    console.print()
    console.print(table)
    console.print()


def export_csv(scored_stocks: list[dict], data_map: dict, name_map: dict = None,
               output_dir: str = ".") -> str:
    """Export full results to CSV. Returns the file path."""
    name_map = name_map or {}
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    path = os.path.join(output_dir, f"nifty50_screener_{date_str}.csv")

    fields = [
        "rank", "symbol", "company", "score", "grade",
        "pe_ratio", "pb_ratio", "roe", "roce",
        "net_margin_pct", "opm_pct",
        "revenue_cagr_3y", "profit_cagr_3y",
        "de_ratio", "interest_coverage",
        "cfo_pat_ratio", "promoter_holding_pct", "pledged_pct",
        "market_cap_cr", "red_flags",
    ]

    ranked = sorted(
        scored_stocks,
        key=lambda x: (x.get("fetch_error", False), -(x.get("score") or 0))
    )

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rank, stock in enumerate(ranked, 1):
            sym  = stock["symbol"]
            data = data_map.get(sym, {})
            def fmt(v, decimals=2):
                return round(v, decimals) if isinstance(v, float) else v
            row = {
                "rank":                rank,
                "symbol":              sym,
                "company":             name_map.get(sym, ""),
                "score":               fmt(stock.get("score"), 1),
                "grade":               stock.get("grade", "N/A"),
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
                "red_flags":           " | ".join(stock.get("red_flags", [])),
            }
            writer.writerow(row)

    return path