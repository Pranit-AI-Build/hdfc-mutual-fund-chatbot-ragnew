import json
import os
from typing import Any, Dict, List, Optional


DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "funds.jsonl")


def _load_funds() -> List[Dict[str, Any]]:
    """Load all fund records from funds.jsonl."""
    funds: List[Dict[str, Any]] = []
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"Data file not found at {DATA_FILE}. "
            "Run extract_groww_hdfc.py first to generate it."
        )
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            funds.append(json.loads(line))
    return funds


def get_fund_by_name(name_substring: str) -> Optional[Dict[str, Any]]:
    """
    Return the first fund whose scheme_name contains the given substring
    (case-insensitive), or None if not found.
    """
    needle = name_substring.lower()
    for fund in _load_funds():
        scheme_name = (fund.get("scheme_name") or "").lower()
        if needle in scheme_name:
            return fund
    return None


def list_funds() -> List[str]:
    """Return a list of all scheme names in the data file."""
    return [fund.get("scheme_name", "") for fund in _load_funds()]


def pretty_print_fund(fund: Dict[str, Any]) -> None:
    """Print key details of a single fund to the console."""
    if not fund:
        print("No fund data.")
        return
    print(f"Scheme name: {fund.get('scheme_name')}")
    print(f"Source URL:  {fund.get('source_url')}")
    print()
    print(f"NAV:         {fund.get('nav')} (as of {fund.get('nav_date')})")
    print(f"Min SIP:     {fund.get('min_sip_amount')}")
    print(f"Fund size:   {fund.get('fund_size')}")
    print(f"Expense:     {fund.get('expense_ratio')}")
    print()
    print("Returns (decimal, e.g. 0.12 = 12%):")
    print(f"  1Y:        {fund.get('returns', {}).get('one_year')}")
    print(f"  3Y:        {fund.get('returns', {}).get('three_year')}")
    print(f"  5Y:        {fund.get('returns', {}).get('five_year')}")
    print(f"  Since inc: {fund.get('returns', {}).get('since_inception')}")
    print()
    print("Top holdings:")
    for holding in (fund.get("top_holdings") or [])[:10]:
        print(
            f"  - {holding.get('company_name')} "
            f"({holding.get('sector')}): {holding.get('weight_percent')}"
        )
    print()
    print("Exit load:")
    print(f"  {fund.get('exit_load')}")
    print()
    print("Tax info (truncated):")
    tax = fund.get("tax_info") or ""
    print(f"  {tax[:300]}{'...' if len(tax) > 300 else ''}")


if __name__ == "__main__":
    # Simple CLI usage:
    import argparse

    parser = argparse.ArgumentParser(description="Query mutual fund data from funds.jsonl")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all scheme names",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Case-insensitive substring to search in scheme_name",
    )
    args = parser.parse_args()

    if args.list:
        for n in list_funds():
            print(n)
    elif args.name:
        fund = get_fund_by_name(args.name)
        if fund is None:
            print(f"No fund found matching: {args.name}")
        else:
            pretty_print_fund(fund)
    else:
        parser.print_help()

