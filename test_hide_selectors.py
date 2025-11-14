#!/usr/bin/env python3
"""
测试自定义隐藏选择器功能
"""

import sys
from pathlib import Path
import tempfile
import shutil

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import Config, PDFConfig
from src.converter import convert_html_to_pdf_sync


def create_test_html():
    """创建测试HTML文件"""
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <title>测试隐藏选择器功能</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }
        .content {
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .footer-container {
            background: black;
            color: white;
            padding: 15px;
            text-align: center;
            border-radius: 5px;
            margin-top: 20px;
        }
        .footer-container p {
            margin: 5px 0;
            font-weight: bold;
        }
        .should-hide {
            background: red;
            color: white;
            padding: 10px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="content">
        <h1>HTML转PDF - 隐藏选择器测试</h1>
        <p>这是一个测试页面，用于验证自定义隐藏选择器功能。</p>

        <h2>正常内容</h2>
        <p>这段内容应该在PDF中正常显示。</p>

        <div class="should-hide">
            这个红色框应该被隐藏（使用 .should-hide 选择器）
        </div>

        <h2>测试列表</h2>
        <ul>
            <li>功能测试1：版权信息隐藏</li>
            <li>功能测试2：自定义选择器</li>
            <li>功能测试3：中文显示</li>
        </ul>
    </div>

    <div class="footer-container">
        <title>Copyright</title>
        <p><b>
            ©2025 浙江智臾科技有限公司 浙ICP备18048711号-3
        </b></p>
    </div>

    <div class="content">
        <p style="color: green; font-weight: bold;">
            ✓ 如果上面的黑色版权框和红色框都没有出现在PDF中，则测试成功！
        </p>
    </div>
</body>
</html>
"""

    # 创建临时目录
    test_dir = Path("./test_output")
    test_dir.mkdir(exist_ok=True)

    # 创建测试HTML文件
    html_file = test_dir / "test_hide_selectors.html"
    html_file.write_text(html_content, encoding='utf-8')

    return html_file, test_dir


def test_hide_selectors():
    """测试隐藏选择器功能"""
    print("=" * 60)
    print("测试自定义隐藏选择器功能")
    print("=" * 60)

    # 创建测试HTML
    print("\n1. 创建测试HTML文件...")
    html_file, test_dir = create_test_html()
    print(f"   ✓ 测试文件: {html_file}")

    # 配置1: 不隐藏任何元素（对照组）
    print("\n2. 测试1 - 不隐藏任何元素...")
    config1 = Config()
    config1.pdf.hide_selectors = []
    pdf_file1 = test_dir / "test_no_hide.pdf"

    result1 = convert_html_to_pdf_sync(
        url=f"file://{html_file.absolute()}",
        output_path=str(pdf_file1),
        config=config1,
        html_path=str(html_file)
    )

    if result1.success:
        print(f"   ✓ PDF生成成功: {pdf_file1}")
        print(f"   ✓ 文件大小: {result1.file_size} 字节")
        print(f"   ✓ 耗时: {result1.duration:.2f}秒")
        print(f"   ⚠ 此PDF应该包含黑色版权框和红色框")
    else:
        print(f"   ✗ 转换失败: {result1.error}")

    # 配置2: 隐藏 .footer-container
    print("\n3. 测试2 - 隐藏版权信息框...")
    config2 = Config()
    config2.pdf.hide_selectors = [".footer-container"]
    pdf_file2 = test_dir / "test_hide_footer.pdf"

    result2 = convert_html_to_pdf_sync(
        url=f"file://{html_file.absolute()}",
        output_path=str(pdf_file2),
        config=config2,
        html_path=str(html_file)
    )

    if result2.success:
        print(f"   ✓ PDF生成成功: {pdf_file2}")
        print(f"   ✓ 文件大小: {result2.file_size} 字节")
        print(f"   ✓ 耗时: {result2.duration:.2f}秒")
        print(f"   ✓ 此PDF应该不包含黑色版权框")
    else:
        print(f"   ✗ 转换失败: {result2.error}")

    # 配置3: 隐藏多个选择器
    print("\n4. 测试3 - 隐藏多个元素...")
    config3 = Config()
    config3.pdf.hide_selectors = [".footer-container", ".should-hide"]
    pdf_file3 = test_dir / "test_hide_multiple.pdf"

    result3 = convert_html_to_pdf_sync(
        url=f"file://{html_file.absolute()}",
        output_path=str(pdf_file3),
        config=config3,
        html_path=str(html_file)
    )

    if result3.success:
        print(f"   ✓ PDF生成成功: {pdf_file3}")
        print(f"   ✓ 文件大小: {result3.file_size} 字节")
        print(f"   ✓ 耗时: {result3.duration:.2f}秒")
        print(f"   ✓ 此PDF应该既不包含黑色版权框，也不包含红色框")
    else:
        print(f"   ✗ 转换失败: {result3.error}")

    # 输出总结
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print(f"\n请查看以下PDF文件验证结果：")
    print(f"  1. {pdf_file1.name} - 对照组（应包含所有元素）")
    print(f"  2. {pdf_file2.name} - 隐藏版权框")
    print(f"  3. {pdf_file3.name} - 隐藏多个元素")
    print(f"\n所有文件位于: {test_dir.absolute()}")
    print()


if __name__ == "__main__":
    try:
        test_hide_selectors()
    except Exception as e:
        print(f"\n✗ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
