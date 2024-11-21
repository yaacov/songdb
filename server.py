import ssl
from http.server import HTTPServer
from app.handlers import SongRequestHandler
from app.db import create_tables, insert_songs
from songs.sample_songs import songs


def run_server():
    create_tables()

    # Insert demo songs list
    insert_songs(songs)

    server_address = ("", 8000)
    httpd = HTTPServer(server_address, SongRequestHandler)

    # Create an SSL context to wrap the socket for HTTPS
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    # Wrap the server socket with SSL
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    print("Starting HTTPS server on port 8000...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Server stopped.")


if __name__ == "__main__":
    run_server()
