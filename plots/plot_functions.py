import matplotlib.pyplot as plt
import pandas as pd

def techniquex_county(df: pd.DataFrame, title: str):
    """Bar plot of technique count for all years"""

    # Group by technique and count occurrences
    df = df.groupby("technique")["technique"].count()

    # Print the first few rows to verify the data
    print(df.head())
    
    # Plot configs
    ax = df.plot(x="technique", y="technique", kind="bar", title=title)
    ax.bar_label(ax.containers[0], fontsize=7)  # Add count labels on top of bars

    plt.xlabel("Technique")
    plt.ylabel("Count")
    plt.xticks(rotation=45, fontsize=7)
    plt.yticks(fontsize=7)

    plt.tight_layout()  # Adjust layout to prevent clipping of labels
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

    plt.tight_layout()
    plt.show()

def percent_technique(df: pd.DataFrame, title: str):

    import numpy as np

    """Pie chart of percentage of each technique for all years"""

    # Count occurences of each technique
    technique_counts = df['technique'].value_counts()

    _, ax = plt.subplots(figsize=(9, 5))  # Larger canvas so the pie can be bigger

    # wedges contains data for pie slice
    wedges, texts, autotexts = ax.pie(
        technique_counts,
        autopct='%.1f%%',  # Show percentage on the pie chart,
        radius=1.15,
    )

    # Style the percentage labels
    for autotext in autotexts:
        autotext.set_fontsize(8)  # Set font size for percentage labels

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))

        # Determine label position based on the angle
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = f"angle,angleA=0,angleB={ang}"

        label = f"{technique_counts.index[i]} ({technique_counts.iloc[i]})"

        ax.annotate(label, xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
                    horizontalalignment=horizontalalignment,
                    fontsize=7,
                    arrowprops=dict(arrowstyle="-", connectionstyle=connectionstyle))
        
    ax.set_title(title, pad=36)

    plt.tight_layout()  # Adjust layout to prevent clipping of labels
    plt.show()
