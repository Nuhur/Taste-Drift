"""Tag every artist in the database with genres from Last.fm.

Spotify no longer returns genres to new apps, and MusicBrainz is missing tags
for many artists, so genres come from Last.fm's crowd-sourced artist tags.

Each run rebuilds the genres and artist_genres tables from scratch, so the
data always comes from one consistent source.
"""
import os
import time
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("LASTFM_API_KEY")
DB_PATH = "data/processed/taste_drift.db"
API_URL = "https://ws.audioscrobbler.com/2.0/"

MIN_TAG_COUNT = 30   # Last.fm tag weight is 0-100; ignore weak tags
MAX_TAGS = 5         # keep the top few genres per artist
# Tags that describe the listener or place, not the music
NOT_GENRES = {
    "seen live", "favorites", "favourites", "favorite", "favourite",
    "awesome", "american", "british", "uk", "usa", "male vocalists",
    "female vocalists", "albums i own",
}


def get_artist_genres(artist_name, retries=3):
    """Return a list of genre names for an artist, [] if none, None on failure."""
    for attempt in range(retries):
        try:
            response = requests.get(
                API_URL,
                params={
                    "method": "artist.gettoptags",
                    "artist": artist_name,
                    "autocorrect": 1,
                    "api_key": API_KEY,
                    "format": "json",
                },
                timeout=15,
            )
        except requests.exceptions.RequestException:
            time.sleep(5 * (attempt + 1))
            continue
        if response.status_code in (429, 500, 502, 503, 504):
            time.sleep(5 * (attempt + 1))
            continue
        data = response.json()
        if "error" in data:  #artist not found
            return []
        tags = data.get("toptags", {}).get("tag", [])
        genres = [
            t["name"].lower()
            for t in tags
            if int(t["count"]) >= MIN_TAG_COUNT and t["name"].lower() not in NOT_GENRES
        ]
        return genres[:MAX_TAGS]
    print(f"  Skipping {artist_name} after {retries} tries")
    return None


def get_or_create_genre(connection, genre_name):
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM genres WHERE name = ?", (genre_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    cursor.execute("INSERT INTO genres (name) VALUES (?)", (genre_name,))
    return cursor.lastrowid


def link_artist_genre(connection, artist_id, genre_id):
    connection.execute(
        "INSERT OR IGNORE INTO artist_genres (artist_id, genre_id) VALUES (?, ?)",
        (artist_id, genre_id),
    )


def main():
    if not API_KEY:
        raise SystemExit("LASTFM_API_KEY is missing - add it to your .env file")

    connection = sqlite3.connect(DB_PATH)
    connection.execute("DELETE FROM artist_genres")
    connection.execute("DELETE FROM genres")
    connection.commit()

    artists = connection.execute("SELECT id, name FROM artists").fetchall()
    print(f"{len(artists)} artists to enrich")

    no_genres = 0
    for i, (artist_id, artist_name) in enumerate(artists, start=1):
        genres = get_artist_genres(artist_name)
        if genres is None:
            continue
        if not genres:
            no_genres += 1
        for genre_name in genres:
            genre_id = get_or_create_genre(connection, genre_name)
            link_artist_genre(connection, artist_id, genre_id)
        connection.commit()
        print(f"[{i}/{len(artists)}] {artist_name}: {genres}")
        time.sleep(0.25)  #stay under Last.fms rate limit

    connection.close()
    print(f"Enrichment complete. {no_genres} artists had no usable genres.")


if __name__ == "__main__":
    main()
