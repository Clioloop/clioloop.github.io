import http.server
import os
import socket
import mimetypes

os.chdir(os.path.dirname(os.path.abspath(__file__)))

mimetypes.add_type('video/mp4', '.mp4')

class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.translate_path(self.path)
        if os.path.isfile(path):
            self.send_head_range(path)
        else:
            super().do_GET()

    def send_head_range(self, path):
        f = None
        try:
            f = open(path, 'rb')
            fs = os.fstat(f.fileno())
            file_size = fs.st_size
            content_type = self.guess_type(path)

            range_header = self.headers.get('Range')
            if range_header:
                start, end = 0, file_size - 1
                range_match = range_header.strip().startswith('bytes=')
                if range_match:
                    range_val = range_header.strip()[6:]
                    parts = range_val.split('-')
                    start = int(parts[0]) if parts[0] else 0
                    end = int(parts[1]) if parts[1] else file_size - 1
                    if start >= file_size:
                        self.send_error(416)
                        return
                    if end >= file_size:
                        end = file_size - 1

                self.send_response(206)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Content-Length', str(end - start + 1))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                f.seek(start)
                remaining = end - start + 1
                while remaining:
                    chunk_size = min(65536, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    self.wfile.write(data)
                    remaining -= len(data)
                return

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(file_size))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            while True:
                data = f.read(65536)
                if not data:
                    break
                self.wfile.write(data)
        finally:
            if f:
                f.close()

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8080
    server = http.server.HTTPServer((host, port), RangeRequestHandler)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    print(f'Serving at http://{ip}:{port}')
    print(f'On your network: http://{ip}:{port}')
    print('Press Ctrl+C to stop')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
