"""Taste Drift analysis: how has my genre mix changed over time?

Reads the SQLite database built by db.py / etl.py / enrich.py, prints a few
summary tables and saves two charts to charts/.
"""
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd

DB_PATH = "data/processed/taste_drift.db"
MIN_MS_PLAYED = 30_000   # ignore plays under 30s (skips / accidental plays)
TOP_N_DRIFT = 6          # genres shown on the drift chart

# Last.fm spells some genres two ways; merge them
ALIASES = {"hip-hop": "hip hop", "rnb": "r&b", "kpop": "k-pop"}

# Umbrella tags that sit on almost every artist; left off the drift chart
# because they hide the sub-genre changes
UMBRELLA = {"rap", "hip hop"}


SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_MUTED = "#52514e"
GRID = "#e1e0d9"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]


def load_plays(conn):
    """One row per play, with its artist and year/quarter."""
    plays = pd.read_sql(
        """
        SELECT s.ts, s.ms_played, ar.id AS artist_id, ar.name AS artist
        FROM streams s
        JOIN tracks t   ON s.track_id = t.id
        JOIN albums al  ON t.album_id = al.id
        JOIN artists ar ON al.artist_id = ar.id
        WHERE s.ms_played >= ?
        """,
        conn,
        params=(MIN_MS_PLAYED,),
    )
    plays["ts"] = pd.to_datetime(plays["ts"], utc=True)
    plays["year"] = plays["ts"].dt.year
    plays["quarter"] = plays["ts"].dt.tz_localize(None).dt.to_period("Q").astype(str)
    return plays


def load_artist_genres(conn):
    ag = pd.read_sql(
        """
        SELECT ag.artist_id, g.name AS genre
        FROM artist_genres ag JOIN genres g ON ag.genre_id = g.id
        """,
        conn,
    )
    ag["genre"] = ag["genre"].replace(ALIASES)
    return ag.drop_duplicates()


def style_axes(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_MUTED, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def chart_top_genres(genre_plays, path):
    top = genre_plays.groupby("genre").size().sort_values(ascending=False).head(10)
    top = top.sort_values()  # biggest bar at the top of a horizontal chart

    fig, ax = plt.subplots(figsize=(8, 5), facecolor=SURFACE)
    ax.barh(top.index, top.values, color=SERIES[0], height=0.6)
    style_axes(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_title("Top 10 genres by plays", loc="left", color=INK, fontsize=13)
    ax.set_xlabel("Plays (30s or longer)", color=INK_MUTED)
    ax.tick_params(axis="y", colors=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.show()  #opens an interactive window; close it to continue
    plt.close(fig)


def chart_genre_drift(genre_plays, path):
    """Share of each quarter's genre-tagged plays that belong to each top genre."""
    specific = genre_plays[~genre_plays["genre"].isin(UMBRELLA)]
    top_genres = (
        specific.groupby("genre").size().sort_values(ascending=False)
        .head(TOP_N_DRIFT).index.tolist()
    )
    counts = genre_plays.groupby(["quarter", "genre"]).size().unstack(fill_value=0)
    share = counts[top_genres].div(
        genre_plays.drop_duplicates(["ts", "artist_id"]).groupby("quarter").size(),
        axis=0,
    ) * 100

    fig, ax = plt.subplots(figsize=(9, 5), facecolor=SURFACE)
    for color, genre in zip(SERIES, top_genres):
        ax.plot(share.index, share[genre], color=color, linewidth=2, marker="o",
                markersize=6, label=genre)
    style_axes(ax)
    ax.set_title("How my genre mix has drifted", loc="left", color=INK, fontsize=13)
    ax.set_ylabel("% of that quarter's plays", color=INK_MUTED)
    ax.set_ylim(0, share.values.max() * 1.15)
    ax.legend(frameon=False, labelcolor=INK, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, -0.1))
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.show()  #opens an interactive window; close it to continue
    plt.close(fig)
    return share


def main():
    conn = sqlite3.connect(DB_PATH)
    plays = load_plays(conn)
    artist_genres = load_artist_genres(conn)
    conn.close()

    #coverage-how much of my listening has a genre at all
    tagged_ids = set(artist_genres["artist_id"])
    coverage = plays["artist_id"].isin(tagged_ids).mean() * 100
    print(f"Plays analysed: {len(plays):,} (>= {MIN_MS_PLAYED // 1000}s each)")
    print(f"Plays with a genre: {coverage:.1f}%\n")

    #top artists per year
    print("Top 5 artists per year")
    for year, group in plays.groupby("year"):
        top = group["artist"].value_counts().head(5)
        print(f"  {year}: " + ", ".join(f"{a} ({n})" for a, n in top.items()))
    print()

    #one row per(play, genre)
    genre_plays = plays.merge(artist_genres, on="artist_id")

    top_genres = genre_plays.groupby("genre").size().sort_values(ascending=False).head(10)
    print("Top 10 genres overall")
    print(top_genres.to_string(), "\n")

    chart_top_genres(genre_plays, "charts/top_genres.png")
    share = chart_genre_drift(genre_plays, "charts/genre_drift.png")
    print("Genre share by quarter (%)")
    print(share.round(1).to_string())
    print("\nSaved charts/top_genres.png and charts/genre_drift.png")


if __name__ == "__main__":
    main()