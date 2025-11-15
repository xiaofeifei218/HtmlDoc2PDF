#!/usr/bin/env python3
"""
测试 --flat-output 参数功能
"""

import sys
import argparse
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config, ConfigLoader, OutputConfig


def parse_test_args():
    """解析命令行参数（简化版）"""
    parser = argparse.ArgumentParser(description='测试 --flat-output 参数')

    parser.add_argument('-i', '--input', type=str, default='.')
    parser.add_argument('-o', '--output', type=str, default='./output')
    parser.add_argument('--flat-output', action='store_true',
                       help='忽略目录结构,所有PDF输出到同一文件夹(平铺模式)')

    return parser.parse_args()


def load_test_config(args) -> Config:
    """加载配置（简化版）"""
    config = ConfigLoader.load_default()

    if args.input:
        config.input.directory = args.input
    if args.output:
        config.output.directory = args.output
    if args.flat_output:
        config.output.keep_structure = False

    return config


def test_scanner_logic():
    """测试扫描器的路径生成逻辑"""
    from src.scanner import FileScanner

    print("=" * 60)
    print("测试 1: 默认模式 (保持目录结构)")
    print("=" * 60)

    # 测试1: 默认模式
    config1 = Config()
    config1.input.directory = "./test_input"
    config1.output.directory = "./test_output"
    config1.output.keep_structure = True  # 默认保持结构

    scanner1 = FileScanner(config1)

    # 模拟一个子目录中的HTML文件
    test_html = Path("./test_input/subdir/page.html").resolve()
    pdf_path1 = scanner1._get_pdf_path(test_html)

    print(f"HTML路径: {test_html}")
    print(f"PDF路径:  {pdf_path1}")
    print(f"keep_structure = True")
    print(f"是否保留了 'subdir' 目录: {'subdir' in str(pdf_path1)}")
    print()

    print("=" * 60)
    print("测试 2: 平铺模式 (--flat-output)")
    print("=" * 60)

    # 测试2: 平铺模式
    config2 = Config()
    config2.input.directory = "./test_input"
    config2.output.directory = "./test_output"
    config2.output.keep_structure = False  # 平铺模式

    scanner2 = FileScanner(config2)
    pdf_path2 = scanner2._get_pdf_path(test_html)

    print(f"HTML路径: {test_html}")
    print(f"PDF路径:  {pdf_path2}")
    print(f"keep_structure = False")
    print(f"是否保留了 'subdir' 目录: {'subdir' in str(pdf_path2)}")
    print()

    print("=" * 60)
    print("测试结果总结")
    print("=" * 60)

    if 'subdir' in str(pdf_path1) and 'subdir' not in str(pdf_path2):
        print("✅ 测试通过!")
        print("   - 默认模式: 保留了目录结构")
        print("   - 平铺模式: 忽略了目录结构")
        return True
    else:
        print("❌ 测试失败!")
        return False


def main():
    """主函数"""
    print("测试 --flat-output 参数功能")
    print()

    # 测试命令行参数解析
    args = parse_test_args()
    print(f"命令行参数:")
    print(f"  --input: {args.input}")
    print(f"  --output: {args.output}")
    print(f"  --flat-output: {args.flat_output}")
    print()

    # 测试配置加载
    config = load_test_config(args)
    print(f"配置结果:")
    print(f"  input.directory: {config.input.directory}")
    print(f"  output.directory: {config.output.directory}")
    print(f"  output.keep_structure: {config.output.keep_structure}")
    print()

    # 验证逻辑
    if args.flat_output and config.output.keep_structure:
        print("❌ 错误: --flat-output 参数没有正确设置 keep_structure=False")
        return 1
    elif not args.flat_output and not config.output.keep_structure:
        print("❌ 错误: 默认应该是 keep_structure=True")
        return 1
    else:
        print("✅ 参数解析正确!")
        print()

    # 测试扫描器逻辑
    if test_scanner_logic():
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
