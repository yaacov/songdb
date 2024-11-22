# Songs Database

This project provides a simple HTTP server that allows you to manage a songs database using an HTTPS REST API. The server supports adding, retrieving, searching, and deleting songs from the database. Songs are stored with metadata, and a similarity search feature is included to find related songs.

## Project Structure
```
project_root/
├── app/
│   ├── __init__.py
│   ├── db.py
│   ├── embeddings.py
│   ├── handlers.py
├── songs/
│   ├── sample_songs.py
├── static/
│   ├── index.html
├── server.py
├── requirements.txt
├── key.pem
├── cert.pem
├── README.md
```

## Requirements
- Python 3.8+
- Install dependencies using:
  ```sh
  pip install -r requirements.txt
  ```
- Generate or obtain `key.pem` and `cert.pem` for HTTPS.
  ```sh
  openssl genrsa -out key.pem 2048
  openssl req -new -key key.pem -out csr.pem
  openssl x509 -req -days 365 -in csr.pem -signkey key.pem -out cert.pem
  ```

## Running the Server
Run the server with:
```sh
python server.py
```
The server will start on port `8000` and will be accessible using HTTPS.

## API Endpoints
### Add a Song
**Endpoint:** `/song`
- **Method:** `POST`
- **Description:** Adds a new song to the database.

### Get a Song
**Endpoint:** `/song?hash=<song_hash>`
- **Method:** `GET`
- **Description:** Retrieves a song by its hash.

### Search Songs
**Endpoint:** `/search`
- **Method:** `POST`
- **Description:** Searches for songs similar to a query.

### Delete a Song
**Endpoint:** `/song?hash=<song_hash>`
- **Method:** `DELETE`
- **Description:** Deletes a song by its hash.

## Prefill the Database with Sample Songs
The project includes an example file `songs/sample_songs.py` that contains a list of sample songs. When you run the server, the database will be prefilled with these songs automatically.

## Demo HTML search
For a demo search page, start the server and then open the page https://localhost:8000/ on a web btrowser.

## Example Usage
### Prefill the Database
When you run `server.py`, it will automatically prefill the database with the sample songs:
```python
# server.py
from app.db import create_tables, insert_songs
from songs.sample_songs import songs

create_tables()
insert_songs(songs)
```

### Search for a Song
To search for a song, send a POST request to `/search` with a JSON body:
```json
{
  "query": "אהבה",
  "top_k": 3
}
```
You can also include optional filters like `artist`, `song`, `album`, or `year` to narrow down the search.

Example curl command:
```sh
curl -k -X POST https://localhost:8000/search -H "Content-Type: application/json" -d '{"query": "אהבה", "top_k": 3}' | jq
```
