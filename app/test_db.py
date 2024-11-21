import unittest
import os
from app.db import (
    get_connection,
    create_tables,
    generate_song_hash,
    insert_songs,
    generate_embedding,
)


class TestDatabaseFunctions(unittest.TestCase):
    TEST_DB = "test_songs.db"

    def setUp(self):
        # Override the database with a test one
        self.db_name = self.TEST_DB
        create_tables(self.db_name)

    def tearDown(self):
        # Remove the test database after each test
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_create_tables(self):
        # Test if the table was created successfully
        conn = get_connection(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='songs'"
        )
        table_exists = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(table_exists, "Table 'songs' should exist after creation.")

    def test_generate_song_hash(self):
        # Test generating a unique hash for a song
        song_data = {
            "artist": "Artist Name",
            "song": "Song Title",
            "album": "Album Name",
            "year": 2023,
            "description": "A great song.",
        }
        song_hash = generate_song_hash(song_data)
        self.assertIsInstance(song_hash, str, "Generated hash should be a string.")
        self.assertEqual(
            len(song_hash), 64, "SHA-256 hash should be 64 characters long."
        )

    def test_insert_songs(self):
        # Test inserting a list of songs into the database
        songs = [
            {
                "artist": "Artist 1",
                "song": "Song 1",
                "album": "Album 1",
                "year": 2023,
                "description": "First test song.",
            },
            {
                "artist": "Artist 2",
                "song": "Song 2",
                "album": "Album 2",
                "year": 2022,
                "description": "Second test song.",
            },
        ]
        insert_songs(songs, self.db_name)

        # Verify that the songs have been inserted
        conn = get_connection(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM songs")
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 2, "There should be two songs in the database.")
        for row in rows:
            self.assertEqual(len(row), 7, "Each row should have 7 columns.")

    def test_insert_duplicate_song(self):
        # Test inserting duplicate songs and ensuring no duplication in the DB
        song = {
            "artist": "Duplicate Artist",
            "song": "Duplicate Song",
            "album": "Duplicate Album",
            "year": 2021,
            "description": "This song will be inserted twice.",
        }
        insert_songs([song], self.db_name)
        insert_songs([song], self.db_name)  # Attempt to insert the same song again

        # Verify only one song exists
        conn = get_connection(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM songs WHERE artist = ?", ("Duplicate Artist",))
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(
            len(rows),
            1,
            "There should be only one instance of the duplicate song in the database.",
        )

    def test_generate_embedding(self):
        # Test if generate_embedding returns a list
        text = "Test song, Artist, Album, 2023, Description."
        embedding = generate_embedding(text)

        self.assertIsInstance(embedding, list, "Embedding should be a list.")
        self.assertTrue(
            all(isinstance(value, float) for value in embedding),
            "All elements in the embedding should be floats.",
        )


if __name__ == "__main__":
    unittest.main()
