"""
文件扫描器模块
负责扫描和过滤待转换的HTML文件
"""

from pathlib import Path
from typing import List, Set
from dataclasses import dataclass
import fnmatch
from urllib.parse import quote
from datetime import datetime

from src.md5_cache import MD5Cache


@dataclass
class FileTask:
    """文件任务"""
    html_path: Path  # HTML文件路径(绝对路径)
    pdf_path: Path  # PDF输出路径(绝对路径)
    url: str  # 访问URL
    priority: int = 0  # 优先级(预留)
    skip: bool = False  # 是否跳过(MD5未变化)
    md5: str = ""  # HTML文件的MD5值

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

        # 生成输出目录名: 输入目录的最末尾文件夹名 + "_PDF_" + 日期时间
        input_folder_name = self.input_dir.name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_folder_name = f"{input_folder_name}_PDF_{timestamp}"

        # 在配置的输出目录下创建新的子目录
        base_output_dir = Path(config.output.directory).resolve()
        self.output_dir = base_output_dir / output_folder_name

        # 初始化MD5缓存
        self.md5_cache = MD5Cache(self.output_dir)

        # 如果指定了复用目录，从该目录加载MD5缓存
        if config.output.reuse_from:
            reuse_path = Path(config.output.reuse_from).resolve()
            reuse_cache_file = reuse_path / MD5Cache.CACHE_FILENAME
            if reuse_cache_file.exists():
                self.md5_cache.load_cache(reuse_cache_file)
            else:
                print(f"警告: 复用目录的MD5缓存文件不存在: {reuse_cache_file}")

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

        # 如果不覆盖且不复用,过滤掉已存在的PDF
        # 复用模式下需要保留所有文件以便进行MD5检查
        if not self.config.output.overwrite and not self.config.output.reuse_from:
            html_files = self._filter_existing(html_files)

        # 构建任务列表
        tasks = []
        for html_file in html_files:
            task = self._create_task(html_file, base_url)
            tasks.append(task)

        # 排序(按路径)
        tasks.sort(key=lambda t: str(t.html_path))

        # 解决平铺模式下的路径冲突
        tasks = self._resolve_path_conflicts(tasks)

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
            # 平铺 - 使用路径前缀避免同名文件冲突
            try:
                rel_path = html_path.relative_to(self.input_dir)
            except ValueError:
                rel_path = Path(html_path.name)

            # 将路径转换为带前缀的文件名
            # 例如: docs/api/index.html -> docs_api_index.pdf
            path_parts = rel_path.with_suffix('.pdf').parts
            if len(path_parts) > 1:
                # 有目录结构,用下划线连接所有部分
                flat_name = '_'.join(path_parts)
            else:
                # 只有文件名
                flat_name = path_parts[0]

            pdf_path = self.output_dir / flat_name

        return pdf_path

    def _create_task(self, html_path: Path, base_url: str) -> FileTask:
        """创建文件任务"""
        pdf_path = self._get_pdf_path(html_path)

        # 计算HTML文件的相对路径（用于MD5缓存的key）
        try:
            rel_path = html_path.relative_to(self.input_dir)
        except ValueError:
            rel_path = Path(html_path.name)

        # 计算HTML文件的MD5
        md5 = MD5Cache.calculate_file_md5(html_path)

        # 检查是否需要跳过（MD5未变化且PDF已存在）
        skip = False
        if self.config.output.reuse_from:
            # 如果MD5未变化且PDF文件在复用目录中存在
            if not self.md5_cache.has_changed(str(rel_path), md5):
                # 检查复用目录中的PDF是否存在
                reuse_pdf_path = Path(self.config.output.reuse_from) / rel_path.with_suffix('.pdf')
                if reuse_pdf_path.exists():
                    skip = True

        # 构建URL
        if base_url:
            # 使用HTTP服务器
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
            url=url,
            md5=md5,
            skip=skip
        )

    def _resolve_path_conflicts(self, tasks: List[FileTask]) -> List[FileTask]:
        """解决平铺模式下的PDF路径冲突

        当多个HTML文件映射到同一个PDF路径时,为后续文件添加数字后缀
        例如: page.pdf, page_1.pdf, page_2.pdf
        """
        if self.config.output.keep_structure:
            # 保持结构模式不需要处理冲突
            return tasks

        # 按PDF路径分组
        path_groups = {}
        for task in tasks:
            pdf_path_str = str(task.pdf_path)
            if pdf_path_str not in path_groups:
                path_groups[pdf_path_str] = []
            path_groups[pdf_path_str].append(task)

        # 处理冲突的路径
        resolved_tasks = []
        for pdf_path_str, task_group in path_groups.items():
            if len(task_group) == 1:
                # 没有冲突,直接添加
                resolved_tasks.append(task_group[0])
            else:
                # 有冲突,为除了第一个之外的所有任务添加数字后缀
                for i, task in enumerate(task_group):
                    if i == 0:
                        # 第一个任务保持原样
                        resolved_tasks.append(task)
                    else:
                        # 后续任务添加数字后缀
                        stem = task.pdf_path.stem
                        suffix = task.pdf_path.suffix
                        parent = task.pdf_path.parent

                        new_name = f"{stem}_{i}{suffix}"
                        new_pdf_path = parent / new_name

                        # 创建新的 FileTask (保持其他字段不变)
                        new_task = FileTask(
                            html_path=task.html_path,
                            pdf_path=new_pdf_path,
                            url=task.url,
                            priority=task.priority,
                            skip=task.skip,
                            md5=task.md5
                        )
                        resolved_tasks.append(new_task)

        # 重新排序
        resolved_tasks.sort(key=lambda t: str(t.html_path))

        return resolved_tasks


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
