import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_split_pdf(file_path):
    """
    加载 PDF 并进行切分
    :param file_path: PDF 文件路径
    :return: 切分后的文档列表 (splits)
    """
    print(f"[Data Ingestion] 正在加载文件: {file_path}")
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # 切分策略：每块 500 字，保留 50 字重叠作为上下文衔接
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    splits = text_splitter.split_documents(docs)
    print(f"[Data Ingestion] 文档已切分为 {len(splits)} 个片段")
    return splits