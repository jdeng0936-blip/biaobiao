"""
种子数据灌入脚本 — 将高分标书评审洞察灌入 pgvector 知识库

用法:
  cd backend && python -m scripts.seed_knowledge

注意: 需要数据库可用。如果数据库不可用会优雅退出。
"""
import json
import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "app" / "data"


def seed_insights():
    """将 seed_high_score_insights.json 灌入 training_chunks 表"""
    try:
        from app.services.knowledge_service import KnowledgeService
    except ImportError:
        print("❌ 无法导入 KnowledgeService，请从 backend/ 目录运行。")
        sys.exit(1)

    insights_file = DATA_DIR / "seed_high_score_insights.json"
    if not insights_file.exists():
        print(f"❌ 种子数据文件不存在: {insights_file}")
        sys.exit(1)

    insights = json.loads(insights_file.read_text(encoding="utf-8"))
    print(f"📦 加载种子数据: {len(insights)} 条评审洞察")

    ks = KnowledgeService()

    success_count = 0
    for i, item in enumerate(insights, 1):
        content = f"【{item['category']}】{item['insight']}"
        result = ks.insert_feedback_chunk(
            content=content,
            section=item["category"],
            tenant_id="seed",
            source_tag="expert_insight",
            metadata={
                "source": item.get("source", "行业数据"),
                "score_impact": item.get("score_impact", "medium"),
            },
        )
        status = "✅" if result else "❌"
        print(f"  {status} [{i}/{len(insights)}] {item['category']}")
        if result:
            success_count += 1

    ks.close()
    print(f"\n🎯 灌入完成: {success_count}/{len(insights)} 条成功")


if __name__ == "__main__":
    seed_insights()
