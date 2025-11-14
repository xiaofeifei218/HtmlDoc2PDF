"""
批量处理器模块
负责多进程任务调度和执行
"""

import time
import shutil
import multiprocessing as mp
from pathlib import Path
from typing import List
from dataclasses import dataclass
from datetime import datetime

from tqdm import tqdm

from src.scanner import FileTask
from src.converter import convert_html_to_pdf_sync, ConversionResult
from src.logger import setup_worker_logger
from src.utils import format_size, format_duration


@dataclass
class ProcessingStats:
    """处理统计信息"""
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    total_size: int = 0  # 总PDF大小(字节)
    total_duration: float = 0.0  # 总耗时(秒)

    def success_rate(self) -> float:
        """成功率"""
        if self.total == 0:
            return 0.0
        return (self.success / self.total) * 100

    def avg_duration(self) -> float:
        """平均耗时"""
        if self.success == 0:
            return 0.0
        return self.total_duration / self.success


class BatchProcessor:
    """批量处理器"""

    def __init__(self, config, tasks: List[FileTask], logger):
        """
        初始化处理器

        Args:
            config: Config对象
            tasks: 任务列表
            logger: 日志对象
        """
        self.config = config
        self.tasks = tasks
        self.logger = logger
        self.stats = ProcessingStats(total=len(tasks))

    def process(self) -> ProcessingStats:
        """
        执行批量处理

        Returns:
            ProcessingStats对象
        """
        if not self.tasks:
            self.logger.warning("没有要处理的任务")
            return self.stats

        # 分离跳过的任务和需要转换的任务
        tasks_to_skip = [t for t in self.tasks if t.skip]
        tasks_to_convert = [t for t in self.tasks if not t.skip]

        self.logger.info(f"开始处理 {len(self.tasks)} 个文件...")
        if tasks_to_skip:
            self.logger.info(f"  - 需要转换: {len(tasks_to_convert)} 个")
            self.logger.info(f"  - 跳过(未变化): {len(tasks_to_skip)} 个")
        self.logger.info(f"并发进程数: {self.config.processing.workers}")

        start_time = time.time()

        # 处理跳过的任务（复制PDF）
        if tasks_to_skip:
            self._handle_skipped_tasks(tasks_to_skip)
            self.stats.skipped = len(tasks_to_skip)

        # 处理需要转换的任务
        results = []
        if tasks_to_convert:
            # 根据workers数量选择处理方式
            if self.config.processing.workers == 1:
                # 单进程处理(便于调试)
                results = self._process_sequential(tasks_to_convert)
            else:
                # 多进程处理
                results = self._process_parallel(tasks_to_convert)

            # 统计结果
            self._collect_stats(results)

        # 总耗时
        total_time = time.time() - start_time

        # 输出统计信息
        self.logger.info("=" * 50)
        self.logger.info("处理完成!")
        self.logger.info(f"总数: {self.stats.total}")
        self.logger.info(f"成功: {self.stats.success}")
        self.logger.info(f"跳过: {self.stats.skipped}")
        self.logger.info(f"失败: {self.stats.failed}")
        if tasks_to_convert:
            self.logger.info(f"成功率: {self.stats.success_rate():.1f}%")
        self.logger.info(f"总PDF大小: {format_size(self.stats.total_size)}")
        self.logger.info(f"总耗时: {format_duration(total_time)}")
        if self.stats.success > 0:
            self.logger.info(f"平均耗时: {format_duration(self.stats.avg_duration())}/文件")
        self.logger.info("=" * 50)

        return self.stats

    def _handle_skipped_tasks(self, tasks: List[FileTask]):
        """
        处理跳过的任务（复制PDF文件）

        Args:
            tasks: 跳过的任务列表
        """
        reuse_dir = Path(self.config.output.reuse_from)

        self.logger.info("正在复制未变化的PDF文件...")
        for task in tqdm(tasks, desc="复制进度"):
            try:
                # 计算源PDF路径（在复用目录中）
                rel_path = task.html_path.relative_to(Path(self.config.input.directory).resolve())
                source_pdf = reuse_dir / rel_path.with_suffix('.pdf')

                # 确保目标目录存在
                task.pdf_path.parent.mkdir(parents=True, exist_ok=True)

                # 复制PDF文件
                shutil.copy2(source_pdf, task.pdf_path)

                # 更新统计
                if task.pdf_path.exists():
                    self.stats.total_size += task.pdf_path.stat().st_size

            except Exception as e:
                self.logger.warning(f"复制PDF失败: {task.html_path.name}, 错误: {e}")

    def _process_sequential(self, tasks: List[FileTask]) -> List[ConversionResult]:
        """顺序处理(单进程)"""
        results = []

        with tqdm(total=len(tasks), desc="转换进度") as pbar:
            for task in tasks:
                result = self._process_single_task(task)
                results.append(result)

                # 更新进度条
                status = "✓" if result.success else "✗"
                pbar.set_postfix_str(f"{status} {Path(task.html_path).name}")
                pbar.update(1)

                # 如果失败且不跳过错误,退出
                if not result.success and not self.config.processing.skip_errors:
                    break

        return results

    def _process_parallel(self, tasks: List[FileTask]) -> List[ConversionResult]:
        """并行处理(多进程)"""
        results = []

        # 创建进程池
        with mp.Pool(
            processes=self.config.processing.workers,
            initializer=_worker_init,
            initargs=(self.config,)
        ) as pool:
            # 提交所有任务
            async_results = []
            for task in tasks:
                async_result = pool.apply_async(_worker_process, (task,))
                async_results.append((task, async_result))

            # 收集结果(带进度条)
            with tqdm(total=len(tasks), desc="转换进度") as pbar:
                for task, async_result in async_results:
                    try:
                        result = async_result.get(timeout=self.config.browser.timeout / 1000 + 10)
                        results.append(result)

                        # 更新进度条
                        status = "✓" if result.success else "✗"
                        pbar.set_postfix_str(f"{status} {Path(task.html_path).name}")
                        pbar.update(1)

                    except mp.TimeoutError:
                        # 超时
                        result = ConversionResult(
                            success=False,
                            html_path=str(task.html_path),
                            pdf_path=str(task.pdf_path),
                            url=task.url,
                            error="进程超时"
                        )
                        results.append(result)
                        pbar.update(1)

                    except Exception as e:
                        # 其他错误
                        result = ConversionResult(
                            success=False,
                            html_path=str(task.html_path),
                            pdf_path=str(task.pdf_path),
                            url=task.url,
                            error=f"进程错误: {str(e)}"
                        )
                        results.append(result)
                        pbar.update(1)

        return results

    def _process_single_task(self, task: FileTask) -> ConversionResult:
        """
        处理单个任务(带重试)

        Args:
            task: FileTask对象

        Returns:
            ConversionResult对象
        """
        last_result = None

        for attempt in range(self.config.processing.retry_count):
            result = convert_html_to_pdf_sync(
                url=task.url,
                output_path=str(task.pdf_path),
                config=self.config,
                html_path=str(task.html_path)
            )

            if result.success:
                if attempt > 0:
                    self.logger.info(f"重试成功 (第{attempt + 1}次): {Path(task.html_path).name}")
                return result

            last_result = result

            # 如果还有重试机会,等待一下
            if attempt < self.config.processing.retry_count - 1:
                self.logger.warning(f"转换失败,{self.config.processing.retry_delay}秒后重试: {Path(task.html_path).name}")
                time.sleep(self.config.processing.retry_delay)

        # 所有重试都失败
        self.logger.error(f"转换失败(已重试{self.config.processing.retry_count}次): {Path(task.html_path).name}, 错误: {last_result.error}")
        return last_result

    def _collect_stats(self, results: List[ConversionResult]):
        """收集统计信息"""
        for result in results:
            if result.success:
                self.stats.success += 1
                self.stats.total_size += result.file_size
                self.stats.total_duration += result.duration
            else:
                self.stats.failed += 1


# 全局变量,用于worker进程
_worker_config = None


def _worker_init(config):
    """Worker进程初始化"""
    global _worker_config
    _worker_config = config

    # 初始化logger
    setup_worker_logger(config.logging)


def _worker_process(task: FileTask) -> ConversionResult:
    """Worker进程处理任务"""
    global _worker_config

    # 处理任务(带重试)
    last_result = None

    for attempt in range(_worker_config.processing.retry_count):
        result = convert_html_to_pdf_sync(
            url=task.url,
            output_path=str(task.pdf_path),
            config=_worker_config,
            html_path=str(task.html_path)
        )

        if result.success:
            return result

        last_result = result

        # 重试延迟
        if attempt < _worker_config.processing.retry_count - 1:
            time.sleep(_worker_config.processing.retry_delay)

    return last_result


if __name__ == "__main__":
    print("批量处理器模块")
    print("该模块需要完整的环境才能测试,请使用main.py进行完整测试")
