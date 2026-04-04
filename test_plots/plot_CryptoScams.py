"""
Test the plotting of crypto scams data.
"""

import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

CDIR = Path(__file__).resolve().parent
print(CDIR)

# Convert to DataFrame
df = pd.read_json(CDIR.parent / "CryptoScams" / "data" / "filtered_r_CryptoScams_2020-2025_posts.jsonl", lines=True)

def plot_yearx_county(df):
    df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year  # Convert date to year, handle errors
    df = df.dropna(subset=["year"])  # Drop rows where date conversion failed

    # Group by year and sum of ups for that year
    df = df.groupby("year")["ups"].sum()

    # Print the first few rows to verify the data
    print(df.head())

    # Plot configs
    df.plot(x="year", y="ups", kind="bar", title="Ups over Time for Crypto Scams Posts")
    plt.xlabel("Year")
    plt.ylabel("Ups")
    plt.xticks(rotation=45)

    plt.show()

if __name__ == "__main__":
    plot_yearx_county(df)
