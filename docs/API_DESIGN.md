# NaturalDB RESTful API 设计

## API 基础路径
```
Base URL: http://localhost:5000/api/v1
```

## API 路由设计

### 1. 用户管理 (Users)

#### 创建用户
```
POST /users
Body: {
  "id": "user123",
  "name": "Alice Smith"
}
Response: {
  "success": true,
  "user": {"id": "user123", "name": "Alice Smith"}
}
```

#### 获取用户列表
```
GET /users
Response: {
  "success": true,
  "users": [...]
}
```

#### 获取用户信息
```
GET /users/:userId
Response: {
  "success": true,
  "user": {...}
}
```

---

### 2. 数据库管理 (Databases)

#### 创建数据库
```
POST /users/:userId/databases
Body: {
  "name": "ecommerce"
}
Response: {
  "success": true,
  "database": {"name": "ecommerce"}
}
```

#### 获取用户的数据库列表
```
GET /users/:userId/databases
Response: {
  "success": true,
  "databases": ["db1", "db2"]
}
```

#### 删除数据库
```
DELETE /users/:userId/databases/:dbName
Response: {
  "success": true,
  "message": "Database deleted"
}
```

---

### 3. 表管理 (Tables/Collections)

#### 创建表
```
POST /users/:userId/databases/:dbName/tables
Body: {
  "name": "products",
  "indexes": {"name": "text"}
}
Response: {
  "success": true,
  "table": {"name": "products", "indexes": {...}}
}
```

#### 获取表列表
```
GET /users/:userId/databases/:dbName/tables
Response: {
  "success": true,
  "tables": ["products", "orders", "users"]
}
```

#### 删除表
```
DELETE /users/:userId/databases/:dbName/tables/:tableName
Response: {
  "success": true,
  "message": "Table deleted"
}
```

---

### 4. 记录 CRUD (Records/Documents)

#### 插入记录
```
POST /users/:userId/databases/:dbName/tables/:tableName/records
Body: {
  "id": "prod123",
  "data": {
    "name": "iPhone 15",
    "price": 999,
    "stock": 50
  }
}
Response: {
  "success": true,
  "record": {"id": "prod123", "data": {...}}
}
```

#### 批量插入
```
POST /users/:userId/databases/:dbName/tables/:tableName/records/batch
Body: {
  "records": [
    {"id": "1", "data": {...}},
    {"id": "2", "data": {...}}
  ]
}
Response: {
  "success": true,
  "inserted": 2
}
```

#### 获取单条记录
```
GET /users/:userId/databases/:dbName/tables/:tableName/records/:recordId
Response: {
  "success": true,
  "record": {"id": "...", "data": {...}}
}
```

#### 获取所有记录
```
GET /users/:userId/databases/:dbName/tables/:tableName/records
Response: {
  "success": true,
  "records": [...],
  "count": 100
}
```

#### 更新记录
```
PUT /users/:userId/databases/:dbName/tables/:tableName/records/:recordId
Body: {
  "data": {
    "name": "iPhone 15 Pro",
    "price": 1099
  }
}
Response: {
  "success": true,
  "record": {...}
}
```

#### 删除记录
```
DELETE /users/:userId/databases/:dbName/tables/:tableName/records/:recordId
Response: {
  "success": true,
  "message": "Record deleted"
}
```

---

### 5. 高级查询 (Advanced Queries)

#### 查询记录（带过滤、排序、分页）
```
POST /users/:userId/databases/:dbName/tables/:tableName/query
Body: {
  "filter": {
    "price": {"operator": "gt", "value": 500}
  },
  "sort": {
    "field": "price",
    "order": "asc"  // or "desc"
  },
  "limit": 10,
  "offset": 0,
  "fields": ["name", "price"]  // 可选：字段投影
}
Response: {
  "success": true,
  "records": [...],
  "count": 5,
  "total": 50
}
```

#### 聚合查询
```
POST /users/:userId/databases/:dbName/tables/:tableName/aggregate
Body: {
  "groupBy": "category",
  "aggregations": {
    "price": "avg",
    "stock": "sum"
  }
}
Response: {
  "success": true,
  "results": {
    "electronics": {"count": 10, "avg_price": 599, "sum_stock": 500},
    "clothing": {"count": 20, "avg_price": 49, "sum_stock": 1000}
  }
}
```

#### 表连接查询
```
POST /users/:userId/databases/:dbName/join
Body: {
  "leftTable": "orders",
  "rightTable": "products",
  "leftField": "product_id",
  "rightField": "id",
  "joinType": "inner",  // or "left"
  "filter": {...},      // 可选
  "limit": 100
}
Response: {
  "success": true,
  "results": [...]
}
```

---

### 6. 导入/导出 (Import/Export)

#### 从 JSON 文件导入
```
POST /users/:userId/databases/:dbName/tables/:tableName/import
Body: {
  "format": "json",
  "data": [...]  // JSON array
}
Response: {
  "success": true,
  "imported": 100
}
```

#### 导出为 JSON
```
GET /users/:userId/databases/:dbName/tables/:tableName/export?format=json
Response: {
  "success": true,
  "data": [...],
  "count": 100
}
```

---

## 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Table 'products' not found"
  }
}
```

## 状态码

- `200 OK` - 成功
- `201 Created` - 创建成功
- `400 Bad Request` - 请求参数错误
- `404 Not Found` - 资源不存在
- `409 Conflict` - 资源冲突（如已存在）
- `500 Internal Server Error` - 服务器错误
