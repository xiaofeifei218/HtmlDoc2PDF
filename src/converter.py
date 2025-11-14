"""
转换器模块
封装Playwright的PDF转换逻辑
"""

import asyncio
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError


@dataclass
class ConversionResult:
    """转换结果"""
    success: bool
    html_path: str
    pdf_path: str
    url: str
    file_size: int = 0  # PDF文件大小(字节)
    duration: float = 0.0  # 转换耗时(秒)
    error: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class PlaywrightConverter:
    """Playwright PDF转换器"""

    def __init__(self, config):
        """
        初始化转换器

        Args:
            config: Config对象
        """
        self.config = config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self._initialized = False

    async def initialize(self):
        """初始化Playwright和浏览器"""
        if self._initialized:
            return

        self.playwright = await async_playwright().start()

        # 浏览器启动参数
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--allow-file-access-from-files',
            '--disable-features=IsolateOrigins,site-per-process',
            '--font-render-hinting=none',
        ]

        self.browser = await self.playwright.chromium.launch(
            headless=self.config.browser.headless,
            args=browser_args
        )

        self._initialized = True

    async def cleanup(self):
        """清理资源"""
        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        self._initialized = False

    async def convert(self, url: str, output_path: Path, html_path: str = "") -> ConversionResult:
        """
        转换单个HTML为PDF

        Args:
            url: HTML的URL
            output_path: PDF输出路径
            html_path: 原始HTML路径(用于记录)

        Returns:
            ConversionResult对象
        """
        if not self._initialized:
            await self.initialize()

        start_time = datetime.now()

        try:
            # 创建浏览器上下文
            context = await self.browser.new_context(
                viewport={
                    'width': self.config.browser.viewport_width,
                    'height': self.config.browser.viewport_height
                },
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'
            )

            # 创建页面
            page: Page = await context.new_page()

            # 导航到URL
            await page.goto(
                url,
                wait_until=self.config.browser.wait_until,
                timeout=self.config.browser.timeout
            )

            # 额外等待时间
            if self.config.browser.wait_after_load > 0:
                await page.wait_for_timeout(self.config.browser.wait_after_load)

            # 计算并设置页面标题为相对路径(用于页眉显示)
            if html_path and self.config.pdf.display_header_footer:
                try:
                    html_file = Path(html_path)
                    input_dir = Path(self.config.input.directory).resolve()

                    # 计算相对路径
                    try:
                        rel_path = html_file.relative_to(input_dir)
                        # 获取输入目录的名称
                        input_dir_name = input_dir.name
                        # 构建完整的相对路径显示(包含输入目录名)
                        display_path = f"{input_dir_name}/{rel_path}".replace('\\', '/')
                    except ValueError:
                        # 如果无法计算相对路径,使用文件名
                        display_path = html_file.name

                    # 注入JavaScript修改页面标题
                    await page.evaluate(f"document.title = '{display_path}'")
                except Exception as e:
                    # 如果出错,忽略并继续
                    pass

            # 注入CSS样式(隐藏不需要的元素)
            await page.add_style_tag(content="""
                /* 隐藏搜索框和导航元素 */
                .search-input,
                .search-box,
                .navheader,
                .no-print {
                    display: none !important;
                }

                /* 优化代码块显示 */
                pre code {
                    white-space: pre-wrap !important;
                    word-break: break-word !important;
                    font-size: 11px !important;
                }

                /* 打印时优化 */
                @media print {
                    .no-print { display: none !important; }
                    a { text-decoration: none; }
                }
            """)

            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 生成PDF
            await page.pdf(
                path=str(output_path),
                format=self.config.pdf.format,
                landscape=self.config.pdf.landscape,
                print_background=self.config.pdf.print_background,
                margin=self.config.pdf.margin,
                scale=self.config.pdf.scale,
                display_header_footer=self.config.pdf.display_header_footer,
                header_template=self.config.pdf.header_template,
                footer_template=self.config.pdf.footer_template,
                prefer_css_page_size=False,
            )

            # 关闭页面和上下文
            await page.close()
            await context.close()

            # 计算耗时和文件大小
            duration = (datetime.now() - start_time).total_seconds()
            file_size = output_path.stat().st_size if output_path.exists() else 0

            return ConversionResult(
                success=True,
                html_path=html_path or url,
                pdf_path=str(output_path),
                url=url,
                file_size=file_size,
                duration=duration
            )

        except PlaywrightTimeoutError as e:
            duration = (datetime.now() - start_time).total_seconds()
            return ConversionResult(
                success=False,
                html_path=html_path or url,
                pdf_path=str(output_path),
                url=url,
                duration=duration,
                error=f"超时: {str(e)}"
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return ConversionResult(
                success=False,
                html_path=html_path or url,
                pdf_path=str(output_path),
                url=url,
                duration=duration,
                error=f"转换失败: {str(e)}"
            )

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()


# 同步包装器(用于多进程)
def convert_html_to_pdf_sync(url: str, output_path: str, config, html_path: str = "") -> ConversionResult:
    """
    同步版本的转换函数(用于多进程)

    Args:
        url: HTML的URL
        output_path: PDF输出路径
        config: Config对象
        html_path: 原始HTML路径

    Returns:
        ConversionResult对象
    """
    async def _convert():
        async with PlaywrightConverter(config) as converter:
            return await converter.convert(url, Path(output_path), html_path)

    return asyncio.run(_convert())


if __name__ == "__main__":
    # 测试代码需要先安装playwright: playwright install chromium
    print("测试转换器模块...")
    print("注意: 需要先运行 'playwright install chromium' 安装浏览器")

    # 创建测试HTML文件
    test_html = Path("./test_converter.html")
    test_html.write_text("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>测试页面</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }
        h1 { color: #333; }
        .content {
            background: white;
            padding: 20px;
            border-radius: 5px;
        }
        code {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="content">
        <h1>HTML转PDF测试</h1>
        <p>这是一个测试页面,用于验证转换器功能。</p>
        <h2>特性测试</h2>
        <ul>
            <li>中文显示测试</li>
            <li>代码高亮: <code>print("Hello World")</code></li>
            <li>背景颜色</li>
        </ul>
    </div>
</body>
</html>
    """, encoding='utf-8')

    print(f"✓ 测试HTML文件已创建: {test_html}")
    print("\n转换器测试需要Playwright环境,请手动测试")
    print(f"测试命令示例:")
    print(f"  python -c 'from src.converter import convert_html_to_pdf_sync; from src.config import Config; convert_html_to_pdf_sync(\"file://{test_html.absolute()}\", \"test.pdf\", Config())'")
