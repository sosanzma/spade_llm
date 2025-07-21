"""Simple web server for the Human Expert interface."""

import logging
import os
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

logger = logging.getLogger("spade_llm.human_interface.web_server")


class CORSRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers."""

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


def run_server(port=8080, directory=None):
    """
    Run a simple HTTP server for the Human Expert web interface.

    Args:
        port: Port to run the server on (default: 8080)
        directory: Directory to serve files from (default: web_client folder)
    """
    if directory is None:
        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        directory = os.path.join(current_dir, "web_client")

    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Change to the directory
    os.chdir(directory)

    # Create server
    handler = partial(CORSRequestHandler, directory=directory)
    httpd = HTTPServer(("localhost", port), handler)

    logger.info(f"Human Expert interface running at http://localhost:{port}")
    logger.info(f"Serving files from: {directory}")
    logger.info("Press Ctrl+C to stop")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        httpd.shutdown()


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
