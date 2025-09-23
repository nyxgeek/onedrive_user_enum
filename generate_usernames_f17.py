"""
Username generation script with caffeine and prayers
    Name: John Smith
    firstname: john
    firstnameletter: j
    lastname: smith
    lastnameletter: s
    letter: any(a-z)
    dot: .
"""
import argparse
import logging
import sys
import os
import string
import gc
import concurrent.futures
import multiprocessing
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Callable, Any
from functools import lru_cache
from dataclasses import dataclass
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, ProgressColumn
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO, stream=sys.stderr, force=True)
logger = logging.getLogger(__name__)
ALPHA_LIST = string.ascii_lowercase


@dataclass
class GeneratorConfig:
    """Configuration for username generation"""
    cpu_processes: int = 10
    batch_size: int = 1000000
    io_threads: int = 20
    write_threshold: int = 0
    limiter: int = 10000000
    memory_limit_percent: int = 80
    buffer_size: int = 65536


class PerformanceMetrics:
    """Track performance metrics during generation"""
    def __init__(self):
        self.start_time = time.time()
        self.usernames_generated = 0
        self.batches_written = 0
        self.memory_peak = 0
        self.last_update = time.time()
    
    def update(self, usernames_count: int, batches_count: int = 0):
        """Update metrics"""
        self.usernames_generated += usernames_count
        self.batches_written += batches_count
        self.last_update = time.time()
    
    def get_throughput(self) -> float:
        """Calculate usernames per second"""
        elapsed = time.time() - self.start_time
        return self.usernames_generated / elapsed if elapsed > 0 else 0
    
    def get_eta(self, total_usernames: int) -> float:
        """Calculate estimated time remaining"""
        if self.usernames_generated == 0:
            return 0
        throughput = self.get_throughput()
        remaining = total_usernames - self.usernames_generated
        return remaining / throughput if throughput > 0 else 0


def validate_cpu_processes(cpu_processes: int) -> int:
    """Validate and adjust CPU processes based on system capabilities"""
    max_processes = multiprocessing.cpu_count()
    if cpu_processes > max_processes:
        logger.warning(f"Requested {cpu_processes} CPU processes, but only {max_processes} available. Using {max_processes}.")
        return max_processes
    elif cpu_processes < 1:
        logger.warning(f"CPU processes must be at least 1. Using 1.")
        return 1
    else:
        return cpu_processes


@lru_cache(maxsize=1000)
def _get_pattern_formatter(pattern_type: str) -> Callable[[str, str], str]:
    """Get optimized pattern formatter with caching"""
    if pattern_type.endswith('_dot_') or 'dot' in pattern_type:
        return lambda outer, inner: f"{outer}.{inner}"
    return lambda outer, inner: f"{outer}{inner}"


def process_outer_batch_mp(outer_batch, inner_items, pattern_type):
    """Process a batch of outer items with their inner loops - multiprocessing version"""
    formatter = _get_pattern_formatter(pattern_type)
    batch_results = []
    for outer_item in outer_batch:
        for inner_item in inner_items:
            batch_results.append(formatter(outer_item, inner_item))
    return batch_results


@lru_cache(maxsize=100)
def _get_triple_pattern_formatter(pattern_type: str) -> Callable[[str, str, str], str]:
    """Get optimized triple pattern formatter with caching"""
    if pattern_type == "firstname_dot_letter_dot_lastname":
        return lambda outer, middle, inner: f"{outer}.{middle}.{inner}"
    return lambda outer, middle, inner: f"{outer}{middle}{inner}"


def process_combinations_batch_mp(combinations_batch, pattern_type):
    """Process a batch of combinations - multiprocessing version"""
    logger.debug(f"Process {os.getpid()}: Starting batch processing for {pattern_type}")
    logger.debug(f"Process {os.getpid()}: Processing {len(combinations_batch)} combinations")
    batch_results = []
    formatter = _get_triple_pattern_formatter(pattern_type)
    for outer_item, middle_item, inner_item in combinations_batch:
        batch_results.append(formatter(outer_item, middle_item, inner_item))
    logger.debug(f"Process {os.getpid()}: Completed batch processing, generated {len(batch_results):,} usernames")
    return batch_results


def process_combinations_batch_2level_mp(combinations_batch, pattern_type):
    """Process a batch of two-level combinations - multiprocessing version"""
    logger.debug(f"Process {os.getpid()}: Starting batch processing for {pattern_type}")
    logger.debug(f"Process {os.getpid()}: Processing {len(combinations_batch)} combinations")
    batch_results = []
    formatter = _get_pattern_formatter(pattern_type)
    for outer_item, inner_item in combinations_batch:
        batch_results.append(formatter(outer_item, inner_item))
    logger.debug(f"Process {os.getpid()}: Completed batch processing, generated {len(batch_results):,} usernames")
    return batch_results


