#!/usr/bin/env python3
"""
Amazon 数据高级查询示例
展示 NaturalDB 的 NoSQL 复杂查询能力
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from naturaldb.query_engine.query_engine import QueryEngine
from naturaldb.entities import User, Database


def demo_advanced_queries():
    """展示高级 NoSQL 查询能力"""
    
    # 初始化查询引擎
    user = User(id="demo_user", name="demo_user")
    database = Database(name="amazon")
    query_engine = QueryEngine(user, database)
    
    print("=" * 80)
    print("🔍 NaturalDB Amazon 数据高级查询示例")
    print("=" * 80)
    
    # 1. 链式查询 - MongoDB 风格
    print("\n【示例 1】链式查询：折扣 > 60% 且评分 > 4.0 的商品，按价格排序")
    print("-" * 80)
    results = (query_engine.table("Products")
               .filter_by("discount_percentage", 60, "gt")
               .filter_by("rating", 4.0, "gt")
               .sort("discounted_price")
               .limit(5)
               .all())
    
    for idx, product in enumerate(results, 1):
        data = product.data
        print(f"{idx}. {data['product_name'][:50]}...")
        print(f"   价格: ₹{data['discounted_price']:.0f} "
              f"(原价: ₹{data['actual_price']:.0f}, "
              f"折扣: {data['discount_percentage']}%)")
        print(f"   评分: {data['rating']} ⭐ ({data['rating_count']} 评价)")
    
    # 2. 嵌套数据查询
    print("\n【示例 2】嵌套数据查询：查找特定类别路径的商品")
    print("-" * 80)
    print("查询类别路径包含 'Computers&Accessories' -> 'NetworkingDevices' 的商品")
    
    all_products = query_engine.find_all("Products")
    network_products = [
        p for p in all_products
        if isinstance(p.data.get('category_path'), list) and
           'Computers&Accessories' in p.data['category_path'] and
           'NetworkingDevices' in p.data['category_path']
    ]
    
    print(f"找到 {len(network_products)} 个网络设备商品")
    for idx, product in enumerate(network_products[:3], 1):
        data = product.data
        print(f"{idx}. {data['product_name'][:60]}...")
        print(f"   类别路径: {' > '.join(data['category_path'])}")
    
    # 3. 聚合查询 - 按类别统计
    print("\n【示例 3】聚合查询：统计每个主类别的商品数量和平均价格")
    print("-" * 80)
    
    # 按主类别（第一级）分组
    category_stats = {}
    for product in all_products:
        path = product.data.get('category_path', [])
        if path:
            main_category = path[0]
            if main_category not in category_stats:
                category_stats[main_category] = {
                    'count': 0,
                    'total_price': 0,
                    'total_rating': 0
                }
            category_stats[main_category]['count'] += 1
            category_stats[main_category]['total_price'] += product.data.get('discounted_price', 0)
            category_stats[main_category]['total_rating'] += product.data.get('rating', 0)
    
    # 计算平均值并排序
    for cat, stats in category_stats.items():
        stats['avg_price'] = stats['total_price'] / stats['count']
        stats['avg_rating'] = stats['total_rating'] / stats['count']
    
    sorted_categories = sorted(category_stats.items(), 
                              key=lambda x: x[1]['count'], 
                              reverse=True)[:5]
    
    for idx, (cat, stats) in enumerate(sorted_categories, 1):
        print(f"{idx}. {cat}")
        print(f"   商品数量: {stats['count']}")
        print(f"   平均价格: ₹{stats['avg_price']:.2f}")
        print(f"   平均评分: {stats['avg_rating']:.2f} ⭐")
    
    # 4. 复杂过滤 - 多条件
    print("\n【示例 4】复杂过滤：价格 < 500 且评分 > 4.5 且评论数 > 1000")
    print("-" * 80)
    
    filtered = [
        p for p in all_products
        if (p.data.get('discounted_price', 0) < 500 and
            p.data.get('rating', 0) > 4.5 and
            p.data.get('rating_count', 0) > 1000)
    ]
    
    # 按评分排序
    filtered.sort(key=lambda x: x.data.get('rating', 0), reverse=True)
    
    print(f"找到 {len(filtered)} 个高性价比商品")
    for idx, product in enumerate(filtered[:5], 1):
        data = product.data
        print(f"{idx}. {data['product_name'][:50]}...")
        print(f"   价格: ₹{data['discounted_price']:.0f} | "
              f"评分: {data['rating']} ⭐ | "
              f"评论数: {data['rating_count']:,}")
    
    # 5. 跨表查询 - 关联 Products 和 Reviews
    print("\n【示例 5】跨表关联查询：找出评论最多的商品及其评论详情")
    print("-" * 80)
    
    # 统计每个商品的评论数
    product_review_count = {}
    all_reviews = query_engine.find_all("Reviews")
    
    for review in all_reviews:
        pid = review.data.get('product_id')
        if pid:
            product_review_count[pid] = product_review_count.get(pid, 0) + 1
    
    # 找出评论最多的商品
    top_reviewed = sorted(product_review_count.items(), 
                         key=lambda x: x[1], 
                         reverse=True)[:3]
    
    for idx, (product_id, review_count) in enumerate(top_reviewed, 1):
        product = query_engine.find_by_id("Products", product_id)
        if product:
            print(f"\n{idx}. {product.data['product_name'][:60]}...")
            print(f"   评论总数: {review_count} 条")
            print(f"   商品评分: {product.data['rating']} ⭐")
            
            # 显示该商品的前 3 条评论
            product_reviews = [r for r in all_reviews 
                             if r.data.get('product_id') == product_id][:3]
            
            for rid, review in enumerate(product_reviews, 1):
                print(f"   └─ 评论 {rid}: {review.data.get('review_title', 'N/A')}")
                content = review.data.get('review_content', '')[:50]
                print(f"      {content}...")
    
    # 6. 投影查询 - 只选择特定字段
    print("\n【示例 6】投影查询：只获取商品名称和价格信息")
    print("-" * 80)
    
    projected = query_engine.project("Products", 
                                    ["product_name", "discounted_price", "actual_price"])
    
    print(f"获取了 {len(projected)} 个商品的投影数据")
    for idx, item in enumerate(projected[:5], 1):
        print(f"{idx}. {item.get('product_name', 'N/A')[:50]}...")
        print(f"   折扣价: ₹{item.get('discounted_price', 0):.0f} | "
              f"原价: ₹{item.get('actual_price', 0):.0f}")
    
    # 7. 分组聚合 - 按类别计算统计信息
    print("\n【示例 7】分组聚合：按末级类别统计平均价格和评分")
    print("-" * 80)
    
    grouped = query_engine.group_by("Products", "category", {
        "discounted_price": "avg",
        "rating": "avg"
    })
    
    # 转换为列表并排序
    grouped_list = [
        (cat, stats) for cat, stats in grouped.items()
        if len(stats) > 5  # 至少 5 个商品
    ]
    grouped_list.sort(key=lambda x: len(x[1]), reverse=True)
    
    print(f"共 {len(grouped_list)} 个类别（至少 5 个商品）")
    for idx, (category, items) in enumerate(grouped_list[:5], 1):
        avg_price = sum(item.data.get('discounted_price', 0) for item in items) / len(items)
        avg_rating = sum(item.data.get('rating', 0) for item in items) / len(items)
        
        print(f"{idx}. {category}")
        print(f"   商品数: {len(items)} | "
              f"平均价格: ₹{avg_price:.2f} | "
              f"平均评分: {avg_rating:.2f} ⭐")
    
    # 8. 高级过滤 - 使用自定义条件
    print("\n【示例 8】高级过滤：性价比分析（评分/价格比）")
    print("-" * 80)
    
    # 计算性价比指数 (rating * 1000 / price)
    value_products = []
    for product in all_products:
        price = product.data.get('discounted_price', 0)
        rating = product.data.get('rating', 0)
        if price > 0 and rating > 0:
            value_score = (rating * 1000) / price
            value_products.append((product, value_score))
    
    # 按性价比排序
    value_products.sort(key=lambda x: x[1], reverse=True)
    
    print("性价比最高的 5 个商品：")
    for idx, (product, score) in enumerate(value_products[:5], 1):
        data = product.data
        print(f"{idx}. {data['product_name'][:50]}...")
        print(f"   价格: ₹{data['discounted_price']:.0f} | "
              f"评分: {data['rating']} ⭐ | "
              f"性价比指数: {score:.2f}")
    
    # 9. 统计查询 - 使用 count
    print("\n【示例 9】统计查询：各种统计信息")
    print("-" * 80)
    
    total_products = query_engine.table("Products").count()
    total_reviews = query_engine.table("Reviews").count()
    total_users = query_engine.table("Users").count()
    total_categories = query_engine.table("Categories").count()
    
    high_rating_count = len([p for p in all_products if p.data.get('rating', 0) >= 4.5])
    low_price_count = len([p for p in all_products if p.data.get('discounted_price', 0) < 300])
    high_discount_count = len([p for p in all_products if p.data.get('discount_percentage', 0) >= 70])
    
    print(f"数据库统计：")
    print(f"  - 总商品数: {total_products:,}")
    print(f"  - 总评论数: {total_reviews:,}")
    print(f"  - 总用户数: {total_users:,}")
    print(f"  - 总类别数: {total_categories:,}")
    print(f"\n商品特征统计：")
    print(f"  - 高评分商品 (≥4.5⭐): {high_rating_count} ({high_rating_count/total_products*100:.1f}%)")
    print(f"  - 低价商品 (<₹300): {low_price_count} ({low_price_count/total_products*100:.1f}%)")
    print(f"  - 高折扣商品 (≥70%): {high_discount_count} ({high_discount_count/total_products*100:.1f}%)")
    
    # 10. 排序 + 限制
    print("\n【示例 10】排序与限制：最贵和最便宜的商品")
    print("-" * 80)
    
    most_expensive = (query_engine.table("Products")
                     .sort("discounted_price", ascending=False)
                     .limit(3)
                     .all())
    
    print("最贵的 3 个商品：")
    for idx, product in enumerate(most_expensive, 1):
        data = product.data
        print(f"{idx}. {data['product_name'][:50]}...")
        print(f"   价格: ₹{data['discounted_price']:.0f} | 评分: {data['rating']} ⭐")
    
    cheapest = (query_engine.table("Products")
               .sort("discounted_price", ascending=True)
               .limit(3)
               .all())
    
    print("\n最便宜的 3 个商品：")
    for idx, product in enumerate(cheapest, 1):
        data = product.data
        print(f"{idx}. {data['product_name'][:50]}...")
        print(f"   价格: ₹{data['discounted_price']:.0f} | 评分: {data['rating']} ⭐")
    
    print("\n" + "=" * 80)
    print("✨ 高级查询演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    try:
        demo_advanced_queries()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
