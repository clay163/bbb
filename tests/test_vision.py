"""Unit tests for app/vision.py — 图像识别与 JSON 解析"""
import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.vision import _extract_json, recognize, encode_image


class TestExtractJson(unittest.TestCase):
    """_extract_json: 从文本中提取 JSON 数组"""

    def test_pure_json(self):
        text = '[{"name": "鸡蛋", "quantity": "3个"}]'
        result = _extract_json(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "鸡蛋")

    def test_markdown_code_block_with_tag(self):
        text = '```json\n[{"name": "鸡蛋"}]\n```'
        result = _extract_json(text)
        self.assertEqual(len(result), 1)

    def test_markdown_code_block_without_tag(self):
        text = '```\n[{"name": "鸡蛋"}]\n```'
        result = _extract_json(text)
        self.assertEqual(len(result), 1)

    def test_json_in_mixed_text(self):
        text = '识别结果：\n[{"name": "鸡蛋"}]\n以上'
        result = _extract_json(text)
        self.assertEqual(len(result), 1)

    def test_invalid_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            _extract_json("no json here")

    def test_empty_array(self):
        self.assertEqual(_extract_json("[]"), [])

    def test_markdown_with_surrounding_text(self):
        text = '结果如下：\n```json\n[{"name": "鸡蛋"}]\n```\n完毕'
        result = _extract_json(text)
        self.assertEqual(len(result), 1)


class TestEncodeImage(unittest.TestCase):
    """encode_image: 图片转 base64"""

    def test_bytes_input(self):
        data = b"fake image data"
        result = encode_image(data)
        self.assertEqual(result, base64.b64encode(data).decode())

    def test_file_path_string_input(self):
        data = b"fake image data"
        f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        try:
            f.write(data)
            f.flush()
            f.close()
            result = encode_image(f.name)
            self.assertEqual(result, base64.b64encode(data).decode())
        finally:
            os.unlink(f.name)

    def test_pathlib_input(self):
        data = b"fake image data"
        f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        try:
            f.write(data)
            f.flush()
            f.close()
            result = encode_image(Path(f.name))
            self.assertEqual(result, base64.b64encode(data).decode())
        finally:
            os.unlink(f.name)


class TestRecognize(unittest.TestCase):
    """recognize: 食材识别"""

    @patch("app.vision.chat_vision")
    def test_success(self, mock_chat_vision):
        mock_chat_vision.return_value = (
            '[{"name": "鸡蛋", "quantity": "3个", "storage": "冷藏"}]'
        )
        result = recognize("base64data")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "鸡蛋")
        self.assertEqual(result[0]["quantity"], "3个")
        self.assertEqual(result[0]["storage"], "冷藏")
        self.assertFalse(result[0]["opened"])

    @patch("app.vision.chat_vision")
    def test_default_quantity_and_storage(self, mock_chat_vision):
        """缺少 quantity/storage -> 默认值"""
        mock_chat_vision.return_value = '[{"name": "鸡蛋"}]'
        result = recognize("base64data")
        self.assertEqual(result[0]["quantity"], "适量")
        self.assertEqual(result[0]["storage"], "冷藏")

    @patch("app.vision.chat_vision")
    def test_invalid_json_returns_empty(self, mock_chat_vision):
        mock_chat_vision.return_value = "无法识别"
        result = recognize("base64data")
        self.assertEqual(result, [])

    @patch("app.vision.chat_vision")
    def test_filter_items_without_name(self, mock_chat_vision):
        """过滤没有 name 字段的项"""
        mock_chat_vision.return_value = (
            '[{"name": "鸡蛋"}, {"quantity": "3个"}, {"name": "番茄"}]'
        )
        result = recognize("base64data")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "鸡蛋")
        self.assertEqual(result[1]["name"], "番茄")

    @patch("app.vision.chat_vision")
    def test_filter_non_dict_items(self, mock_chat_vision):
        """过滤非 dict 项"""
        mock_chat_vision.return_value = '["字符串", 123, {"name": "鸡蛋"}]'
        result = recognize("base64data")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "鸡蛋")

    @patch("app.vision.chat_vision")
    def test_empty_list(self, mock_chat_vision):
        mock_chat_vision.return_value = "[]"
        result = recognize("base64data")
        self.assertEqual(result, [])

    @patch("app.vision.chat_vision")
    def test_opened_always_false(self, mock_chat_vision):
        """识别结果 opened 始终为 False"""
        mock_chat_vision.return_value = '[{"name": "鸡蛋", "opened": true}]'
        result = recognize("base64data")
        self.assertFalse(result[0]["opened"])

    @patch("app.vision.chat_vision")
    def test_multiple_items(self, mock_chat_vision):
        mock_chat_vision.return_value = (
            '[{"name": "鸡蛋"}, {"name": "番茄"}, {"name": "青菜"}]'
        )
        result = recognize("base64data")
        self.assertEqual(len(result), 3)

    @patch("app.vision.chat_vision")
    def test_chat_vision_called_with_prompt(self, mock_chat_vision):
        """chat_vision 被调用时传入 image_base64 和 PROMPT"""
        mock_chat_vision.return_value = "[]"
        recognize("my_image_data")
        call_args = mock_chat_vision.call_args[0]
        self.assertEqual(call_args[0], "my_image_data")
        self.assertIn("食材", call_args[1])


if __name__ == "__main__":
    unittest.main()