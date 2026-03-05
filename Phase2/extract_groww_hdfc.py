import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

import requests
from bs4 import BeautifulSoup


FUND_URLS = [
    "https://groww.in/mutual-funds/hdfc-banking-financial-services-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-nifty-next-50-index-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
]


@dataclass
class FundSize:
    amount: Optional[float]
    currency: Optional[str]
    unit: Optional[str]


@dataclass
class Holding:
    company_name: str
    sector: Optional[str]
    weight_percent: Optional[float]


def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _parse_currency_amount(text: str) -> Optional[float]:
    """
    Extract numeric amount from strings like:
    - "₹36,940.54 Cr"
    - "₹100"
    """
    if not text:
        return None
    # Keep digits, commas, dot
    m = re.search(r"([0-9][0-9,]*\.?[0-9]*)", text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _parse_percentage(text: str) -> Optional[float]:
    """
    Convert strings like '0.73%' or '+19.0%' to decimal (e.g. 0.0073, 0.19).
    """
    if not text:
        return None
    m = re.search(r"(-?\+?[0-9]+(?:\.[0-9]+)?)\s*%", text)
    if not m:
        return None
    try:
        return float(m.group(1)) / 100.0
    except ValueError:
        return None


def _find_line_index(lines: List[str], prefix: str) -> Optional[int]:
    prefix_lower = prefix.lower()
    for idx, line in enumerate(lines):
        if line.lower().startswith(prefix_lower):
            return idx
    return None


def extract_from_text(text: str, source_url: str) -> Dict[str, Any]:
    """
    Heuristic extractor based on the rendered text structure observed on Groww pages.
    This does not rely on specific HTML tags; instead, it uses label lines like
    'NAV:', 'Min. for SIP', 'Fund size', 'Expense ratio', '### Exit Load', etc.
    """
    lines = [_clean_text(l) for l in text.splitlines()]
    # Remove empty lines
    lines = [l for l in lines if l]

    data: Dict[str, Any] = {
        "source_url": source_url,
        "scheme_name": None,
        "nav": None,
        "nav_date": None,
        "min_sip_amount": None,
        "fund_size": {"amount": None, "currency": "INR", "unit": None},
        "expense_ratio": None,
        "fund_managers": [],
        "returns": {
            "one_year": None,
            "three_year": None,
            "five_year": None,
            "since_inception": None,
        },
        "top_holdings": [],
        "holding_analysis": {"by_sector": [], "by_market_cap": [], "raw_text": None},
        "exit_load": None,
        "tax_info": None,
        "description": None,
    }

    # 1) Scheme name – first non-empty line that looks like a title for the page
    if lines:
        data["scheme_name"] = lines[0]

    # 2) NAV and NAV date
    idx_nav = _find_line_index(lines, "NAV:")
    if idx_nav is not None:
        # Example:
        # "NAV: 02 Mar '26"
        # "₹150.04"
        nav_line = lines[idx_nav]
        nav_parts = nav_line.split("NAV:")
        if len(nav_parts) > 1:
            data["nav_date"] = nav_parts[1].strip() or None
        if idx_nav + 1 < len(lines):
            nav_value_line = lines[idx_nav + 1]
            data["nav"] = _parse_currency_amount(nav_value_line)

    # 3) Minimum SIP amount
    idx_sip = _find_line_index(lines, "Min. for SIP")
    if idx_sip is not None and idx_sip + 1 < len(lines):
        data["min_sip_amount"] = int(_parse_currency_amount(lines[idx_sip + 1]) or 0)

    # 4) Fund size
    idx_fund_size = _find_line_index(lines, "Fund size")
    if idx_fund_size is not None and idx_fund_size + 1 < len(lines):
        fund_size_line = lines[idx_fund_size + 1]
        amount = _parse_currency_amount(fund_size_line)
        unit_match = re.search(r"(Cr|Lakh|Crore)", fund_size_line)
        unit = unit_match.group(1) if unit_match else None
        data["fund_size"] = {
            "amount": amount,
            "currency": "INR",
            "unit": unit,
        }

    # 5) Expense ratio
    idx_exp = _find_line_index(lines, "Expense ratio")
    if idx_exp is not None:
        # Sometimes the percentage is on the next line
        candidates = []
        if idx_exp < len(lines):
            candidates.append(lines[idx_exp])
        if idx_exp + 1 < len(lines):
            candidates.append(lines[idx_exp + 1])
        for c in candidates:
            perc = _parse_percentage(c)
            if perc is not None:
                data["expense_ratio"] = perc
                break

    # 6) Returns: try to locate a table row "Fund returns" in "Returns and rankings"
    # Example row:
    # "| Fund returns | +19.0% | +20.8% | +20.0% | +18.6% |"
    fund_returns_line = next(
        (l for l in lines if "Fund returns" in l and "%" in l), None
    )
    if fund_returns_line:
        # Extract all percentages from the row
        percents = re.findall(r"(-?\+?[0-9]+(?:\.[0-9]+)?)\s*%", fund_returns_line)
        # According to observed structure: columns are 3Y, 5Y, 10Y, All
        # but user requested 1Y/3Y/5Y/since inception. These Groww rows
        # may not directly give 1Y; we map what we can:
        if len(percents) >= 1:
            data["returns"]["three_year"] = float(percents[0]) / 100.0
        if len(percents) >= 2:
            data["returns"]["five_year"] = float(percents[1]) / 100.0
        # Map "All" column (last) as since inception surrogate, if available
        if len(percents) >= 4:
            data["returns"]["since_inception"] = float(percents[3]) / 100.0

    # 7) Top holdings – parse markdown-like table after "## Holdings"
    idx_holdings = _find_line_index(lines, "## Holdings")
    if idx_holdings is not None:
        # Expect header line like "| Name | Sector | Instruments | Assets |"
        i = idx_holdings + 1
        while i < len(lines):
            line = lines[i]
            if line.startswith("| Name ") and "|" in line:
                # Next line is separator, then multiple holding rows
                i += 2
                while i < len(lines):
                    row = lines[i]
                    if not row.startswith("|"):
                        break
                    cols = [c.strip() for c in row.strip("|").split("|")]
                    if len(cols) >= 4:
                        name_col = cols[0]
                        # Remove markdown link syntax if present: [Name](url)
                        name_match = re.search(r"\[([^\]]+)\]", name_col)
                        company_name = name_match.group(1) if name_match else name_col
                        sector = cols[1] or None
                        weight = _parse_percentage(cols[3])
                        data["top_holdings"].append(
                            {
                                "company_name": company_name,
                                "sector": sector,
                                "weight_percent": weight,
                            }
                        )
                    i += 1
                break
            i += 1

    # 8) Exit load – look under "### Exit Load" and capture following description lines
    idx_exit_heading = _find_line_index(lines, "### Exit Load")
    if idx_exit_heading is not None:
        exit_lines: List[str] = []
        i = idx_exit_heading + 1
        while i < len(lines):
            line = lines[i]
            # Stop at next heading
            if line.startswith("### "):
                break
            # Collect lines that mention "Exit load" or look like rules/dates
            if "Exit load" in line or re.search(r"\d{2} \w{3} \d{2,4}", line):
                exit_lines.append(line)
            i += 1
        if exit_lines:
            data["exit_load"] = " ".join(exit_lines)

    # 9) Tax info – if there is a specific tax section; otherwise fall back to generic explanation
    # Look for lines around the "Tax" glossary definition under "Understand terms"
    idx_tax_def = _find_line_index(lines, "##### Tax")
    if idx_tax_def is not None:
        tax_lines: List[str] = []
        i = idx_tax_def + 1
        while i < len(lines):
            line = lines[i]
            if line.startswith("##### "):  # next glossary term
                break
            tax_lines.append(line)
            i += 1
        if tax_lines:
            data["tax_info"] = " ".join(tax_lines)

    # 10) Description – take first meaningful overview paragraph after NAV/summary
    # As a heuristic, capture text between NAV block and "## Holdings" (bounded).
    description_lines: List[str] = []
    start_idx = idx_nav if idx_nav is not None else 0
    end_idx = idx_holdings if idx_holdings is not None else len(lines)
    for i in range(start_idx, end_idx):
        line = lines[i]
        # Skip obvious labels and headings, keep slightly longer text lines
        if (
            line.startswith("NAV:")
            or line.startswith("Min. for SIP")
            or line.startswith("Fund size")
            or line.startswith("Expense ratio")
            or line.startswith("### ")
            or line.startswith("## ")
            or len(line) < 40
        ):
            continue
        description_lines.append(line)
    if description_lines:
        data["description"] = " ".join(description_lines)

    return data


def fetch_and_extract(url: str) -> Dict[str, Any]:
    print(f"Fetching: {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n")
    record = extract_from_text(text, source_url=url)
    return record


def main() -> None:
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "funds.jsonl")

    with open(output_path, "w", encoding="utf-8") as f:
        for url in FUND_URLS:
            try:
                record = fetch_and_extract(url)
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            except Exception as e:
                # Log error and continue with other URLs
                print(f"Error processing {url}: {e}")

    print(f"Wrote extracted data to {output_path}")


if __name__ == "__main__":
    main()

