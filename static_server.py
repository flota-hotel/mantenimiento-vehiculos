#!/usr/bin/env python3
"""
Servidor HTTP simple para servir archivos estáticos
"""
import http.server
import socketserver
import os
import sys

PORT = 3000
DIRECTORY = "/home/user/webapp"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        sys.stdout.write(f"{self.log_date_time_string()} - {format%args}\n")
        sys.stdout.flush()

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Servidor corriendo en puerto {PORT}")
        sys.stdout.flush()
        httpd.serve_forever()