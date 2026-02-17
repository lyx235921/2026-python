import sys
import os

print("Python 解释器路径:", sys.executable)

try:
    import langchain

    print("✅ 成功导入 langchain:", langchain.__file__)

    from langchain.chains import RetrievalQA

    print("✅ 成功导入 RetrievalQA")

except ImportError as e:
    print("❌ 导入失败:", e)
    print("当前搜索路径 sys.path:", sys.path)