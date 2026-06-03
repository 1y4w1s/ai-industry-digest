"""快速验证脚本"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("验证 collector 模块")
print("=" * 50)

# 1. Article 数据模型
from collector.base import Article
a = Article(title="测试文章", url="https://example.com", source_name="测试源", raw_content="测试内容")
print(f"[OK] Article 模型: {a.title} - {a.source_name}")

# 2. 加载配置
import yaml
with open("config/sources.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
print(f"[OK] 信息源配置: {len(config['sources'])} 个源")

# 3. arXiv 采集
from collector.arxiv_collector import ArxivCollector
source = [s for s in config['sources'] if s['id'] == 'arxiv_ai'][0]
collector = ArxivCollector(source)
arts = collector.collect()
print(f"[OK] arXiv cs.AI: 采集到 {len(arts)} 篇论文")

# 4. run.py 语法检查
import py_compile
py_compile.compile("run.py", doraise=True)
print("[OK] run.py 语法检查通过")

# 5. 数据库模块导入
from api.models.database import DatabaseManager
print("[OK] database.py 导入成功")

print("\n" + "=" * 50)
print("全部验证通过!")
print("=" * 50)
