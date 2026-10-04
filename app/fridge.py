import json
from datetime import datetime, date, timedelta
from pathlib import Path

SHELF_LIFE_FILE = Path(__file__).resolve().parent.parent / "data" / "shelf_life.json"
_rules = None


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

    return {
        **item,
        "category": category,
        "shelf_days": days,
        "expire_date": expire.isoformat(),
        "days_left": days_left,
        "status": status,
        "tip": tip,
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