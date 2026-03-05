import json
import os
from typing import Any, Dict, List


DATA_DIR = os.path.dirname(__file__)
INPUT_PATH = os.path.join(DATA_DIR, "data", "funds.jsonl")
OUTPUT_PATH = os.path.join(DATA_DIR, "data", "funds_pretty.json")


def main() -> None:
    funds: List[Dict[str, Any]] = []
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            funds.append(json.loads(line))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        json.dump(funds, out, ensure_ascii=False, indent=2)

    print(f"Wrote pretty JSON array to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

