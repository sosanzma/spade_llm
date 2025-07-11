#!/usr/bin/env python3
"""Quick start script for the Human Expert web interface."""

import sys
import os
from .web_server import run_server


def main():
    """Start the Human Expert web interface server."""
    print("SPADE LLM - Human Expert Web Interface")
    print("=" * 40)
    
    # Get port from command line or use default
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid port number '{sys.argv[1]}'")
            sys.exit(1)
    
    print(f"\nStarting server on port {port}...")
    print(f"Open http://localhost:{port} in your browser")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        run_server(port)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
