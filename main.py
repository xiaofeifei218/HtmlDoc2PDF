#!/usr/bin/env python3
"""
HtmlDoc2PDF - HTML文档批量转PDF工具
主程序入口
"""

import sys
import argparse
from pathlib import Path

from src.config import Config, ConfigLoader
from src.logger import Logger
from src.server import LocalHTTPServer
from src.scanner import FileScanner
from src.processor import BatchProcessor


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='HtmlDoc2PDF - HTML文档批量转PDF工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用
  python main.py --input ./docs --output ./pdfs

  # 使用配置文件
  python main.py --config config/dolphindb.yaml

  # 自定义参数
  python main.py -i ./docs -o ./pdfs -w 8 --port 8000

  # 平铺模式(所有PDF输出到同一文件夹)
  python main.py -i ./docs -o ./pdfs --flat-output

  # 只扫描不转换(预览)
  python main.py -i ./docs --dry-run
        """
    )

    parser.add_argument(
        '-c', '--config',
        help='配置文件路径(YAML格式)',
        type=str
    )

    parser.add_argument(
        '-i', '--input',
        help='输入目录',
        type=str
    )

    parser.add_argument(
        '-o', '--output',
        help='输出目录',
        type=str
    )

    parser.add_argument(
        '-w', '--workers',
        help='并发进程数(默认:4)',
        type=int
    )

    parser.add_argument(
        '--port',
        help='HTTP服务器端口(默认:8000)',
        type=int
    )

    parser.add_argument(
        '--no-server',
        help='不启动HTTP服务器,使用file://协议',
        action='store_true'
    )

    parser.add_argument(
        '--overwrite',
        help='覆盖已存在的PDF文件',
        action='store_true'
    )

    parser.add_argument(
        '--reuse-from',
        help='复用指定目录的MD5缓存(增量转换)',
        type=str
    )

    parser.add_argument(
        '--dry-run',
        help='只扫描不转换(预览模式)',
        action='store_true'
    )

    parser.add_argument(
        '--debug',
        help='调试模式(详细日志)',
        action='store_true'
    )

    parser.add_argument(
        '--flat-output',
        help='忽略目录结构,所有PDF输出到同一文件夹(平铺模式)',
        action='store_true'
    )

    return parser.parse_args()


def load_config(args) -> Config:
    """
    加载配置

    Args:
        args: 命令行参数

    Returns:
        Config对象
    """
    # 加载基础配置
    if args.config:
        # 从配置文件加载
        config = ConfigLoader.load_from_yaml(args.config)
    else:
        # 使用默认配置
        config = ConfigLoader.load_default()

    # 命令行参数覆盖
    if args.input:
        config.input.directory = args.input

    if args.output:
        config.output.directory = args.output

    if args.workers:
        config.processing.workers = args.workers

    if args.port:
        config.server.port = args.port

    if args.no_server:
        config.server.enabled = False

    if args.overwrite:
        config.output.overwrite = True

    if args.reuse_from:
        config.output.reuse_from = args.reuse_from

    if args.flat_output:
        config.output.keep_structure = False

    if args.debug:
        config.logging.level = "DEBUG"
        config.processing.workers = 1  # 调试模式使用单进程

    return config


def main():
    """主函数"""
    # 解析参数
    args = parse_args()

    # 加载配置
    try:
        config = load_config(args)
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return 1

    # 验证配置
    errors = config.validate()
    if errors:
        print("❌ 配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        return 1

    # 初始化日志
    Logger.initialize(config.logging)
    logger = Logger.get_logger()

    logger.info("=" * 50)
    logger.info("HtmlDoc2PDF - HTML文档批量转PDF工具")
    logger.info("=" * 50)
    logger.info(f"输入目录: {config.input.directory}")
    logger.info(f"输出目录: {config.output.directory}")
    logger.info(f"并发进程: {config.processing.workers}")
    logger.info("=" * 50)

    # 启动HTTP服务器(如果需要)
    server = None
    base_url = ""

    if config.server.enabled:
        logger.info("正在启动HTTP服务器...")
        server = LocalHTTPServer(
            root_dir=config.input.directory,
            port=config.server.port,
            auto_find_port=config.server.auto_find_port
        )

        if not server.start():
            logger.error("HTTP服务器启动失败")
            return 1

        base_url = server.get_base_url()
        logger.info(f"✓ HTTP服务器已启动: {base_url}")
    else:
        logger.info("使用file://协议(未启动HTTP服务器)")

    try:
        # 扫描文件
        logger.info("正在扫描文件...")
        scanner = FileScanner(config)
        tasks = scanner.scan(base_url=base_url)

        if not tasks:
            logger.warning("未找到任何需要转换的文件")
            return 0

        logger.info(f"✓ 找到 {len(tasks)} 个文件待转换")

        # 预览模式
        if args.dry_run:
            logger.info("\n预览模式 - 将要转换的文件:")
            for i, task in enumerate(tasks, 1):
                logger.info(f"  {i}. {Path(task.html_path).name}")
                logger.info(f"     -> {task.pdf_path}")
            logger.info(f"\n共 {len(tasks)} 个文件")
            logger.info("(使用 --dry-run 参数,未执行实际转换)")
            return 0

        # 执行批量处理
        processor = BatchProcessor(config, tasks, logger)
        stats = processor.process()

        # 保存MD5缓存（无论是否复用都要保存）
        logger.info("正在保存MD5缓存...")
        for task in tasks:
            # 计算相对路径
            try:
                rel_path = task.html_path.relative_to(Path(config.input.directory).resolve())
            except ValueError:
                rel_path = Path(task.html_path.name)

            # 保存MD5
            scanner.md5_cache.set_md5(str(rel_path), task.md5)

        if scanner.md5_cache.save_cache():
            logger.info(f"✓ MD5缓存已保存: {scanner.md5_cache.cache_file}")
        else:
            logger.warning("MD5缓存保存失败")

        # 返回码: 如果有失败的,返回1
        return 0 if stats.failed == 0 else 1

    except KeyboardInterrupt:
        logger.warning("\n用户中断")
        return 130

    except Exception as e:
        logger.error(f"发生错误: {e}", exc_info=True)
        return 1

    finally:
        # 停止HTTP服务器
        if server:
            server.stop()
            logger.info("HTTP服务器已停止")


if __name__ == "__main__":
    sys.exit(main())
