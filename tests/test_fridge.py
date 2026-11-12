"""Unit tests for app/fridge.py — 食材分类、保质期计算、时间线分组"""
import unittest
from datetime import date, timedelta

from app.fridge import match_category, compute_item, timeline, _shelf_days


def _today():
    return date.today()


def _days_ago(n):
    return (_today() - timedelta(days=n)).isoformat()


class TestMatchCategory(unittest.TestCase):
    """match_category: 10 类食材匹配 + 未知兜底"""

    def test_all_ten_categories(self):
        """每个类别至少一个代表食材能正确匹配"""
        cases = [
            ("青菜", "叶菜类"),
            ("胡萝卜", "根茎类"),
            ("西红柿", "瓜果类"),
            ("鸡蛋", "蛋奶类"),
            ("猪肉", "肉类"),
            ("鱼", "水产类"),
            ("米饭", "主食类"),
            ("剩菜", "熟食类"),
            ("木耳", "干货类"),
            ("苹果", "水果类"),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(match_category(name), expected)

    def test_name_contains_example(self):
        """食材名包含例子字符串 -> 匹配"""
        self.assertEqual(match_category("大白菜"), "叶菜类")

    def test_example_contains_name(self):
        """例子字符串包含食材名 -> 匹配"""
        self.assertEqual(match_category("菜"), "叶菜类")

    def test_unknown_food(self):
        self.assertEqual(match_category("外星食材"), "其他")

    def test_empty_string(self):
        """空字符串: '' in '青菜' 为 True -> 匹配第一个类别叶菜类"""
        self.assertEqual(match_category(""), "叶菜类")


class TestShelfDays(unittest.TestCase):
    """_shelf_days: 冷藏/冷冻/常温 + fallback + 未知类别"""

    def test_chilled(self):
        self.assertEqual(_shelf_days("叶菜类", "冷藏"), 3)

    def test_frozen(self):
        self.assertEqual(_shelf_days("叶菜类", "冷冻"), 30)

    def test_room_fallback_to_chilled(self):
        """叶菜类没有 days_room -> fallback to days_chilled=3"""
        self.assertEqual(_shelf_days("叶菜类", "常温"), 3)

    def test_egg_dairy_frozen_fallback(self):
        """蛋奶类没有 days_frozen -> fallback to days_chilled=21"""
        self.assertEqual(_shelf_days("蛋奶类", "冷冻"), 21)

    def test_dry_goods_chilled_fallback(self):
        """干货类没有 days_chilled -> fallback to days_room=180"""
        self.assertEqual(_shelf_days("干货类", "冷藏"), 180)

    def test_unknown_category_returns_default(self):
        self.assertEqual(_shelf_days("未知类别", "冷藏"), 3)

    def test_unknown_category_frozen(self):
        self.assertEqual(_shelf_days("未知类别", "冷冻"), 3)

    def test_unknown_category_room(self):
        self.assertEqual(_shelf_days("未知类别", "常温"), 3)


class TestComputeItem(unittest.TestCase):
    """compute_item: 冷藏/冷冻/常温 × 开封/未开封 × 状态组合"""

    # --- 状态分支 ---

    def test_expired(self):
        """已过期: days_left < 0"""
        item = {"name": "猪肉", "purchase_date": _days_ago(10)}
        result = compute_item(item)
        self.assertEqual(result["status"], "expired")
        self.assertLess(result["days_left"], 0)
        self.assertEqual(result["category"], "肉类")

    def test_expiring(self):
        """即将过期: days_left <= 1"""
        # 虾->水产类 冷藏days=2, opened->max(1,1)=1, days_left=1
        item = {"name": "虾", "purchase_date": _today().isoformat(), "opened": True}
        result = compute_item(item)
        self.assertEqual(result["status"], "expiring")
        self.assertLessEqual(result["days_left"], 1)

    def test_freeze_suggested(self):
        """建议冷冻: 冷藏 + days_left<=3 + 冷冻天数>冷藏天数"""
        # 青菜->叶菜类 冷藏days=3 冷冻days=30, purchase=yesterday
        # expire=today+2, days_left=2, 30>3 -> freeze_suggested
        item = {"name": "青菜", "purchase_date": _days_ago(1)}
        result = compute_item(item)
        self.assertEqual(result["status"], "freeze_suggested")
        self.assertLessEqual(result["days_left"], 3)

    def test_fresh(self):
        """仍可存放"""
        item = {"name": "胡萝卜", "purchase_date": _today().isoformat()}
        result = compute_item(item)
        self.assertEqual(result["status"], "fresh")
        self.assertGreater(result["days_left"], 3)

    # --- 开封逻辑 ---

    def test_opened_halves_days(self):
        """开封后保质期减半"""
        r_closed = compute_item({"name": "胡萝卜", "purchase_date": _today().isoformat()})
        r_opened = compute_item(
            {"name": "胡萝卜", "purchase_date": _today().isoformat(), "opened": True}
        )
        self.assertEqual(r_closed["shelf_days"], 14)
        self.assertEqual(r_opened["shelf_days"], 7)

    def test_opened_minimum_one_day(self):
        """开封后最少 1 天 (水产 days=2, opened->max(1,1)=1)"""
        item = {"name": "鱼", "purchase_date": _today().isoformat(), "opened": True}
        result = compute_item(item)
        self.assertEqual(result["shelf_days"], 1)

    # --- 日期解析 ---

    def test_invalid_date_fallback_today(self):
        """日期解析失败 -> 使用今天"""
        item = {"name": "猪肉", "purchase_date": "invalid-date"}
        result = compute_item(item)
        self.assertEqual(result["days_left"], 3)
        # 冷藏+days_left=3+冷冻90>3 -> freeze_suggested
        self.assertEqual(result["status"], "freeze_suggested")

    def test_uses_added_at_when_no_purchase_date(self):
        """没有 purchase_date 时使用 added_at"""
        item = {"name": "猪肉", "added_at": _days_ago(10)}
        result = compute_item(item)
        self.assertEqual(result["status"], "expired")

    def test_iso_datetime_with_t(self):
        """带 T 的 ISO 日期时间"""
        dt = _days_ago(10) + "T12:00:00"
        item = {"name": "猪肉", "purchase_date": dt}
        result = compute_item(item)
        self.assertEqual(result["status"], "expired")

    def test_no_date_fields(self):
        """既无 purchase_date 也无 added_at -> base=today"""
        item = {"name": "猪肉"}
        result = compute_item(item)
        self.assertEqual(result["days_left"], 3)

    # --- category / storage ---

    def test_explicit_category(self):
        """直接提供 category"""
        item = {"name": "xxx", "category": "肉类", "purchase_date": _days_ago(10)}
        result = compute_item(item)
        self.assertEqual(result["category"], "肉类")
        self.assertEqual(result["status"], "expired")

    def test_default_storage_chilled(self):
        """默认存储方式为冷藏"""
        item = {"name": "猪肉", "purchase_date": _today().isoformat()}
        result = compute_item(item)
        self.assertEqual(result["shelf_days"], 3)

    def test_frozen_storage(self):
        """冷冻存储"""
        item = {"name": "猪肉", "storage": "冷冻", "purchase_date": _today().isoformat()}
        result = compute_item(item)
        self.assertEqual(result["shelf_days"], 90)
        self.assertEqual(result["status"], "fresh")

    def test_room_storage(self):
        """常温存储"""
        item = {"name": "胡萝卜", "storage": "常温", "purchase_date": _today().isoformat()}
        result = compute_item(item)
        self.assertEqual(result["shelf_days"], 30)

    # --- 结果字段 ---

    def test_tip_included(self):
        """结果包含 tip"""
        result = compute_item({"name": "猪肉", "purchase_date": _today().isoformat()})
        self.assertIn("tip", result)
        self.assertTrue(result["tip"])

    def test_tip_empty_for_unknown_category(self):
        """未知类别 tip 为空字符串"""
        result = compute_item(
            {"name": "外星食材", "category": "未知", "purchase_date": _today().isoformat()}
        )
        self.assertEqual(result["tip"], "")

    def test_original_fields_preserved(self):
        """原始字段保留"""
        item = {
            "name": "猪肉",
            "purchase_date": _today().isoformat(),
            "custom_field": "abc",
        }
        result = compute_item(item)
        self.assertEqual(result["custom_field"], "abc")
        self.assertEqual(result["name"], "猪肉")

    def test_expire_date_format(self):
        """expire_date 为 ISO 格式字符串"""
        result = compute_item({"name": "猪肉", "purchase_date": _today().isoformat()})
        self.assertIsInstance(result["expire_date"], str)
        date.fromisoformat(result["expire_date"])


class TestTimeline(unittest.TestCase):
    """timeline: 分组、排序、边界"""

    def test_empty_list(self):
        """空列表 -> sections=[], all=[]"""
        result = timeline([])
        self.assertEqual(result["sections"], [])
        self.assertEqual(result["all"], [])

    def test_mixed_statuses_ordered(self):
        """多种状态 -> 按 expired/expiring/freeze_suggested/fresh 排序"""
        items = [
            {"name": "猪肉", "purchase_date": _days_ago(10)},  # expired
            {"name": "青菜", "purchase_date": _days_ago(1)},  # freeze_suggested
            {"name": "胡萝卜", "purchase_date": _today().isoformat()},  # fresh
        ]
        result = timeline(items)
        keys = [s["key"] for s in result["sections"]]
        self.assertEqual(keys, ["expired", "freeze_suggested", "fresh"])
        self.assertEqual(len(result["all"]), 3)

    def test_single_status(self):
        """全部同状态 -> 只有一个 section"""
        items = [
            {"name": "胡萝卜", "purchase_date": _today().isoformat()},
            {"name": "土豆", "purchase_date": _today().isoformat()},
        ]
        result = timeline(items)
        self.assertEqual(len(result["sections"]), 1)
        self.assertEqual(result["sections"][0]["key"], "fresh")
        self.assertEqual(len(result["sections"][0]["items"]), 2)

    def test_section_labels(self):
        """section 包含正确中文标签"""
        result = timeline([{"name": "猪肉", "purchase_date": _days_ago(10)}])
        self.assertEqual(result["sections"][0]["label"], "已过期")

    def test_all_enriched(self):
        """all 字段包含所有增强后的 item"""
        items = [
            {"name": "猪肉", "purchase_date": _days_ago(10)},
            {"name": "胡萝卜", "purchase_date": _today().isoformat()},
        ]
        result = timeline(items)
        self.assertEqual(len(result["all"]), 2)
        for it in result["all"]:
            self.assertIn("status", it)
            self.assertIn("days_left", it)


if __name__ == "__main__":
    unittest.main()