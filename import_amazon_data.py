#!/usr/bin/env python3
"""
Amazon CSV Data Import Script
导入 Amazon 商品数据到 NaturalDB
分表设计：Products, Reviews, Users, Categories
"""

import csv
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from naturaldb.storage_system.storage import Storage
from naturaldb.query_engine.query_engine import QueryEngine
from naturaldb.entities import User, Database, Record
from naturaldb.env_config import config


def parse_csv_line(line):
    """解析 CSV 一行数据，处理逗号分隔的复杂情况"""
    # CSV 中某些字段包含逗号，已经被引号包围
    # 使用 csv.reader 正确处理
    return next(csv.reader([line]))


def extract_categories(category_path):
    """从类别路径中提取所有层级的类别"""
    if not category_path or category_path == '':
        return []
    # 类别格式: "Computers&Accessories|Accessories&Peripherals|Cables"
    categories = category_path.split('|')
    return [cat.strip() for cat in categories if cat.strip()]


def parse_price(price_str):
    """解析印度卢比价格字符串"""
    if not price_str or price_str == '':
        return 0.0
    # 移除货币符号和逗号: "₹1,099" -> 1099.0
    price_str = price_str.replace('₹', '').replace(',', '').strip()
    try:
        return float(price_str)
    except ValueError:
        return 0.0


def parse_percentage(percent_str):
    """解析百分比字符串"""
    if not percent_str or percent_str == '':
        return 0
    # 移除百分号: "64%" -> 64
    percent_str = percent_str.replace('%', '').strip()
    try:
        return int(percent_str)
    except ValueError:
        return 0


def parse_rating(rating_str):
    """解析评分字符串"""
    if not rating_str or rating_str == '':
        return 0.0
    try:
        return float(rating_str)
    except ValueError:
        return 0.0


def parse_rating_count(count_str):
    """解析评分数量字符串"""
    if not count_str or count_str == '':
        return 0
    # 移除逗号: "24,269" -> 24269
    count_str = count_str.replace(',', '').strip()
    try:
        return int(count_str)
    except ValueError:
        return 0


def split_multi_value(value_str):
    """分割多值字段（逗号分隔）"""
    if not value_str or value_str == '':
        return []
    return [v.strip() for v in value_str.split(',') if v.strip()]


