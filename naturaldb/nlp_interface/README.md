# NaturalDB Layer 3 - Natural Language Interface

Layer 3 提供了基于 OpenAI Function Calling 的自然语言查询接口，让用户可以使用自然语言与数据库交互。

## 架构概述

```
自然语言查询
     ↓
NLQueryProcessor (调用 OpenAI API)
     ↓
Function Calls (结构化的函数调用)
     ↓
FunctionExecutor (执行数据库操作)
     ↓
QueryEngine (Layer 2)
     ↓
Storage (Layer 1)
```

## 核心组件

### 1. `function_calling.py` - 工具注册系统

自动将 Python 函数/方法转换为 OpenAI Function Calling 格式。

**功能:**
- `OpenAiTool`: 将单个函数包装为 OpenAI tool
- `ToolRegistry`: 批量注册类方法或函数

**示例:**
```python
from naturaldb.nlp_interface.function_calling import ToolRegistry

# 自动注册类的所有公共方法
tools = ToolRegistry.register_class_methods(
    target_class=QueryEngine,
    exclude_methods=['_private_method'],
    method_descriptions={'insert': 'Insert a new record'},
    param_descriptions={'insert': {'table_name': 'The table name'}}
)
```

### 2. `tool_registry.py` - 数据库工具注册表

将所有 `QueryEngine` 方法自动注册为 OpenAI tools。

**功能:**
- 自动生成所有数据库操作的工具定义
- 提供详细的描述和参数说明
- 标记敏感操作（update, delete）

**示例:**
```python
from naturaldb.nlp_interface.tool_registry import DatabaseToolRegistry

# 获取所有可用工具
tools = DatabaseToolRegistry.get_all_tools()

# 获取敏感操作列表
sensitive = DatabaseToolRegistry.get_sensitive_operations()
```

### 3. `nl_query_processor.py` - 自然语言查询处理器

与 OpenAI API 通信，将自然语言转换为函数调用。

**功能:**
- 单次查询处理
- 多轮对话支持
- 自动执行函数调用

**示例:**
```python
from naturaldb.nlp_interface.nl_query_processor import NLQueryProcessor

processor = NLQueryProcessor(api_key="your-openai-key")

# 处理查询
result = processor.process_query(
    user_query="Find all products with price > 100",
    tools=tools,
    context="Available tables: products, orders"
)

# 多轮对话
result = processor.process_with_execution(
    user_query="Create a products table and add some items",
    tools=tools,
    executor_callback=lambda name, args: execute_function(name, args)
)
```

### 4. `executor.py` - 函数执行器

执行 OpenAI 返回的函数调用，调用实际的数据库操作。

**功能:**
- 将函数调用映射到 QueryEngine 方法
- 处理敏感操作的确认
- 批量执行多个操作
- 结果序列化

**示例:**
```python
from naturaldb.nlp_interface.executor import FunctionExecutor

executor = FunctionExecutor(
    query_engine=engine,
    confirmation_callback=lambda op, args: confirm(op, args)
)

# 执行单个操作
result = executor.execute("find_all", {"table_name": "products"})

# 批量执行
results = executor.execute_batch([
    {"name": "create_table", "arguments": {"table_name": "users"}},
    {"name": "insert", "arguments": {"table_name": "users", ...}}
])
```

### 5. `naturaldb.py` - 统一主接口

整合所有组件，提供简单的高级 API。

**功能:**
- 一行代码执行自然语言查询
- 支持交互式多轮对话
- 自动处理确认流程
- 降级支持（无 OpenAI API key 时仍可用）

**示例:**
```python
from naturaldb.nlp_interface.naturaldb import NaturalDB
from naturaldb.entities import User, Database

user = User(id="alice", name="Alice")
db = Database(name="ecommerce")

# 初始化
natural_db = NaturalDB(user, db)

# 执行自然语言查询
result = natural_db.query("Show me all products with price > 100")

if result['success']:
    print(result['result'])
else:
    print(result['error'])

# 交互式查询（多轮对话）
result = natural_db.query_interactive(
    "Create a products table, add 3 items, then show me the most expensive one"
)

# 直接访问 QueryEngine（不使用 NLP）
products = natural_db.engine.find_all("products")
```

## 使用示例

### 基本查询

