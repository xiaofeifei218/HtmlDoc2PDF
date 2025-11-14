"""
MD5缓存管理模块
负责计算文件MD5、保存和加载MD5缓存
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional


class MD5Cache:
    """MD5缓存管理器"""

    CACHE_FILENAME = "_md5_cache.json"

    def __init__(self, output_dir: Path):
        """
        初始化MD5缓存

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.cache_file = self.output_dir / self.CACHE_FILENAME
        self.cache: Dict[str, str] = {}

    @staticmethod
    def calculate_file_md5(file_path: Path) -> str:
        """
        计算文件的MD5值

        Args:
            file_path: 文件路径

        Returns:
            MD5字符串
        """
        md5_hash = hashlib.md5()

        with open(file_path, 'rb') as f:
            # 分块读取，避免大文件占用过多内存
            for chunk in iter(lambda: f.read(8192), b''):
                md5_hash.update(chunk)

        return md5_hash.hexdigest()

    def load_cache(self, cache_file: Optional[Path] = None) -> bool:
        """
        从文件加载MD5缓存

        Args:
            cache_file: 缓存文件路径，如果不指定则使用默认路径

        Returns:
            是否成功加载
        """
        if cache_file is None:
            cache_file = self.cache_file
        else:
            cache_file = Path(cache_file)

        if not cache_file.exists():
            self.cache = {}
            return False

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                self.cache = json.load(f)
            return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"警告: 加载MD5缓存失败: {e}")
            self.cache = {}
            return False

    def save_cache(self) -> bool:
        """
        保存MD5缓存到文件

        Returns:
            是否成功保存
        """
        try:
            # 确保输出目录存在
            self.output_dir.mkdir(parents=True, exist_ok=True)

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"错误: 保存MD5缓存失败: {e}")
            return False

    def get_md5(self, rel_path: str) -> Optional[str]:
        """
        获取缓存中的MD5值

        Args:
            rel_path: 相对路径（相对于输入目录）

        Returns:
            MD5值，如果不存在返回None
        """
        # 统一路径分隔符为正斜杠
        normalized_path = str(rel_path).replace('\\', '/')
        return self.cache.get(normalized_path)

    def set_md5(self, rel_path: str, md5: str):
        """
        设置MD5值

        Args:
            rel_path: 相对路径（相对于输入目录）
            md5: MD5值
        """
        # 统一路径分隔符为正斜杠
        normalized_path = str(rel_path).replace('\\', '/')
        self.cache[normalized_path] = md5

    def has_changed(self, rel_path: str, current_md5: str) -> bool:
        """
        检查文件是否有变化

        Args:
            rel_path: 相对路径
            current_md5: 当前文件的MD5值

        Returns:
            True表示文件有变化或是新文件，False表示无变化
        """
        cached_md5 = self.get_md5(rel_path)

        # 如果缓存中不存在，说明是新文件
        if cached_md5 is None:
            return True

        # 对比MD5值
        return cached_md5 != current_md5

    def get_cache_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息

        Returns:
            统计字典
        """
        return {
            'total_entries': len(self.cache),
            'cache_file_exists': self.cache_file.exists()
        }


if __name__ == "__main__":
    # 测试代码
    import tempfile
    import shutil

    print("测试MD5缓存管理器...")

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # 创建测试文件
        test_file = tmpdir_path / "test.html"
        test_file.write_text("<html><body>Hello</body></html>", encoding='utf-8')

        # 计算MD5
        md5 = MD5Cache.calculate_file_md5(test_file)
        print(f"✓ MD5计算成功: {md5}")

        # 创建缓存管理器
        output_dir = tmpdir_path / "output"
        cache = MD5Cache(output_dir)

        # 设置MD5
        cache.set_md5("test.html", md5)

        # 保存缓存
        if cache.save_cache():
            print(f"✓ 缓存保存成功: {cache.cache_file}")

        # 加载缓存
        new_cache = MD5Cache(output_dir)
        if new_cache.load_cache():
            print("✓ 缓存加载成功")

        # 检查MD5
        loaded_md5 = new_cache.get_md5("test.html")
        if loaded_md5 == md5:
            print(f"✓ MD5匹配: {loaded_md5}")

        # 检查是否有变化
        has_changed = new_cache.has_changed("test.html", md5)
        print(f"✓ 文件无变化: {not has_changed}")

        # 修改文件
        test_file.write_text("<html><body>Hello World</body></html>", encoding='utf-8')
        new_md5 = MD5Cache.calculate_file_md5(test_file)
        has_changed = new_cache.has_changed("test.html", new_md5)
        print(f"✓ 文件有变化: {has_changed}")

        # 统计信息
        stats = new_cache.get_cache_stats()
        print(f"✓ 缓存统计: {stats}")

    print("\nMD5缓存管理器测试完成!")
