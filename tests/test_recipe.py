"""Unit tests for app/recipe.py — 菜谱生成与 JSON 解析"""
import json
import unittest
from unittest.mock import patch

from app.recipe import _extract_json, generate_recipes


class TestExtractJson(unittest.TestCase):
    """_extract_json: 从文本中提取 JSON 数组"""

    def test_pure_json(self):
        text = '[{"name": "炒鸡蛋", "time_min": 10}]'
        result = _extract_json(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "炒鸡蛋")

    def test_markdown_code_block_with_json_tag(self):
        text = '```json\n[{"name": "炒鸡蛋"}]\n```'
        result = _extract_json(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "炒鸡蛋")

    def test_markdown_code_block_without_tag(self):
        text = '```\n[{"name": "炒鸡蛋"}]\n```'
        result = _extract_json(text)
        self.assertEqual(len(result), 1)

    def test_json_embedded_in_mixed_text(self):
        """JSON 数组被包裹在杂乱文本中"""
        text = '这是菜谱：\n[{"name": "炒鸡蛋"}]\n请享用'
        result = _extract_json(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "炒鸡蛋")

    def test_multiple_items(self):
        text = '[{"name": "炒鸡蛋"}, {"name": "番茄汤"}]'
        result = _extract_json(text)
        self.assertEqual(len(result), 2)

    def test_invalid_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            _extract_json("not json at all")

    def test_empty_array(self):
        result = _extract_json("[]")
        self.assertEqual(result, [])

    def test_markdown_with_surrounding_text(self):
        """markdown 代码块前后有文本"""
        text = '好的，这是结果：\n```json\n[{"name": "炒鸡蛋"}]\n```\n希望你喜欢'
        result = _extract_json(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "炒鸡蛋")


class TestGenerateRecipes(unittest.TestCase):
    """generate_recipes: 菜谱生成"""

    @patch("app.recipe.chat")
    def test_success(self, mock_chat):
        mock_chat.return_value = '[{"name": "番茄炒蛋", "time_min": 15}]'
        result = generate_recipes(["鸡蛋", "番茄"], "清淡", 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "番茄炒蛋")
        mock_chat.assert_called_once()

    @patch("app.recipe.chat")
    def test_failure_returns_error_recipe(self, mock_chat):
        """LLM 返回非 JSON -> 返回生成失败菜谱"""
        mock_chat.return_value = "无法生成菜谱"
        result = generate_recipes(["鸡蛋"], "", 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "生成失败")
        self.assertEqual(result[0]["steps"], [])
        self.assertEqual(result[0]["time_min"], 0)
        self.assertIn("无法生成菜谱", result[0]["description"])

    @patch("app.recipe.chat")
    def test_empty_ingredients(self, mock_chat):
        """空食材列表 -> prompt 包含 '暂无食材'"""
        mock_chat.return_value = '[{"name": "清炒时蔬"}]'
        generate_recipes([], "", 1)
        messages = mock_chat.call_args[0][0]
        self.assertIn("暂无食材", messages[0]["content"])

    @patch("app.recipe.chat")
    def test_default_preference(self, mock_chat):
        """空偏好 -> prompt 包含 '无特殊要求'"""
        mock_chat.return_value = "[]"
        generate_recipes(["鸡蛋"], "", 1)
        messages = mock_chat.call_args[0][0]
        self.assertIn("无特殊要求", messages[0]["content"])

    @patch("app.recipe.chat")
    def test_custom_preference(self, mock_chat):
        """自定义偏好传入 prompt"""
        mock_chat.return_value = "[]"
        generate_recipes(["鸡蛋"], "快手", 2)
        messages = mock_chat.call_args[0][0]
        self.assertIn("快手", messages[0]["content"])

    @patch("app.recipe.chat")
    def test_ingredients_formatted_in_prompt(self, mock_chat):
        """食材以列表格式传入 prompt"""
        mock_chat.return_value = "[]"
        generate_recipes(["鸡蛋", "番茄"], "", 1)
        messages = mock_chat.call_args[0][0]
        self.assertIn("- 鸡蛋", messages[0]["content"])
        self.assertIn("- 番茄", messages[0]["content"])

    @patch("app.recipe.chat")
    def test_temperature_passed(self, mock_chat):
        """temperature=0.8 传给 chat"""
        mock_chat.return_value = "[]"
        generate_recipes(["鸡蛋"], "", 1)
        kwargs = mock_chat.call_args[1]
        self.assertEqual(kwargs["temperature"], 0.8)


if __name__ == "__main__":
    unittest.main()