def import_amazon_data():
    """导入 Amazon CSV 数据"""
    
    # 初始化存储系统
    base_path = config.get_data_path()
    user_name = "demo_user"
    db_name = "amazon"
    
    print(f"🚀 开始导入 Amazon 数据到 NaturalDB")
    print(f"📁 数据路径: {base_path}")
    print(f"👤 用户: {user_name}")
    print(f"💾 数据库: {db_name}")
    print("-" * 60)
    
    # 创建用户目录
    user_path = os.path.join(base_path, user_name)
    os.makedirs(user_path, exist_ok=True)
    print(f"✅ 创建用户目录: {user_path}")
    
    # 初始化用户和数据库实体
    user = User(id=user_name, name=user_name)
    database = Database(name=db_name)
    
    # 创建存储和查询引擎
    storage = Storage()
    storage.create_user(user)
    storage.create_database(user, database)
    
    query_engine = QueryEngine(user, database)
    
    print(f"✅ 初始化数据库: {db_name}")
    
    # CSV 文件路径
    csv_file = os.path.join(Path(__file__).parent, "data", "amazon.csv")
    
    if not os.path.exists(csv_file):
        print(f"❌ 错误: CSV 文件不存在: {csv_file}")
        return
    
    print(f"📄 读取 CSV 文件: {csv_file}")
    print("-" * 60)
    
    # 用于去重和统计
    products_map = {}  # product_id -> product data
    reviews_map = {}   # review_id -> review data
    users_set = set()  # user_id set
    categories_set = set()  # category name set
    
    # 读取并解析 CSV
    print("📖 解析 CSV 数据...")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader, 1):
            if idx % 100 == 0:
                print(f"   处理第 {idx} 行...")
            
            product_id = row.get('product_id', '').strip()
            if not product_id:
                continue
            
            # 提取商品信息
            if product_id not in products_map:
                category_path = row.get('category', '')
                categories = extract_categories(category_path)
                
                products_map[product_id] = {
                    'product_id': product_id,
                    'product_name': row.get('product_name', '').strip(),
                    'category': categories[-1] if categories else 'Unknown',  # 最后一级类别
                    'category_path': categories,  # 完整类别路径
                    'discounted_price': parse_price(row.get('discounted_price', '')),
                    'actual_price': parse_price(row.get('actual_price', '')),
                    'discount_percentage': parse_percentage(row.get('discount_percentage', '')),
                    'rating': parse_rating(row.get('rating', '')),
                    'rating_count': parse_rating_count(row.get('rating_count', '')),
                    'about_product': row.get('about_product', '').strip(),
                    'img_link': row.get('img_link', '').strip(),
                    'product_link': row.get('product_link', '').strip(),
                }
                
                # 收集所有类别
                for cat in categories:
                    categories_set.add(cat)
            
            # 提取评论信息（一个产品可能有多条评论）
            review_ids = split_multi_value(row.get('review_id', ''))
            user_ids = split_multi_value(row.get('user_id', ''))
            user_names = split_multi_value(row.get('user_name', ''))
            review_titles = split_multi_value(row.get('review_title', ''))
            review_contents = split_multi_value(row.get('review_content', ''))
            
            # 确保所有列表长度一致
            max_len = max(len(review_ids), len(user_ids), len(user_names), 
                         len(review_titles), len(review_contents))
            
            # 填充到相同长度
            review_ids += [''] * (max_len - len(review_ids))
            user_ids += [''] * (max_len - len(user_ids))
            user_names += [''] * (max_len - len(user_names))
            review_titles += [''] * (max_len - len(review_titles))
            review_contents += [''] * (max_len - len(review_contents))
            
            # 处理每条评论
            for i in range(max_len):
                review_id = review_ids[i].strip()
                user_id = user_ids[i].strip()
                user_name = user_names[i].strip()
                
                if review_id and review_id not in reviews_map:
                    reviews_map[review_id] = {
                        'review_id': review_id,
                        'product_id': product_id,
                        'user_id': user_id,
                        'user_name': user_name,
                        'review_title': review_titles[i].strip(),
                        'review_content': review_contents[i].strip(),
                    }
                
                # 收集用户
                if user_id:
                    users_set.add((user_id, user_name))
    
    print(f"✅ CSV 解析完成")
    print(f"   - 商品数量: {len(products_map)}")
    print(f"   - 评论数量: {len(reviews_map)}")
    print(f"   - 用户数量: {len(users_set)}")
    print(f"   - 类别数量: {len(categories_set)}")
    print("-" * 60)
    
    # 导入商品数据
    print("📦 导入商品数据到 Products 表...")
    for idx, (product_id, product_data) in enumerate(products_map.items(), 1):
        record = Record(id=product_id, data=product_data)
        query_engine.insert("Products", record)
        if idx % 50 == 0:
            print(f"   已导入 {idx}/{len(products_map)} 个商品")
    print(f"✅ 成功导入 {len(products_map)} 个商品")
    
    # 导入评论数据
    print("💬 导入评论数据到 Reviews 表...")
    for idx, (review_id, review_data) in enumerate(reviews_map.items(), 1):
        record = Record(id=review_id, data=review_data)
        query_engine.insert("Reviews", record)
        if idx % 100 == 0:
            print(f"   已导入 {idx}/{len(reviews_map)} 条评论")
    print(f"✅ 成功导入 {len(reviews_map)} 条评论")
    
    # 导入用户数据
    print("👥 导入用户数据到 Users 表...")
    for idx, (user_id, user_name) in enumerate(sorted(users_set), 1):
        user_data = {
            'user_id': user_id,
            'user_name': user_name,
        }
        record = Record(id=user_id, data=user_data)
        query_engine.insert("Users", record)
        if idx % 100 == 0:
            print(f"   已导入 {idx}/{len(users_set)} 个用户")
    print(f"✅ 成功导入 {len(users_set)} 个用户")
    
    # 导入类别数据
    print("📂 导入类别数据到 Categories 表...")
    for idx, category in enumerate(sorted(categories_set), 1):
        category_data = {
            'category_name': category,
            'category_id': f"cat_{idx}",
        }
        record = Record(id=f"cat_{idx}", data=category_data)
        query_engine.insert("Categories", record)
    print(f"✅ 成功导入 {len(categories_set)} 个类别")
    
    print("-" * 60)
    print("🎉 数据导入完成！")
    print("\n📊 数据统计:")
    print(f"   - Products 表: {len(products_map)} 条记录")
    print(f"   - Reviews 表: {len(reviews_map)} 条记录")
    print(f"   - Users 表: {len(users_set)} 条记录")
    print(f"   - Categories 表: {len(categories_set)} 条记录")
    
    # 显示一些示例查询
    print("\n" + "=" * 60)
    print("📝 示例查询展示 NoSQL 能力:")
    print("=" * 60)
    
    # 1. 简单过滤查询
    print("\n1️⃣ 查询折扣大于 50% 的商品:")
    high_discount = query_engine.table("Products").filter_by("discount_percentage", 50, "gt").all()
    print(f"   找到 {len(high_discount)} 个商品")
    if high_discount:
        sample = high_discount[0].data
        print(f"   示例: {sample['product_name'][:50]}... (折扣: {sample['discount_percentage']}%)")
    
    # 2. 嵌套字段查询
    print("\n2️⃣ 查询包含 'USB' 类别路径的商品:")
    usb_products = [p for p in query_engine.find_all("Products") 
                    if 'USB' in str(p.data.get('category_path', []))]
    print(f"   找到 {len(usb_products)} 个 USB 相关商品")
    if usb_products:
        sample = usb_products[0].data
        print(f"   示例: {sample['product_name'][:50]}...")
    
    # 3. 聚合查询
    print("\n3️⃣ 按类别分组统计商品数量:")
    category_groups = query_engine.group_by("Products", "category", {})
    print(f"   共 {len(category_groups)} 个类别")
    for cat, items in list(category_groups.items())[:3]:
        print(f"   - {cat}: {len(items)} 个商品")
    
    # 4. 排序查询
    print("\n4️⃣ 评分最高的 5 个商品:")
    top_rated = query_engine.table("Products").sort("rating", ascending=False).limit(5).all()
    for idx, product in enumerate(top_rated, 1):
        data = product.data
        print(f"   {idx}. {data['product_name'][:40]}... (评分: {data['rating']})")
    
    # 5. 价格范围查询
    print("\n5️⃣ 价格在 200-500 之间的商品:")
    price_range = [p for p in query_engine.find_all("Products")
                   if 200 <= p.data.get('discounted_price', 0) <= 500]
    print(f"   找到 {len(price_range)} 个商品")
    
    # 6. 跨表关联（手动）
    print("\n6️⃣ 找到评论最多的 3 个商品:")
    products_with_reviews = {}
    for review in query_engine.find_all("Reviews"):
        pid = review.data.get('product_id')
        if pid:
            products_with_reviews[pid] = products_with_reviews.get(pid, 0) + 1
    
    top_reviewed = sorted(products_with_reviews.items(), key=lambda x: x[1], reverse=True)[:3]
    for idx, (pid, count) in enumerate(top_reviewed, 1):
        product = query_engine.find_by_id("Products", pid)
        if product:
            print(f"   {idx}. {product.data['product_name'][:40]}... ({count} 条评论)")
    
    print("\n" + "=" * 60)
    print("✨ 导入脚本执行完毕！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        import_amazon_data()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
