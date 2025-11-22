# NaturalDB Test Suite

This directory contains comprehensive test cases for the NaturalDB storage system.

## Test Coverage

### `test_storage.py`
Complete test suite for the storage layer with the following test classes:

1. **TestStorage** - Tests for the base Storage class
   - Path generation and sanitization
   - User creation and deletion
   - Database creation and deletion
   - Edge cases with special characters

2. **TestDatabaseStorage** - Tests for DatabaseStorage class
   - Initialization and metadata management
   - Table creation and deletion
   - Metadata persistence
   - Length operations

3. **TestTableStorage** - Tests for TableStorage class
   - Record CRUD operations
   - Metadata management
   - Record listing and counting
   - Path sanitization for security

4. **TestThreadSafety** - Concurrent operation tests
   - Concurrent writes to different records
   - Concurrent reads and writes
   - Concurrent metadata updates
   - Lock manager verification

5. **TestEdgeCases** - Edge case testing
   - Very long names
   - Special characters and unicode
   - Empty and nested data structures
   - Large records

6. **TestIntegration** - Integration tests
   - Complete workflow from user to records
   - Multiple databases and tables
   - Data isolation verification

## Running Tests

### Install test dependencies:
```bash
pip install -r requirements-test.txt
```

### Run all tests:
```bash
pytest
```

### Run with coverage report:
```bash
pytest --cov=naturaldb --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_storage.py
```

### Run specific test class:
```bash
pytest tests/test_storage.py::TestStorage
```

### Run specific test:
```bash
pytest tests/test_storage.py::TestStorage::test_create_user
```

### Run tests in parallel:
```bash
pytest -n auto
```

### Run tests with verbose output:
```bash
pytest -v
```

### Run only fast tests (skip slow ones):
```bash
pytest -m "not slow"
```

## Test Statistics

- **Total Test Cases:** 50+
- **Test Classes:** 6
- **Coverage Target:** >90%
- **Thread Safety Tests:** 3
- **Integration Tests:** 2

## Key Features Tested

✅ **Security**
- Path sanitization against directory traversal
- Special character handling
- Unicode support

✅ **Thread Safety**
- Concurrent reads and writes
- Lock manager functionality
- Race condition prevention

✅ **CRUD Operations**
- Create, Read, Update, Delete for all entities
- Metadata persistence
- Data integrity

✅ **Error Handling**
- Nonexistent resource access
- Invalid inputs
- Edge cases

✅ **Data Integrity**
- JSON serialization/deserialization
- Nested data structures
- Large datasets

## Continuous Integration

These tests are designed to run in CI/CD pipelines with:
- Automatic test discovery
- Coverage reporting
- Parallel execution support
- Clear failure messages

## Adding New Tests

When adding new features to NaturalDB, please:

1. Add corresponding test cases in the appropriate test class
2. Ensure tests are independent (use fixtures)
3. Test both success and failure cases
4. Include thread safety tests if relevant
5. Update this README with new test coverage
