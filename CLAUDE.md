# CLAUDE.md - AI Assistant Guide for HtmlDoc2PDF

This document provides comprehensive information about the HtmlDoc2PDF codebase for AI assistants working with this repository.

## 📋 Project Overview

**HtmlDoc2PDF** is a Playwright-based HTML to PDF batch conversion tool specifically designed for DolphinDB technical documentation. It converts HTML files to PDF format with high fidelity, supporting modern web features, CSS, and JavaScript.

**Key Features:**
- Playwright + Chromium rendering engine for perfect HTML/CSS/JS support
- Multi-process concurrent processing (6 workers can process 500+ files in ~5 minutes)
- Built-in HTTP server to solve resource path issues
- Flexible YAML configuration and CLI parameters
- Robust error handling with automatic retry mechanism
- Incremental conversion (skips existing PDFs)
- Real-time progress feedback with tqdm
- Optimized for DolphinDB documentation structure

**Technology Stack:**
- Python 3.7+
- Playwright (async_playwright)
- PyYAML for configuration
- tqdm for progress bars
- multiprocessing for parallelization

---

## 🏗️ Codebase Structure

```
HtmlDoc2PDF/
├── src/                      # Source code modules
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management with dataclasses
│   ├── logger.py            # Multi-process safe logging with colors
│   ├── utils.py             # Utility functions (path, format, network)
│   ├── server.py            # Local HTTP server for serving HTML files
│   ├── converter.py         # Playwright PDF converter (async)
│   ├── scanner.py           # File scanner with glob pattern matching
│   └── processor.py         # Batch processor with multiprocessing
├── config/                   # Configuration files
│   ├── default.yaml         # Default configuration template
│   └── dolphindb.yaml       # DolphinDB-specific configuration
├── main.py                  # CLI entry point
├── test_installation.py     # Installation verification script
├── requirements.txt         # Python dependencies
├── README.md                # User-facing documentation (Chinese)
├── USAGE.md                 # Detailed usage guide (Chinese)
└── .gitignore              # Git ignore patterns

Output Directories (gitignored):
├── output/                  # Generated PDF files
└── logs/                    # Conversion logs
```

---

## 🔧 Module Architecture

### 1. **config.py** - Configuration Management
- **Purpose:** Centralized configuration using dataclasses
- **Key Classes:**
  - `InputConfig`: Input directory, include/exclude patterns
  - `OutputConfig`: Output directory, structure options
  - `ServerConfig`: HTTP server settings
  - `PDFConfig`: PDF format, margins, headers/footers
  - `BrowserConfig`: Playwright browser options
  - `ProcessingConfig`: Concurrency, retry settings
  - `LoggingConfig`: Log levels and output
  - `Config`: Main config class combining all sub-configs
  - `ConfigLoader`: Load/save YAML configs

- **Design Pattern:** Dataclass-based configuration with validation
- **Key Methods:**
  - `Config.validate()`: Returns list of validation errors
  - `ConfigLoader.load_from_yaml()`: Load from YAML file
  - `ConfigLoader.merge_configs()`: Deep merge configurations

### 2. **logger.py** - Logging System
- **Purpose:** Multi-process safe logging with colored console output
- **Key Classes:**
  - `ColoredFormatter`: ANSI color formatting for console
  - `Logger`: Singleton logger manager

- **Features:**
  - Separate file and console handlers
  - Process ID tracking for multiprocessing
  - Timestamp support in log file names
  - Color-coded log levels (DEBUG=cyan, INFO=green, WARNING=yellow, ERROR=red)

### 3. **utils.py** - Utility Functions
- **Purpose:** Helper functions for common tasks
- **Key Functions:**
  - `normalize_path()`: Standardize and resolve paths
  - `ensure_dir()`: Create directory if not exists
  - `build_output_path()`: Generate PDF output path
  - `format_size()`: Human-readable file sizes (B, KB, MB, GB)
  - `format_duration()`: Human-readable time (s, m, h)
  - `find_available_port()`: Find unused network port
  - `is_port_in_use()`: Check port availability
  - `sanitize_filename()`: Remove illegal file name characters

### 4. **server.py** - HTTP Server
- **Purpose:** Local HTTP server to serve HTML files and resources
- **Key Classes:**
  - `SilentHTTPRequestHandler`: Silent HTTP handler (no access logs)
  - `LocalHTTPServer`: Threaded HTTP server manager

- **Features:**
  - Auto port finding if requested port is occupied
  - Runs in background daemon thread
  - Context manager support (`with` statement)
  - Proper cleanup on shutdown

### 5. **converter.py** - PDF Conversion
- **Purpose:** Playwright-based HTML to PDF conversion
- **Key Classes:**
  - `ConversionResult`: Dataclass for conversion results
  - `PlaywrightConverter`: Async converter using Playwright

