import json
import sqlite3
import os



db_path = "data/processed/taste_drift.db"
raw_dir = "data/raw"


def get_or_create_artist(connection, artist_name):
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM artists WHERE name = ?", (artist_name,))
    result = cursor.fetchone()

    if result:
        return result[0]  # Return the existing artist ID
    else:
        cursor.execute("INSERT INTO artists (name) VALUES (?)", (artist_name,))
        connection.commit()
        return cursor.lastrowid  # Return the new artist ID



def get_or_create_album(connection, album_name, artist_id):
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM albums WHERE name = ? AND artist_id = ?", (album_name, artist_id))
    result = cursor.fetchone()

    if result:
        return result[0]  # Return the existing album ID
    else:
        cursor.execute("INSERT INTO albums (name, artist_id) VALUES (?, ?)", (album_name, artist_id))
        connection.commit()
        return cursor.lastrowid  # Return the new album ID



def get_or_create_track(connection, track_name, album_id):
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM tracks WHERE name = ? AND album_id = ?", (track_name, album_id))
    result = cursor.fetchone()

    if result:
        return result[0]  # Return the existing track ID
    else:
        cursor.execute("INSERT INTO tracks (name, album_id) VALUES (?, ?)", (track_name, album_id))
        connection.commit()
        return cursor.lastrowid  # Return the new track ID


def load_file(connection, filePath):
    with open(filePath, "r", encoding="utf-8") as f:
        records = json.load(f)

        for data in records:
            track_name = data.get("master_metadata_track_name")
            if track_name is None:
                continue  # Skip if track name is missing

            artist_name = data.get("master_metadata_album_artist_name")
            album_name = data.get("master_metadata_album_album_name")
            ts = data.get("ts")
            ms_played = data.get("ms_played")

            artst_id = get_or_create_artist(connection, artist_name)
            album_id = get_or_create_album(connection, album_name, artst_id)
            track_id = get_or_create_track(connection, track_name, album_id)

            connection.execute(
                "INSERT INTO streams (track_id, ts, ms_played) VALUES (?, ?, ?)",
                (track_id, ts, ms_played),
            )



def main():
    connection = sqlite3.connect(db_path)

    for file_name in os.listdir(raw_dir):
        if file_name.endswith(".json") and "Audio" in file_name:
            file_path = os.path.join(raw_dir, file_name)
            print(f"Loading{file_path} ...")
            load_file(connection, file_path)
            connection.commit()

    connection.close()
    print("ETL process completed successfully.") # extract, transform, and load data into the database



if __name__ == "__main__":
    main()