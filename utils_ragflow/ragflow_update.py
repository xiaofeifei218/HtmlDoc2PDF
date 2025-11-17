
#%% 
import os
import json
from pathlib import Path
from ragflow_sdk import RAGFlow

API_KEY = "ragflow-MqUTSQiCBlQBNmn4xdqThfz2Xm_FzyMJ7uf_6BLhTpk"
HOST = "http://192.168.50.217:8081"
DOC_ROOT = "/Users/xiaofeifei/Scripts/HtmlDoc2PDF/output/documentation.2.00.17.zh_PDF_20251116234111"

meta_dict=json.load(open(DOC_ROOT+"/metadata.json", "r"))
meta_dict=meta_dict["documents"]

rag = RAGFlow(API_KEY, HOST)
datasetList = rag.list_datasets(name="dolphinDB")
dataset = datasetList[0]

error_msg = []
# 遍历目录树
for file in os.listdir(DOC_ROOT):
    if file.endswith('.pdf'):
        file_path = Path(DOC_ROOT) / file
        relative_path = file_path.relative_to(DOC_ROOT)

        meta_fields = meta_dict.get(str(relative_path))
        if not meta_fields:
            print(f"✗ 未找到元数据: {relative_path}")
            error_msg.append(f"✗ 未找到元数据: {relative_path}")
            continue
        print(meta_fields)
        
        # 1. 上传文档
        with open(file_path, 'rb') as f:
            blob = f.read()
        docs = dataset.upload_documents([{
            "display_name": str(file),
            "blob": blob
        }])
        
        # 2. 立即添加元数据
        docs[0].update({"meta_fields": meta_fields})
        print(f"✓ 已上传: {relative_path}")

print(error_msg)