```python
from naturaldb.nlp_interface.naturaldb import NaturalDB
from naturaldb.entities import User, Database
import os

# 设置 API key
os.environ["OPENAI_API_KEY"] = "your-key-here"

# 初始化
user = User(id="user1", name="John")
database = Database(name="shop_db")
db = NaturalDB(user, database)

# 查询示例
queries = [
    "Create a table called products",
    "Insert a product: id=1, name='Laptop', price=999",
    "Show me all products",
    "Find products with price > 500",
    "Sort products by price descending",
    "Count how many products we have",
]

for query in queries:
    print(f"\nQuery: {query}")
    result = db.query(query)
    print(f"Result: {result}")
```

### 带确认的敏感操作

```python
def confirm_operation(operation: str, args: dict) -> bool:
    """确认敏感操作"""
    print(f"⚠️  About to {operation}: {args}")
    response = input("Continue? (yes/no): ")
    return response.lower() == 'yes'

db = NaturalDB(
    user, 
    database, 
    confirmation_callback=confirm_operation
)

# 这会触发确认
result = db.query("Delete all products with price < 10")
```

### 交互式多轮查询

```python
# LLM 可以执行多个步骤并根据结果调整
result = db.query_interactive(
    "Create a products table, add 5 different products, "
    "then show me the 3 most expensive ones"
)

print(f"Final response: {result['response']}")
print(f"Operations executed: {len(result['execution_history'])}")
```

### 无 OpenAI API 的降级使用

```python
# 即使没有 API key，仍然可以使用
db = NaturalDB(user, database)  # nlp_enabled = False

# 直接使用 QueryEngine
from naturaldb.entities import Table, Record

table = Table(name="users", indexes={})
db.engine.create_table(table)

record = Record(id="1", data={"name": "Alice", "age": 30})
db.engine.insert("users", record)

users = db.engine.find_all("users")
```

## 支持的操作

Layer 3 自动将以下 QueryEngine 操作转换为自然语言工具：

### 表管理
- `create_table` - 创建表
- `list_tables` - 列出所有表

### CRUD 操作
- `insert` - 插入记录
- `find_by_id` - 根据 ID 查找
- `find_all` - 查找所有记录
- `update` - 更新记录 (敏感操作)
- `delete` - 删除记录 (敏感操作)

### 查询操作
- `filter` - 过滤记录
- `project` - 选择特定字段
- `rename` - 重命名字段
- `select` - 复杂 SQL 风格查询
- `group_by` - 分组和聚合
- `sort` / `order_by` - 排序
- `join` - 连接表

### 导入导出
- `import_from_json_file` - 从 JSON 文件导入
- `export_to_json_file` - 导出到 JSON 文件

## 环境变量

```bash
# 必需（用于自然语言功能）
export OPENAI_API_KEY="sk-..."

# 可选（用于测试）
export NATURALDB_DATA_PATH="/path/to/data"
```

## 依赖

```bash
pip install openai>=1.0.0
```

## 运行演示

```bash
# 设置 API key
export OPENAI_API_KEY="your-key-here"

# 运行演示
python demo_natural_language.py
```

## 技术细节

### 工具自动注册

`ToolRegistry.register_class_methods()` 使用 Python 的 `inspect` 模块：
1. 获取类的所有公共方法
2. 提取方法签名和参数类型
3. 解析 docstring 获取描述
4. 生成 OpenAI Function Calling schema
5. 自动处理类型映射（包括 `Optional`, `List`, `Dict` 等）

### OpenAI Function Calling 流程

1. 用户输入自然语言查询
2. `NLQueryProcessor` 调用 OpenAI API with tools
3. OpenAI 返回需要调用的函数列表
4. `FunctionExecutor` 将函数调用映射到 QueryEngine 方法
5. 执行数据库操作并返回结果
6. 可选：将结果反馈给 LLM 继续对话

### 类型安全

所有组件都使用 Python type hints，并通过 `# type: ignore` 处理 OpenAI SDK 的类型限制。

## 未来改进

- [ ] 支持更多 LLM 提供商（Anthropic, Azure OpenAI）
- [ ] 添加查询缓存
- [ ] 支持查询优化建议
- [ ] 添加查询历史和撤销功能
- [ ] Flask/FastAPI REST API 封装
- [ ] WebSocket 支持流式响应
- [ ] 查询性能分析和日志

## 贡献

Layer 3 的设计使得添加新功能非常简单：

1. 在 `QueryEngine` 添加新方法
2. 自动注册系统会将其转换为工具
3. 无需手动编写工具定义！
