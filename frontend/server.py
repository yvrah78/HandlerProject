#!/usr/bin/env python3
"""
Simple HTTP server to serve the Project Handler frontend.
"""
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys

class CORSRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support."""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


def run_server(port=3000):
    """Run the HTTP server."""
    # Change to public directory
    public_dir = os.path.join(os.path.dirname(__file__), 'public')
    os.chdir(public_dir)

    # Get local IP
    import subprocess
    try:
        local_ip = subprocess.check_output(['hostname', '-I']).decode().strip().split()[0]
    except:
        local_ip = '127.0.0.1'

    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║       PROJECT HANDLER - Frontend Server                  ║
╚══════════════════════════════════════════════════════════╝

✅ Frontend server running at:

   🖥️  Local:   http://localhost:{port}
   📱 Remote:  http://{local_ip}:{port}

📝 Instructions:
   1. Make sure the API is running at http://{local_ip}:8000
   2. Open the URL in your browser
   3. For iPad/mobile: use the Remote URL
   4. Explore the dashboard and test the system

🛑 Press Ctrl+C to stop the server

""")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        sys.exit(0)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    run_server(port)
