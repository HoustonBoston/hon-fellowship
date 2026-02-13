"""
Categorize DFPI crypto scam data by scam type.

The raw CSV has a `scam_type` column where multiple labels are often
concatenated without a delimiter (e.g. "Fraudulent Trading PlatformPig
Butchering Scam").  This script normalises those values, explodes
multi-label rows, and prints per-type counts.

Outputs
-------
data/scam_type_counts.csv        – count per scam type
data/dfpi_scams_exploded.csv     – one row per (record, scam_type) pair
"""

import re
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
INPUT = DATA_DIR / "dfpi_crypto_scam_data.csv"

# ── known scam-type labels (order matters: longest first so greedy
#    matching picks the right boundary) ──────────────────────────────
KNOWN_TYPES = [
    "Crypto Giveaway/Airdrop Scam",
    "Crypto Wallet Drainer Attack",
    "Fraudulent Trading Platform",
    "High Yield Investment Program",
    "Investment Group Scam",
    "Liquidity Mining Scam",
    "AI Investment Scam",
    "Bait and Switch Scam",
    "Pig Butchering Scam",
    "Romance Scam",
    "Rug Pull Scam",
    "Signal Selling Scam",
]

# Build a regex that matches any known type (longest-first to avoid
# partial matches).
_sorted = sorted(KNOWN_TYPES, key=len, reverse=True)
_pattern = re.compile("|".join(re.escape(t) for t in _sorted))


def split_scam_types(raw: str) -> list[str]:
    """Extract all known scam-type labels from a (possibly concatenated) string."""
    if pd.isna(raw):
        return []
    found = _pattern.findall(str(raw))
    return found if found else [str(raw).strip()]


def main():
    df = pd.read_csv(INPUT)
    print(f"Loaded {len(df)} rows from {INPUT.name}\n")

    # ── split & explode ────────────────────────────────────────────
    df["scam_type_list"] = df["scam_type"].apply(split_scam_types)
    exploded = df.explode("scam_type_list")

    # ── counts ─────────────────────────────────────────────────────
    counts = (
        exploded["scam_type_list"]
        .value_counts()
        .rename_axis("scam_type")
        .reset_index(name="count")
    )

    # add a total row to the counts table so the CSV includes the overall sum
    total = int(counts["count"].sum())
    total_row = pd.DataFrame([{"scam_type": "Total", "count": total}])
    counts_with_total = pd.concat([counts, total_row], ignore_index=True)

    print("=== Scam-type counts ===")
    print(counts_with_total.to_string(index=False))
    print(f"\nTotal labels (incl. multi-label): {total}")

    # ── save outputs ───────────────────────────────────────────────
    counts_with_total.to_csv(DATA_DIR / "scam_type_counts.csv", index=False)
    exploded.to_csv(DATA_DIR / "dfpi_scams_exploded.csv", index=False)
    print(f"\nSaved  {DATA_DIR / 'scam_type_counts.csv'}")
    print(f"Saved  {DATA_DIR / 'dfpi_scams_exploded.csv'}")


if __name__ == "__main__":
    main()
