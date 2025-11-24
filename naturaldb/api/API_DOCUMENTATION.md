# NaturalDB REST API Documentation

完整的 RESTful API 文档，提供类似 Firebase/MongoDB 的 HTTP 接口。

## 快速开始

### 启动服务器

```bash
# 默认启动 (127.0.0.1:5000)
python run_api.py

# 自定义主机和端口
python run_api.py --host 0.0.0.0 --port 8080

# 启用调试模式
python run_api.py --debug

# 指定数据存储路径
python run_api.py --base-path ./my_data
```

### 测试 API

```bash
# 健康检查
curl http://localhost:5000/health

# 获取 API 信息
curl http://localhost:5000/
```

## API 端点

### 用户管理 (User Management)

#### 列出所有用户
```http
GET /api/users
```

响应:
```json
{
  "success": true,
  "count": 2,
  "users": [
    {
      "id": "user1",
      "name": "user1",
      "database_count": 3
    }
  ]
}
```

#### 创建用户
```http
POST /api/users
Content-Type: application/json

{
  "user_id": "alice",
  "name": "Alice Smith"
}
```

响应:
```json
{
  "success": true,
  "message": "User alice created successfully",
  "user": {
    "id": "alice",
    "name": "Alice Smith"
  }
}
```

#### 获取用户信息
```http
GET /api/users/{user_id}
```

响应:
```json
{
  "success": true,
  "user": {
    "id": "alice",
    "name": "alice",
    "database_count": 2,
    "databases": [
      {
        "name": "mydb",
        "table_count": 5
      }
    ]
  }
}
```

#### 获取用户统计信息
```http
GET /api/users/{user_id}/stats
```

响应:
```json
{
  "success": true,
  "user_id": "alice",
  "statistics": {
    "databases": 2,
    "tables": 10,
    "records": 1523
  }
}
```

#### 删除用户
```http
DELETE /api/users/{user_id}
```

⚠️ **警告**: 这将删除用户的所有数据库和记录！

### 数据库管理 (Database Management)

#### 列出用户的所有数据库
```http
GET /api/databases?user_id={user_id}
```

响应:
```json
{
  "success": true,
  "user_id": "alice",
  "databases": ["mydb", "testdb"]
}
```

#### 创建数据库
```http
POST /api/databases
Content-Type: application/json

{
  "user_id": "alice",
  "db_name": "mydb"
}
```

#### 获取数据库信息
```http
GET /api/databases/{user_id}/{db_name}
```

响应:
```json
{
  "success": true,
  "database": {
    "user_id": "alice",
    "db_name": "mydb",
    "exists": true
  }
}
```

#### 删除数据库
```http
DELETE /api/databases/{user_id}/{db_name}
```

### 表管理 (Table Management)

#### 列出数据库中的所有表
```http
GET /api/databases/{user_id}/{db_name}/tables
```

响应:
```json
{
  "success": true,
  "user_id": "alice",
  "db_name": "mydb",
  "tables": ["users", "products", "orders"]
}
```

#### 创建表
```http
POST /api/databases/{user_id}/{db_name}/tables
Content-Type: application/json

{
  "table_name": "products",
  "indexes": ["category", "price"]
}
```

#### 获取表信息
```http
GET /api/databases/{user_id}/{db_name}/tables/{table_name}
```

响应:
```json
{
  "success": true,
  "table": {
    "name": "products",
    "record_count": 150,
    "exists": true
  }
}
```

### 记录管理 (Record Management)

#### 列出所有记录
```http
GET /api/databases/{user_id}/{db_name}/tables/{table_name}/records
GET /api/databases/{user_id}/{db_name}/tables/{table_name}/records?limit=10&offset=20
```

响应:
```json
{
  "success": true,
  "user_id": "alice",
  "db_name": "mydb",
  "table_name": "products",
  "total": 150,
  "count": 10,
  "records": [
    {
      "id": "1",
      "name": "Laptop",
      "price": 999.99,
      "category": "Electronics"
    }
  ]
}
```

#### 创建记录
```http
POST /api/databases/{user_id}/{db_name}/tables/{table_name}/records
Content-Type: application/json

{
  "id": "123",
  "data": {
    "name": "Laptop",
    "price": 999.99,
    "category": "Electronics"
  }
}
```

#### 获取单个记录
```http
GET /api/databases/{user_id}/{db_name}/tables/{table_name}/records/{record_id}
```

响应:
```json
{
  "success": true,
  "record": {
    "id": "123",
    "name": "Laptop",
    "price": 999.99
  }
}
```

#### 更新记录
```http
PUT /api/databases/{user_id}/{db_name}/tables/{table_name}/records/{record_id}
Content-Type: application/json

{
  "data": {
    "name": "Gaming Laptop",
    "price": 1299.99,
    "category": "Electronics"
  }
}
```

