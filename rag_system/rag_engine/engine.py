from langchain_ollama import OllamaLLM  # 注意这里名字变了，是 OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

MODEL_NAME = "qwen2.5:7b"


def format_docs(docs):
    """把检索到的多个文档片段拼接成一个字符串"""
    return "\n\n".join(doc.page_content for doc in docs)


def build_rag_chain(retriever):
    """
    使用 LCEL (LangChain Expression Language) 构建纯净版 RAG 链
    不依赖旧版 chains 模块，兼容性最强
    """
    print("[RAG Engine] 正在初始化大模型 (LCEL架构)...")
    llm = OllamaLLM(model=MODEL_NAME)

    # 1. 定义提示词模板
    template = """
    你是一个考研复试助手。请根据下面的【上下文】来回答【问题】。
    如果你在上下文中找不到答案，就诚实地说“资料里没有提到相关内容”，不要编造。

    【上下文】:
    {context}

    【问题】:
    {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    # 2. 构建核心处理链
    # 逻辑：检索文档 -> 格式化文档 -> 填入Prompt -> 发给大模型 -> 解析结果
    rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )

    return rag_chain