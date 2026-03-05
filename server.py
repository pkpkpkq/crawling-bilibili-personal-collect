import http.server
import socketserver
import os

PORT = 8001
DIRECTORY = "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        os.chdir(DIRECTORY)
        print(f"Bilibili收藏报告服务器已启动")
        print(f"请在浏览器中打开 http://localhost:{PORT}")
        print("(按下 Ctrl+C 即可停止服务器)")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n服务器已停止。", flush=True)
except OSError as e:
    print(f"启动服务器失败: {e}")
    print(f"端口 {PORT} 可能已被占用，请检查并关闭占用该端口的程序后重试。")
