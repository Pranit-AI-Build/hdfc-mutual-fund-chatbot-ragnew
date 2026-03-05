import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional


DATA_DIR = os.path.dirname(__file__)
INPUT_PATH = os.path.join(DATA_DIR, "data", "funds.jsonl")
OUTPUT_PATH = os.path.join(DATA_DIR, "data", "funds.normalized.jsonl")


def _clean_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    # Collapse whitespace and strip
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned or None


def _extract_risk_level(description: str) -> Optional[str]:
    """
    Look for patterns like:
    'is rated Very High risk.'
    """
    m = re.search(r"is rated ([A-Za-z ]+?) risk", description)
    if m:
        return m.group(1).strip()
    return None


def _extract_fund_manager_names(description: str) -> List[str]:
    """
    Very simple heuristic:
    Capture names before 'is the Current Fund Manager of'.
    """
    names: List[str] = []
    for m in re.finditer(
        r"([A-Z][A-Za-z .']+?) is the Current Fund Manager of", description
    ):
        name = m.group(1).strip()
        if name and name not in names:
            names.append(name)
    return names


def _extract_exit_load(existing_exit_load: Optional[str], description: str) -> Optional[str]:
    """
    Use existing exit_load value if present; otherwise, try to collect
    sentences starting with 'Exit load'.
    """
    if existing_exit_load:
        return _clean_text(existing_exit_load)

    # Find phrases starting with 'Exit load'
    matches = re.findall(r"(Exit load[^.]*\.)", description)
    if not matches:
        return None
    # Deduplicate while preserving order
    seen = set()
    parts: List[str] = []
    for m in matches:
        part = _clean_text(m)
        if part and part not in seen:
            seen.add(part)
            parts.append(part)
    return " ".join(parts) if parts else None


def _extract_tax_info(description: str) -> Optional[str]:
    """
    Extract a concise generic tax explanation if present.
    We look for the glossary-like sentence starting with 'A percentage of your capital gains...'.
    """
    m = re.search(
        r"(A percentage of your capital gains payable to the government .*?type of fund\.)",
        description,
    )
    if m:
        return _clean_text(m.group(1))
    return None


def _normalize_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    # Description may only exist in the original extractor output
    description = raw.get("description") or ""
    description = _clean_text(description) or ""

    risk_level = _extract_risk_level(description)
    fund_managers = _extract_fund_manager_names(description)
    exit_load = _extract_exit_load(raw.get("exit_load"), description)
    tax_info = _extract_tax_info(description)

    # Fund size: handle both original structured form and already-normalized string
    fund_size_raw = raw.get("fund_size")
    if isinstance(fund_size_raw, dict):
        amount = fund_size_raw.get("amount")
        unit = fund_size_raw.get("unit")
        currency = fund_size_raw.get("currency") or "INR"
        if amount is not None:
            if unit:
                fund_size_str = f"{amount} {unit} {currency}"
            else:
                fund_size_str = f"{amount} {currency}"
        else:
            fund_size_str = None
    else:
        # Already a simple string or None
        fund_size_str = fund_size_raw

    # Clean fund name: drop trailing '- NAV, Mutual Fund Performance & Portfolio'
    raw_name = raw.get("scheme_name") or raw.get("fund_name") or ""
    fund_name = re.sub(
        r"\s*-\s*NAV, Mutual Fund Performance & Portfolio\s*$", "", raw_name
    ).strip()

    # Returns mapping to new keys, using numbers or null.
    # Handle both original keys (one_year, three_year, ...) and already-normalized keys (1_year, 3_year, ...)
    returns_raw = raw.get("returns") or {}
    if "one_year" in returns_raw:
        returns_norm = {
            "1_year": returns_raw.get("one_year"),
            "3_year": returns_raw.get("three_year"),
            "5_year": returns_raw.get("five_year"),
            "since_inception": returns_raw.get("since_inception"),
        }
    else:
        returns_norm = {
            "1_year": returns_raw.get("1_year"),
            "3_year": returns_raw.get("3_year"),
            "5_year": returns_raw.get("5_year"),
            "since_inception": returns_raw.get("since_inception"),
        }

    # Top holdings: flatten to company/percentage only, keep as array (possibly empty)
    top_holdings_raw = raw.get("top_holdings") or []
    top_holdings_norm = []
    for h in top_holdings_raw:
        top_holdings_norm.append(
            {
                "company": _clean_text(h.get("company_name")),
                "percentage": h.get("weight_percent"),
            }
        )

    # Holding analysis: keep as object; clean raw_text if present
    holding_analysis_raw = raw.get("holding_analysis") or {}
    if "raw_text" in holding_analysis_raw:
        holding_analysis_raw["raw_text"] = _clean_text(holding_analysis_raw["raw_text"])

    # Ensure containers follow the requested schema:
    # - fund_managers: always a list (possibly empty)
    # - top_holdings: always a list (possibly empty)
    # - holding_analysis: always an object/dict (possibly empty)
    fund_managers_final = fund_managers if fund_managers is not None else []
    top_holdings_final = top_holdings_norm if top_holdings_norm is not None else []
    holding_analysis_final = holding_analysis_raw if holding_analysis_raw is not None else {}

    normalized = {
        "fund_name": fund_name or None,
        "source_url": raw.get("source_url") or None,
        "nav": raw.get("nav"),
        "nav_date": raw.get("nav_date") or None,
        "minimum_sip": raw.get("min_sip_amount"),
        "fund_size": fund_size_str,
        "expense_ratio": raw.get("expense_ratio"),
        "risk_level": risk_level,
        "fund_managers": fund_managers_final,
        "returns": returns_norm,
        "top_holdings": top_holdings_final,
        "holding_analysis": holding_analysis_final,
        "exit_load": exit_load,
        "tax_info": tax_info,
    }

    return normalized


def _iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main() -> None:
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"Input JSONL not found at {INPUT_PATH}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out_f:
        for raw in _iter_jsonl(INPUT_PATH):
            norm = _normalize_record(raw)
            out_f.write(json.dumps(norm, ensure_ascii=False) + "\n")

    # Replace original file atomically
    os.replace(OUTPUT_PATH, INPUT_PATH)
    print(f"Normalized data written back to {INPUT_PATH}")


if __name__ == "__main__":
    main()

