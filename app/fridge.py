import json
import re
from datetime import datetime, date, timedelta
from pathlib import Path

SHELF_LIFE_FILE = Path(__file__).resolve().parent.parent / "data" / "shelf_life.json"
_rules = None

FOOD_CALORIES = {
    "鸡蛋": 70, "鸭蛋": 90, "鹌鹑蛋": 15,
    "牛奶": 150, "酸奶": 100, "奶酪": 350, "黄油": 700,
    "西红柿": 18, "番茄": 18, "黄瓜": 16, "茄子": 25, "青椒": 22,
    "胡萝卜": 32, "萝卜": 23, "白萝卜": 23, "土豆": 77, "马铃薯": 77,
    "青菜": 15, "白菜": 17, "菠菜": 28, "生菜": 15, "芹菜": 22,
    "西兰花": 36, "花菜": 25, "韭菜": 26, "空心菜": 20,
    "米饭": 174, "剩米饭": 174, "粥": 88, "剩饭": 174,
    "面条": 280, "挂面": 340, "意面": 350, "米粉": 220,
    "面包": 313, "馒头": 223, "吐司": 290,
    "鸡肉": 165, "鸡腿": 184, "鸡翅": 203,
    "猪肉": 395, "排骨": 278, "火腿": 330, "培根": 541,
    "牛肉": 125, "牛排": 271,
    "鱼": 145, "三文鱼": 208, "带鱼": 127, "鲈鱼": 105,
    "虾": 99, "大虾": 99, "蟹": 103, "螃蟹": 103,
    "豆腐": 81, "豆干": 140, "腐竹": 459,
    "洋葱": 40, "大蒜": 149, "蒜": 149, "姜": 80,
    "玉米": 112, "南瓜": 26, "冬瓜": 12, "丝瓜": 20,
    "蘑菇": 22, "香菇": 26, "金针菇": 32,
    "苹果": 52, "香蕉": 89, "柠檬": 37, "橙子": 47,
    "草莓": 32, "葡萄": 67, "西瓜": 30, "梨": 57, "桃": 39,
    "芒果": 60, "菠萝": 50, "猕猴桃": 61, "樱桃": 50,
    "饺子": 250, "包子": 227, "馄饨": 200,
    "剩菜": 200, "汤": 80,
}

CATEGORY_CALORIES = {
    "叶菜类": 25, "根茎类": 80, "瓜果类": 20, "蛋奶类": 150,
    "肉类": 250, "水产类": 120, "主食类": 130, "熟食类": 200,
    "干货类": 350, "水果类": 60, "其他": 100,
}


CN_NUMS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "两": 2}


def _parse_quantity(qty: str) -> float:
    qty = qty.strip()
    if "半" in qty:
        return 0.5
    m = re.search(r"(\d+(?:\.\d+)?)", qty)
    if m:
        return float(m.group(1))
    for cn, val in CN_NUMS.items():
        if cn in qty:
            return float(val)
    if qty in ("适量", "一些", "若干"):
        return 1.0
    if qty in ("少量", "一点", "少许"):
        return 0.5
    return 1.0


def _weight_multiplier(qty: str) -> float:
    if "斤" in qty:
        return 5.0
    if "kg" in qty.lower() or "公斤" in qty:
        return 10.0
    if "两" in qty and "斤" not in qty:
        return 0.5
    return 1.0


def estimate_calories(name: str, quantity: str = "适量", category: str = "") -> int:
    per_unit = 100
    for key, cal in FOOD_CALORIES.items():
        if key in name:
            per_unit = cal
            break
    else:
        per_unit = CATEGORY_CALORIES.get(category, 100)
    count = _parse_quantity(quantity)
    weight_mult = _weight_multiplier(quantity)
    return round(per_unit * count * weight_mult)


def _load_rules() -> dict:
    global _rules
    if _rules is None:
        _rules = json.loads(SHELF_LIFE_FILE.read_text(encoding="utf-8"))
    return _rules


def match_category(name: str) -> str | None:
    rules = _load_rules()
    for cat, info in rules.items():
        for ex in info.get("examples", []):
            if ex in name or name in ex:
                return cat
    return "其他"


def _shelf_days(category: str, storage: str) -> int:
    rules = _load_rules()
    info = rules.get(category, {})
    if storage == "冷冻":
        d = info.get("days_frozen")
    elif storage == "常温":
        d = info.get("days_room")
    else:
        d = info.get("days_chilled")
    if d is None:
        for key in ("days_chilled", "days_room", "days_frozen"):
            if info.get(key):
                d = info[key]
                break
    return d or 3


def compute_item(item: dict) -> dict:
    name = item.get("name", "")
    storage = item.get("storage", "冷藏")
    opened = item.get("opened", False)
    category = item.get("category") or match_category(name)

    days = _shelf_days(category, storage)
    if opened:
        days = max(1, days // 2)

    purchase = item.get("purchase_date") or item.get("added_at", "")
    try:
        if "T" in purchase:
            base = datetime.fromisoformat(purchase).date()
        else:
            base = date.fromisoformat(purchase[:10])
    except Exception:
        base = date.today()

    expire = base + timedelta(days=days)
    today = date.today()
    days_left = (expire - today).days

    if days_left < 0:
        status = "expired"
    elif days_left <= 1:
        status = "expiring"
    elif storage == "冷藏" and days_left <= 3 and _shelf_days(category, "冷冻") > days:
        status = "freeze_suggested"
    else:
        status = "fresh"

    tip = _load_rules().get(category, {}).get("tip", "")
    calories = estimate_calories(name, item.get("quantity", "适量"), category)

    return {
        **item,
        "category": category,
        "shelf_days": days,
        "expire_date": expire.isoformat(),
        "days_left": days_left,
        "status": status,
        "tip": tip,
        "calories": calories,
    }


def timeline(items: list[dict]) -> dict:
    enriched = [compute_item(it) for it in items]
    groups = {"expiring": [], "fresh": [], "freeze_suggested": [], "expired": []}
    for it in enriched:
        groups[it["status"]].append(it)
    order = ["expired", "expiring", "freeze_suggested", "fresh"]
    labels = {
        "expired": "已过期",
        "expiring": "即将过期",
        "freeze_suggested": "建议冷冻",
        "fresh": "仍可存放",
    }
    return {
        "sections": [
            {"key": k, "label": labels[k], "items": groups[k]}
            for k in order if groups[k]
        ],
        "all": enriched,
    }