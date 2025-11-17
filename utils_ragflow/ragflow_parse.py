
#%% 
import os
import json
from pathlib import Path
from ragflow_sdk import RAGFlow

API_KEY = "ragflow-MqUTSQiCBlQBNmn4xdqThfz2Xm_FzyMJ7uf_6BLhTpk"
HOST = "http://192.168.50.217:8081"


rag = RAGFlow(API_KEY, HOST)
datasetList = rag.list_datasets(name="dolphinDB")
dataset = datasetList[0]

documents = dataset.list_documents(page_size=3000)
ids = [doc.id for doc in documents]
print(len(ids))
# dataset.parse_documents(ids)
dataset.async_parse_documents(ids)