"""Unit tests for app/storage.py — 数据存储 CRUD 操作"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app.storage as storage


class TestStorage(unittest.TestCase):
    """storage 模块全部 CRUD 操作，使用临时 JSON 文件隔离"""

    def setUp(self):
        """每个测试使用独立临时文件"""
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        self._tmp.write(json.dumps({"items": [], "consumed": [], "expired_log": []}))
        self._tmp.close()
        self.db_path = Path(self._tmp.name)

    def tearDown(self):
        self.db_path.unlink(missing_ok=True)

    # --- list_items ---

    def test_list_items_empty(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            self.assertEqual(storage.list_items(), [])

    # --- add_item ---

    def test_add_item_auto_id_and_added_at(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            result = storage.add_item({"name": "猪肉"})
            self.assertIn("id", result)
            self.assertTrue(result["id"])
            self.assertIn("added_at", result)
            items = storage.list_items()
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["name"], "猪肉")

    def test_add_item_preserves_existing_id(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            result = storage.add_item({"name": "猪肉", "id": "custom-id"})
            self.assertEqual(result["id"], "custom-id")

    def test_add_item_preserves_existing_added_at(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            result = storage.add_item(
                {"name": "猪肉", "added_at": "2024-01-01T00:00:00"}
            )
            self.assertEqual(result["added_at"], "2024-01-01T00:00:00")

    def test_add_multiple_items(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            storage.add_item({"name": "猪肉"})
            storage.add_item({"name": "牛肉"})
            self.assertEqual(len(storage.list_items()), 2)

    # --- update_item ---

    def test_update_item_found(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            storage.add_item({"name": "猪肉", "id": "item1"})
            result = storage.update_item("item1", {"name": "牛肉"})
            self.assertIsNotNone(result)
            self.assertEqual(result["name"], "牛肉")
            self.assertEqual(result["id"], "item1")

    def test_update_item_not_found(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            result = storage.update_item("nonexistent", {"name": "牛肉"})
            self.assertIsNone(result)

    def test_update_item_multiple_fields(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            storage.add_item({"name": "猪肉", "id": "item1", "storage": "冷藏"})
            result = storage.update_item("item1", {"storage": "冷冻", "opened": True})
            self.assertEqual(result["storage"], "冷冻")
            self.assertTrue(result["opened"])

    # --- remove_item ---

    def test_remove_item_success(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            storage.add_item({"name": "猪肉", "id": "item1"})
            self.assertTrue(storage.remove_item("item1"))
            self.assertEqual(storage.list_items(), [])

    def test_remove_item_not_found(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            self.assertFalse(storage.remove_item("nonexistent"))

    # --- consume_item ---

    def test_consume_item_success(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            storage.add_item({"name": "猪肉", "id": "item1"})
            self.assertTrue(storage.consume_item("item1"))
            self.assertEqual(storage.list_items(), [])
            consumed = storage.get_consumed()
            self.assertEqual(len(consumed), 1)
            self.assertEqual(consumed[0]["name"], "猪肉")
            self.assertIn("consumed_at", consumed[0])

    def test_consume_item_not_found(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            self.assertFalse(storage.consume_item("nonexistent"))

    # --- log_expired ---

    def test_log_expired(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            storage.log_expired({"name": "过期猪肉"})
            log = storage.get_expired_log()
            self.assertEqual(len(log), 1)
            self.assertEqual(log[0]["name"], "过期猪肉")
            self.assertIn("expired_at", log[0])

    # --- get_consumed / get_expired_log ---

    def test_get_consumed_empty(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            self.assertEqual(storage.get_consumed(), [])

    def test_get_expired_log_empty(self):
        with patch.object(storage, "DB_FILE", self.db_path):
            self.assertEqual(storage.get_expired_log(), [])

    # --- _load 文件不存在 ---

    def test_load_no_file_returns_default(self):
        """文件不存在时返回默认结构"""
        nonexistent = Path(tempfile.gettempdir()) / "nonexistent_db_test.json"
        nonexistent.unlink(missing_ok=True)
        with patch.object(storage, "DB_FILE", nonexistent):
            self.assertEqual(storage.list_items(), [])
            self.assertEqual(storage.get_consumed(), [])
            self.assertEqual(storage.get_expired_log(), [])

    def test_persistence_across_operations(self):
        """多次操作持久化正确"""
        with patch.object(storage, "DB_FILE", self.db_path):
            storage.add_item({"name": "猪肉", "id": "i1"})
            storage.add_item({"name": "牛肉", "id": "i2"})
            storage.consume_item("i1")
            self.assertEqual(len(storage.list_items()), 1)
            self.assertEqual(storage.list_items()[0]["name"], "牛肉")
            self.assertEqual(len(storage.get_consumed()), 1)


if __name__ == "__main__":
    unittest.main()