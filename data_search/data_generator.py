import pandas as pd
import random

# === 1. 定义仿真数据 ===
# 模拟厦大计算机系的几个热门方向
research_areas = [
    "人工智能", "计算机视觉", "自然语言处理", "知识图谱",
    "网络安全", "大数据分析", "云计算", "物联网"
]

# 模拟导师库 (你可以把你想报的导师名字加进去)
professors = [
    {"name": "张教授", "school": "厦门大学", "title": "教授"},
    {"name": "李副教授", "school": "厦门大学", "title": "副教授"},
    {"name": "王博导", "school": "厦门大学", "title": "教授"},
    {"name": "赵讲师", "school": "厦门大学", "title": "讲师"},
    {"name": "陈大牛", "school": "厦门大学", "title": "杰青"},
    {"name": "刘新星", "school": "厦门大学", "title": "副教授"},
]

# === 2. 生成关系数据 ===
data = []

for prof in professors:
    # 每个导师随机擅长 1-3 个方向
    areas = random.sample(research_areas, k=random.randint(1, 3))
    for area in areas:
        data.append({
            "Professor": prof["name"],
            "Title": prof["title"],
            "School": prof["school"],
            "Research_Area": area
        })

# === 3. 保存为 CSV ===
df = pd.DataFrame(data)
df.to_csv("professors.csv", index=False, encoding="utf-8-sig")

print("✅ 仿真数据已生成：professors.csv")
print(df.head())