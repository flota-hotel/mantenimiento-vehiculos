#!/usr/bin/env python3
"""
Preview Server para Sistema Vehicular
Sirve los archivos de dist/ en puerto 8080 para demostración
"""
import http.server
import socketserver
import os
import sys

# Cambiar al directorio dist
os.chdir('/home/user/webapp/dist')

PORT = 8080

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        sys.stdout.write(f"[{self.log_date_time_string()}] {format%args}\n")
        sys.stdout.flush()

if __name__ == "__main__":
    print(f"🚀 Starting Sistema Vehicular Preview Server on port {PORT}")
    print(f"📁 Serving files from: {os.getcwd()}")
    sys.stdout.flush()
    
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
        print(f"✅ Server running at http://0.0.0.0:{PORT}")
        print("🔗 Use GetServiceUrl tool to get public URL")
        sys.stdout.flush()
        httpd.serve_forever()