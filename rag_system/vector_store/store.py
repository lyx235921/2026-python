from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings  # 使用你刚才安装的新包

# 全局配置
MODEL_NAME = "qwen2.5:7b"


def create_vector_store(splits, progress_callback=None):
    """
    接收文档片段，生成向量库检索器 (支持进度显示)
    :param splits: 切分后的文档片段
    :param progress_callback: 进度回调函数 function(current, total)
    :return: 检索器对象 (retriever)
    """
    print("[Vector Store] 正在初始化向量数据库...")

    # 1. 初始化 Embedding 模型
    embeddings = OllamaEmbeddings(model=MODEL_NAME)

    # 2. 初始化一个空的 Chroma 向量数据库
    vectorstore = Chroma(embedding_function=embeddings)

    total_docs = len(splits)
    batch_size = 10  # 每 10 个片段处理一次，这样进度条更新比较丝滑

    # 3. 分批处理 (Batch Processing)
    print(f"[Vector Store] 开始向量化，共 {total_docs} 个片段...")

    for i in range(0, total_docs, batch_size):
        # 截取当前批次
        batch = splits[i: i + batch_size]

        # 添加到数据库 (这一步会调用显卡进行计算)
        vectorstore.add_documents(batch)

        # 计算当前进度并回调
        current_progress = min(i + batch_size, total_docs)
        if progress_callback:
            progress_callback(current_progress, total_docs)

    print("[Vector Store] 向量化完成！")

    # 4. 转换为检索器
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    return retriever