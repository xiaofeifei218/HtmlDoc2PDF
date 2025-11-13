# 使用指南

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境(推荐)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器(必需!)
playwright install chromium
```

### 2. 基本使用

#### 方式一:使用配置文件(推荐)

```bash
# 使用DolphinDB专用配置
python main.py --config config/dolphindb.yaml

# 使用默认配置
python main.py --config config/default.yaml
```

#### 方式二:命令行参数

```bash
# 最简单的用法
python main.py --input ./docs --output ./pdfs

# 自定义并发数
python main.py -i ./docs -o ./pdfs --workers 8

# 指定HTTP服务器端口
python main.py -i ./docs -o ./pdfs --port 8080

# 不使用HTTP服务器(使用file://协议)
python main.py -i ./docs -o ./pdfs --no-server

# 覆盖已存在的PDF
python main.py -i ./docs -o ./pdfs --overwrite
```

### 3. 调试和预览

```bash
# 预览模式(只扫描不转换)
python main.py -i ./docs --dry-run

# 调试模式(详细日志 + 单进程)
python main.py -i ./docs -o ./pdfs --debug
```

## 针对DolphinDB文档的使用

假设你的DolphinDB文档在当前目录:

```bash
# 1. 检查配置文件
cat config/dolphindb.yaml

# 2. 预览将要转换的文件
python main.py --config config/dolphindb.yaml --dry-run

# 3. 执行批量转换
python main.py --config config/dolphindb.yaml

# 4. 转换完成后查看输出
ls -lh output/
```

## 常见问题

### Q: 提示"playwright not found"

**A:** 需要安装Playwright浏览器:
```bash
playwright install chromium
```

### Q: 中文显示为方块

**A:** 系统缺少中文字体,安装中文字体:
```bash
# Ubuntu/Debian
sudo apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei

# CentOS
sudo yum install -y wqy-microhei-fonts wqy-zenhei-fonts
```

### Q: 端口8000被占用

**A:** 使用其他端口:
```bash
python main.py -i ./docs -o ./pdfs --port 8080
```
或者在配置文件中设置 `auto_find_port: true`

### Q: 部分文件转换失败

**A:** 查看日志文件了解详情:
```bash
cat logs/conversion.log
```
可以增加重试次数(在配置文件中修改 `retry_count`)

### Q: 想要只转换特定目录

**A:** 修改配置文件的 `include_patterns`:
```yaml
input:
  include_patterns:
    - "tools/**/*.html"
    - "plugins/**/*.html"
```

### Q: 某些文件不想转换

**A:** 使用 `exclude_patterns`:
```yaml
input:
  exclude_patterns:
    - "oxygen-webhelp/**"
    - "**/search.html"
```

## 配置文件说明

详见 `config/dolphindb.yaml` 和 `config/default.yaml` 的注释。

主要配置项:

- `input.directory`: 输入目录
- `input.include_patterns`: 包含模式(glob)
- `input.exclude_patterns`: 排除模式(glob)
- `output.directory`: 输出目录
- `output.keep_structure`: 是否保持目录结构
- `processing.workers`: 并发进程数
- `browser.timeout`: 页面加载超时(毫秒)
- `pdf.format`: PDF格式(A4/Letter/A3等)
- `pdf.margin`: 页边距

## 性能优化建议

1. **调整并发数**: 根据你的CPU核心数设置 `workers`
   - 4核CPU: workers=4
   - 8核CPU: workers=6-8
   - 16核CPU: workers=8-12

2. **调整超时时间**: 如果文档较大或网络慢:
   ```yaml
   browser:
     timeout: 120000  # 120秒
     wait_after_load: 3000  # 额外等待3秒
   ```

3. **使用SSD**: 输出目录放在SSD上可以提升性能

4. **关闭不必要的浏览器特性**: 已经优化过了,无需额外配置

## 日志查看

日志文件位置: `./logs/conversion.log`

```bash
# 查看日志
tail -f logs/conversion.log

# 查看错误
grep ERROR logs/conversion.log

# 查看统计信息
grep "处理完成" logs/conversion.log
```

## 输出结构

如果 `keep_structure: true`:
```
input/
  tools/
    sqltools.html
  plugins/
    py/py.html

output/
  tools/
    sqltools.pdf
  plugins/
    py/py.pdf
```

如果 `keep_structure: false`:
```
output/
  sqltools.pdf
  py.pdf
```
