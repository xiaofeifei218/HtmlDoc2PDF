#!/usr/bin/env python3
"""
安装测试脚本
验证所有依赖是否正确安装
"""

import sys


def test_python_version():
    """测试Python版本"""
    print("检查Python版本...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python版本过低: {version.major}.{version.minor}")
        print("  需要Python 3.8或更高版本")
        return False


def test_imports():
    """测试Python包导入"""
    packages = [
        ('yaml', 'PyYAML'),
        ('playwright', 'Playwright'),
        ('tqdm', 'tqdm'),
    ]

    all_ok = True
    print("\n检查Python包...")

    for module_name, package_name in packages:
        try:
            __import__(module_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} 未安装")
            print(f"    安装命令: pip install {package_name.lower()}")
            all_ok = False

    return all_ok


def test_playwright_browser():
    """测试Playwright浏览器"""
    print("\n检查Playwright浏览器...", end=" ")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
        print("✓ Chromium浏览器已安装")
        return True
    except Exception as e:
        print(f"✗ Chromium浏览器未安装")
        print(f"  错误: {e}")
        print("  安装命令: playwright install chromium")
        return False


def test_project_modules():
    """测试项目模块"""
    print("\n检查项目模块...")
    modules = [
        'src.config',
        'src.logger',
        'src.utils',
        'src.server',
        'src.converter',
        'src.scanner',
        'src.processor',
    ]

    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module} 导入失败")
            print(f"    错误: {e}")
            all_ok = False

    return all_ok


def test_config_files():
    """测试配置文件"""
    print("\n检查配置文件...")
    from pathlib import Path

    config_files = [
        'config/default.yaml',
        'config/dolphindb.yaml',
    ]

    all_ok = True
    for config_file in config_files:
        path = Path(config_file)
        if path.exists():
            print(f"  ✓ {config_file}")
        else:
            print(f"  ✗ {config_file} 不存在")
            all_ok = False

    return all_ok


def main():
    """主函数"""
    print("=" * 50)
    print("HtmlDoc2PDF 安装测试")
    print("=" * 50)

    results = []

    # 测试Python版本
    results.append(("Python版本", test_python_version()))

    # 测试包导入
    results.append(("Python包", test_imports()))

    # 测试Playwright浏览器
    results.append(("Playwright浏览器", test_playwright_browser()))

    # 测试项目模块
    results.append(("项目模块", test_project_modules()))

    # 测试配置文件
    results.append(("配置文件", test_config_files()))

    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 50)

    if all_passed:
        print("\n🎉 所有测试通过!项目可以正常使用")
        print("\n快速开始:")
        print("  python main.py --input ./docs --output ./pdfs --dry-run")
        return 0
    else:
        print("\n❌ 部分测试失败,请根据上述提示修复问题")
        print("\n常见解决方案:")
        print("  1. 安装依赖: pip install -r requirements.txt")
        print("  2. 安装浏览器: playwright install chromium")
        return 1


if __name__ == "__main__":
    sys.exit(main())
