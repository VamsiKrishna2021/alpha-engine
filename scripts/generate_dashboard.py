"""
generate_dashboard.py — Renders HTML dashboard from Jinja2 templates
=====================================================================
Takes scan_results.json and produces the final HTML for GitHub Pages.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from scripts.config import CFG
from scripts.utils import ensure_dirs
from scripts.sector_rotation import sector_color

logger = logging.getLogger("alpha_engine")


def load_scan_results() -> dict:
    """Load the latest scan results from JSON."""
    path = os.path.join(CFG.DATA_DIR, "scan_results.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load scan results: {e}")
        return {}


def generate_dashboard(results: dict = None):
    """Generate the HTML dashboard from templates and scan results."""
    ensure_dirs()

    if results is None:
        results = load_scan_results()

    if not results:
        logger.warning("No scan results available. Generating empty dashboard.")
        results = {
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "scan_time": "N/A",
            "regime": {"regime_score": 0, "label": "NO DATA", "color": "#9e9e9e"},
            "breadth": {},
            "breadth_history": [],
            "sectors": [],
            "deployment": {},
            "top_stocks": [],
            "top_gainers": [],
            "top_losers": [],
            "scan_stats": {},
        }

    # Setup Jinja2
    env = Environment(
        loader=FileSystemLoader(CFG.TEMPLATE_DIR),
        autoescape=True,
    )

    # Add custom filters
    env.filters["sector_color"] = sector_color
    env.filters["abs"] = abs
    env.globals["sector_color"] = sector_color

    # Render main dashboard
    template = env.get_template("index.html")
    html = template.render(
        data=results,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S ET"),
    )

    output_path = os.path.join(CFG.OUTPUT_DIR, "index.html")
    with open(output_path, "w") as f:
        f.write(html)
    logger.info(f"Dashboard generated: {output_path}")

    # Copy static files to output
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    output_static = os.path.join(CFG.OUTPUT_DIR, "static")
    os.makedirs(output_static, exist_ok=True)

    for filename in os.listdir(static_dir):
        src = os.path.join(static_dir, filename)
        dst = os.path.join(output_static, filename)
        with open(src, "r") as f:
            content = f.read()
        with open(dst, "w") as f:
            f.write(content)

    # (analyse.html removed — analyser is now inline on main dashboard)

    # Copy scan_results.json to output for frontend access
    results_src = os.path.join(CFG.DATA_DIR, "scan_results.json")
    results_dst = os.path.join(CFG.OUTPUT_DIR, "scan_results.json")
    if os.path.exists(results_src):
        with open(results_src, "r") as f:
            content = f.read()
        with open(results_dst, "w") as f:
            f.write(content)

    logger.info("Dashboard generation complete.")


def generate_analyse_page(ticker_data: dict):
    """Generate a single-stock analysis page."""
    ensure_dirs()

    env = Environment(
        loader=FileSystemLoader(CFG.TEMPLATE_DIR),
        autoescape=True,
    )

    # Save analysis data as JSON for the frontend
    analysis_path = os.path.join(CFG.OUTPUT_DIR, "analysis_data.json")
    with open(analysis_path, "w") as f:
        json.dump(ticker_data, f, indent=2, default=str)

    logger.info(f"Analysis data saved for {ticker_data.get('ticker', 'unknown')}")


if __name__ == "__main__":
    generate_dashboard()
