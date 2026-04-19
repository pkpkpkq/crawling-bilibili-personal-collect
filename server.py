import http.server
import socketserver

PORT = 8001
DIRECTORY = "."


class SafeHandler(http.server.SimpleHTTPRequestHandler):
    """只允许访问报告相关文件，阻止敏感文件泄露"""

    ALLOWED_PREFIXES = ("/html_report/", "/cache/", "/index.html")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        if not any(self.path.startswith(p) for p in self.ALLOWED_PREFIXES):
            self.send_error(403, "Forbidden")
            return
        super().do_GET()


def main():
    try:
        with socketserver.TCPServer(("", PORT), SafeHandler) as httpd:
            print("Bilibili收藏报告服务器已启动")
            print(f"请在浏览器中打开 http://localhost:{PORT}")
            print("(按下 Ctrl+C 即可停止服务器)")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止。", flush=True)
    except OSError as e:
        print(f"启动服务器失败: {e}")
        print(f"端口 {PORT} 可能已被占用，请检查并关闭占用该端口的程序后重试。")


if __name__ == "__main__":
    main()
