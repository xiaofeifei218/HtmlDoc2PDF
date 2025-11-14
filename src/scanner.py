"""
文件扫描器模块
负责扫描和过滤待转换的HTML文件
"""

from pathlib import Path
from typing import List, Set
from dataclasses import dataclass
import fnmatch
from urllib.parse import quote


@dataclass
class FileTask:
    """文件任务"""
    html_path: Path  # HTML文件路径(绝对路径)
    pdf_path: Path  # PDF输出路径(绝对路径)
    url: str  # 访问URL
    priority: int = 0  # 优先级(预留)

    def __str__(self):
        return f"{self.html_path.name} -> {self.pdf_path.name}"


class FileScanner:
    """文件扫描器"""

    def __init__(self, config):
        """
        初始化扫描器

        Args:
            config: Config对象
        """
        self.config = config
        self.input_dir = Path(config.input.directory).resolve()
        self.output_dir = Path(config.output.directory).resolve()

    def scan(self, base_url: str = "") -> List[FileTask]:
        """
        扫描文件

        Args:
            base_url: HTTP服务器的基础URL(如 http://localhost:8000)

        Returns:
            FileTask列表
        """
        # 收集所有匹配的HTML文件
        html_files = self._collect_html_files()

        # 过滤掉排除的文件
        html_files = self._apply_exclusions(html_files)

        # 如果不覆盖,过滤掉已存在的PDF
        if not self.config.output.overwrite:
            html_files = self._filter_existing(html_files)

        # 构建任务列表
        tasks = []
        for html_file in html_files:
            task = self._create_task(html_file, base_url)
            tasks.append(task)

        # 排序(按路径)
        tasks.sort(key=lambda t: str(t.html_path))

        return tasks

    def _collect_html_files(self) -> Set[Path]:
        """收集所有匹配include模式的HTML文件"""
        html_files = set()

        for pattern in self.config.input.include_patterns:
            if self.config.input.recursive:
                # 递归搜索
                matches = self.input_dir.rglob(pattern)
            else:
                # 非递归搜索
                matches = self.input_dir.glob(pattern)

            for match in matches:
                if match.is_file():
                    html_files.add(match.resolve())

        return html_files

    def _apply_exclusions(self, html_files: Set[Path]) -> Set[Path]:
        """应用排除规则"""
        if not self.config.input.exclude_patterns:
            return html_files

        filtered = set()

        for html_file in html_files:
            # 获取相对路径
            try:
                rel_path = html_file.relative_to(self.input_dir)
            except ValueError:
                # 如果不在输入目录下,跳过
                continue

            # 检查是否匹配排除模式
            excluded = False
            for pattern in self.config.input.exclude_patterns:
                if fnmatch.fnmatch(str(rel_path), pattern):
                    excluded = True
                    break

                # 也检查Unix风格的路径(用/分隔)
                unix_path = str(rel_path).replace('\\', '/')
                if fnmatch.fnmatch(unix_path, pattern):
                    excluded = True
                    break

            if not excluded:
                filtered.add(html_file)

        return filtered

    def _filter_existing(self, html_files: Set[Path]) -> Set[Path]:
        """过滤掉已存在的PDF"""
        filtered = set()

        for html_file in html_files:
            pdf_path = self._get_pdf_path(html_file)
            if not pdf_path.exists():
                filtered.add(html_file)

        return filtered

    def _get_pdf_path(self, html_path: Path) -> Path:
        """获取PDF输出路径"""
        if self.config.output.keep_structure:
            # 保持目录结构
            try:
                rel_path = html_path.relative_to(self.input_dir)
            except ValueError:
                # 如果不在输入目录下,直接使用文件名
                rel_path = Path(html_path.name)

            pdf_path = self.output_dir / rel_path.with_suffix('.pdf')
        else:
            # 平铺
            pdf_path = self.output_dir / html_path.with_suffix('.pdf').name

        return pdf_path

    def _create_task(self, html_path: Path, base_url: str) -> FileTask:
        """创建文件任务"""
        pdf_path = self._get_pdf_path(html_path)

        # 构建URL
        if base_url:
            # 使用HTTP服务器
            try:
                rel_path = html_path.relative_to(self.input_dir)
            except ValueError:
                rel_path = Path(html_path.name)

            # 转换为URL路径(使用正斜杠)
            url_path = str(rel_path).replace('\\', '/')
            # URL编码路径（特别是中文和特殊字符）
            # 对路径的每个部分分别编码，保留斜杠
            encoded_parts = [quote(part, safe='') for part in url_path.split('/')]
            encoded_path = '/'.join(encoded_parts)
            url = f"{base_url.rstrip('/')}/{encoded_path}"
        else:
            # 使用file://协议
            url = html_path.as_uri()

        return FileTask(
            html_path=html_path,
            pdf_path=pdf_path,
            url=url
        )


if __name__ == "__main__":
    # 测试代码
    from src.config import Config

    print("测试文件扫描器...")

    # 创建测试目录结构
    test_dir = Path("./test_scan")
    test_dir.mkdir(exist_ok=True)

    # 创建一些测试HTML文件
    (test_dir / "page1.html").write_text("<html><body>Page 1</body></html>")
    (test_dir / "page2.html").write_text("<html><body>Page 2</body></html>")

    subdir = test_dir / "subdir"
    subdir.mkdir(exist_ok=True)
    (subdir / "page3.html").write_text("<html><body>Page 3</body></html>")

    # 创建一个应该被排除的文件
    (subdir / "search.html").write_text("<html><body>Search</body></html>")

    print(f"✓ 测试文件已创建在: {test_dir}")

    # 创建配置
    config = Config()
    config.input.directory = str(test_dir)
    config.input.recursive = True
    config.input.include_patterns = ["**/*.html"]
    config.input.exclude_patterns = ["**/search.html"]
    config.output.directory = "./test_output"
    config.output.keep_structure = True

    # 扫描
    scanner = FileScanner(config)
    tasks = scanner.scan(base_url="http://localhost:8000")

    print(f"\n✓ 扫描完成,找到 {len(tasks)} 个文件:")
    test_dir_abs = test_dir.resolve()
    for i, task in enumerate(tasks, 1):
        try:
            rel = task.html_path.relative_to(test_dir_abs)
        except ValueError:
            rel = task.html_path.name
        print(f"  {i}. {rel}")
        print(f"     -> {task.pdf_path}")
        print(f"     URL: {task.url}")

    # 清理
    import shutil
    shutil.rmtree(test_dir)
    print(f"\n✓ 测试文件已清理")

    print("\n文件扫描器测试完成!")
