import json
import mimetypes
import os
import sqlite3
import numpy as np
from http.server import BaseHTTPRequestHandler
from urllib.parse import unquote, urlparse, parse_qs
from app.db import generate_song_hash, get_connection
from app.embeddings import generate_embedding, perform_faiss_similarity_search

conn = get_connection()
cursor = conn.cursor()


class SongRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/song":
            self.handle_add_song()
        elif parsed_path.path == "/search":
            self.handle_search_songs()
        else:
            self.send_error(404, "Endpoint not found")

    def do_GET(self):
        parsed_path = urlparse(self.path)
        file_path = unquote(parsed_path.path.lstrip("/"))

        if parsed_path.path == "/":
            # Serve the static index.html for the root path
            file_path = "static/index.html"
        else:
            # Prepend static directory to look for files
            file_path = os.path.join("static", file_path)

        # Check if the file exists and serve it
        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.serve_file(file_path)
        elif parsed_path.path == "/song":
            # Handle specific /song endpoint
            self.handle_get_song()
        else:
            # File not found, return 404
            self.send_error(404, "File not found")

    def serve_file(self, file_path):
        """Serve a static file."""
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "text/html"
        
        try:
            with open(file_path, "rb") as file:
                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.end_headers()
                self.wfile.write(file.read())
        except Exception as e:
            self.send_error(500, f"Error serving file: {e}")

    def do_DELETE(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/song":
            self.handle_delete_song()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_add_song(self):
        """
        Handles the addition of a new song to the database.

        Reads the request body, parses JSON data, generates an embedding, and inserts the song into the database.
        Sends an appropriate response to the client.
        """
        # Read the content length and body
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)

        # Parse JSON data
        try:
            song_data = json.loads(post_data.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        # Generate song hash and embedding
        song_hash = generate_song_hash(song_data)
        full_text = f"{song_data.get('song', '')}, {song_data.get('artist', '')}, {song_data.get('album', '')}, {song_data.get('year', '')}, {song_data.get('description', '')}"
        embedding = generate_embedding(full_text)
        embedding_str = json.dumps(embedding)

        # Insert into database
        try:
            cursor.execute(
                """
            INSERT INTO songs (hash, artist, song, album, year, description, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    song_hash,
                    song_data.get("artist", ""),
                    song_data.get("song", ""),
                    song_data.get("album", ""),
                    song_data.get("year", None),
                    song_data.get("description", ""),
                    embedding_str,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            self.send_error(409, "Song already exists")
            return

        # Send response
        self._send_json_response(
            201, {"hash": song_hash, "message": "Song added successfully"}
        )

    def handle_get_song(self):
        """
        Handles retrieving a song from the database by its hash.

        Parses query parameters, fetches the song from the database, and sends the song details to the client.
        """
        # Parse query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        song_hash = query_params.get("hash", [None])[0]

        if not song_hash:
            self.send_error(400, "Missing song hash")
            return

        # Retrieve song from database
        cursor.execute(
            "SELECT hash, artist, song, album, year, description FROM songs WHERE hash = ?",
            (song_hash,),
        )
        row = cursor.fetchone()

        if row:
            song_hash_db, artist_db, song_name_db, album_db, year_db, description_db = (
                row
            )
            song_data = {
                "hash": song_hash_db,
                "artist": artist_db,
                "song": song_name_db,
                "album": album_db,
                "year": year_db,
                "description": description_db,
            }
            self._send_json_response(200, song_data)
        else:
            self.send_error(404, "Song not found")

    def handle_delete_song(self):
        """
        Handles deleting a song from the database by its hash.

        Parses query parameters, deletes the song from the database if it exists, and sends an appropriate response.
        """
        # Parse query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        song_hash = query_params.get("hash", [None])[0]

        if not song_hash:
            self.send_error(400, "Missing song hash")
            return

        # Check if song exists and delete it
        cursor.execute("SELECT hash FROM songs WHERE hash = ?", (song_hash,))
        row = cursor.fetchone()

        if row:
            cursor.execute("DELETE FROM songs WHERE hash = ?", (song_hash,))
            conn.commit()
            self._send_json_response(
                200, {"message": f"Song with hash {song_hash} has been deleted."}
            )
        else:
            self.send_error(404, "Song not found")

    def handle_search_songs(self):
        """
        Handles the search for songs based on the provided query and optional filters.
        """
        try:
            # Read and parse JSON data from request body
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            search_data = json.loads(post_data.decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON")
            return

        # Extract search parameters from parsed data
        query = search_data.get("query", "")
        top_k = search_data.get("top_k", 5)
        artist = search_data.get("artist", "")
        song = search_data.get("song", "")
        album = search_data.get("album", "")
        year = search_data.get("year", None)

        # Validate query parameter
        if not query:
            self.send_error(400, "Missing search query")
            return

        # Generate query embedding
        query_embedding = generate_embedding(query)

        # Construct SQL query with optional filters
        sql_query, params = self._construct_sql_query(artist, song, album, year)

        # Execute SQL query and retrieve results
        cursor.execute(sql_query, params)
        rows = cursor.fetchall()

        # Extract embeddings and metadata
        embeddings, metadata = self._extract_embeddings_and_metadata(rows)

        # Perform similarity search if embeddings are available
        if embeddings:
            response = perform_faiss_similarity_search(
                embeddings, metadata, query_embedding, top_k
            )
        else:
            response = []

        # Send response
        self._send_json_response(200, response)

    def _construct_sql_query(self, artist, song, album, year):
        """
        Constructs an SQL query with optional filters based on the provided parameters.
        """
        sql_query = "SELECT hash, artist, song, album, year, description, embedding FROM songs WHERE 1=1"
        params = []
        if artist:
            sql_query += " AND artist = ?"
            params.append(artist)
        if song:
            sql_query += " AND song = ?"
            params.append(song)
        if album:
            sql_query += " AND album = ?"
            params.append(album)
        if year:
            sql_query += " AND year = ?"
            params.append(year)
        return sql_query, params

    def _extract_embeddings_and_metadata(self, rows):
        """
        Extracts embeddings and metadata from the retrieved database rows.
        """
        embeddings = []
        metadata = []
        for row in rows:
            (
                song_hash,
                artist_name,
                song_name,
                album_name,
                year_value,
                description,
                embedding_str,
            ) = row
            embedding = np.array(json.loads(embedding_str), dtype=np.float32)
            embeddings.append(embedding)
            metadata.append(
                {
                    "hash": song_hash,
                    "artist": artist_name,
                    "song": song_name,
                    "album": album_name,
                    "year": year_value,
                    "description": description,
                }
            )
        return embeddings, metadata

    def _send_json_response(self, status_code, response_data):
        """
        Helper method to send a JSON response.

        Args:
            status_code (int): HTTP status code to send.
            response_data (dict): Dictionary containing response data to send as JSON.
        """
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
