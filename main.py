#!/usr/bin/env python3
"""
main.py  –  Nifty 50 Fundamental Stock Screener
Usage:
    python main.py                          # Screen all 50 stocks
    python main.py --top 10                 # Show only top 10
    python main.py --detail INFY TCS        # Full breakdown for specific stocks
    python main.py --export                 # Export results to CSV
    python main.py --flags-only             # Show only stocks with red flags
    python main.py --delay 2.0              # Set request delay (seconds, be polite!)
"""

import argparse
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# ── make sure local modules resolve when running from any directory ─────────
sys.path.insert(0, str(Path(__file__).parent))

from screener  import fetch_fundamentals
from criteria  import score_stock
from universe  import get_screener_symbols, get_name_map
from report    import (
    print_summary_table,
    print_stock_detail,
    print_red_flag_report,
    export_csv,
    console,
)


def parse_args():
    p = argparse.ArgumentParser(
        description="Nifty 50 Fundamental Screener — powered by Screener.in",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--top",        type=int,   default=None,
                   help="Show only top N stocks in summary table")
    p.add_argument("--detail",     nargs="+",  metavar="SYMBOL",
                   help="Print full criterion breakdown for these symbols")
    p.add_argument("--export",     action="store_true",
                   help="Export full results to a dated CSV file")
    p.add_argument("--flags-only", action="store_true",
                   help="Skip summary table; show only red-flag report")
    p.add_argument("--delay",      type=float, default=1.5,
                   help="Seconds to wait between Screener.in requests (default: 1.5)")
    p.add_argument("--symbols",    nargs="+",  metavar="SYMBOL",
                   help="Override: screen only these symbols instead of full Nifty 50")
    return p.parse_args()


def main():
    args     = parse_args()
    name_map = get_name_map()

    symbols = args.symbols if args.symbols else get_screener_symbols()

    console.print(f"\n[bold blue]Nifty 50 Fundamental Screener[/bold blue]")
    console.print(f"[dim]Fetching data for {len(symbols)} stocks from Screener.in "
                  f"(delay: {args.delay}s between requests)[/dim]\n")

    # ── Fetch + Score ────────────────────────────────────────────────────────
    all_data    = {}
    all_results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Fetching fundamentals...", total=len(symbols))

        for sym in symbols:
            progress.update(task, description=f"Fetching [cyan]{sym}[/cyan]...")
            data   = fetch_fundamentals(sym, delay=args.delay)
            result = score_stock(data)
            all_data[sym]    = data
            all_results.append(result)
            progress.advance(task)

    console.print(f"[green]✔[/green] Done fetching {len(symbols)} stocks.\n")

    # ── Determine what to display ─────────────────────────────────────────────
    detail_syms = {s.upper() for s in (args.detail or [])}

    # Detail view for specific stocks
    if detail_syms:
        for result in all_results:
            if result["symbol"] in detail_syms:
                print_stock_detail(result, all_data.get(result["symbol"], {}), name_map)
    else:
        if not args.flags_only:
            display_results = all_results
            if args.top:
                # Sort and take top N (excluding errors)
                ranked = sorted(
                    [r for r in all_results if not r.get("fetch_error")],
                    key=lambda x: -(x.get("score") or 0)
                )
                display_results = ranked[:args.top]
            print_summary_table(display_results, name_map)

        # Red flag report
        print_red_flag_report(all_results, name_map)

    # ── CSV Export ────────────────────────────────────────────────────────────
    if args.export:
        path = export_csv(all_results, all_data, name_map, output_dir="output")
        console.print(f"[green]✔[/green] Exported to [bold]{path}[/bold]\n")

    # ── Quick stats ───────────────────────────────────────────────────────────
    if not detail_syms:
        scored = [r for r in all_results if r.get("score") is not None]
        if scored:
            avg = sum(r["score"] for r in scored) / len(scored)
            top = max(scored, key=lambda x: x["score"])
            bot = min(scored, key=lambda x: x["score"])
            console.print(
                f"[dim]Avg score: {avg:.1f}  |  "
                f"Best: {top['symbol']} ({top['score']:.1f})  |  "
                f"Worst: {bot['symbol']} ({bot['score']:.1f})[/dim]\n"
            )


if __name__ == "__main__":
    main()