#!/usr/bin/env python3
"""
测试平铺模式下同名文件夹的处理

测试场景:
1. 不同文件夹下的同名文件 (docs/page.html, guide/page.html)
2. 多层嵌套的同名文件
3. 边缘情况: 路径前缀冲突 (docs/api_index.html vs docs_api/index.html)
"""

import shutil
from pathlib import Path
from src.config import Config
from src.scanner import FileScanner


def create_test_structure():
    """创建测试目录结构"""
    test_dir = Path("./test_duplicate")

    # 清理旧的测试目录
    if test_dir.exists():
        shutil.rmtree(test_dir)

    # 创建测试文件
    test_files = [
        "docs/page.html",
        "guide/page.html",
        "api/page.html",
        "docs/api/index.html",
        "guide/api/index.html",
        "docs/api_index.html",  # 这个会与 docs/api/index.html 冲突
        "tutorials/basics/setup.html",
        "examples/basics/setup.html",  # 与上面冲突
    ]

    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Page</title>
</head>
<body>
    <h1>Test Content - {}</h1>
    <p>This is a test file for duplicate folder handling.</p>
</body>
</html>
"""

    for file_path in test_files:
        full_path = test_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(html_content.format(file_path), encoding='utf-8')

    return test_dir


def test_flat_output():
    """测试平铺输出模式"""
    print("=" * 80)
    print("测试平铺模式下的同名文件夹处理")
    print("=" * 80)

    # 创建测试结构
    test_dir = create_test_structure().resolve()  # 转换为绝对路径
    print(f"\n✓ 测试目录已创建: {test_dir}")

    # 显示输入文件结构
    print("\n输入文件结构:")
    for html_file in sorted(test_dir.rglob("*.html")):
        rel_path = html_file.relative_to(test_dir)
        print(f"  - {rel_path}")

    # 配置
    config = Config()
    config.input.directory = str(test_dir)
    config.input.recursive = True
    config.input.include_patterns = ["**/*.html"]
    config.output.directory = "./test_output"
    config.output.keep_structure = False  # 平铺模式
    config.output.overwrite = True

    # 扫描
    scanner = FileScanner(config)
    tasks = scanner.scan()

    print(f"\n✓ 扫描完成,找到 {len(tasks)} 个任务")

    # 显示输出映射
    print("\n输出文件映射 (HTML → PDF):")
    print("-" * 80)

    pdf_paths = set()
    duplicates = []

    for task in tasks:
        rel_html = task.html_path.relative_to(test_dir)
        pdf_name = task.pdf_path.name

        # 检查是否有重复的PDF路径
        if str(task.pdf_path) in pdf_paths:
            duplicates.append(str(task.pdf_path))
        pdf_paths.add(str(task.pdf_path))

        print(f"  {rel_html}")
        print(f"    → {pdf_name}")

    # 检查结果
    print("\n" + "=" * 80)
    print("验证结果:")
    print("=" * 80)

    if duplicates:
        print(f"\n✗ 失败! 发现 {len(duplicates)} 个重复的PDF路径:")
        for dup in duplicates:
            print(f"  - {dup}")
        return False
    else:
        print("\n✓ 成功! 所有PDF路径都是唯一的")

    # 验证路径前缀
    print("\n验证路径前缀策略:")
    expected_mappings = {
        "docs/page.html": "docs_page.pdf",
        "guide/page.html": "guide_page.pdf",
        "api/page.html": "api_page.pdf",
        "docs/api/index.html": "docs_api_index.pdf",
        "guide/api/index.html": "guide_api_index.pdf",
        "docs/api_index.html": "docs_api_index_1.pdf",  # 冲突,添加后缀
        "tutorials/basics/setup.html": "tutorials_basics_setup.pdf",
        "examples/basics/setup.html": "examples_basics_setup.pdf",
    }

    all_correct = True
    for task in tasks:
        rel_html = str(task.html_path.relative_to(test_dir))
        expected_pdf = expected_mappings.get(rel_html)
        actual_pdf = task.pdf_path.name

        if expected_pdf and expected_pdf != actual_pdf:
            print(f"  ✗ {rel_html}")
            print(f"    期望: {expected_pdf}")
            print(f"    实际: {actual_pdf}")
            all_correct = False
        elif expected_pdf:
            print(f"  ✓ {rel_html} → {actual_pdf}")

    print("\n" + "=" * 80)
    if all_correct and not duplicates:
        print("✓ 所有测试通过!")
        print("=" * 80)
        return True
    else:
        print("✗ 测试失败!")
        print("=" * 80)
        return False


def test_keep_structure():
    """测试保持结构模式(作为对照)"""
    print("\n" + "=" * 80)
    print("对照测试: 保持目录结构模式")
    print("=" * 80)

    test_dir = Path("./test_duplicate").resolve()

    config = Config()
    config.input.directory = str(test_dir)
    config.input.recursive = True
    config.input.include_patterns = ["**/*.html"]
    config.output.directory = "./test_output"
    config.output.keep_structure = True  # 保持结构

    scanner = FileScanner(config)
    tasks = scanner.scan()

    print(f"\n✓ 扫描完成,找到 {len(tasks)} 个任务")
    print("\n输出文件映射:")

    for task in tasks:
        rel_html = task.html_path.relative_to(test_dir)
        rel_pdf = task.pdf_path.relative_to(scanner.output_dir)
        print(f"  {rel_html}")
        print(f"    → {rel_pdf}")

    print("\n✓ 保持结构模式下,所有文件都有独立的路径")


if __name__ == "__main__":
    try:
        # 运行测试
        success = test_flat_output()
        test_keep_structure()

        # 清理
        print("\n正在清理测试文件...")
        test_dir = Path("./test_duplicate")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        print("✓ 测试文件已清理")

        if success:
            print("\n" + "=" * 80)
            print("🎉 修复验证成功! 平铺模式下不会出现文件覆盖问题")
            print("=" * 80)
        else:
            print("\n⚠️  测试失败,需要进一步检查")
            exit(1)

    except Exception as e:
        print(f"\n✗ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
