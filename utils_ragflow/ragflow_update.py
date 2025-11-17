
#%% 
import os
import json
from pathlib import Path
from ragflow_sdk import RAGFlow

API_KEY = "ragflow-MqUTSQiCBlQBNmn4xdqThfz2Xm_FzyMJ7uf_6BLhTpk"
HOST = "http://192.168.50.217:8081"
DOC_ROOT = "/Users/xiaofeifei/Scripts/HtmlDoc2PDF/output/documentation.2.00.17.zh_PDF_20251115223325/"

meta_dict=json.load(open(DOC_ROOT+"metadata.json", "r"))
meta_dict=meta_dict["documents"]
raise
rag = RAGFlow(API_KEY, HOST)
datasetList = rag.list_datasets(name="dolphinDB")
dataset = datasetList[0]


# 遍历目录树
for file in os.listdir(DOC_ROOT):
    if file.endswith('.pdf'):
        file_path = Path(DOC_ROOT) / file
        relative_path = file_path.relative_to(DOC_ROOT)
        
        # 1. 上传文档
        with open(file_path, 'rb') as f:
            blob = f.read()
        raise
        docs = dataset.upload_documents([{
            "display_name": str(file),
            "blob": blob
        }])
        
        # 2. 立即添加元数据
        path_parts = relative_path.parts
        meta_fields = {
            "full_path": str(relative_path),
            "category_level1": path_parts[0] if len(path_parts) > 0 else "",
            "category_level2": path_parts[1] if len(path_parts) > 1 else "",
            "category_level3": path_parts[2] if len(path_parts) > 2 else "",
            "breadcrumb": " > ".join(path_parts[:-1]),
            "filename": file
        }
        
        docs[0].update({"meta_fields": meta_fields})
        print(f"✓ 已上传: {relative_path}")