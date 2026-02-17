import streamlit as st
from neo4j import GraphDatabase

# === 1. 数据库配置 (必须与 build_graph.py 一致) ===
URI = "neo4j://localhost:7687"  # 如果刚才用的是 neo4j:// 这里也要改
AUTH = ("neo4j", "12345678")  # 你的密码


# === 2. 连接数据库 ===
@st.cache_resource
def get_driver():
    return GraphDatabase.driver(URI, auth=AUTH)


def get_all_areas():
    """查询所有的研究方向供用户选择"""
    driver = get_driver()
    query = "MATCH (a:Area) RETURN a.name AS name"
    with driver.session() as session:
        result = session.run(query)
        return [record["name"] for record in result]


def recommend_professors(area_name):
    """核心算法：根据方向推荐导师"""
    driver = get_driver()
    # Cypher 查询：找到专门研究(SPECIALIZES_IN)该方向(Area)的教授(Professor)
    query = """
    MATCH (p:Professor)-[:SPECIALIZES_IN]->(a:Area {name: $area})
    MATCH (p)-[:BELONGS_TO]->(s:School)
    RETURN p.name AS name, p.title AS title, s.name AS school
    """
    with driver.session() as session:
        result = session.run(query, area=area_name)
        return [dict(record) for record in result]


# === 3. 页面布局 ===
st.set_page_config(page_title="厦大计算机导师推荐系统", page_icon="🎓")

st.title("🎓 基于知识图谱的导师推荐系统")
st.markdown("### 🎯 结合你的信管与计算机背景")
st.markdown("该系统利用 **Neo4j 图数据库** 构建了【导师-方向-学校】的三元关系网，能通过多跳查询快速进行精准推荐。")

st.divider()

# 侧边栏
with st.sidebar:
    st.header("🔍 筛选条件")
    try:
        all_areas = get_all_areas()
        selected_area = st.selectbox("请选择你感兴趣的研究方向：", all_areas)
        st.success(f"已连接图数据库，加载 {len(all_areas)} 个方向")
    except Exception as e:
        st.error("数据库连接失败，请检查 Neo4j 是否启动")
        st.stop()

# 主界面：展示推荐结果
if selected_area:
    st.subheader(f"🌟 【{selected_area}】方向的推荐导师：")

    professors = recommend_professors(selected_area)

    if professors:
        # 使用列布局展示卡片
        cols = st.columns(3)
        for i, prof in enumerate(professors):
            with cols[i % 3]:
                st.info(f"**{prof['name']}**")
                st.caption(f"职称：{prof['title']}")
                st.caption(f"所属：{prof['school']}")
                st.button(f"查看 {prof['name']} 详情", key=i)
    else:
        st.warning("该方向暂时没有录入导师数据。")

st.divider()
st.markdown("**项目技术栈：** Python | Streamlit | Neo4j (Graph Database) | Cypher Query Language")