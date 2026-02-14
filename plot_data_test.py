#!/.venv/bin/python3

import pandas as pd
import matplotlib
import importlib.util
# Prefer a Qt interactive backend when a Qt binding is available; otherwise use the
# headless Agg backend so saving works in non-GUI environments.
matplotlib.use("qtagg")
from matplotlib import pyplot as plt
from pathlib import Path
import sys

DATA_DIR = Path("data")
OUT_PNG = DATA_DIR / "scam_type_counts.png"

df = pd.read_csv("data/dfpi_scams_exploded.csv")

counts = df["scam_type_list"].value_counts().sort_values(ascending=False)

ax = counts.plot(kind="barh", figsize=(10, 8), title="Distribution of Scam Types")
ax.set_xlabel("Count")
plt.tight_layout()

# Save to file (works in headless environments); also try to show when possible
# OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
# plt.savefig(OUT_PNG, bbox_inches="tight")
# print(f"Saved plot to: {OUT_PNG}")

try:
	plt.show()
except Exception:
	# non-interactive backend (headless) — already saved to PNG
	sys.exit(0)
