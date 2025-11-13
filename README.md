# HtmlDoc2PDF

基于Playwright的HTML文档批量转PDF工具,专为DolphinDB技术文档设计。

## 特性

- ✅ 基于Playwright + Chromium,完美支持现代Web特性
- ✅ 多进程并发处理,提升转换效率
- ✅ 内置HTTP服务器,自动解决资源路径问题
- ✅ 灵活的配置系统(YAML + 命令行)
- ✅ 完善的错误处理和重试机制
- ✅ 支持断点续转
- ✅ 实时进度显示和详细日志

## 快速开始

### 安装

```bash
# 1. 克隆仓库
git clone <repo-url>
cd HtmlDoc2PDF

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装Playwright浏览器
playwright install chromium
```

### 基础使用

```bash
# 使用默认配置
python main.py --input ./docs --output ./pdfs

# 使用配置文件
python main.py --config config/dolphindb.yaml

# 自定义参数
python main.py \
  --input ./docs \
  --output ./pdfs \
  --workers 6 \
  --port 8000
```

## 配置说明

详见 `config/default.yaml` 和 `config/dolphindb.yaml`

## 开发状态

🚧 当前版本: v0.1.0-alpha
📅 最后更新: 2025-11-13

## 许可证

MIT License
