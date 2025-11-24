# NaturalDB Flask REST API

完整的 RESTful API 实现,提供类似 Firebase/MongoDB 的 HTTP 接口。

## 📁 项目结构

```
naturaldb/
├── api/
│   ├── __init__.py              # API 包初始化
│   ├── app.py                   # Flask 应用工厂
│   ├── API_DOCUMENTATION.md     # 完整 API 文档
│   └── controllers/             # REST 控制器
│       ├── __init__.py          # 控制器包初始化
│       ├── database_controller.py   # 数据库 CRUD
│       ├── table_controller.py      # 表 CRUD
│       ├── record_controller.py     # 记录 CRUD
│       ├── query_controller.py      # 高级查询
│       └── user_controller.py       # 用户管理
├── query_engine/                # Layer 2: 查询引擎
├── storage_system/              # Layer 1: 存储系统
└── ...
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install flask flask-cors
```

### 2. 启动服务器

```bash
# 默认启动 (127.0.0.1:5000)
python run_api.py

# 自定义配置
python run_api.py --host 0.0.0.0 --port 8080 --debug
```

### 3. 测试 API

```bash
# 健康检查
curl http://localhost:5000/health

# 运行完整测试
python test_api.py
```

## 📚 API 端点概览

### 用户管理
- `GET /api/users` - 列出所有用户
- `POST /api/users` - 创建用户
- `GET /api/users/{user_id}` - 获取用户信息
- `GET /api/users/{user_id}/stats` - 获取用户统计
- `DELETE /api/users/{user_id}` - 删除用户

### 数据库管理
- `GET /api/databases?user_id={user_id}` - 列出用户的数据库
- `POST /api/databases` - 创建数据库
- `GET /api/databases/{user_id}/{db_name}` - 获取数据库信息
- `DELETE /api/databases/{user_id}/{db_name}` - 删除数据库

### 表管理
- `GET /api/databases/{user_id}/{db_name}/tables` - 列出表
- `POST /api/databases/{user_id}/{db_name}/tables` - 创建表
- `GET /api/databases/{user_id}/{db_name}/tables/{table_name}` - 获取表信息

### 记录管理
- `GET /api/databases/{user_id}/{db_name}/tables/{table_name}/records` - 列出记录
- `POST /api/databases/{user_id}/{db_name}/tables/{table_name}/records` - 创建记录
- `GET /api/databases/{user_id}/{db_name}/tables/{table_name}/records/{id}` - 获取记录
- `PUT /api/databases/{user_id}/{db_name}/tables/{table_name}/records/{id}` - 更新记录
- `DELETE /api/databases/{user_id}/{db_name}/tables/{table_name}/records/{id}` - 删除记录

### 高级查询
- `POST /api/databases/{user_id}/{db_name}/query` - 执行复杂查询
- `POST /api/databases/{user_id}/{db_name}/query/count` - 计数查询
- `POST /api/databases/{user_id}/{db_name}/query/aggregate` - 聚合查询

## 💡 使用示例

### Python 客户端

```python
import requests

BASE_URL = "http://localhost:5000"

# 1. 创建用户
requests.post(f"{BASE_URL}/api/users", json={
    "user_id": "alice",
    "name": "Alice"
})

# 2. 创建数据库
requests.post(f"{BASE_URL}/api/databases", json={
    "user_id": "alice",
    "db_name": "mydb"
})

# 3. 创建表
requests.post(f"{BASE_URL}/api/databases/alice/mydb/tables", json={
    "table_name": "products"
})

# 4. 插入记录
requests.post(
    f"{BASE_URL}/api/databases/alice/mydb/tables/products/records",
    json={
        "id": "1",
        "data": {"name": "Laptop", "price": 999.99}
    }
)

# 5. 查询记录
response = requests.post(
    f"{BASE_URL}/api/databases/alice/mydb/query",
    json={
        "table": "products",
        "filters": [
            {"field": "price", "operator": "lt", "value": 1000}
        ],
        "sort": [{"field": "price", "direction": "desc"}],
        "limit": 10
    }
)
print(response.json())
```

### cURL 示例

```bash
# 创建用户
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "name": "Alice"}'

# 查询记录
curl -X POST http://localhost:5000/api/databases/alice/mydb/query \
  -H "Content-Type: application/json" \
  -d '{
    "table": "products",
    "filters": [{"field": "price", "operator": "lt", "value": 1000}],
    "limit": 5
  }'
```

### JavaScript/Fetch

```javascript
const BASE_URL = 'http://localhost:5000';

// 查询记录
async function queryRecords(userId, dbName, querySpec) {
  const response = await fetch(
    `${BASE_URL}/api/databases/${userId}/${dbName}/query`,
    {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(querySpec)
    }
  );
  return await response.json();
}

// 使用
queryRecords('alice', 'mydb', {
  table: 'products',
  filters: [{field: 'category', operator: 'eq', value: 'Electronics'}],
  limit: 10
}).then(data => console.log(data));
```

