from neo4j import GraphDatabase
import pandas as pd

# === 配置数据库连接 ===
# 如果你的密码不是 12345678，请在这里修改
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "12345678")


class KnowledgeGraph:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def clear_database(self):
        """清空旧数据，防止重复"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("🧹 数据库已清空")

    def create_graph(self, csv_file):
        """读取 CSV 并创建图谱"""
        df = pd.read_csv(csv_file)

        with self.driver.session() as session:
            for index, row in df.iterrows():
                prof_name = row['Professor']
                title = row['Title']
                school = row['School']
                area = row['Research_Area']

                # 这里的 Cypher 语句是核心！(面试考点)
                # MERGE 只有当节点不存在时才创建，防止重复
                query = """
                MERGE (p:Professor {name: $prof_name, title: $title})
                MERGE (s:School {name: $school})
                MERGE (a:Area {name: $area})

                MERGE (p)-[:BELONGS_TO]->(s)
                MERGE (p)-[:SPECIALIZES_IN]->(a)
                """

                session.run(query, prof_name=prof_name, title=title, school=school, area=area)

            print(f"✅ 已导入 {len(df)} 条关系数据")


# === 运行构建 ===
if __name__ == "__main__":
    try:
        kg = KnowledgeGraph(URI, AUTH)
        kg.clear_database()  # 先清空
        kg.create_graph("professors.csv")  # 再导入
        kg.close()
        print("🎉 知识图谱构建完成！请去 Neo4j Browser 查看效果。")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("请检查：\n1. Neo4j Desktop 是否已启动？\n2. 密码是否正确？")