import matplotlib.pyplot as plt
import pandas as pd

def techniquex_county(df: pd.DataFrame, title: str):
    """Bar plot of technique count for all years"""

    # Group by technique and count occurrences
    df = df.groupby("technique")["technique"].count()

    # Print the first few rows to verify the data
    print(df.head())

    # Plot configs
    df.plot(x="technique", y="technique", kind="bar", title=title)
    plt.xlabel("Technique")
    plt.ylabel("Count")
    plt.xticks(rotation=45, fontsize=7)
    plt.yticks(fontsize=7)

    plt.show()

def technique_county_overtimex(df: pd.DataFrame, title: str):
    
    """Multi-line plot of technique count for each year"""
    
    # Group by year and technique, count occurrences for each technique, and unstack for plotting
    yearly = df.groupby(["year", "technique"]).size().unstack(fill_value=0)
    yearly.index = yearly.index.astype(int)  # Ensure the index is of type int for plotting

    ax = yearly.plot(
        kind="line", 
        title=title,
        figsize=(6, 3),
    )
    ax.title.set_fontsize(7)

    ax.set_xlabel("Year").set_fontsize(8)
    # Set x-ticks to the years and rotate them for better readability
    ax.set_xticks(yearly.index)  
    ax.set_xticklabels(yearly.index, rotation=45, fontsize=5)
    ax.set_ylabel("Count").set_fontsize(8)
    plt.yticks(fontsize=7)

    ax.legend(
        title="Technique",
        fontsize=7,
        title_fontsize=8,
        prop={"size": 6}    # Keep the legend smaller
    )

    plt.show()
