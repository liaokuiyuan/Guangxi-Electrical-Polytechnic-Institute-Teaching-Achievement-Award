#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地静态预览服务器（支持 HTTP Range / 断点与拖动进度条）

python -m http.server 不支持 Range 请求，导致本地预览视频时无法快进/拖动。
本脚本在标准库 SimpleHTTPRequestHandler 基础上增加单区间 Range 支持，
用法：

    python tools/serve.py            # 默认 8080 端口，根目录为项目根
    python tools/serve.py 8081       # 指定端口
    python tools/serve.py 8081 D:\\path\\to\\site

然后浏览器访问 http://127.0.0.1:8080/
"""
import os
import sys
import http.server
import socketserver
import re

BLOCK = 64 * 1024


class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        fs = os.fstat(f.fileno())
        file_len = fs.st_size
        ctype = self.guess_type(path)
        self._range = None

        range_header = self.headers.get("Range")
        if range_header:
            m = re.match(r"bytes=(\d*)-(\d*)\s*$", range_header.strip())
            if m and (m.group(1) or m.group(2)):
                start_s, end_s = m.group(1), m.group(2)
                if start_s == "":                      # bytes=-N （最后 N 字节）
                    start = max(0, file_len - int(end_s))
                    end = file_len - 1
                else:
                    start = int(start_s)
                    end = int(end_s) if end_s else file_len - 1
                end = min(end, file_len - 1)

                if start > end or start >= file_len:
                    self.send_response(416)
                    self.send_header("Content-Range", "bytes */%d" % file_len)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    f.close()
                    return None

                self._range = (start, end)
                self.send_response(206)
                self.send_header("Content-Type", ctype)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, file_len))
                self.send_header("Content-Length", str(end - start + 1))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.end_headers()
                f.seek(start)
                return f

        # 普通请求：完整内容 + 声明支持 Range
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(file_len))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def copyfile(self, source, outputfile):
        rng = getattr(self, "_range", None)
        if rng:
            start, end = rng
            remaining = end - start + 1
            while remaining > 0:
                chunk = source.read(min(BLOCK, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        else:
            super().copyfile(source, outputfile)

    def log_message(self, fmt, *args):
        # 精简日志：忽略 Range 造成的刷屏，只保留错误
        if args and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    root = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    handler = lambda *a, **kw: RangeHTTPRequestHandler(*a, directory=root, **kw)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), handler) as httpd:
        print("Serving %s at http://127.0.0.1:%d/  (Range supported)" % (root, port))
        httpd.serve_forever()


if __name__ == "__main__":
    main()