def format_count(count: int) -> str:
    """Format count with appropriate suffix (no decimal for <1000, decimal for k/m)"""
    if count < 1000:
        return str(count)
    elif count < 1000000:
        return f"{count/1000:.1f}k"
    else:
        return f"{count/1000000:.1f}m"


class CustomProgressColumn(ProgressColumn):
    """Custom progress column showing x/y format with appropriate suffixes"""
    def render(self, task):
        if task.total:
            completed_str = format_count(task.completed)
            total_str = format_count(task.total)
            return f"[progress.completed]{completed_str}/{total_str}"
        return f"[progress.completed]{task.completed}"


class UsernameGenerator:
    def __init__(self, firstname_file: str, lastname_file: str, output_dir: str, processes: int = 8, 
                 batch_size: int = 300000, io_threads: int = 16, write_threshold: int = 0, 
                 clean_first: bool = False, limiter: int = 10000000):
        self.firstname_file = Path(firstname_file)
        self.lastname_file = Path(lastname_file)
        self.output_dir = Path(output_dir)
        self.cpu_processes = validate_cpu_processes(processes)
        self.batch_size = batch_size
        self.io_threads = io_threads
        self.write_threshold = write_threshold
        self.clean_first = clean_first
        self.limiter = limiter
        self.config = GeneratorConfig(
            cpu_processes=self.cpu_processes,
            batch_size=self.batch_size,
            io_threads=self.io_threads,
            write_threshold=self.write_threshold,
            limiter=self.limiter
        )
        self.metrics = PerformanceMetrics()
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Initialized with {self.cpu_processes} CPU processes, batch size {batch_size}")
        logger.info(f"Limiter {limiter:,}, output directory {output_dir}")

    def _should_continue_generation(self, current_count: int) -> bool:
        """Check if we should continue generating based on limiter"""
        if self.limiter == 0:
            return True  # Unlimited
        return current_count < self.limiter

    def _is_variant_pattern(self, pattern_name: str) -> bool:
        """Check if a pattern is a variant pattern that should use the limiter"""
        variant_patterns = ["firstname_dot_lastname",
                            "firstname_lastname",
                            "lastname_dot_firstname",
                            "lastname_firstname",
                            "firstname_dot_letter_dot_lastname",
                            "firstname_letter_lastname",
                            "firstname_dot_lastname_500x20k",
                            "firstname_dot_lastname_200x50k",
                            "firstname_dot_lastname_1kx10k",
                            "firstname_lastname_1kx10k",
                            "lastname_dot_firstname_1kx10k",
                            "lastname_firstname_1kx10k",
                            "firstname_dot_letter_dot_lastname_300x1750",
                            "firstname_letter_lastname_300x1750"]
        return pattern_name in variant_patterns

    def read_names(self, filename: Path, limit: int = None) -> List[str]:
        """Read names from file with optional limit"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                names = [line.strip() for line in f if line.strip()]
            return names[:limit] if limit else names
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
            raise

    def clean_output_directory(self, output_path: Path):
        """Clean x** files from output directory"""
        try:
            if output_path.exists():
                for file_path in output_path.glob("x*"):
                    if file_path.is_file():
                        file_path.unlink()
                        logger.debug(f"Removed {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning output directory {output_path}: {e}")
            raise

    async def _async_write_batches(self, batches_to_write: List[tuple], pattern_name: str) -> int:
        """Write batches asynchronously with controlled concurrency"""
        if not batches_to_write:
            return 0
        
        max_io_workers = min(self.io_threads, len(batches_to_write))
        semaphore = asyncio.Semaphore(max_io_workers)
        
        async def write_batch_with_semaphore(batch_data):
            async with semaphore:
                batch_num, batch_content = batch_data
                return await self._async_write_batch(batch_content, pattern_name, batch_num)
        
        tasks = [write_batch_with_semaphore(batch_data) for batch_data in batches_to_write]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_writes = sum(1 for result in results if result is True)
        failed_writes = len(results) - successful_writes
        
        if failed_writes > 0:
            logger.warning(f"Failed to write {failed_writes} out of {len(batches_to_write)} batches for {pattern_name}")
        
        logger.debug(f"Async wrote {successful_writes}/{len(batches_to_write)} batches for {pattern_name}")
        return successful_writes

    def _write_batches_concurrently(self, batches_to_write, output_path: Path, pattern_name: str):
        """Write batches with controlled concurrency to prevent I/O overload"""
        max_io_workers = min(2, len(batches_to_write))
        def write_single_batch(batch_data):
            batch_num, batch_content = batch_data
            batch_file = f"{output_path}/x{batch_num:03d}"
            try:
                with open(batch_file, 'w', encoding='utf-8') as batch_f:
                    batch_f.write('\n'.join(batch_content) + '\n')
                return True
            except Exception as e:
                logger.error(f"Error writing batch {batch_num}: {e}")
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_io_workers) as io_executor:
            future_to_batch = {
                io_executor.submit(write_single_batch, batch_data): batch_data 
                for batch_data in batches_to_write
            }
            completed_writes = 0
            for future in concurrent.futures.as_completed(future_to_batch):
                try:
                    success = future.result()
                    if success:
                        completed_writes += 1
                        if len(batches_to_write) > 100 and completed_writes % 50 == 0:
                            logger.info(f"Written {completed_writes}/{len(batches_to_write)} batches for {pattern_name}")
                except Exception as e:
                    batch_data = future_to_batch[future]
                    logger.error(f"Failed to write batch {batch_data[0]}: {e}")
                    completed_writes += 1
            gc.collect()

    def _common_generation_logic(self, pattern_name: str, total_work: int, progress_total: int, 
                                ordered_usernames: List[str], progress, task) -> bool:
        """Common logic for both concurrency methods"""
        if self._is_variant_pattern(pattern_name) and not self._should_continue_generation(len(ordered_usernames)):
            logger.debug(f"Reached limiter of {self.limiter:,} usernames, stopping generation")
            progress.update(task, completed=progress_total)
            return False
        
        if progress_total == self.limiter:
            current_progress = min(len(ordered_usernames), self.limiter)
            progress.update(task, completed=current_progress)
        else:
            progress.update(task, advance=len(ordered_usernames))
        
        return True

    def process_pattern_serial(self, pattern_name: str, generator_func, *args):
        """Process a username pattern - generation functions now handle their own concurrency"""
        try:
            generator_func(*args)
        except Exception as e:
            logger.error(f"Failed to process {pattern_name}: {e}")
            raise

    def _generate_with_concurrency(self, outer_items: List[str], inner_items: List[str], 
                                 pattern_name: str) -> List[str]:
        """Generate usernames following the exact specified logic"""
        logger.debug(f"Starting _generate_with_concurrency for {pattern_name}")
        logger.debug(f"Outer items: {len(outer_items)}, Inner items: {len(inner_items)}")
        total_work = len(outer_items) * len(inner_items)
        if self.limiter > 0 and self.limiter < total_work and self._is_variant_pattern(pattern_name):
            progress_total = self.limiter
        else:
            progress_total = total_work
        logger.debug(f"Total work units: {total_work:,}")
        logger.debug(f"Progress total: {progress_total:,} (limiter: {self.limiter:,})")
        logger.debug(f"Using {self.cpu_processes} CPU processes and {self.io_threads} I/O threads")
        batch_num = 1
        ordered_usernames = []
        with Progress(TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=None), "[progress.percentage]{task.percentage:>3.0f}%",
                      "•", CustomProgressColumn(), "•", TimeElapsedColumn(), "•", TimeRemainingColumn(),
                      console=None, auto_refresh=True) as progress:
            task = progress.add_task(f"Processing {pattern_name}", total=progress_total)
            combinations_per_round = 2500000  # Process 2.5 million combinations per round
            total_combinations = len(outer_items) * len(inner_items)
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.cpu_processes) as cpu_executor:
                for round_start in range(0, total_combinations, combinations_per_round):
                    round_end = min(round_start + combinations_per_round, total_combinations)
                    logger.debug(f"Starting round: processing combinations {round_start}-{round_end-1}")
                    round_combinations = []
                    count = 0
                    for outer_item in outer_items:
                        for inner_item in inner_items:
                            if count >= round_start and count < round_end:
                                round_combinations.append((outer_item, inner_item))
                            count += 1
                            if count >= round_end:
                                break
                        if count >= round_end:
                            break
                    futures = []
                    combinations_per_process = max(1, len(round_combinations) // self.cpu_processes)
                    for i in range(0, len(round_combinations), combinations_per_process):
                        batch_combinations = round_combinations[i:i + combinations_per_process]
                        future = cpu_executor.submit(process_combinations_batch_2level_mp, batch_combinations, pattern_name)
                        futures.append(future)
                    round_results = []
                    for future in concurrent.futures.as_completed(futures):
                        batch_results = future.result()
                        round_results.extend(batch_results)
                    ordered_usernames.extend(round_results)
                    logger.debug(f"Round completed: {len(round_results)} usernames generated, total in memory: {len(ordered_usernames):,}")
                    if progress_total == self.limiter:
                        current_progress = min(len(ordered_usernames), self.limiter)
                        progress.update(task, completed=current_progress)
                    else:
                        progress.update(task, advance=len(round_results))
                    
                    if self._is_variant_pattern(pattern_name) and not self._should_continue_generation(len(ordered_usernames)):
                        logger.debug(f"Reached limiter of {self.limiter:,} usernames, stopping generation")
                        progress.update(task, completed=progress_total)
                        break
                    if self.write_threshold > 0:
                        write_threshold = self.batch_size * self.write_threshold
                        if len(ordered_usernames) >= write_threshold:
                            batches_to_write = len(ordered_usernames) // self.batch_size
                            logger.debug(f"Writing {batches_to_write} batches to disk (batch size: {self.batch_size}, threshold: {write_threshold})")
                            with concurrent.futures.ThreadPoolExecutor(max_workers=self.io_threads) as io_executor:
                                io_futures = []
                                for _ in range(batches_to_write):
                                    batch_data = ordered_usernames[:self.batch_size]
                                    ordered_usernames = ordered_usernames[self.batch_size:]
                                    io_future = io_executor.submit(self._write_batch_to_file, batch_data, pattern_name, batch_num)
                                    io_futures.append(io_future)
                                    batch_num += 1
                                for io_future in concurrent.futures.as_completed(io_futures):
                                    io_future.result()  # Check for errors
                                logger.debug(f"Completed writing {batches_to_write} batches to disk")
                            gc.collect()
                            logger.debug(f"Memory freed, {len(ordered_usernames):,} usernames remaining in memory")
            if ordered_usernames:
                logger.debug(f"Writing final batch with {len(ordered_usernames)} remaining usernames")
                self._write_batch_to_file(ordered_usernames, pattern_name, batch_num)
                batch_num += 1
        logger.debug(f"Completed _generate_with_concurrency for {pattern_name}")
        return []

    def _generate_with_triple_concurrency(self, outer_items: List[str], middle_items: List[str], inner_items: List[str],
                                        pattern_name: str) -> List[str]:
        """Generate usernames following the exact specified logic"""
        logger.debug(f"Starting _generate_with_triple_concurrency for {pattern_name}")
        logger.debug(f"Outer items: {len(outer_items)}, Middle items: {len(middle_items)}, Inner items: {len(inner_items)}")
        total_work = len(outer_items) * len(middle_items) * len(inner_items)
        if self.limiter > 0 and self.limiter < total_work and self._is_variant_pattern(pattern_name):
            progress_total = self.limiter
        else:
            progress_total = total_work
        logger.debug(f"Total work units: {total_work:,}")
        logger.debug(f"Progress total: {progress_total:,} (limiter: {self.limiter:,})")
        logger.debug(f"Using {self.cpu_processes} CPU processes and {self.io_threads} I/O threads")
        batch_num = 1
        ordered_usernames = []
        with Progress(TextColumn("[bold blue]{task.description}"), BarColumn(bar_width=None), "[progress.percentage]{task.percentage:>3.0f}%",
                                 "•", CustomProgressColumn(), "•", TimeElapsedColumn(), "•", TimeRemainingColumn(),
                                 console=None, auto_refresh=True ) as progress:
            task = progress.add_task(f"Processing {pattern_name}", total=progress_total)
            combinations_per_round = 2500000
            total_combinations = len(outer_items) * len(middle_items) * len(inner_items)
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.cpu_processes) as cpu_executor:
                for round_start in range(0, total_combinations, combinations_per_round):
                    round_end = min(round_start + combinations_per_round, total_combinations)
                    logger.debug(f"Starting round: processing combinations {round_start}-{round_end-1}")
                    round_combinations = []
                    count = 0
                    for outer_item in outer_items:
                        for middle_item in middle_items:
                            for inner_item in inner_items:
                                if count >= round_start and count < round_end:
                                    round_combinations.append((outer_item, middle_item, inner_item))
                                count += 1
                                if count >= round_end:
                                    break
                            if count >= round_end:
                                break
                        if count >= round_end:
                            break
                    futures = []
                    combinations_per_process = max(1, len(round_combinations) // self.cpu_processes)
                    for i in range(0, len(round_combinations), combinations_per_process):
                        batch_combinations = round_combinations[i:i + combinations_per_process]
                        future = cpu_executor.submit(process_combinations_batch_mp, batch_combinations, pattern_name)
                        futures.append(future)
                    round_results = []
                    for future in concurrent.futures.as_completed(futures):
                        batch_results = future.result()
                        round_results.extend(batch_results)
                    ordered_usernames.extend(round_results)
                    logger.debug(f"Round completed: {len(round_results)} usernames generated, total in memory: {len(ordered_usernames):,}")
                    if progress_total == self.limiter:
                        current_progress = min(len(ordered_usernames), self.limiter)
                        progress.update(task, completed=current_progress)
                    else:
                        progress.update(task, advance=len(round_results))
                    
                    if self._is_variant_pattern(pattern_name) and not self._should_continue_generation(len(ordered_usernames)):
                        logger.debug(f"Reached limiter of {self.limiter:,} usernames, stopping generation")
                        progress.update(task, completed=progress_total)
                        break
                    if self.write_threshold > 0:
                        write_threshold = self.batch_size * self.write_threshold
                        if len(ordered_usernames) >= write_threshold:
                            batches_to_write = len(ordered_usernames) // self.batch_size
                            logger.debug(f"Writing {batches_to_write} batches to disk (batch size: {self.batch_size}, threshold: {write_threshold})")
                            with concurrent.futures.ThreadPoolExecutor(max_workers=self.io_threads) as io_executor:
                                io_futures = []
                                for _ in range(batches_to_write):
                                    batch_data = ordered_usernames[:self.batch_size]
                                    ordered_usernames = ordered_usernames[self.batch_size:]
                                    io_future = io_executor.submit(self._write_batch_to_file, batch_data, pattern_name, batch_num)
                                    io_futures.append(io_future)
                                    batch_num += 1
                                for io_future in concurrent.futures.as_completed(io_futures):
                                    io_future.result()
                                logger.debug(f"Completed writing {batches_to_write} batches to disk")
                            gc.collect()
                            logger.debug(f"Memory freed, {len(ordered_usernames):,} usernames remaining in memory")
            if ordered_usernames:
                logger.debug(f"Writing final batch with {len(ordered_usernames)} remaining usernames")
                self._write_batch_to_file(ordered_usernames, pattern_name, batch_num)
                batch_num += 1
        logger.debug(f"Completed _generate_with_triple_concurrency for {pattern_name}")
        return []

    def _process_triple_outer_batch(self, outer_batch: List[str], middle_items: List[str], inner_items: List[str], generate_func):
        """Process a batch of outer items with their triple nested loops"""
        batch_results = []
        for outer_item in outer_batch:
            for middle_item in middle_items:
                for inner_item in inner_items:
                    batch_results.append(generate_func(outer_item, middle_item, inner_item))
        return batch_results

    def _process_outer_batch(self, outer_batch: List[str], inner_items: List[str], generate_func):
        """Process a batch of outer items with their inner loops"""
        batch_results = []
        for outer_item in outer_batch:
            for inner_item in inner_items:
                batch_results.append(generate_func(outer_item, inner_item))
        return batch_results

    async def _async_write_batch(self, usernames: List[str], pattern_name: str, batch_num: int) -> bool:
        """Async write a batch of usernames to file"""
        if not usernames:
            logger.warning(f"Attempted to write empty batch {batch_num} for pattern {pattern_name}")
            return False
        
        safe_pattern_name = pattern_name.replace('.', '_').replace('/', '_').replace('\\', '_')
        pattern_dir = Path(f"{self.output_dir}/tron_{safe_pattern_name}")
        pattern_dir.mkdir(parents=True, exist_ok=True)
        batch_file = pattern_dir / f"x{batch_num:03d}"
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_write_batch, usernames, batch_file)
            self.metrics.update(len(usernames), 1)
            logger.debug(f"Async wrote batch {batch_num}: {len(usernames)} usernames to {batch_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to async write batch {batch_num} to {batch_file}: {e}")
            return False
    
    def _sync_write_batch(self, usernames: List[str], batch_file: Path):
        """Synchronous write helper for async operations"""
        with open(batch_file, 'w', encoding='utf-8', buffering=self.config.buffer_size) as f:
            f.write('\n'.join(usernames) + '\n')

    def _write_batch_to_file(self, usernames: List[str], pattern_name: str, batch_num: int):
        """Write a batch of usernames to file - optimized for performance"""
        if not usernames:
            logger.warning(f"Attempted to write empty batch {batch_num} for pattern {pattern_name}")
            return
        logger.debug(f"Writing batch {batch_num} for pattern {pattern_name}: {len(usernames)} usernames")
        safe_pattern_name = pattern_name.replace('.', '_').replace('/', '_').replace('\\', '_')
        pattern_dir = Path(f"{self.output_dir}/tron_{safe_pattern_name}")
        pattern_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created/verified directory: {pattern_dir}")
        batch_file = pattern_dir / f"x{batch_num:03d}"
        logger.debug(f"Writing to file: {batch_file}")
        try:
            self._sync_write_batch(usernames, batch_file)
            file_size = batch_file.stat().st_size
            self.metrics.update(len(usernames), 1)
            logger.debug(f"Successfully wrote batch {batch_num}: {len(usernames)} usernames, {file_size:,} bytes to {batch_file}")
        except Exception as e:
            logger.error(f"Failed to write batch {batch_num} to {batch_file}: {e}")
            raise

    def generate_firstnameletter_lastname(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "firstnameletter_lastname") -> List[str]:
        """Generate jsmith pattern: {firstnameletter}{lastname}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        firstnameletters = sorted({firstname[0].lower() for firstname in firstnames if firstname and firstname[0].isalpha()})
        logger.debug(f"Extracted {len(firstnameletters)} unique firstname letters: {firstnameletters}")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(firstnameletters, lastnames, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_lastname_firstnameletter(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "lastname_firstnameletter") -> List[str]:
        """Generate smithj pattern: {lastname}{firstnameletter}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        firstnameletters = sorted({firstname[0].lower() for firstname in firstnames if firstname and firstname[0].isalpha()})
        logger.debug(f"Extracted {len(firstnameletters)} unique firstname letters: {firstnameletters}")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(lastnames, firstnameletters, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_firstnameletter_dot_lastname(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "firstnameletter_dot_lastname") -> List[str]:
        """Generate j.smith pattern: {firstnameletter}.{lastname}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        firstnameletters = sorted({firstname[0].lower() for firstname in firstnames if firstname and firstname[0].isalpha()})
        logger.debug(f"Extracted {len(firstnameletters)} unique firstname letters: {firstnameletters}")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(firstnameletters, lastnames, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_lastname_dot_firstnameletter(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "lastname_dot_firstnameletter") -> List[str]:
        """Generate smith.j pattern: {lastname}.{firstnameletter}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        firstnameletters = sorted({firstname[0].lower() for firstname in firstnames if firstname and firstname[0].isalpha()})
        logger.debug(f"Extracted {len(firstnameletters)} unique firstname letters: {firstnameletters}")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(lastnames, firstnameletters, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_firstname_lastnameletter(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "firstname_lastnameletter") -> List[str]:
        """Generate johns pattern: {firstname}{lastnameletter}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        lastnameletters = sorted({lastname[0].lower() for lastname in lastnames if lastname and lastname[0].isalpha()})
        logger.debug(f"Extracted {len(lastnameletters)} unique lastname letters: {lastnameletters}")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(firstnames, lastnameletters, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_lastnameletter_firstname(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "lastnameletter_firstname") -> List[str]:
        """Generate sjohn pattern: {lastnameletter}{firstname}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        lastnameletters = sorted({lastname[0].lower() for lastname in lastnames if lastname and lastname[0].isalpha()})
        logger.debug(f"Extracted {len(lastnameletters)} unique lastname letters: {lastnameletters}")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(lastnameletters, firstnames, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_firstname_dot_lastnameletter(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "firstname_dot_lastnameletter") -> List[str]:
        """Generate john.s pattern: {firstname}.{lastnameletter}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        lastnameletters = sorted({lastname[0].lower() for lastname in lastnames if lastname and lastname[0].isalpha()})
        logger.debug(f"Extracted {len(lastnameletters)} unique lastname letters: {lastnameletters}")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(firstnames, lastnameletters, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_lastnameletter_dot_firstname(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "lastnameletter_dot_firstname") -> List[str]:
        """Generate s.john pattern: {lastnameletter}.{firstname}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        lastnameletters = sorted({lastname[0].lower() for lastname in lastnames if lastname and lastname[0].isalpha()})
        logger.debug(f"Extracted {len(lastnameletters)} unique lastname letters: {lastnameletters}")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(lastnameletters, firstnames, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_lastname_firstnameletter_letter(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "lastname_firstnameletter_letter") -> List[str]:
        """Generate smithja pattern: {lastname}{firstnameletter}{letter}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        firstnameletters = sorted({firstname[0].lower() for firstname in firstnames if firstname and firstname[0].isalpha()})
        logger.debug(f"Extracted {len(firstnameletters)} unique firstname letters: {firstnameletters}")
        logger.debug(f"Using {len(ALPHA_LIST)} letters from ALPHA_LIST: {ALPHA_LIST}")
        logger.debug(f"Starting triple concurrency processing...")
        result = self._generate_with_triple_concurrency(lastnames, firstnameletters, ALPHA_LIST, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_firstname_dot_lastname(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "firstname_dot_lastname") -> List[str]:
        """Generate john.smith pattern: {firstname}.{lastname}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(firstnames, lastnames, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_firstname_lastname(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "firstname_lastname") -> List[str]:
        """Generate johnsmith pattern: {firstname}{lastname}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(firstnames, lastnames, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_lastname_dot_firstname(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "lastname_dot_firstname") -> List[str]:
        """Generate smith.john pattern: {lastname}.{firstname}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(lastnames, firstnames, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_lastname_firstname(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "lastname_firstname") -> List[str]:
        """Generate smithjohn pattern: {lastname}{firstname}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        logger.debug(f"Starting dual concurrency processing...")
        result = self._generate_with_concurrency(lastnames, firstnames, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_firstname_dot_letter_dot_lastname(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "firstname_dot_letter_dot_lastname") -> List[str]:
        """Generate john.j.smith pattern: {firstname}.{letter}.{lastname}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        logger.debug(f"Using {len(ALPHA_LIST)} letters from ALPHA_LIST: {ALPHA_LIST}")
        logger.debug(f"Starting triple concurrency processing...")
        result = self._generate_with_triple_concurrency(firstnames, ALPHA_LIST, lastnames, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_firstname_letter_lastname(self, firstnames: List[str], lastnames: List[str], pattern_name: str = "firstname_letter_lastname") -> List[str]:
        """Generate johnjsmith pattern: {firstname}{letter}{lastname}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Input: {len(firstnames)} firstnames, {len(lastnames)} lastnames")
        logger.debug(f"Using {len(ALPHA_LIST)} letters from ALPHA_LIST: {ALPHA_LIST}")
        logger.debug(f"Starting triple concurrency processing...")
        result = self._generate_with_triple_concurrency(firstnames, ALPHA_LIST, lastnames, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def generate_letter_letter_letter(self, pattern_name: str = "letter_letter_letter") -> List[str]:
        """Generate jjs_all pattern: {letter1}{letter2}{letter3}"""
        logger.debug(f"Starting {pattern_name} generation")
        logger.debug(f"Using {len(ALPHA_LIST)} letters from ALPHA_LIST: {ALPHA_LIST}")
        logger.debug(f"Starting triple concurrency processing...")
        result = self._generate_with_triple_concurrency(ALPHA_LIST, ALPHA_LIST, ALPHA_LIST, pattern_name)
        logger.debug(f"Completed {pattern_name} generation")
        return result

    def run_all_patterns(self, firstnames: List[str], lastnames: List[str]):
        """Run all patterns"""
        if self.clean_first:
            logger.info("Cleaning pattern output directories")
            import shutil
            pattern_dirs = ["firstnameletter_lastname", "lastname_firstnameletter", "firstnameletter_dot_lastname",
                            "lastname_dot_firstnameletter", "firstname_lastnameletter", "lastnameletter_firstname",
                            "firstname_dot_lastnameletter", "lastnameletter_dot_firstname", "lastname_firstnameletter_letter",
                            "firstname_lastname", "lastname_dot_firstname", "lastname_firstname",
                            "firstname_dot_letter_dot_lastname", "firstname_letter_lastname", "firstname_dot_lastname",
                            "firstname_dot_lastname_500x20k", "firstname_dot_lastname_200x50k", "firstname_dot_lastname_1kx10k",
                            "firstname_lastname_1kx10k", "lastname_dot_firstname_1kx10k", "lastname_firstname_1kx10k",
                            "firstname_dot_letter_dot_lastname_300x1750", "firstname_letter_lastname_300x1750", "letter_letter_letter"]
            for pattern_dir in pattern_dirs:
                pattern_path = self.output_dir / pattern_dir
                if pattern_path.exists():
                    shutil.rmtree(pattern_path)
                    logger.debug(f"Cleaned directory: {pattern_path}")
        
        all_patterns = [# General patterns
                        ("firstnameletter_lastname", self.generate_firstnameletter_lastname, firstnames, lastnames),
                        ("lastname_firstnameletter", self.generate_lastname_firstnameletter, firstnames, lastnames),
                        ("firstnameletter_dot_lastname", self.generate_firstnameletter_dot_lastname, firstnames, lastnames),
                        ("lastname_dot_firstnameletter",self.generate_lastname_dot_firstnameletter, firstnames, lastnames),
                        ("firstname_lastnameletter", self.generate_firstname_lastnameletter, firstnames, lastnames),
                        ("lastnameletter_firstname", self.generate_lastnameletter_firstname, firstnames, lastnames),
                        ("firstname_dot_lastnameletter", self.generate_firstname_dot_lastnameletter, firstnames, lastnames),
                        ("lastnameletter_dot_firstname", self.generate_lastnameletter_dot_firstname, firstnames, lastnames),
                        ("lastname_firstnameletter_letter", self.generate_lastname_firstnameletter_letter, firstnames, lastnames),
                        # Full name patterns
                        ("firstname_lastname", self.generate_firstname_lastname, firstnames, lastnames),
                        ("lastname_dot_firstname", self.generate_lastname_dot_firstname, firstnames, lastnames),
                        ("lastname_firstname", self.generate_lastname_firstname, firstnames, lastnames),
                        ("firstname_dot_letter_dot_lastname", self.generate_firstname_dot_letter_dot_lastname, firstnames, lastnames),
                        ("firstname_letter_lastname", self.generate_firstname_letter_lastname, firstnames, lastnames),
                        # Variant patterns
                        ("firstname_dot_lastname", self.generate_firstname_dot_lastname, firstnames, lastnames),
                        ("firstname_dot_lastname_500x20k", self.generate_firstname_dot_lastname, firstnames[:500], lastnames[:20000]),
                        ("firstname_dot_lastname_200x50k", self.generate_firstname_dot_lastname, firstnames[:200], lastnames[:50000]),
                        ("firstname_dot_lastname_1kx10k", self.generate_firstname_dot_lastname, firstnames[:1000], lastnames[:10000]),
                        ("firstname_lastname_1kx10k", self.generate_firstname_lastname, firstnames[:1000], lastnames[:10000]),
                        ("lastname_dot_firstname_1kx10k", self.generate_lastname_dot_firstname, firstnames[:1000], lastnames[:10000]),
                        ("lastname_firstname_1kx10k", self.generate_lastname_firstname, firstnames[:1000], lastnames[:10000]),
                        ("firstname_dot_letter_dot_lastname_300x1750", self.generate_firstname_dot_letter_dot_lastname, firstnames[:300], lastnames[:1750]),
                        ("firstname_letter_lastname_300x1750", self.generate_firstname_letter_lastname, firstnames[:300], lastnames[:1750]),
                        ("letter_letter_letter", self.generate_letter_letter_letter),]
        for _, pattern_data in enumerate(all_patterns):
            pattern_name = pattern_data[0]
            try:
                if len(pattern_data) == 5:
                    pattern_name, func, first_arg, last_arg, display_name = pattern_data
                    self.process_pattern_serial(pattern_name, func, first_arg, last_arg, display_name)
                elif len(pattern_data) == 4:
                    pattern_name, func, first_arg, last_arg = pattern_data
                    self.process_pattern_serial(pattern_name, func, first_arg, last_arg)
                elif len(pattern_data) == 3:
                    pattern_name, func, arg = pattern_data
                    self.process_pattern_serial(pattern_name, func, arg)
                else:
                    pattern_name, func = pattern_data
                    self.process_pattern_serial(pattern_name, func)
            except Exception as e:
                logger.error(f"Failed to process {pattern_name}: {e}")
                continue
            gc.collect()

    def _count_file_lines_fast(self, file_path: Path) -> int:
        """Fast line counting using buffered reading"""
        try:
            with open(file_path, 'rb') as f:
                return sum(1 for _ in f)
        except Exception as e:
            logger.warning(f"Could not count lines in {file_path}: {e}")
            return 0

    def _process_file_for_counts(self, username_file: Path) -> tuple:
        """Process a single file for counting - multiprocessing version"""
        pattern_dir = username_file.parent
        count = self._count_file_lines_fast(username_file)
        return pattern_dir, count

    def generate_username_counts_csv(self):
        """Generate CSV file with username counts for each pattern directory - optimized"""
        try:
            csv_file = f"{self.output_dir}username_counts.txt"
            logger.info("Starting fast username count generation...")
            username_files = [f for f in self.output_dir.rglob("x*") if f.is_file()]
            logger.info(f"Found {len(username_files)} files to process")
            if not username_files:
                logger.warning("No username files found to count")
                return
            pattern_counts = {}
            max_workers = min(self.cpu_processes, len(username_files))
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(self._process_file_for_counts, username_file): username_file for 
                                  username_file in username_files}
                completed = 0
                for future in concurrent.futures.as_completed(future_to_file):
                    try:
                        pattern_dir, count = future.result()
                        if pattern_dir not in pattern_counts:
                            pattern_counts[pattern_dir] = 0
                        pattern_counts[pattern_dir] += count
                        completed += 1
                        if completed % 100 == 0:
                            logger.info(f"Processed {completed}/{len(username_files)} files")
                    except Exception as e:
                        username_file = future_to_file[future]
                        logger.warning(f"Error processing {username_file}: {e}")
            logger.info("Writing CSV results...")
            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write("count,pattern,directory\n")
                for pattern_dir, total_count in sorted(pattern_counts.items()):
                    pattern_name = pattern_dir.name.replace("tron_", "").replace("_", ".")
                    f.write(f"{total_count},{pattern_name},{pattern_dir}\n")
            total_usernames = sum(pattern_counts.values())
            logger.info(f"Generated username counts CSV: {csv_file}")
            logger.info(f"Total usernames counted: {total_usernames:,} across {len(pattern_counts)} patterns")
        except Exception as e:
            logger.error(f"Error generating username counts CSV: {e}")
            raise

    def run(self):
        """Main execution method"""
        firstnames = self.read_names(self.firstname_file)
        lastnames = self.read_names(self.lastname_file)
        logger.info(f"Loaded {len(firstnames)} firstnames and {len(lastnames)} lastnames")
        logger.info("Starting all pattern generation...")
        self.run_all_patterns(firstnames, lastnames)
        logger.info("Generating username counts CSV...")
        self.generate_username_counts_csv()
        logger.info("We're finished!")

def main():
    """Main function with warning notice and argument parsing"""
    warning_msg = """*************************************************************************************
 HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP GIGS OF DISK SPACE!!! 
*************************************************************************************\n
"""
    parser = argparse.ArgumentParser(description='Generate usernames')
    parser.add_argument('-f', '--firstname', required=True, help='Firstname file path')
    parser.add_argument('-l', '--lastname', required=True, help='Lastname file path')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('-p', '--processes', type=int, default=10, help='Number of CPU processes (I/O threads will be processes * 2) (default: 8)')
    parser.add_argument('-c', '--batch-size', type=int, default=1000000, help='Batch size for file splitting (default: 1000000)')
    parser.add_argument('-w', '--write-threshold', type=int, default=0, help='Write threshold multiplier (default: 0)')
    parser.add_argument('--limiter', type=int, default=10000000, help='Limit total combinations generated (set to 0 for unlimited) (default: 10,000,000)')
    parser.add_argument('--clean-first', action='store_true', help='Clean output directories before generating new files')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging for detailed output')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")
    else:
        logging.getLogger().setLevel(logging.INFO)
    print(warning_msg * 5)
    input("Press Enter to continue...")
    
    if args.batch_size < 1000:
        logger.error("Batch size must be at least 1000")
        sys.exit(1)
    try:
        io_threads = args.processes * 2
        generator = UsernameGenerator(args.firstname, args.lastname, args.output, args.processes, args.batch_size, io_threads, args.write_threshold, args.clean_first, args.limiter)
        generator.run()
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()