## 🔍 高级查询示例

### 过滤和排序

```json
{
  "table": "products",
  "filters": [
    {"field": "category", "operator": "eq", "value": "Electronics"},
    {"field": "price", "operator": "gte", "value": 100},
    {"field": "price", "operator": "lt", "value": 1000}
  ],
  "sort": [
    {"field": "price", "direction": "desc"}
  ],
  "limit": 10,
  "skip": 0
}
```

### 投影(只返回特定字段)

```json
{
  "table": "products",
  "project": ["name", "price"],
  "filters": [
    {"field": "category", "operator": "eq", "value": "Electronics"}
  ]
}
```

### 聚合查询

```json
{
  "table": "products",
  "group_by": "category",
  "aggregations": {
    "total_price": {"field": "price", "operation": "sum"},
    "avg_price": {"field": "price", "operation": "avg"},
    "count": {"field": "*", "operation": "count"}
  }
}
```

## 🎯 支持的操作符

### 比较操作符
- `eq` - 等于
- `ne` - 不等于
- `gt` - 大于
- `gte` - 大于等于
- `lt` - 小于
- `lte` - 小于等于

### 集合操作符
- `in` - 在列表中
- `nin` - 不在列表中

### 字符串操作符
- `contains` - 包含子串

### 聚合操作
- `sum` - 求和
- `avg` - 平均值
- `count` - 计数
- `min` - 最小值
- `max` - 最大值

## 🔧 架构设计

### 1. 控制器层 (Controllers)
- 处理 HTTP 请求/响应
- 请求验证
- 错误处理
- 返回 JSON 格式数据

### 2. 查询引擎层 (Query Engine)
- 使用链式 API 构建查询
- 执行复杂查询操作
- 支持过滤、排序、分页、聚合

### 3. 存储层 (Storage System)
- 文件系统操作
- 数据持久化
- 并发控制

### Blueprint 注册

```python
# app.py
app.register_blueprint(database_bp, url_prefix='/api/databases')
app.register_blueprint(table_bp, url_prefix='/api/databases/<user_id>/<db_name>/tables')
app.register_blueprint(record_bp, url_prefix='/api/databases/<user_id>/<db_name>/tables/<table_name>/records')
app.register_blueprint(query_bp, url_prefix='/api/databases/<user_id>/<db_name>/query')
app.register_blueprint(user_bp, url_prefix='/api/users')
```

## 📊 响应格式

### 成功响应
```json
{
  "success": true,
  "data": {...}
}
```

### 错误响应
```json
{
  "error": "错误描述信息"
}
```

### HTTP 状态码
- `200 OK` - 成功
- `201 Created` - 创建成功
- `400 Bad Request` - 请求参数错误
- `404 Not Found` - 资源不存在
- `409 Conflict` - 资源冲突
- `500 Internal Server Error` - 服务器错误
- `501 Not Implemented` - 功能未实现

## 🔐 安全注意事项

1. **认证和授权** - 当前未实现,生产环境需添加
2. **输入验证** - 已实现基本验证,可进一步加强
3. **CORS 配置** - 默认允许所有来源,生产环境需限制
4. **SQL 注入** - 使用 JSON 存储,不受影响
5. **目录遍历** - 使用 `sanitize_name` 防护

## 🚧 未来改进

- [ ] 添加 JWT 认证
- [ ] 实现用户权限系统
- [ ] 添加 API 速率限制
- [ ] 支持批量操作
- [ ] 实现事务支持
- [ ] 添加数据备份/恢复
- [ ] WebSocket 支持实时更新
- [ ] GraphQL 接口
- [ ] API 版本控制
- [ ] 详细的日志记录

## 📝 完整文档

查看 `naturaldb/api/API_DOCUMENTATION.md` 获取详细的 API 文档,包括:
- 所有端点的详细说明
- 请求/响应示例
- 错误处理
- 多种编程语言的客户端示例

## 🧪 测试

运行测试脚本:

```bash
# 启动服务器
python run_api.py

# 在另一个终端运行测试
python test_api.py
```

测试脚本将执行:
- ✅ 健康检查
- ✅ 用户 CRUD
- ✅ 数据库 CRUD
- ✅ 表 CRUD
- ✅ 记录 CRUD
- ✅ 高级查询
- ✅ 聚合操作
- ✅ 统计信息

## 🎉 特性

- ✅ 完整的 RESTful API
- ✅ MongoDB 风格的查询语法
- ✅ 支持复杂过滤和排序
- ✅ 聚合查询支持
- ✅ 分页支持
- ✅ CORS 已启用
- ✅ 错误处理完善
- ✅ 易于使用的客户端示例

## 💬 联系

如有问题或建议,请查看项目文档或提交 issue。
