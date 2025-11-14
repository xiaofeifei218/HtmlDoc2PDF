"""
配置管理模块
负责加载、合并和验证配置
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class InputConfig:
    """输入配置"""
    directory: str = "."
    recursive: bool = True
    include_patterns: List[str] = field(default_factory=lambda: ["**/*.html"])
    exclude_patterns: List[str] = field(default_factory=list)


@dataclass
class OutputConfig:
    """输出配置"""
    directory: str = "./output"
    keep_structure: bool = True
    overwrite: bool = False


@dataclass
class ServerConfig:
    """HTTP服务器配置"""
    enabled: bool = True
    port: int = 8000
    auto_find_port: bool = True


@dataclass
class PDFConfig:
    """PDF配置"""
    format: str = "A4"  # A4, Letter, A3
    landscape: bool = False
    margin: Dict[str, str] = field(default_factory=lambda: {
        "top": "15mm",
        "bottom": "15mm",
        "left": "12mm",
        "right": "12mm"
    })
    print_background: bool = True
    scale: float = 1.0
    display_header_footer: bool = False
    header_template: str = ""
    footer_template: str = ""


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = True
    timeout: int = 60000  # ms
    wait_until: str = "networkidle"  # load, domcontentloaded, networkidle
    wait_after_load: int = 2000  # ms
    viewport_width: int = 1280
    viewport_height: int = 1024


@dataclass
class ProcessingConfig:
    """处理配置"""
    workers: int = 4
    retry_count: int = 3
    retry_delay: int = 2  # seconds
    skip_errors: bool = True


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    file: str = "./logs/conversion.log"
    console: bool = True
    format: str = "[{time}] [{level}] [{process}] {message}"


@dataclass
class Config:
    """完整配置"""
    input: InputConfig = field(default_factory=InputConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    pdf: PDFConfig = field(default_factory=PDFConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """从字典创建配置"""
        return cls(
            input=InputConfig(**data.get('input', {})),
            output=OutputConfig(**data.get('output', {})),
            server=ServerConfig(**data.get('server', {})),
            pdf=PDFConfig(**data.get('pdf', {})),
            browser=BrowserConfig(**data.get('browser', {})),
            processing=ProcessingConfig(**data.get('processing', {})),
            logging=LoggingConfig(**data.get('logging', {}))
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def validate(self) -> List[str]:
        """
        验证配置的有效性

        Returns:
            错误信息列表,如果为空则配置有效
        """
        errors = []

        # 验证输入目录
        if not os.path.exists(self.input.directory):
            errors.append(f"输入目录不存在: {self.input.directory}")

        # 验证PDF格式
        valid_formats = ["A4", "Letter", "A3", "A5", "Legal", "Tabloid"]
        if self.pdf.format not in valid_formats:
            errors.append(f"无效的PDF格式: {self.pdf.format}, 支持的格式: {valid_formats}")

        # 验证scale
        if not 0.1 <= self.pdf.scale <= 2.0:
            errors.append(f"PDF缩放比例必须在0.1-2.0之间: {self.pdf.scale}")

        # 验证浏览器等待策略
        valid_wait = ["load", "domcontentloaded", "networkidle"]
        if self.browser.wait_until not in valid_wait:
            errors.append(f"无效的等待策略: {self.browser.wait_until}, 支持: {valid_wait}")

        # 验证超时时间
        if self.browser.timeout < 1000:
            errors.append(f"超时时间过短: {self.browser.timeout}ms, 建议至少10000ms")

        # 验证并发进程数
        if self.processing.workers < 1:
            errors.append(f"并发进程数必须大于0: {self.processing.workers}")
        if self.processing.workers > 32:
            errors.append(f"并发进程数过大: {self.processing.workers}, 建议不超过32")

        # 验证日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level.upper() not in valid_levels:
            errors.append(f"无效的日志级别: {self.logging.level}, 支持: {valid_levels}")

        return errors


class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load_from_yaml(file_path: str) -> Config:
        """
        从YAML文件加载配置

        Args:
            file_path: YAML配置文件路径

        Returns:
            Config对象

        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML格式错误
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if data is None:
            data = {}

        return Config.from_dict(data)

    @staticmethod
    def load_default() -> Config:
        """加载默认配置"""
        return Config()

    @staticmethod
    def merge_configs(base: Config, override: Dict[str, Any]) -> Config:
        """
        合并配置

        Args:
            base: 基础配置
            override: 覆盖的配置字典

        Returns:
            合并后的Config对象
        """
        base_dict = base.to_dict()

        # 深度合并
        def deep_merge(d1: Dict, d2: Dict) -> Dict:
            result = d1.copy()
            for key, value in d2.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        merged_dict = deep_merge(base_dict, override)
        return Config.from_dict(merged_dict)

    @staticmethod
    def save_to_yaml(config: Config, file_path: str):
        """
        保存配置到YAML文件

        Args:
            config: Config对象
            file_path: 输出文件路径
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)


def create_default_config_file(output_path: str = "config/default.yaml"):
    """
    创建默认配置文件

    Args:
        output_path: 输出路径
    """
    config = Config()
    ConfigLoader.save_to_yaml(config, output_path)
    print(f"默认配置文件已创建: {output_path}")


if __name__ == "__main__":
    # 测试代码
    print("测试配置模块...")

    # 创建默认配置
    config = Config()
    print(f"默认配置: workers={config.processing.workers}, format={config.pdf.format}")

    # 验证配置
    errors = config.validate()
    if errors:
        print(f"配置验证失败: {errors}")
    else:
        print("配置验证通过!")

    # 保存配置
    create_default_config_file()
