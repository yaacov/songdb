import json
import sqlite3
import hashlib
from app.embeddings import generate_embedding


def get_connection(db_name="songs.db"):
    return sqlite3.connect(db_name)


def create_tables(db_name="songs.db"):
    conn = get_connection(db_name)
    cursor = conn.cursor()
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS songs (
        hash TEXT PRIMARY KEY,
        artist TEXT,
        song TEXT,
        album TEXT,
        year INTEGER,
        description TEXT,
        embedding TEXT
    )
    """
    )
    conn.commit()
    conn.close()


def generate_song_hash(song_data):
    """
    Generates a unique SHA-256 hash for a song based on its metadata.

    Args:
        song_data (dict): Dictionary containing song metadata with keys 'artist', 'song', 'album', 'year', and 'description'.

    Returns:
        str: SHA-256 hash representing the unique identity of the song.
    """
    song_string = f"{song_data.get('artist', '')}|{song_data.get('song', '')}|{song_data.get('album', '')}|{song_data.get('year', '')}|{song_data.get('description', '')}"
    return hashlib.sha256(song_string.encode("utf-8")).hexdigest()


def insert_songs(songs, db_name="songs.db"):
    """
    Inserts a list of songs into the SQLite database. Each song's metadata and embedding are stored.

    Args:
        songs (list): A list of dictionaries, where each dictionary contains metadata for a song, including 'artist', 'song', 'album', 'year', and 'description'.

    Raises:
        sqlite3.Error: If there is an issue with the database connection or insertion.
    """
    conn = get_connection(db_name)
    cursor = conn.cursor()

    for song in songs:
        song_hash = generate_song_hash(song)
        full_text = f"{song.get('song', '')}, {song.get('artist', '')}, {song.get('album', '')}, {song.get('year', '')}, {song.get('description', '')}"
        embedding = generate_embedding(full_text)
        embedding_str = json.dumps(embedding)

        try:
            cursor.execute(
                """
            INSERT INTO songs (hash, artist, song, album, year, description, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    song_hash,
                    song.get("artist", ""),
                    song.get("song", ""),
                    song.get("album", ""),
                    song.get("year", ""),
                    song.get("description", ""),
                    embedding_str,
                ),
            )
        except sqlite3.IntegrityError:
            # Ignore if the song already exists in the database
            pass

    conn.commit()
    conn.close()
