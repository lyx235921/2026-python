import streamlit as st
import os
import tempfile
import sys

# --- 关键路径配置 ---
# 获取当前文件的上一级目录 (即 rag_system 根目录)，加入到 Python 搜索路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# 导入自定义模块
from data_ingestion.loader import load_and_split_pdf
from vector_store.store import create_vector_store
from rag_engine.engine import build_rag_chain

# --- 页面设置 ---
st.set_page_config(page_title="考研复试助手", page_icon="🎓")
st.title("🎓 考研复试 RAG 系统 (工程版)")

# --- 侧边栏 ---
with st.sidebar:
    st.header("📚 知识库上传")
    uploaded_file = st.file_uploader("上传 PDF 资料", type="pdf")

    if st.button("重置系统"):
        st.session_state.clear()
        st.rerun()

# --- 主逻辑 ---
if uploaded_file:
    # 1. 初始化系统 (如果尚未初始化)
    if 'rag_chain' not in st.session_state:
        with st.spinner('系统正在初始化 (ETL -> Embedding -> RAG)...'):
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            try:
                # === 调用各层模块 ===
                # Step 1: 加载与切分
                splits = load_and_split_pdf(tmp_path)

                # --- 新增：进度条逻辑 ---
                # 创建一个空的进度条组件
                progress_text = "正在调用显卡进行向量化，请稍候..."
                my_bar = st.progress(0, text=progress_text)


                def update_progress(current, total):
                    percent = int((current / total) * 100)
                    my_bar.progress(percent, text=f"{progress_text} ({current}/{total})")


                # Step 2: 向量化存储 (传入回调函数)
                # 注意：这里把 update_progress 传进去了
                retriever = create_vector_store(splits, progress_callback=update_progress)

                # 向量化完成后，清空进度条
                my_bar.empty()
                # -----------------------

                # Step 3: 构建引擎 (返回可执行的 LCEL 链)
                rag_chain = build_rag_chain(retriever)

                # 存入 Session
                st.session_state['rag_chain'] = rag_chain
                st.session_state['retriever'] = retriever

                st.success(f"✅ 知识库加载完毕！共处理 {len(splits)} 个片段。")

            except Exception as e:
                st.error(f"初始化失败: {e}")
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

                    # 2. 聊天交互界面
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 处理用户输入
    if prompt := st.chat_input("请输入你的专业课问题..."):
        # 显示用户提问
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 回答
        with st.chat_message("assistant"):
            chain = st.session_state['rag_chain']
            retriever = st.session_state.get('retriever')

            with st.spinner("AI 正在思考 (基于本地 Qwen 模型)..."):
                try:
                    # --- 核心修改点 1: 调用方式变了 ---
                    # 旧版: response = chain.invoke({"query": prompt})
                    # 新版 LCEL: 直接传入问题字符串即可
                    result = chain.invoke(prompt)

                    st.markdown(result)

                    # --- 核心修改点 2: 手动检索来源 ---
                    # 因为 StrOutputParser 只返回字符串，我们需要手动再检索一次来展示来源
                    # 这虽然多了一次计算，但为了 UI 展示是值得的
                    if retriever:
                        with st.expander("查看参考依据 (Source Documents)"):
                            source_docs = retriever.invoke(prompt)
                            for i, doc in enumerate(source_docs):
                                st.markdown(f"**📄 来源 {i + 1} (页码: {doc.metadata.get('page', '?')}):**")
                                st.caption(doc.page_content[:200] + "...")
                                st.divider()

                    # 存入历史
                    st.session_state.messages.append({"role": "assistant", "content": result})

                except Exception as e:
                    st.error(f"生成回答时出错: {e}")

else:
    st.info("👈 请在左侧上传考研资料 PDF 以启动系统")