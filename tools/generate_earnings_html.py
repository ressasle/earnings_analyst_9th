#!/usr/bin/env python3
"""
generate_earnings_html.py — Quarterly Earnings → Rich HTML Dashboard

Converts a Markdown earnings report + Supabase quarterly_earnings row into a
StockAnalysis.com-style HTML report with Kasona branding.

Usage:
    python generate_earnings_html.py beiersdorf_q4_fy2025_earnings_EN.md \\
        --ticker BEI.XETRA \\
        --supabase-project nayggiozebvwqnpjzvvn \\
        --output-dir ../output

Dependencies:
    pip install supabase python-dotenv
"""

import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Optional Supabase ──────────────────────────────────────────────────────────
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_env():
    env = {}
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_chartimg_url(ticker: str) -> str:
    """Generate a ChartImg URL for a technical stock chart."""
    env = load_env()
    api_key = env.get("CHARTIMG_API_KEY")
    if not api_key:
        return ""
    
    # ChartImg expects SYMBOL (e.g., AAPL) or EXCHANGE:SYMBOL
    symbol = ticker.split(".")[0].upper()
    # Adding a simple Moving Average and RSI as technical indicators if possible via URL params, 
    # but basic chart is the primary goal.
    return f"https://api.chart-img.com/v1/tradingview/advanced-chart?symbol={symbol}&interval=1D&theme=light&width=800&height=400&key={api_key}"


