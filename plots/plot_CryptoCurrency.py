"""
Test the plotting of crypto scams data.
"""

import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

CDIR = Path(__file__).resolve().parent
print(CDIR)

# Convert to DataFrame
df = pd.read_json(CDIR.parent / "CryptoCurrency" / "data" / "filtered_r_CryptoCurrency_2020-2025_posts_with_technique.jsonl", lines=True)

def plot_yearx_county(df):
    df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year  # Convert date to year, handle errors
    df = df.dropna(subset=["year"])  # Drop rows where date conversion failed

    # Group by technique and count occurrences
    df = df.groupby("technique")["technique"].count()

    # Print the first few rows to verify the data
    print(df.head())

    # Plot configs
    df.plot(x="technique", y="technique", kind="bar", title="Technique Count over Time for Crypto Currency Posts")
    plt.xlabel("Technique")
    plt.ylabel("Count")
    plt.xticks(rotation=45)

    plt.show()

if __name__ == "__main__":
    plot_yearx_county(df)
