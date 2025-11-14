# 元数据生成器使用说明

## 概述

`generate_metadata.py` 是一个独立的工具，用于从HTML文档生成元数据JSON文件，便于在导入RAGflow时提供文档的分类和路径信息。

## 为什么需要元数据？

当HTML文档具有复杂的目录结构时，转换为PDF后导入RAGflow会丢失文档的层级关系和上下文信息。元数据JSON文件可以：

- 保留文档的分类层级信息
- 记录文档的完整路径
- 提取文档的中文标题
- 方便RAGflow进行文档分类和检索优化

## 功能特点

✅ **自动提取HTML标题**：从 `<h1>` 或 `<title>` 标签提取中文标题
✅ **分类层级识别**：自动识别3级目录结构
✅ **路径映射**：建立HTML到PDF的路径映射关系
✅ **统一格式输出**：生成标准JSON格式，易于程序处理
✅ **无需LLM**：纯字符串处理，快速高效

## 安装依赖

```bash
pip install beautifulsoup4 lxml
```

或使用项目的requirements.txt：

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python generate_metadata.py \
  --html-dir ./downloaded_html \
  --pdf-dir ./output \
  --output ./metadata.json
```

### 简写参数

```bash
python generate_metadata.py -i ./docs -p ./pdfs -o metadata.json
```

### 完整参数说明

| 参数 | 简写 | 必填 | 说明 |
|------|------|------|------|
| `--html-dir` | `-i` | ✅ | HTML文件根目录 |
| `--pdf-dir` | `-p` | ✅ | PDF输出目录（预期的PDF存放位置） |
| `--output` | `-o` | ❌ | 输出JSON文件路径（默认：metadata.json） |
| `--extensions` | - | ❌ | 要扫描的文件扩展名（默认：.html .htm） |

### 示例

#### 示例1：扫描DolphinDB文档

```bash
python generate_metadata.py \
  -i ./dolphindb_docs \
  -p ./dolphindb_pdfs \
  -o ./dolphindb_metadata.json
```

#### 示例2：指定多个文件扩展名

```bash
python generate_metadata.py \
  -i ./docs \
  -p ./pdfs \
  -o metadata.json \
  --extensions .html .htm .xhtml
```

## 工作流程

推荐的工作流程：

```
1. 下载HTML文档
   └─> 存放到指定目录（如 ./dolphindb_docs）

2. 生成元数据
   └─> python generate_metadata.py -i ./dolphindb_docs -p ./output -o metadata.json

3. 转换PDF
   └─> python main.py -i ./dolphindb_docs -o ./output

4. 导入RAGflow
   └─> 使用metadata.json辅助文档分类
```

## 输出格式

生成的JSON文件结构：

```json
{
  "metadata_version": "1.0",
  "generated_at": "2025-11-14T10:30:00",
  "html_base_dir": "/path/to/html",
  "pdf_output_dir": "/path/to/pdf",
  "total_documents": 123,
  "documents": {
    "db_distr_comp-cfg-cluster.pdf": {
      "pdf_path": "/path/to/pdf/db_distr_comp/cfg/cluster.pdf",
      "pdf_filename": "db_distr_comp-cfg-cluster.pdf",
      "source_html": "db_distr_comp/cfg/cluster.html",
      "title": "集群配置",
      "category_level1": "db_distr_comp",
      "category_level2": "cfg",
      "category_level3": "cluster",
      "breadcrumb": "集群配置",
      "path_depth": 3
    },
    ...
  }
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `pdf_path` | PDF文件的完整路径 |
| `pdf_filename` | PDF文件名（使用路径连字符连接） |
| `source_html` | 源HTML文件的相对路径 |
| `title` | 从HTML中提取的标题 |
| `category_level1` | 第一级分类（目录名） |
| `category_level2` | 第二级分类（子目录名） |
| `category_level3` | 第三级分类（文件名） |
| `breadcrumb` | 面包屑导航（当前为标题，可扩展） |
| `path_depth` | 路径深度 |

## 使用场景

### 场景1：RAGflow导入前生成

在转换PDF之前生成元数据，用于指导PDF生成过程（预留功能）。

### 场景2：已有PDF后生成

即使PDF已经生成，只要HTML文件还在，就可以生成元数据用于后续的文档分类和检索。

### 场景3：更新元数据

当HTML文档结构发生变化时，可以重新运行脚本更新元数据。

## 注意事项

1. **路径一致性**：确保指定的 `--pdf-dir` 与实际PDF生成的目录一致
2. **HTML编码**：脚本使用UTF-8编码读取HTML，确保文件编码正确
3. **标题提取**：优先从 `<h1>` 提取标题，其次 `<title>`，最后使用文件名
4. **目录结构**：支持任意深度的目录，但只记录前3级分类

## 扩展功能

如需更复杂的元数据提取，可以修改 `MetadataExtractor` 类：

- 提取文档摘要
- 识别文档类型（教程、API文档、配置说明等）
- 生成完整的面包屑导航（需读取父级目录）
- 添加自定义字段

## 故障排除

### 问题1：找不到HTML文件

**错误信息**：`警告: 在 xxx 中未找到任何HTML文件`

**解决方法**：
- 检查 `--html-dir` 路径是否正确
- 确认目录下确实有 `.html` 或 `.htm` 文件

### 问题2：无法提取标题

**现象**：生成的JSON中 `title` 字段是文件名

**原因**：HTML文件中没有 `<h1>` 或 `<title>` 标签

**解决方法**：这是正常行为，脚本会使用文件名作为后备

### 问题3：路径不一致

**现象**：`pdf_path` 路径与实际PDF位置不符

**原因**：`--pdf-dir` 参数与实际PDF输出目录不一致

**解决方法**：使用与 `main.py -o` 相同的输出目录

## 后续改进计划

- [ ] 支持从已有PDF目录反向生成元数据
- [ ] 生成目录导航PDF文档
- [ ] 支持自定义元数据字段
- [ ] 提供元数据合并功能
- [ ] 生成可视化的文档结构图

## 技术细节

- **语言**：Python 3.6+
- **依赖**：BeautifulSoup4, lxml
- **性能**：纯字符串处理，不依赖LLM，速度快
- **编码**：统一使用UTF-8
- **路径处理**：使用POSIX风格路径（/）

## 联系与反馈

如有问题或建议，请提交Issue或PR。