#### 删除记录
```http
DELETE /api/databases/{user_id}/{db_name}/tables/{table_name}/records/{record_id}
```

### 高级查询 (Advanced Queries)

#### 执行复杂查询
```http
POST /api/databases/{user_id}/{db_name}/query
Content-Type: application/json

{
  "table": "products",
  "filters": [
    {"field": "category", "operator": "eq", "value": "Electronics"},
    {"field": "price", "operator": "lt", "value": 1000}
  ],
  "sort": [
    {"field": "price", "direction": "desc"}
  ],
  "limit": 10,
  "skip": 0,
  "project": ["name", "price"]
}
```

支持的操作符:
- `eq`: 等于
- `ne`: 不等于
- `gt`: 大于
- `gte`: 大于等于
- `lt`: 小于
- `lte`: 小于等于
- `in`: 在列表中
- `nin`: 不在列表中
- `contains`: 包含

响应:
```json
{
  "success": true,
  "user_id": "alice",
  "db_name": "mydb",
  "table": "products",
  "count": 5,
  "results": [
    {
      "name": "Smartphone",
      "price": 799.99
    }
  ]
}
```

#### 计数查询
```http
POST /api/databases/{user_id}/{db_name}/query/count
Content-Type: application/json

{
  "table": "products",
  "filters": [
    {"field": "category", "operator": "eq", "value": "Electronics"}
  ]
}
```

响应:
```json
{
  "success": true,
  "user_id": "alice",
  "db_name": "mydb",
  "table": "products",
  "count": 45
}
```

#### 聚合查询
```http
POST /api/databases/{user_id}/{db_name}/query/aggregate
Content-Type: application/json

{
  "table": "products",
  "group_by": "category",
  "aggregations": {
    "total_price": {"field": "price", "operation": "sum"},
    "avg_price": {"field": "price", "operation": "avg"},
    "count": {"field": "*", "operation": "count"}
  },
  "filters": [
    {"field": "price", "operator": "gt", "value": 0}
  ]
}
```

支持的聚合操作:
- `sum`: 求和
- `avg`: 平均值
- `count`: 计数
- `min`: 最小值
- `max`: 最大值

响应:
```json
{
  "success": true,
  "user_id": "alice",
  "db_name": "mydb",
  "table": "products",
  "group_by": "category",
  "count": 3,
  "results": [
    {
      "category": "Electronics",
      "total_price": 15000,
      "avg_price": 750,
      "count": 20
    }
  ]
}
```

## 错误处理

所有错误响应遵循统一格式:

```json
{
  "error": "错误描述信息"
}
```

HTTP 状态码:
- `200 OK`: 成功
- `201 Created`: 创建成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `409 Conflict`: 资源已存在
- `500 Internal Server Error`: 服务器内部错误
- `501 Not Implemented`: 功能未实现

## 使用示例

### Python 客户端示例

```python
import requests

BASE_URL = "http://localhost:5000"

# 创建用户
response = requests.post(f"{BASE_URL}/api/users", json={
    "user_id": "alice",
    "name": "Alice"
})
print(response.json())

# 创建数据库
response = requests.post(f"{BASE_URL}/api/databases", json={
    "user_id": "alice",
    "db_name": "mydb"
})
print(response.json())

# 创建表
response = requests.post(
    f"{BASE_URL}/api/databases/alice/mydb/tables",
    json={"table_name": "products", "indexes": ["category"]}
)
print(response.json())

# 插入记录
response = requests.post(
    f"{BASE_URL}/api/databases/alice/mydb/tables/products/records",
    json={
        "id": "1",
        "data": {
            "name": "Laptop",
            "price": 999.99,
            "category": "Electronics"
        }
    }
)
print(response.json())

# 查询记录
response = requests.post(
    f"{BASE_URL}/api/databases/alice/mydb/query",
    json={
        "table": "products",
        "filters": [
            {"field": "category", "operator": "eq", "value": "Electronics"}
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
    "filters": [
      {"field": "price", "operator": "lt", "value": 1000}
    ],
    "limit": 5
  }'
```

### JavaScript/Fetch 示例

```javascript
const BASE_URL = 'http://localhost:5000';

// 创建用户
async function createUser(userId, name) {
  const response = await fetch(`${BASE_URL}/api/users`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({user_id: userId, name: name})
  });
  return await response.json();
}

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

## CORS 配置

API 默认启用 CORS，允许跨域访问。可以在 `naturaldb/api/app.py` 中修改 CORS 配置。

## 环境变量

- `NATURALDB_BASE_PATH`: 数据存储基础路径 (默认: `./data`)

## 注意事项

1. 所有 ID 和名称应避免使用特殊字符
2. 删除操作是永久性的，无法恢复
3. 建议在生产环境中添加认证和授权机制
4. 大量数据查询时建议使用分页 (limit/skip)
5. 复杂聚合查询可能影响性能
