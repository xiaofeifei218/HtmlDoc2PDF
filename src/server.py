"""
HTTP服务器模块
提供本地HTTP服务,解决资源路径问题
"""

import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional
import os

from src.utils import find_available_port, is_port_in_use


class SilentHTTPRequestHandler(SimpleHTTPRequestHandler):
    """静默的HTTP请求处理器(不输出访问日志)"""

    # 类变量,存储服务器根目录
    server_root = None

    def log_message(self, format, *args):
        """覆盖log_message方法,禁止输出日志"""
        pass

    def handle(self):
        """处理请求,捕获并静默处理连接错误"""
        try:
            super().handle()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            # 客户端主动断开连接(如Chrome/Playwright加载完资源后关闭连接)
            # 这是正常行为,静默处理
            pass
        except Exception:
            # 其他未预期的错误也静默处理,避免打断主程序
            pass

    def translate_path(self, path):
        """重写路径转换方法,使用指定的根目录"""
        # 调用父类方法获取路径
        path = super().translate_path(path)

        # 如果设置了server_root,则将路径重定向到该目录
        if self.server_root:
            # 获取相对路径
            relpath = os.path.relpath(path, os.getcwd())
            # 构建新的绝对路径
            path = os.path.join(self.server_root, relpath)

        return path


class LocalHTTPServer:
    """本地HTTP服务器"""

    def __init__(self, root_dir: str, port: int = 8000, auto_find_port: bool = True):
        """
        初始化HTTP服务器

        Args:
            root_dir: 服务器根目录
            port: 端口号
            auto_find_port: 如果端口被占用,是否自动查找可用端口
        """
        self.root_dir = Path(root_dir).resolve()
        self.requested_port = port
        self.port = port
        self.auto_find_port = auto_find_port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False

    def start(self) -> bool:
        """
        启动服务器

        Returns:
            是否启动成功
        """
        if self.running:
            return True

        # 检查端口
        if is_port_in_use(self.requested_port):
            if self.auto_find_port:
                new_port = find_available_port(self.requested_port)
                if new_port is None:
                    return False
                self.port = new_port
            else:
                return False

        try:
            # 设置请求处理器的服务器根目录
            SilentHTTPRequestHandler.server_root = str(self.root_dir)

            # 创建服务器
            self.server = HTTPServer(('localhost', self.port), SilentHTTPRequestHandler)

            # 在后台线程中运行
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()

            # 等待服务器启动
            time.sleep(0.5)

            self.running = True
            return True

        except Exception as e:
            print(f"启动HTTP服务器失败: {e}")
            return False

    def _run_server(self):
        """在后台运行服务器"""
        try:
            self.server.serve_forever()
        except Exception:
            pass

    def stop(self):
        """停止服务器"""
        if self.server and self.running:
            self.server.shutdown()
            self.server.server_close()
            self.running = False

            if self.thread:
                self.thread.join(timeout=2)

    def get_base_url(self) -> str:
        """获取基础URL"""
        return f"http://localhost:{self.port}"

    def build_url(self, file_path: Path) -> str:
        """
        构建文件的完整URL

        Args:
            file_path: 文件路径(可以是绝对或相对于root_dir的路径)

        Returns:
            完整URL
        """
        # 转换为绝对路径
        if not file_path.is_absolute():
            file_path = (self.root_dir / file_path).resolve()

        # 计算相对于root_dir的路径
        try:
            rel_path = file_path.relative_to(self.root_dir)
        except ValueError:
            # 如果文件不在root_dir下,只使用文件名
            rel_path = Path(file_path.name)

        # 构建URL(使用正斜杠)
        url_path = str(rel_path).replace('\\', '/')
        return f"{self.get_base_url()}/{url_path}"

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


if __name__ == "__main__":
    # 测试代码
    print("测试HTTP服务器...")

    # 创建测试HTML文件
    test_dir = Path("./test_server")
    test_dir.mkdir(exist_ok=True)

    test_html = test_dir / "test.html"
    test_html.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>测试页面</title>
</head>
<body>
    <h1>这是一个测试页面</h1>
    <p>用于测试HTTP服务器</p>
</body>
</html>
    """, encoding='utf-8')

    # 启动服务器
    print(f"启动HTTP服务器,根目录: {test_dir}")
    server = LocalHTTPServer(str(test_dir), port=8000, auto_find_port=True)

    if server.start():
        print(f"✓ 服务器启动成功,端口: {server.port}")
        print(f"✓ 基础URL: {server.get_base_url()}")

        # 构建URL
        url = server.build_url(test_html)
        print(f"✓ 测试文件URL: {url}")

        print("\n服务器运行中,等待5秒...")
        print(f"你可以在浏览器中访问: {url}")
        time.sleep(5)

        # 停止服务器
        server.stop()
        print("✓ 服务器已停止")

        # 清理测试文件
        test_html.unlink()
        test_dir.rmdir()
        print("✓ 测试文件已清理")

    else:
        print("✗ 服务器启动失败")

    print("\nHTTP服务器测试完成!")