- **Features:**
  - Async/await architecture
  - Browser instance reuse for efficiency
  - CSS injection to hide unnecessary elements (search boxes, navigation)
  - Timeout handling
  - Resource cleanup with context manager
  - Synchronous wrapper `convert_html_to_pdf_sync()` for multiprocessing

- **Browser Launch Args:**
  ```python
  --no-sandbox
  --disable-setuid-sandbox
  --disable-dev-shm-usage
  --disable-web-security
  --allow-file-access-from-files
  --disable-features=IsolateOrigins,site-per-process
  --font-render-hinting=none
  ```

### 6. **scanner.py** - File Scanner
- **Purpose:** Scan and filter HTML files based on patterns
- **Key Classes:**
  - `FileTask`: Dataclass representing a conversion task
  - `FileScanner`: File discovery and filtering

- **Features:**
  - Glob pattern matching for include/exclude
  - Recursive and non-recursive scanning
  - Existing PDF detection (for incremental conversion)
  - URL construction (HTTP or file://)
  - Directory structure preservation

### 7. **processor.py** - Batch Processing
- **Purpose:** Orchestrate multi-process batch conversion
- **Key Classes:**
  - `ProcessingStats`: Statistics tracking
  - `BatchProcessor`: Main processing coordinator

- **Features:**
  - Sequential mode (workers=1) for debugging
  - Parallel mode (multiprocessing.Pool) for production
  - Retry mechanism with configurable attempts and delay
  - Progress bar using tqdm
  - Worker process initialization
  - Statistics collection (success rate, total size, duration)

### 8. **main.py** - CLI Entry Point
- **Purpose:** Command-line interface and application orchestration
- **Key Functions:**
  - `parse_args()`: argparse setup
  - `load_config()`: Config loading with CLI overrides
  - `main()`: Application lifecycle management

- **Workflow:**
  1. Parse CLI arguments
  2. Load configuration (file or default)
  3. Apply CLI overrides
  4. Validate configuration
  5. Initialize logging
  6. Start HTTP server (if enabled)
  7. Scan files
  8. Process batch (or dry-run preview)
  9. Cleanup and shutdown

---

## ⚙️ Configuration System

### Configuration Hierarchy
1. **Default values** in dataclass definitions
2. **YAML file** configuration (`--config`)
3. **CLI arguments** override YAML settings

### Key Configuration Sections

#### Input Configuration
```yaml
input:
  directory: "."                    # Input root directory
  recursive: true                   # Recursive scanning
  include_patterns:                 # Glob patterns to include
    - "**/*.html"
  exclude_patterns:                 # Glob patterns to exclude
    - "oxygen-webhelp/**"
```

#### Output Configuration
```yaml
output:
  directory: "./output"             # Output directory
  keep_structure: true              # Preserve directory structure
  overwrite: false                  # Skip existing PDFs
```

#### PDF Configuration
```yaml
pdf:
  format: "A4"                      # A4, Letter, A3, A5, Legal, Tabloid
  landscape: false                  # Portrait or landscape
  margin:
    top: "15mm"
    bottom: "15mm"
    left: "12mm"
    right: "12mm"
  print_background: true            # Include background colors/images
  scale: 0.95                       # Page scale (0.1-2.0)
  display_header_footer: false      # Show header/footer
```

#### Processing Configuration
```yaml
processing:
  workers: 6                        # Concurrent processes (1-32)
  retry_count: 3                    # Retry attempts
  retry_delay: 2                    # Delay between retries (seconds)
  skip_errors: true                 # Continue on errors
```

---

## 🔄 Development Workflows

### Adding New Features

1. **New Configuration Options:**
   - Add field to appropriate `*Config` dataclass in `config.py`
   - Add validation in `Config.validate()` if needed
   - Update YAML files in `config/`
   - Document in README.md

2. **New PDF Processing Options:**
   - Modify `PlaywrightConverter.convert()` in `converter.py`
   - Add configuration to `PDFConfig`
   - Test with `test_installation.py` or manual testing

3. **New File Filtering:**
   - Modify `FileScanner` methods in `scanner.py`
   - Add configuration options to `InputConfig`
   - Test with `--dry-run` mode

### Testing Strategy

**Installation Testing:**
```bash
python test_installation.py
```

**Dry-Run Testing:**
```bash
python main.py --config config/dolphindb.yaml --dry-run
```

**Debug Mode (Single Process):**
```bash
python main.py --input ./docs --output ./pdfs --debug
```

**Module-Level Testing:**
Each module has `if __name__ == "__main__"` test code:
```bash
python -m src.config
python -m src.scanner
python -m src.server
```

### Common Development Tasks

#### 1. Modify Playwright Browser Settings
**Location:** `converter.py:54-67`
```python
browser_args = [
    '--no-sandbox',
    # Add new args here
]
```

#### 2. Change PDF Styling
**Location:** `converter.py:126-147`
```python
await page.add_style_tag(content="""
    /* Add custom CSS here */
""")
```

#### 3. Add New CLI Argument
**Location:** `main.py:18-93`
```python
parser.add_argument(
    '--new-option',
    help='Description',
    type=str
)
```

#### 4. Modify Retry Logic
**Location:** `processor.py:179-213`
```python
for attempt in range(self.config.processing.retry_count):
    # Retry logic here
```

#### 5. Change Log Format
**Location:** `config/default.yaml` or `logger.py:88-94`
```yaml
logging:
  format: "[{time}] [{level}] {message}"
```

---

## 📝 Code Style & Conventions

### Python Style
- **Docstrings:** Google-style docstrings for all public functions/classes
- **Type Hints:** Used throughout for function parameters and returns
- **Imports:** Grouped (stdlib, third-party, local) with blank lines
- **Line Length:** Generally < 100 characters
- **Encoding:** UTF-8 with Chinese comments/strings

### Naming Conventions
- **Classes:** PascalCase (`PlaywrightConverter`)
- **Functions/Methods:** snake_case (`convert_html_to_pdf_sync`)
- **Constants:** UPPER_SNAKE_CASE (`COLORS`, `RESET`)
- **Private:** Leading underscore (`_worker_init`, `_process_single_task`)

### Documentation Language
- **User-facing docs:** Chinese (README.md, USAGE.md, log messages)
- **Code comments:** Mixed Chinese/English
- **Docstrings:** Chinese with English technical terms

### Error Handling
- **Configuration errors:** Validate early, return error list
- **Runtime errors:** Try-except with logging, return ConversionResult
- **Multiprocessing errors:** Timeout handling, process pool cleanup
- **Resource cleanup:** Context managers (`with` statements)

---

## 🐛 Debugging & Troubleshooting

### Debug Mode
Enable with `--debug` flag:
- Sets log level to DEBUG
- Forces single-process mode (workers=1)
- More detailed error messages

### Common Issues & Solutions

#### 1. "playwright not found"
**Solution:** Install Playwright browsers
```bash
playwright install chromium
```

#### 2. Chinese Characters Display as Blocks
**Solution:** Install Chinese fonts
```bash
# Ubuntu/Debian
sudo apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei

# CentOS
sudo yum install -y wqy-microhei-fonts
```

#### 3. Port Already in Use
**Solution:** Use `auto_find_port: true` or specify different port
```bash
python main.py --port 8080
```

#### 4. Conversion Timeouts
**Solution:** Increase timeout in config
```yaml
browser:
  timeout: 120000  # 120 seconds
  wait_after_load: 3000
```

#### 5. Multiprocessing Issues on Windows
**Note:** multiprocessing requires `if __name__ == "__main__"` guard
**Current code:** Already properly structured

### Log File Analysis
```bash
# View full log
cat logs/conversion.log

# Show errors only
grep ERROR logs/conversion.log

# Show statistics
grep "处理完成" logs/conversion.log

# Follow live updates
tail -f logs/conversion.log
```

---

## 🔍 Key Design Decisions

### 1. **Multiprocessing Over Threading**
- **Rationale:** Python GIL limits threading; multiprocessing achieves true parallelism
- **Trade-off:** Higher memory usage, but much faster for CPU-bound tasks
- **Implementation:** `multiprocessing.Pool` with worker initialization

### 2. **HTTP Server for Resource Loading**
- **Rationale:** `file://` protocol has CORS restrictions; HTTP solves this
- **Alternative:** `--no-server` flag uses `file://` if resources are embedded
- **Implementation:** Threaded HTTP server in background

### 3. **Async Playwright with Sync Wrapper**
- **Rationale:** Playwright is async-first, but multiprocessing needs sync functions
- **Implementation:** `convert_html_to_pdf_sync()` wraps async code with `asyncio.run()`

### 4. **Dataclass-Based Configuration**
- **Rationale:** Type safety, validation, easy serialization
- **Alternative:** Plain dicts (rejected for lack of type safety)
- **Implementation:** Nested dataclasses with `from_dict()` factory

### 5. **Incremental Conversion (Skip Existing)**
- **Rationale:** Large doc sets take time; incremental updates are common
- **Implementation:** `_filter_existing()` in scanner.py
- **Override:** `--overwrite` flag forces re-conversion

---

## 🚀 Performance Optimization

### Current Performance
| Workers | Time (~500 files) | Memory | CPU |
|---------|-------------------|--------|-----|
| 1       | ~25 minutes       | ~500MB | 1 core 100% |
| 4       | ~7 minutes        | ~2GB   | 4 cores 100% |
| 6       | ~5 minutes        | ~3GB   | 6 cores 100% |
| 8       | ~4 minutes        | ~4GB   | 8 cores 100% |

### Optimization Guidelines

**1. Worker Count Tuning:**
- Optimal: CPU cores - 1 (leave headroom for OS)
- Maximum: 32 (enforced in validation)
- Trade-off: Memory vs. speed

**2. Browser Settings:**
```yaml
browser:
  headless: true              # Always keep headless=true
  wait_until: "networkidle"   # vs "load" or "domcontentloaded"
  wait_after_load: 2000       # Reduce if content is simple
```

**3. Output Location:**
- Use SSD for output directory
- Network drives significantly slow down I/O

**4. Exclude Patterns:**
- Exclude as much as possible upfront
- Scanning is fast, conversion is slow

---

## 🔐 Security Considerations

### Browser Security Flags
- `--no-sandbox`: Required for containers, reduces security
- `--disable-web-security`: Allows cross-origin resources
- **Recommendation:** Only process trusted HTML files

### File Path Handling
- All paths resolved to absolute paths
- `sanitize_filename()` prevents path traversal
- Input validation in `Config.validate()`

### Logging Sensitivity
- Logs include file paths (may contain sensitive info)
- Logs stored locally, not transmitted
- Consider log rotation for long-running instances

---

## 📚 External Dependencies

### Required
- **playwright** (v1.40.0): Browser automation
- **pyyaml** (v6.0.1): YAML parsing
- **tqdm** (v4.66.1): Progress bars

### Optional
- **pytest** (v7.4.3): Testing framework
- **pytest-asyncio** (v0.21.1): Async test support
- **python-dotenv** (v1.0.0): Environment variables

### System Dependencies
- **Chromium browser:** Installed via `playwright install chromium`
- **Chinese fonts:** Required for Chinese text rendering

---

## 🛠️ AI Assistant Guidelines

### When Making Changes

1. **Always read relevant files first** before making changes
2. **Test with `--dry-run`** before full conversion
3. **Use `--debug` mode** when troubleshooting
4. **Check validation** with `Config.validate()`
5. **Update both code and docs** when adding features
6. **Preserve Chinese language** in user-facing messages
7. **Maintain type hints** for all functions
8. **Add docstrings** for new public methods

### Common Tasks Quick Reference

| Task | Files to Modify | Testing Method |
|------|----------------|----------------|
| Add CLI flag | `main.py` | Run with `--help` |
| Change PDF settings | `config.py`, `converter.py` | Single file test |
| Modify file filtering | `scanner.py` | Use `--dry-run` |
| Adjust retry logic | `processor.py` | Debug mode |
| Update logging | `logger.py` | Check log files |
| HTTP server config | `server.py` | Standalone test |

### Code Review Checklist
- [ ] Type hints added for new functions
- [ ] Docstrings in Google format (Chinese)
- [ ] Error handling with appropriate logging
- [ ] Resource cleanup (context managers)
- [ ] Configuration validation if needed
- [ ] Updated YAML files if config changed
- [ ] Manual testing performed
- [ ] No hardcoded paths or credentials

---

## 📖 Additional Resources

### Internal Documentation
- `README.md`: User guide and quick start (Chinese)
- `USAGE.md`: Detailed usage examples (Chinese)
- `config/default.yaml`: Full configuration reference with comments
- `config/dolphindb.yaml`: Production example for DolphinDB docs

### External References
- [Playwright Python Docs](https://playwright.dev/python/docs/intro)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [Python multiprocessing](https://docs.python.org/3/library/multiprocessing.html)

---

## 🔄 Version History

### v0.1.0 (2025-11-13) - Initial Release
- Core framework (config, logger, utils)
- HTTP server for resource serving
- Playwright PDF converter
- File scanner with glob matching
- Batch processor with multiprocessing
- Complete CLI interface
- DolphinDB-specific optimizations

### Planned Features (v0.2.0+)
- PDF bookmarks from HTML headings
- Watermark support
- PDF encryption/password protection
- Docker containerization
- Web UI for non-technical users

---

## 📝 Notes for Claude Code

### When Committing
- Commit messages should be in English
- Follow conventional commits format: `type(scope): message`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Example: `feat(converter): add support for custom CSS injection`

### When Creating PRs
- Title: Clear, descriptive summary
- Body:
  - Summary section (2-3 bullet points)
  - Test plan section (how it was tested)
- Base branch: Usually `main`

### Testing Before Push
```bash
# 1. Verify installation
python test_installation.py

# 2. Dry run test
python main.py --input ./test_files --dry-run

# 3. Small batch test
python main.py --input ./test_files --output ./test_output --workers 2

# 4. Check logs
cat logs/conversion.log | grep ERROR
```

---

**Last Updated:** 2025-11-14
**Maintained By:** AI Assistant (Claude)
**Contact:** Open GitHub issue for questions
