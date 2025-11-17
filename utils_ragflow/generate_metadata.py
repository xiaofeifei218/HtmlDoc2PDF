#!/usr/bin/env python3
"""
元数据生成器 - 从HTML文档生成元数据JSON文件
用于RAGflow导入时提供文档分类和路径信息
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from bs4 import BeautifulSoup
import sys


class MetadataExtractor:
    """元数据提取器"""

    def __init__(self, html_base_dir: str, pdf_output_dir: str):
        """
        初始化提取器

        Args:
            html_base_dir: HTML文件根目录
            pdf_output_dir: PDF输出目录
        """
        self.html_base_dir = Path(html_base_dir).resolve()
        self.pdf_output_dir = Path(pdf_output_dir).resolve()

    def extract_title_from_html(self, html_path: Path) -> Optional[str]:
        """
        从HTML文件中提取标题

        优先级: <h1> > <title> > 文件名

        Args:
            html_path: HTML文件路径

        Returns:
            提取的标题，失败返回None
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')

            # 优先从<h1>提取
            h1 = soup.find('h1')
            if h1 and h1.get_text().strip():
                return h1.get_text().strip()

            # 其次从<title>提取
            title = soup.find('title')
            if title and title.get_text().strip():
                # 去除常见的后缀
                title_text = title.get_text().strip()
                # 移除常见的分隔符后的内容
                for sep in [' - ', ' | ', ' :: ']:
                    if sep in title_text:
                        title_text = title_text.split(sep)[0].strip()
                return title_text

            # 最后使用文件名
            return html_path.stem

        except Exception as e:
            print(f"警告: 无法从 {html_path} 提取标题: {e}", file=sys.stderr)
            return None

    def generate_pdf_filename(self, relative_html_path: str) -> str:
        """
        生成PDF文件名（使用路径分隔符连接）

        Args:
            relative_html_path: 相对HTML路径，如 "db_distr_comp/cfg/cluster.html"

        Returns:
            PDF文件名，如 "db_distr_comp-cfg-cluster.pdf"
        """
        # 移除.html后缀，替换路径分隔符为连字符
        pdf_name = relative_html_path.replace('.html', '.pdf')
        return pdf_name

    def extract_metadata(self, html_path: Path) -> Optional[Dict]:
        """
        从单个HTML文件提取元数据

        Args:
            html_path: HTML文件绝对路径

        Returns:
            元数据字典，失败返回None
        """
        try:
            # 计算相对路径
            try:
                relative_path = html_path.relative_to(self.html_base_dir)
            except ValueError:
                print(f"警告: {html_path} 不在基础目录 {self.html_base_dir} 下", file=sys.stderr)
                return None

            # 转换为POSIX路径（统一使用/作为分隔符）
            relative_path_str = relative_path.as_posix()

            # 提取路径层级
            path_parts = relative_path_str.replace('.html', '').split('/')

            # 生成PDF文件名和路径
            pdf_filename = self.generate_pdf_filename(relative_path_str)

            # PDF路径可能在多级子目录中，保持与HTML相同的目录结构
            pdf_relative_path = str(relative_path).replace('.html', '.pdf')
            pdf_path = self.pdf_output_dir / pdf_relative_path

            # 提取标题
            title = self.extract_title_from_html(html_path)
            if not title:
                title = path_parts[-1]  # 使用文件名作为后备

            # 构建元数据
            metadata = {
                "title": title,
                'name':path_parts[-1],
                "path": pdf_filename,
                "category_level1": path_parts[0] if len(path_parts) > 0 else "",
                "category_level2": path_parts[1] if len(path_parts) > 1 else "",
                "category_level3": path_parts[2] if len(path_parts) > 2 else "",
                # "path_depth": len(path_parts),
            }

            return metadata

        except Exception as e:
            print(f"错误: 处理 {html_path} 时出错: {e}", file=sys.stderr)
            return None

    def scan_and_generate(self, output_json: str, file_extensions: List[str] = None) -> bool:
        """
        扫描HTML目录并生成元数据JSON

        Args:
            output_json: 输出JSON文件路径
            file_extensions: 要扫描的文件扩展名列表，默认['.html', '.htm']

        Returns:
            成功返回True，失败返回False
        """
        if file_extensions is None:
            file_extensions = ['.html', '.htm']

        print(f"正在扫描目录: {self.html_base_dir}")
        print(f"PDF输出目录: {self.pdf_output_dir}")

        # 检查HTML基础目录是否存在
        if not self.html_base_dir.exists():
            print(f"错误: HTML目录不存在: {self.html_base_dir}", file=sys.stderr)
            return False

        # 扫描所有HTML文件
        html_files = []
        for ext in file_extensions:
            html_files.extend(self.html_base_dir.rglob(f"*{ext}"))

        if not html_files:
            print(f"警告: 在 {self.html_base_dir} 中未找到任何HTML文件", file=sys.stderr)
            return False

        print(f"找到 {len(html_files)} 个HTML文件")

        # 生成元数据
        metadata_collection = {
            "metadata_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "html_base_dir": str(self.html_base_dir),
            "pdf_output_dir": str(self.pdf_output_dir),
            "total_documents": 0,
            "documents": {}
        }

        success_count = 0
        failed_count = 0

        for html_file in sorted(html_files):
            print(f"处理: {html_file.relative_to(self.html_base_dir)}", end=" ... ")

            metadata = self.extract_metadata(html_file)
            if metadata:
                # 使用PDF文件名作为key
                metadata_collection["documents"][metadata["name"]] = metadata
                success_count += 1
                print("✓")
            else:
                failed_count += 1
                print("✗")

        metadata_collection["total_documents"] = success_count

        # 保存JSON
        try:
            output_path = Path(output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_collection, f, ensure_ascii=False, indent=2)

            print(f"\n✓ 元数据已保存到: {output_path}")
            print(f"  成功: {success_count} 个")
            if failed_count > 0:
                print(f"  失败: {failed_count} 个")

            return True

        except Exception as e:
            print(f"\n错误: 保存JSON文件失败: {e}", file=sys.stderr)
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='从HTML文档生成元数据JSON文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用
  python generate_metadata.py \\
    --html-dir ./downloaded_html \\
    --pdf-dir ./output \\
    --output ./metadata.json

  # 使用简写参数
  python generate_metadata.py -i ./docs -p ./pdfs -o metadata.json

  # 指定文件扩展名
  python generate_metadata.py -i ./docs -p ./pdfs -o metadata.json --extensions .html .htm
        """
    )

    parser.add_argument(
        '-i', '--html-dir',
        required=True,
        help='HTML文件根目录'
    )

    parser.add_argument(
        '-p', '--pdf-dir',
        required=True,
        help='PDF输出目录'
    )

    parser.add_argument(
        '-o', '--output',
        default='metadata.json',
        help='输出JSON文件路径 (默认: metadata.json)'
    )

    parser.add_argument(
        '--extensions',
        nargs='+',
        default=['.html', '.htm'],
        help='要扫描的文件扩展名 (默认: .html .htm)'
    )

    args = parser.parse_args()

    # 创建提取器
    extractor = MetadataExtractor(
        html_base_dir=args.html_dir,
        pdf_output_dir=args.pdf_dir
    )

    # 执行生成
    success = extractor.scan_and_generate(
        output_json=args.output,
        file_extensions=args.extensions
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
