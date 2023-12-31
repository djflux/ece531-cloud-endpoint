#!/usr/bin/env python

import argparse
import http.server
import json
import os
import syslog

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

    def do_POST(self):
        content_length = 0
        content_length = int(self.headers.get("Content-Length"))
        body = self.rfile.read(content_length)
        syslog.syslog(body.decode())
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', '-b', default='0.0.0.0', metavar='ADDRESS',
                        help='Specify alternate bind address '
                             '[default: all interfaces]')
    parser.add_argument('port', action='store',
                        default=8008, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 8008]')
    args = parser.parse_args()

    HTTPRequestHandler.server_version = "ECE531Server/0.0.1"
    HTTPRequestHandler.sys_version    = ""

    http.server.test(HandlerClass=HTTPRequestHandler, port=args.port, bind=args.bind)
