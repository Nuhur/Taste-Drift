CREATE TABLE IF NOT EXISTS streams (
    id integer PRIMARY KEY,
    track_id INTEGER REFERENCES tracks(id),
    ts TEXT,
    ms_played INTEGER
);

CREATE TABLE IF NOT EXISTS artists (
    id integer PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS albums (
    id integer PRIMARY KEY,
    name TEXT NOT NULL,
    artist_id INTEGER REFERENCES artists(id)
);

CREATE TABLE IF NOT EXISTS tracks (
    id integer PRIMARY KEY,
    name TEXT NOT NULL,
    album_id INTEGER REFERENCES albums(id)
);

CREATE TABLE IF NOT EXISTS genres (
    id integer PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS artist_genres (
    artist_id INTEGER REFERENCES artists(id),
    genre_id INTEGER REFERENCES genres(id),
    PRIMARY KEY (artist_id, genre_id)
);