# NaturalDB 文档目录

本目录包含 NaturalDB 项目的技术文档。

## 文档列表

### 设计文档
- **API_DESIGN.md** - REST API 设计文档
- **REFACTORING_SUMMARY.md** - Layer 2 查询引擎重构总结

### 实现文档
- **FLASK_API_SUMMARY.md** - Flask REST API 实现总结

### API 文档
详细的 API 使用文档位于：
- `naturaldb/api/README.md` - API 使用指南
- `naturaldb/api/API_DOCUMENTATION.md` - 完整 API 参考文档

### 测试文档
- `tests/README.md` - 测试说明文档

### NLP 接口文档
- `naturaldb/nlp_interface/README.md` - 自然语言接口文档

## 快速开始

启动 API 服务器：
```bash
# 从项目根目录
python run_api.py

# 或从 naturaldb 目录
cd naturaldb
python naturaldb.py
```

运行测试：
```bash
pytest
```