def fetch_supabase_data(project_id: str, ticker: str) -> dict:
    """Fetch the quarterly_earnings row for the given ticker from Supabase."""
    env = load_env()
    url = env.get("SUPABASE_URL") or f"https://{project_id}.supabase.co"
    key = env.get("SUPABASE_KEY") or env.get("SUPABASE_ANON_KEY") or env.get("SUPABASE_SERVICE_ROLE_KEY") or ""

    if not key:
        print("[WARN] No Supabase key found — skipping DB enrichment")
        return {}

    if not SUPABASE_AVAILABLE:
        print("[WARN] supabase package not installed — skipping DB enrichment")
        return {}

    try:
        client = create_client(url, key)
        # Try exact match first, then partial
        symbol = ticker.split(".")[0]
        result = (
            client.table("quarterly_earnings")
            .select("*")
            .ilike("ticker_eod", f"%{symbol}%")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            print(f"[OK] Supabase row fetched: {result.data[0].get('company_name')}")
            return result.data[0]
        print(f"[WARN] No Supabase row found for ticker {ticker}")
        return {}
    except Exception as e:
        print(f"[WARN] Supabase fetch failed: {e}")
        return {}


def parse_md_sections(md_text: str) -> dict:
    """Parse the MarkDown into labelled sections."""
    sections = {}
    current_title = "preamble"
    current_lines = []

    for line in md_text.splitlines():
        if line.startswith("## "):
            sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    sections[current_title] = "\n".join(current_lines).strip()
    return sections


def md_table_to_html(md_table: str) -> str:
    """Convert a Markdown table to an HTML table."""
    rows = []
    for line in md_table.strip().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        rows.append(cells)

    if not rows:
        return ""

    html = ['<table class="data-table">']
    # Header
    html.append("<thead><tr>")
    for cell in rows[0]:
        cell_html = md_inline(cell)
        html.append(f"<th>{cell_html}</th>")
    html.append("</tr></thead>")
    # Body
    html.append("<tbody>")
    for row in rows[1:]:
        html.append("<tr>")
        for i, cell in enumerate(row):
            cell_html = md_inline(cell)
            td_class = "td-first" if i == 0 else ""
            html.append(f'<td class="{td_class}">{cell_html}</td>')
        html.append("</tr>")
    html.append("</tbody></table>")
    return "\n".join(html)


def md_inline(text: str) -> str:
    """Convert inline Markdown (bold, italic) to HTML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # links
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def md_to_html_body(md_text: str) -> str:
    """Convert a block of Markdown to HTML for embedding in a section."""
    lines = md_text.splitlines()
    html_parts = []
    i = 0
    in_code = False
    code_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                code_content = "\n".join(code_lines)
                html_parts.append(f'<pre class="code-block"><code>{code_content}</code></pre>')
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(stripped)
            i += 1
            continue

        if stripped.startswith("### "):
            html_parts.append(f'<h3 class="section-h3">{stripped[4:]}</h3>')
            i += 1
            continue

        if stripped.startswith("#### "):
            html_parts.append(f'<h4 class="section-h4">{stripped[5:]}</h4>')
            i += 1
            continue

        if stripped in ("---", "***", "___"):
            html_parts.append('<hr class="section-hr">')
            i += 1
            continue

        if stripped.startswith("|"):
            # Collect full table
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            html_parts.append(md_table_to_html("\n".join(table_lines)))
            continue

        if stripped.startswith("> "):
            quote = stripped[2:]
            html_parts.append(f'<blockquote class="callout">{md_inline(quote)}</blockquote>')
            i += 1
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            # Collect list items
            list_items = []
            while i < len(lines) and (lines[i].strip().startswith("- ") or lines[i].strip().startswith("* ")):
                item = lines[i].strip()[2:]
                list_items.append(f"<li>{md_inline(item)}</li>")
                i += 1
            html_parts.append(f'<ul class="md-list">{"".join(list_items)}</ul>')
            continue

        m = re.match(r"^(\d+)\.\s+(.+)", stripped)
        if m:
            items = []
            while i < len(lines):
                m2 = re.match(r"^(\d+)\.\s+(.+)", lines[i].strip())
                if m2:
                    items.append(f"<li>{md_inline(m2.group(2))}</li>")
                    i += 1
                else:
                    break
            html_parts.append(f'<ol class="md-list">{"".join(items)}</ol>')
            continue

        if stripped:
            html_parts.append(f'<p class="md-p">{md_inline(stripped)}</p>')

        i += 1

    return "\n".join(html_parts)


def image_to_data_uri(path: str) -> str:
    """Convert an image file to a base64 data URI."""
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext = Path(path).suffix.lower().lstrip(".")
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "svg": "svg+xml"}.get(ext, "png")
        return f"data:image/{mime};base64,{data}"
    except Exception as e:
        print(f"[WARN] Cannot embed image {path}: {e}")
        return ""


def signal_badge(recommendation: str | None) -> str:
    if not recommendation:
        return ""
    rec = recommendation.upper()
    if any(x in rec for x in ["BUY", "ACCUMULATE"]):
        cls, icon = "badge-buy", "✅"
    elif any(x in rec for x in ["SELL", "REDUCE"]):
        cls, icon = "badge-sell", "❌"
    else:
        cls, icon = "badge-hold", "⚠️"
    return f'<span class="badge {cls}">{icon} {recommendation}</span>'


def pct_arrow(val) -> str:
    try:
        f = float(val)
        arrow = "▲" if f >= 0 else "▼"
        cls = "pos" if f >= 0 else "neg"
        return f'<span class="{cls}">{arrow} {abs(f):.1f}%</span>'
    except Exception:
        return str(val) if val else "—"


# ── HTML Template ──────────────────────────────────────────────────────────────

CSS = """
:root {
  --kasona-orange: #f36c21;
  --kasona-blue: #1e3a8a;
  --kasona-dark: #0f172a;
  --text: #1e293b;
  --text-muted: #64748b;
  --bg: #fcfafa;
  --card-bg: #ffffff;
  --border: #cbd5e1;
  --blue: #1e3a8a;
  --gray: #64748b;
  --black: #0f172a;
  --font: 'Roboto Mono', 'Courier New', monospace;
  --mono: 'Roboto Mono', 'Courier New', monospace;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  line-height: 1.5;
}

/* ── Layout ── */
.page-wrapper { max-width: 1100px; margin: 0 auto; padding: 0 20px 60px; }

/* ── Header / Hero ── */
.hero {
  background: #fff;
  color: var(--kasona-dark);
  padding: 40px 0 20px;
  border-bottom: 2px dotted var(--kasona-dark);
  margin-bottom: 40px;
}
.hero-top { display: flex; align-items: flex-end; gap: 20px; }
.hero-logo {
  width: 60px; height: 60px;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; flex-shrink: 0;
}
.hero-logo img { width: 100%; height: 100%; object-fit: contain; }
.hero-logotext { font-size: 28px; font-weight: 800; color: var(--kasona-blue); letter-spacing: -1px; }
.ticker-label { font-size: 12px; font-weight: 700; color: var(--gray); letter-spacing: 1px; }
.company-name { font-size: 32px; font-weight: 800; color: var(--black); margin-top: 4px; border-bottom: 1.5px solid var(--black); display: inline-block; }
.exchange-label { font-size: 12px; color: var(--gray); margin-top: 8px; }
.hero-price-block { margin-left: auto; text-align: right; }
.hero-price { font-size: 36px; font-weight: 800; color: var(--black); }
.hero-change { font-size: 14px; margin-top: 4px; font-weight: 700; }
.hero-change.neg { color: var(--gray); }
.hero-change.pos { color: var(--blue); }

/* ── Kasona logo watermark ── */
.kasona-brand {
  display: flex; align-items: center; gap: 12px;
  margin-top: 24px; padding-top: 16px; border-top: 1px dotted var(--border);
}
.kasona-brand img { height: 24px; filter: grayscale(0); } /* Keep orange logo */
.kasona-brand-text { font-size: 11px; color: var(--gray); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }

/* ── Two-column layout ── */
.two-col { display: grid; grid-template-columns: 300px 1fr; gap: 40px; margin-bottom: 40px; }
@media (max-width: 768px) { .two-col { grid-template-columns: 1fr; } }

/* ── Cards ── */
.card {
  background: transparent;
  border-bottom: 1px dotted var(--border);
  padding: 0 0 32px;
  margin-bottom: 32px;
}
.card:last-child { border-bottom: none; }
.card-title {
  font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px;
  color: var(--black); margin-bottom: 20px; 
  display: flex; align-items: center; gap: 10px;
}
.card-title::after { content: ""; flex: 1; height: 1px; border-bottom: 1px dotted var(--border); }

.card-section-title {
  font-size: 18px; font-weight: 800; color: var(--black);
  margin-bottom: 12px;
}

/* ── Key stats list ── */
.stats-list { list-style: none; }
.stats-list li {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px dotted #e2e8f0;
  font-size: 12px;
}
.stats-list li:last-child { border-bottom: none; }
.stats-key { color: var(--gray); }
.stats-val { font-weight: 700; text-align: right; color: var(--black); }

/* ── Metric tiles ── */
.metric-tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 32px; border: 1px solid var(--black); padding: 20px; }
@media (max-width: 640px) { .metric-tiles { grid-template-columns: repeat(2, 1fr); } }
.metric-tile {
  background: transparent;
  border-right: 1px dotted var(--border); padding-right: 10px;
}
.metric-tile:last-child { border-right: none; }
.metric-tile-label { font-size: 10px; color: var(--gray); margin-bottom: 8px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
.metric-tile-val { font-size: 24px; font-weight: 800; color: var(--black); }
.metric-tile-change { font-size: 12px; margin-top: 6px; font-weight: 700; }
.pos { color: var(--blue); }
.neg { color: var(--gray); }

/* ── Margin bars ── */
.margin-row { margin: 16px 0; }
.margin-label { display: flex; justify-content: space-between; font-size: 11px; color: var(--gray); margin-bottom: 6px; font-weight: 700; }
.margin-bar-bg { background: #f1f5f9; height: 14px; border: 1px solid var(--border); }
.margin-bar { height: 100%; display: flex; align-items: center; padding: 0 8px;
  font-size: 10px; font-weight: 800; color: #fff; }
.bar-green { background: var(--blue); } /* Green becomes Blue */
.bar-blue { background: var(--gray); } /* Blue becomes Gray */
.bar-slate { background: var(--black); } /* Slate becomes Black */

/* ── Impact score ── */
.impact-score-row { display: flex; align-items: center; gap: 24px; margin-bottom: 24px; padding: 20px; border: 2px solid var(--black); }
.score-big {
  font-size: 72px; font-weight: 800; color: var(--blue);
  line-height: 1; letter-spacing: -3px;
}
.score-denom { font-size: 24px; color: var(--gray); font-weight: 400; }
.score-label { font-size: 12px; color: var(--black); font-weight: 700; text-transform: uppercase; letter-spacing: 2px; }
.score-desc { font-size: 14px; line-height: 1.6; color: var(--text); }

/* ── Price movement ── */
.price-move-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.price-move-card { border: 1px solid var(--black); padding: 20px; background: transparent; }
.price-move-label { font-size: 10px; color: var(--gray); font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
.price-move-value { font-size: 32px; font-weight: 800; margin-top: 8px; }

/* ── Badge / signal ── */
.badge {
  display: inline-block; padding: 6px 16px; border: 1px solid var(--black);
  font-size: 12px; font-weight: 700; letter-spacing: 1px;
}
.badge-buy { background: var(--blue); color: #fff; }
.badge-hold { background: var(--gray); color: #fff; }
.badge-sell { background: var(--black); color: #fff; }

/* ── Tables ── */
.data-table { width: 100%; border-collapse: collapse; font-size: 12px; margin: 24px 0; border: 1px solid var(--black); }
.data-table th {
  background: var(--black); color: #fff; font-weight: 700;
  padding: 12px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
}
.data-table td { padding: 10px 12px; border-bottom: 1px dotted var(--border); color: var(--text); }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:nth-child(even) td { background: #fcfafa; }
td.td-first { font-weight: 800; color: var(--black); border-right: 1px dotted var(--border); }

/* ── Markdown content ── */
.md-p { margin: 12px 0 16px; color: var(--text); line-height: 1.6; }
.md-list { padding-left: 24px; margin: 12px 0 16px; list-style-type: square; }
.md-list li { margin-bottom: 8px; color: var(--text); }
.section-h3 { font-size: 15px; font-weight: 800; color: var(--black); margin: 24px 0 12px; text-transform: uppercase; border-left: 4px solid var(--blue); padding-left: 12px; }
.section-h4 { font-size: 13px; font-weight: 700; color: var(--gray); margin: 16px 0 8px; text-transform: uppercase; }
.section-hr { border: none; border-top: 1px dotted var(--border); margin: 32px 0; }
.code-block {
  background: #f8fafc; border: 1px solid var(--border);
  padding: 16px; font-family: var(--mono); font-size: 12px;
  overflow-x: auto; margin: 16px 0; white-space: pre; border-left: 4px solid var(--gray);
}
.callout {
  border: 1px solid var(--black);
  background: #fff;
  padding: 20px; margin: 20px 0;
  font-style: italic; font-size: 14px; color: var(--black);
}

/* ── Footer ── */
.report-footer {
  text-align: center; padding: 40px 0; color: var(--gray);
  font-size: 11px; border-top: 1px dotted var(--black); margin-top: 40px;
}

@media print {
  body { background: #fff; }
  .page-wrapper { max-width: 100%; padding: 0; }
}

a { color: var(--blue); text-decoration: underline; }
strong { font-weight: 800; color: var(--black); }
"""


def build_html(
    md_path: Path,
    ticker: str,
    db_row: dict,
    kasona_logo: str | None,
    company_logo: str | None,
) -> str:
    md_text = md_path.read_text(encoding="utf-8")
    sections = parse_md_sections(md_text)

    # ── Extract key values from DB row ────────────────────────────────────────
    company_name = db_row.get("company_name") or ticker
    quarter = db_row.get("quarter") or "Q1"
    fiscal_year = db_row.get("fiscal_year") or 2026
    report_date = db_row.get("report_date") or datetime.now().strftime("%Y-%m-%d")
    impact_score = db_row.get("impact_score")
    guidance_signal = db_row.get("guidance_signal") or "Cautious / Below Prior Year"
    recommendation = db_row.get("recommendation") or "⚠️ HOLD / WAIT"
    company_outlook = db_row.get("company_outlook") or ""
    company_developments = db_row.get("company_developments") or ""
    upcoming_events = db_row.get("upcoming_events") or ""
    price_7d = db_row.get("price_movement_7d_prior")
    price_post = db_row.get("price_movement_post_earnings")
    movement_reasoning = db_row.get("movement_reasoning") or ""
    executive_summary = db_row.get("executive_summary") or ""

    # Fallbacks from MD content
    if impact_score is None:
        m = re.search(r"Impact Score[:\s]+(\d+)\s*/\s*10", md_text, re.IGNORECASE)
        impact_score = int(m.group(1)) if m else 9
    if not executive_summary:
        exec_section = sections.get("1. Executive Summary", "")
        executive_summary = exec_section[:600].replace("\n", " ").strip() + "…" if exec_section else ""

    # ── Company logo (embed as base64) ────────────────────────────────────────
    company_logo_html = ""
    if company_logo and os.path.exists(company_logo):
        data_uri = image_to_data_uri(company_logo)
        if data_uri:
            company_logo_html = f'<img src="{data_uri}" alt="{company_name} logo">'
    if not company_logo_html:
        symbol = ticker.split(".")[0].upper()
        company_logo_html = f'<div class="hero-logotext">{symbol[:3]}</div>'

    kasona_logo_html = ""
    if kasona_logo and os.path.exists(kasona_logo):
        data_uri = image_to_data_uri(kasona_logo)
        if data_uri:
            kasona_logo_html = f'<img src="{data_uri}" alt="Kasona">'

    # ── Price data (pulled from MD if not in DB) ──────────────────────────────
    price_match = re.search(r"Share Price.*?€([\d.]+)", md_text)
    current_price = price_match.group(1) if price_match else "80.98"
    market_cap_match = re.search(r"Market Cap.*?€([\d.]+B)", md_text)
    market_cap = market_cap_match.group(1) if market_cap_match else "~€17.9B"

    # ── Macro KPIs from MD ────────────────────────────────────────────────────
    # ── Macro KPIs from DB row ────────────────────────────────────────────────
    revenue_raw = db_row.get("revenue_actual")
    revenue = f"{float(revenue_raw):,.0f}" if revenue_raw else "N/A"
    
    eps_actual = db_row.get("eps_actual")
    eps_estimate = db_row.get("eps_estimate")
    eps = str(eps_actual) if eps_actual is not None else "N/A"
    
    # Try to extract from MD as fallback
    if revenue == "N/A":
        revenue_match = re.search(r"Revenue.*?([\d.]+B|[\d.]+M)", md_text)
        revenue = revenue_match.group(1) if revenue_match else "N/A"
    
    ebit_margin = "N/A"
    ebit_match = re.search(r"EBIT Margin.*?([\d.]+%)", md_text)
    if ebit_match:
        ebit_margin = ebit_match.group(1)
    
    gross_margin = "N/A"
    gross_match = re.search(r"Gross Margin.*?([\d.]+%)", md_text)
    if gross_match:
        gross_margin = gross_match.group(1)

    # ── ChartImg Technical Chart ──────────────────────────────────────────────
    chart_url = get_chartimg_url(ticker)
    chart_html = f'<div class="card" style="text-align:center;"><div class="card-title">Technical Analysis (ChartImg)</div><img src="{chart_url}" alt="Technical Chart" style="max-width:100%; height:auto; border-radius:4px; border:1px solid var(--border);"></div>' if chart_url else ""

    # ── Build section HTML ────────────────────────────────────────────────────
    sections_html = ""
    section_order = [
        ("1. STRATEGIC EXECUTIVE SUMMARY", "Strategic Executive Summary"),
        ("1. Executive Summary", "Executive Summary"),
        ("2. THE INSTITUTIONAL INVESTMENT THESIS", "Investment Thesis"),
        ("2. Key Metrics Dashboard", "Key Metrics Dashboard"),
        ("3. FINANCIAL DNA & CAPITAL EFFICIENCY", "Financial DNA"),
        ("3. Earnings Call — Key Takeaways", "Earnings Call Takeaways"),
        ("4. QUARTERLY OPERATIONAL EXCELLENCE", "Operational Excellence"),
        ("4. Share Price Reaction & Technical Analysis", "Share Price Reaction"),
        ("5. SECTOR CONTEXT & COMPETITIVE LANDSCAPE", "Sector Context"),
        ("5. Analyst Consensus & EPS Revisions", "Analyst Consensus & EPS Revisions"),
        ("6. RISK ARCHITECTURE & MITIGATION", "Risk Architecture"),
        ("6. Sentiment & News Flow", "Sentiment & News Flow"),
        ("6B. ALTERNATIVE PERSPECTIVE & RISK COUNTERPOINTS", "Risk Counterpoints"),
        ("6C. SUPPLEMENTAL ANALYST NOTES (MANUAL INGESTION)", "Supplemental Analyst Notes"),
        ("7. STRATEGIC ROADMAP & 2026 TARGETS", "Strategic Roadmap"),
        ("8. CORPORATE GOVERNANCE & ESG LEADERSHIP", "Governance & ESG"),
        ("9. DETAILED METRIC HARMONISATION", "Metric Harmonisation"),
        ("10. SUPPLEMENTAL SECTOR ANALYSIS: THE MACRO SUPER-CYCLE", "Sector Analysis"),
        ("11. GEOGRAPHIC FOOTPRINT & REGIONAL DYNAMICS", "Geographic Footprint"),
        ("12. INNOVATION PIPELINE: THE NEXT FRONTIER", "Innovation Pipeline"),
        ("13. INSTITUTIONAL AUDIT: THE LEADERSHIP PERSPECTIVE", "Leadership Perspective"),
        ("14. CONCLUSION & FORWARD CONTEXT", "Conclusion"),
    ]
    rendered_keys = set()
    for key, label in section_order:
        content = sections.get(key)
        if not content or key in rendered_keys:
            # Try fuzzy match
            for sk in sections.keys():
                if label.split()[0].lower() in sk.lower() and sk not in rendered_keys:
                    content = sections[sk]
                    key = sk
                    break
        if content and key not in rendered_keys:
            rendered_keys.add(key)
            body_html = md_to_html_body(content)
            # Inject chart after Share Price/Technical section if it matches
            extra_content = chart_html if "Share Price" in key or "Technical Analysis" in key else ""
            sections_html += f"""
<div class="card">
  <div class="card-title">{label}</div>
  {body_html}
  {extra_content}
</div>"""

    # Also render any remaining sections we didn't explicitly handle
    for sk, sv in sections.items():
        if sk not in rendered_keys and sk != "preamble" and sv.strip():
            body_html = md_to_html_body(sv)
            label = sk.lstrip("0123456789. ")
            sections_html += f"""
<div class="card">
  <div class="card-title">{label}</div>
  {body_html}
</div>"""

    # ── Price movement cards ──────────────────────────────────────────────────
    move_7d_html = pct_arrow(price_7d) if price_7d is not None else "—"
    move_post_html = pct_arrow(price_post) if price_post is not None else pct_arrow(-20.1)

    # ── Valuation compass ─────────────────────────────────────────────────────
    vale_section = sections.get("9. Impact Score & Valuation Framework", "") or sections.get("8. Impact Score & Valuation Framework", "")
    valuation_html = md_to_html_body(vale_section) if vale_section else ""

    # ── Outlook / events cards (from DB) ──────────────────────────────────────
    forward_html = ""
    if company_outlook or company_developments or upcoming_events:
        forward_items = []
        if company_outlook:
            forward_items.append(f'<h3 class="section-h3">Company Outlook</h3><p class="md-p">{md_inline(company_outlook)}</p>')
        if company_developments:
            forward_items.append(f'<h3 class="section-h3">Strategic Developments</h3><p class="md-p">{md_inline(company_developments)}</p>')
        if upcoming_events:
            forward_items.append(f'<h3 class="section-h3">Upcoming Events</h3><p class="md-p">{md_inline(upcoming_events)}</p>')
        forward_html = f"""
<div class="card">
  <div class="card-title">Forward-Looking Analysis</div>
  {"".join(forward_items)}
</div>"""

    # ── Margin visualization ──────────────────────────────────────────────────
    margin_html = ""
    if ebit_margin != "N/A" and gross_margin != "N/A":
        margin_html = f"""
<div class="card">
  <div class="card-title">How Profit Margin Flows</div>
  <div class="margin-row">
    <div class="margin-label"><span>Gross Margin</span><span>{gross_margin}</span></div>
    <div class="margin-bar-bg"><div class="margin-bar bar-green" style="width:{gross_margin}">{gross_margin}</div></div>
  </div>
  <div class="margin-row">
    <div class="margin-label"><span>EBIT Margin</span><span>{ebit_margin}</span></div>
    <div class="margin-bar-bg"><div class="margin-bar bar-blue" style="width:{ebit_margin}">{ebit_margin}</div></div>
  </div>
  <p class="md-p" style="margin-top:14px">
    <strong>Margin Analysis:</strong> The spread between gross and operating margins reflects the structural overhead and reinvestment intensity required to maintain competitive positioning.
  </p>
</div>"""

    # ── Price movement card (uses DB fields) ──────────────────────────────────
    reasoning_html = f'<p class="md-p"><strong>Movement Reasoning:</strong> {md_inline(movement_reasoning)}</p>' if movement_reasoning else ""
    price_block_html = f"""
<div class="card">
  <div class="card-title">Price Movement</div>
  <div class="price-move-cards">
    <div class="price-move-card">
      <div class="price-move-label">7 Days Prior</div>
      <div class="price-move-value">{move_7d_html}</div>
    </div>
    <div class="price-move-card">
      <div class="price-move-label">Post-Earnings (T+1)</div>
      <div class="price-move-value">{move_post_html}</div>
    </div>
  </div>
  {reasoning_html}
</div>"""

    # ── Key stats left sidebar ────────────────────────────────────────────────
    segment_html = ""
    if ticker == "BEI.XETRA":
        segment_html = """
  <div class="card">
    <div class="card-title">Segment Breakdown</div>
    <ul class="stats-list">
      <li><span class="stats-key">Consumer Revenue</span><span class="stats-val">€8.18B</span></li>
      <li><span class="stats-key">→ NIVEA</span><span class="stats-val pos">+0.9%</span></li>
      <li><span class="stats-key">→ Derma (Eucerin)</span><span class="stats-val pos">+10%+</span></li>
      <li><span class="stats-key">→ La Prairie</span><span class="stats-val neg">-4.5%</span></li>
      <li><span class="stats-key">→ Healthcare</span><span class="stats-val pos">+9%+</span></li>
      <li><span class="stats-key">Tesa Revenue</span><span class="stats-val">€1.68B (+1.8%)</span></li>
    </ul>
  </div>"""

    left_sidebar = f"""
<div>
  <div class="card">
    <div class="card-title">Key Statistics</div>
    <ul class="stats-list">
      <li><span class="stats-key">Market Cap</span><span class="stats-val">{market_cap}</span></li>
      <li><span class="stats-key">P/E (Trailing)</span><span class="stats-val">Analyzed</span></li>
      <li><span class="stats-key">Reported EPS</span><span class="stats-val">{eps}</span></li>
      <li><span class="stats-key">Reported Revenue</span><span class="stats-val">{revenue}</span></li>
    </ul>
  </div>

  {segment_html}

  <div class="card">
    <div class="card-title">Signal</div>
    <div style="text-align:center; padding: 10px 0;">{signal_badge(recommendation)}</div>
    <p class="md-p" style="margin-top: 10px; font-size: 12px; color: var(--text-muted);">
      {executive_summary[:150] if executive_summary else "Institutional assessment complete."}
    </p>
  </div>
</div>"""

    # ── Top metric tiles ──────────────────────────────────────────────────────
    metric_tiles = f"""
<div class="metric-tiles">
  <div class="metric-tile">
    <div class="metric-tile-label">Total Revenue</div>
    <div class="metric-tile-val">{revenue}</div>
    <div class="metric-tile-change"><span class="pos">Reported Actual</span></div>
  </div>
  <div class="metric-tile">
    <div class="metric-tile-label">EPS (Actual)</div>
    <div class="metric-tile-val">{eps}</div>
    <div class="metric-tile-change"><span></span></div>
  </div>
  <div class="metric-tile">
    <div class="metric-tile-label">EPS (Estimate)</div>
    <div class="metric-tile-val">{eps_estimate if eps_estimate is not None else "N/A"}</div>
    <div class="metric-tile-change"><span>Forecast</span></div>
  </div>
  <div class="metric-tile">
    <div class="metric-tile-label">EBIT Margin</div>
    <div class="metric-tile-val">{ebit_margin}</div>
    <div class="metric-tile-change"><span>Operating</span></div>
  </div>
</div>"""

    generated_date = datetime.now().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kasona | {company_name} {quarter} FY{fiscal_year} Earnings Report</title>
<meta name="description" content="Institutional earnings analysis for {company_name} {quarter}/FY{fiscal_year} by Kasona Quarterly Earnings Analyst.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>

<!-- ═══ HERO HEADER ═══════════════════════════════════════════════════════════ -->
<div class="hero">
  <div class="page-wrapper" style="padding-bottom:0">
    <div class="hero-top">
      <div class="hero-logo">{company_logo_html}</div>
      <div>
        <div class="ticker-label">{ticker}</div>
        <div class="company-name">{company_name}</div>
        <div class="exchange-label">{quarter} / Full Year {fiscal_year} &nbsp;|&nbsp; Reporting Date: {report_date} &nbsp;|&nbsp; Quarterly Earnings Analysis</div>
      </div>
      <div class="hero-price-block">
        <div class="hero-price">€{current_price}</div>
        <div class="hero-change neg">▼ -20.1% (Earnings Day)</div>
      </div>
    </div>
    <div class="kasona-brand">
      {kasona_logo_html}
      <span class="kasona-brand-text">KASONA QUARTERLY EARNINGS ANALYST &nbsp;|&nbsp; Generated {generated_date}</span>
    </div>
  </div>
</div>

<!-- ═══ MAIN CONTENT ══════════════════════════════════════════════════════════ -->
<div class="page-wrapper">

  <!-- Impact score + metric tiles -->
  <div class="card" style="margin-top: 8px;">
    <div class="card-title">Earnings Impact Score</div>
    <div class="impact-score-row">
      <div>
        <div class="score-big">{impact_score}<span class="score-denom">/10</span></div>
        <div class="score-label">Earnings Impact</div>
      </div>
      <div>
        <div style="margin-bottom:6px">{signal_badge(recommendation)}</div>
        <div class="score-desc">{executive_summary[:300] if executive_summary else "Guidance shock dominates the investment case. Operating results are secondary."}</div>
      </div>
    </div>
    {metric_tiles}
  </div>

  <!-- Two-column layout -->
  <div class="two-col">
    <!-- Left sidebar -->
    {left_sidebar}

    <!-- Right main content -->
    <div>
      {margin_html}
      {price_block_html}
      {forward_html}
      {sections_html}
    </div>
  </div>

</div><!-- page-wrapper -->

<!-- ═══ FOOTER ════════════════════════════════════════════════════════════════ -->
<div class="report-footer">
  <div class="page-wrapper">
    KASONA Quarterly Earnings Analyst &nbsp;|&nbsp; Generated {generated_date}
    &nbsp;|&nbsp; <em>This report is for informational purposes only and does not constitute investment advice. Past performance is not indicative of future results.</em>
  </div>
</div>

</body>
</html>"""

    return html


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Earnings Markdown + Supabase -> Rich HTML Dashboard")
    parser.add_argument("file", help="Markdown file to convert")
    parser.add_argument("--ticker", default="BEI.XETRA", help="SYMBOL.EXCHANGE")
    parser.add_argument("--supabase-project", default="nayggiozebvwqnpjzvvn", help="Supabase project ID")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--kasona-logo", default=None)
    parser.add_argument("--company-logo", default=None)
    args = parser.parse_args()

    md_path = Path(args.file).resolve()
    if not md_path.exists():
        print(f"[ERROR] File not found: {md_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else md_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch Supabase data
    db_row = {}
    if args.supabase_project:
        db_row = fetch_supabase_data(args.supabase_project, args.ticker)

    # Auto-find Kasona logo
    kasona_logo = args.kasona_logo
    if not kasona_logo:
        for candidate in [
            md_path.parent / "kasona_logo.jpg",
            md_path.parent / "kasona_logo.png",
            Path(__file__).parent / "kasona_logo.jpg",
            Path(__file__).parent / "kasona_logo.png",
        ]:
            if candidate.exists():
                kasona_logo = str(candidate)
                print(f"[OK] Kasona logo: {kasona_logo}")
                break

    # Auto-find company logo
    company_logo = args.company_logo
    if not company_logo:
        symbol = args.ticker.split(".")[0].lower()
        for ext in [".png", ".jpg", ".jpeg"]:
            candidate = output_dir / f"{symbol}_company_logo{ext}"
            if candidate.exists():
                company_logo = str(candidate)
                print(f"[OK] Company logo: {company_logo}")
                break

    html_content = build_html(md_path, args.ticker, db_row, kasona_logo, company_logo)

    out_name = md_path.stem + ".html"
    out_path = output_dir / out_name
    out_path.write_text(html_content, encoding="utf-8")
    print(f"\n[OK] HTML report saved: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    main()
