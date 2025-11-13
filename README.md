# HtmlDoc2PDF

基于Playwright的HTML文档批量转PDF工具,专为DolphinDB技术文档设计。

## ✨ 特性

- ✅ **完美渲染**: 基于Playwright + Chromium,完美支持现代Web特性、CSS和JavaScript
- ✅ **高效并发**: 多进程并发处理,6个worker可在5分钟内处理500+文件
- ✅ **智能路径**: 内置HTTP服务器,自动解决HTML资源路径问题
- ✅ **灵活配置**: 支持YAML配置文件和命令行参数,配置项丰富
- ✅ **容错机制**: 完善的错误处理和自动重试机制,跳过失败项继续处理
- ✅ **断点续转**: 自动跳过已存在的PDF,支持增量转换
- ✅ **实时反馈**: tqdm进度条实时显示,彩色日志清晰明了
- ✅ **DolphinDB优化**: 专门针对DolphinDB文档目录结构优化

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone <repo-url>
cd HtmlDoc2PDF

# 创建虚拟环境(推荐)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器(必需!)
playwright install chromium

# 验证安装
python test_installation.py
```

### 2. 基础使用

```bash
# 方式1: 使用配置文件(推荐)
python main.py --config config/dolphindb.yaml

# 方式2: 命令行参数
python main.py --input ./docs --output ./pdfs

# 预览模式(只扫描不转换)
python main.py --input ./docs --dry-run
```

### 3. 高级用法

```bash
# 自定义并发数和端口
python main.py -i ./docs -o ./pdfs --workers 8 --port 8080

# 覆盖已存在的PDF
python main.py -i ./docs -o ./pdfs --overwrite

# 调试模式(详细日志+单进程)
python main.py -i ./docs -o ./pdfs --debug

# 不使用HTTP服务器(file://协议)
python main.py -i ./docs -o ./pdfs --no-server
```

## 📖 项目结构

```
HtmlDoc2PDF/
├── src/
│   ├── config.py          # 配置管理
│   ├── logger.py          # 日志系统
│   ├── utils.py           # 工具函数
│   ├── server.py          # HTTP服务器
│   ├── converter.py       # PDF转换器
│   ├── scanner.py         # 文件扫描器
│   └── processor.py       # 批量处理器
├── config/
│   ├── default.yaml       # 默认配置
│   └── dolphindb.yaml     # DolphinDB专用配置
├── main.py                # 主程序入口
├── test_installation.py   # 安装测试脚本
├── USAGE.md               # 详细使用指南
└── requirements.txt       # Python依赖
```

## 🎯 针对DolphinDB文档

```bash
# 1. 将DolphinDB文档放在当前目录或指定位置
# 2. 检查配置
cat config/dolphindb.yaml

# 3. 预览(推荐先预览)
python main.py --config config/dolphindb.yaml --dry-run

# 4. 批量转换
python main.py --config config/dolphindb.yaml

# 5. 查看输出
ls -lh output/
```

配置文件 `config/dolphindb.yaml` 已针对DolphinDB文档优化:
- ✅ 包含所有核心目录(tools, plugins, tutorials, funcs等)
- ✅ 排除oxygen-webhelp框架文件
- ✅ 6个并发进程,适合大规模转换
- ✅ 页边距、页眉页脚优化

## 📊 性能预估

基于DolphinDB文档(约500-800个HTML文件):

| 并发数 | 预估时间 | 内存占用 | CPU使用 |
|--------|---------|----------|---------|
| 1      | ~25分钟 | ~500MB   | 1核100% |
| 4      | ~7分钟  | ~2GB     | 4核100% |
| 6      | ~5分钟  | ~3GB     | 6核100% |
| 8      | ~4分钟  | ~4GB     | 8核100% |

## 🛠️ 配置说明

主要配置项(详见配置文件注释):

```yaml
input:
  directory: "./docs"               # 输入目录
  include_patterns: ["**/*.html"]   # 包含模式
  exclude_patterns: []              # 排除模式

output:
  directory: "./output"             # 输出目录
  keep_structure: true              # 保持目录结构

processing:
  workers: 6                        # 并发进程数
  retry_count: 3                    # 重试次数

pdf:
  format: "A4"                      # 页面格式
  margin: {top: "15mm", ...}        # 页边距
  print_background: true            # 打印背景
```

## 🐛 故障排查

### 问题1: "playwright not found"
```bash
# 安装Playwright浏览器
playwright install chromium
```

### 问题2: 中文显示为方块
```bash
# Ubuntu/Debian
sudo apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei

# CentOS
sudo yum install -y wqy-microhei-fonts
```

### 问题3: 端口被占用
```bash
# 使用其他端口
python main.py -i ./docs -o ./pdfs --port 8080

# 或在配置文件中设置
server:
  auto_find_port: true
```

### 问题4: 部分文件转换失败
```bash
# 查看详细日志
cat logs/conversion.log | grep ERROR

# 增加重试次数(配置文件)
processing:
  retry_count: 5
  retry_delay: 3
```

更多问题见 [USAGE.md](USAGE.md)

## 📚 文档

- [USAGE.md](USAGE.md) - 详细使用指南
- [config/default.yaml](config/default.yaml) - 完整配置说明
- [config/dolphindb.yaml](config/dolphindb.yaml) - DolphinDB专用配置示例

## 🔧 开发状态

- ✅ **v0.1.0** (当前): 核心功能完成,可用于生产环境
- 🎯 **v0.2.0** (规划): 添加书签、水印、加密等高级功能
- 🎯 **v0.3.0** (规划): Docker支持、Web UI

## 📝 更新日志

### v0.1.0 (2025-11-13)
- ✅ 完成基础框架(配置、日志、工具函数)
- ✅ 实现HTTP服务器解决资源路径
- ✅ 实现Playwright转换器
- ✅ 实现文件扫描器(glob匹配+排除规则)
- ✅ 实现批量处理器(多进程并发)
- ✅ 完整的命令行接口
- ✅ 针对DolphinDB文档优化

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request!
