#!/usr/bin/env python

import argparse
import http.server
import json
import os

class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_PUT(self):
        path = self.translate_path(self.path)
        if path.endswith('/'):
            self.send_response(405, "Method Not Allowed")
            self.wfile.write("PUT not allowed on a directory\n".encode())
            return
        else:
            try:
                os.makedirs(os.path.dirname(path))
            except FileExistsError: pass
            length = int(self.headers['Content-Length'])
            with open(path, 'wb') as f:
                f.write(self.rfile.read(length))
            self.send_response(201, "Created")
            self.end_headers()
            self.wfile.write((os.path.split(path)[1] + " created\n").encode())

    def do_GET(self):
        data = {}
        data['id'] = 0
        json_response = json.dumps(data)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json_response.encode())
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', '-b', default='0.0.0.0', metavar='ADDRESS',
                        help='Specify alternate bind address '
                             '[default: all interfaces]')
    parser.add_argument('port', action='store',
                        default=8008, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 8000]')
    args = parser.parse_args()

    http.server.test(HandlerClass=HTTPRequestHandler, port=args.port, bind=args.bind)
