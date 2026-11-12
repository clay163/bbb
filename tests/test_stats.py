"""Unit tests for app/stats.py — 统计分析"""
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from app.stats import _to_date, _saving_streak, get_stats


def _today():
    return date.today()


class TestToDate(unittest.TestCase):
    """_to_date: 字符串转日期"""

    def test_valid_date(self):
        self.assertEqual(_to_date("2024-01-15"), date(2024, 1, 15))

    def test_valid_datetime(self):
        self.assertEqual(_to_date("2024-01-15T12:30:00"), date(2024, 1, 15))

    def test_empty_string(self):
        self.assertIsNone(_to_date(""))

    def test_none(self):
        self.assertIsNone(_to_date(None))

    def test_invalid_string(self):
        self.assertIsNone(_to_date("invalid"))


class TestSavingStreak(unittest.TestCase):
    """_saving_streak: 连续节约天数"""

    def test_empty(self):
        self.assertEqual(_saving_streak([]), 0)

    def test_today_only(self):
        consumed = [{"consumed_at": _today().isoformat()}]
        self.assertEqual(_saving_streak(consumed), 1)

    def test_consecutive_three_days(self):
        consumed = [
            {"consumed_at": (_today() - timedelta(days=i)).isoformat()}
            for i in range(3)
        ]
        self.assertEqual(_saving_streak(consumed), 3)

    def test_gap_breaks_streak(self):
        """今天和前天有记录，昨天没有 -> streak=1"""
        consumed = [
            {"consumed_at": _today().isoformat()},
            {"consumed_at": (_today() - timedelta(days=2)).isoformat()},
        ]
        self.assertEqual(_saving_streak(consumed), 1)

    def test_no_today(self):
        """今天没有记录 -> streak=0"""
        consumed = [{"consumed_at": (_today() - timedelta(days=1)).isoformat()}]
        self.assertEqual(_saving_streak(consumed), 0)

    def test_invalid_dates_ignored(self):
        consumed = [
            {"consumed_at": _today().isoformat()},
            {"consumed_at": "invalid"},
        ]
        self.assertEqual(_saving_streak(consumed), 1)

    def test_missing_consumed_at_key(self):
        """缺少 consumed_at 键"""
        consumed = [{"name": "猪肉"}, {"consumed_at": _today().isoformat()}]
        self.assertEqual(_saving_streak(consumed), 1)


class TestGetStats(unittest.TestCase):
    """get_stats: 统计计算"""

    @patch("app.stats.storage")
    def test_empty_data(self, mock_storage):
        mock_storage.get_consumed.return_value = []
        mock_storage.get_expired_log.return_value = []
        mock_storage.list_items.return_value = []
        result = get_stats()
        self.assertEqual(result["week_expired_count"], 0)
        self.assertEqual(result["week_consumed_count"], 0)
        self.assertEqual(result["waste_cost"], 0.0)
        self.assertEqual(result["saved_cost"], 0.0)
        self.assertEqual(result["saving_streak_days"], 0)
        self.assertEqual(result["total_in_fridge"], 0)

    @patch("app.stats.storage")
    def test_week_filtering(self, mock_storage):
        """只统计一周内的数据，超过 7 天的被过滤"""
        today_str = _today().isoformat()
        old_str = (_today() - timedelta(days=10)).isoformat()
        mock_storage.get_consumed.return_value = [
            {"consumed_at": today_str},
            {"consumed_at": old_str},
        ]
        mock_storage.get_expired_log.return_value = [
            {"expired_at": today_str},
            {"expired_at": old_str},
        ]
        mock_storage.list_items.return_value = [{"id": "1"}, {"id": "2"}]
        result = get_stats()
        self.assertEqual(result["week_expired_count"], 1)
        self.assertEqual(result["week_consumed_count"], 1)
        self.assertEqual(result["waste_cost"], 5.0)
        self.assertEqual(result["saved_cost"], 5.0)
        self.assertEqual(result["total_in_fridge"], 2)

    @patch("app.stats.storage")
    def test_saving_streak_in_stats(self, mock_storage):
        """连续节约天数正确计算"""
        consumed = [
            {"consumed_at": (_today() - timedelta(days=i)).isoformat()}
            for i in range(3)
        ]
        mock_storage.get_consumed.return_value = consumed
        mock_storage.get_expired_log.return_value = []
        mock_storage.list_items.return_value = []
        result = get_stats()
        self.assertEqual(result["saving_streak_days"], 3)

    @patch("app.stats.storage")
    def test_invalid_dates_filtered(self, mock_storage):
        """无效日期被过滤"""
        mock_storage.get_consumed.return_value = [
            {"consumed_at": "invalid"},
            {"consumed_at": ""},
        ]
        mock_storage.get_expired_log.return_value = [{"expired_at": "invalid"}]
        mock_storage.list_items.return_value = []
        result = get_stats()
        self.assertEqual(result["week_expired_count"], 0)
        self.assertEqual(result["week_consumed_count"], 0)

    @patch("app.stats.storage")
    def test_cost_calculation(self, mock_storage):
        """费用计算: waste=expired*5, saved=consumed*5"""
        mock_storage.get_consumed.return_value = [
            {"consumed_at": _today().isoformat()},
            {"consumed_at": _today().isoformat()},
        ]
        mock_storage.get_expired_log.return_value = [
            {"expired_at": _today().isoformat()},
        ]
        mock_storage.list_items.return_value = []
        result = get_stats()
        self.assertEqual(result["waste_cost"], 5.0)
        self.assertEqual(result["saved_cost"], 10.0)

    @patch("app.stats.storage")

    def test_exactly_seven_days_ago_included(self, mock_storage):
        """恰好 7 天前的数据应被包含 (>= week_ago)"""
        boundary_str = (_today() - timedelta(days=7)).isoformat()
        mock_storage.get_consumed.return_value = [{"consumed_at": boundary_str}]
        mock_storage.get_expired_log.return_value = [{"expired_at": boundary_str}]
        mock_storage.list_items.return_value = []
        result = get_stats()
        self.assertEqual(result["week_consumed_count"], 1)
        self.assertEqual(result["week_expired_count"], 1)


if __name__ == "__main__":
    unittest.main()