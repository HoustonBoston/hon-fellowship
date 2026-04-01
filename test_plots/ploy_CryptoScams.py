"""
Test the plotting of crypto scams data.
"""

import matplotlib.pyplot as plt
import pandas as pd

# Convert to DataFrame
df = pd.read_json("C:\\Users\\myhor\\projects\\hon-fellowship\\CryptoScams\\data\\filtered_r_CryptoScams_2020-2025_posts.jsonl", lines=True)
df["date"] = pd.to_datetime(df["date"], errors="coerce")  # Convert date to datetime, handle errors
df = df.dropna(subset=["date"])  # Drop rows where date conversion failed

df.plot(x="date", y="ups", kind="line", title="Ups over Time for Crypto Scams Posts")
plt.xlabel("Date")
plt.ylabel("Ups")
plt.xticks(rotation=45)

plt.show()
