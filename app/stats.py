from datetime import datetime, date, timedelta

from . import storage

AVG_PRICE = 5.0


def _to_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        return None


def _saving_streak(consumed: list[dict]) -> int:
    days = {_to_date(c.get("consumed_at")) for c in consumed}
    days.discard(None)
    streak = 0
    d = date.today()
    while d in days:
        streak += 1
        d -= timedelta(days=1)
    return streak


def get_stats() -> dict:
    consumed = storage.get_consumed()
    expired_log = storage.get_expired_log()
    today = date.today()
    week_ago = today - timedelta(days=7)

    week_expired = [e for e in expired_log
                    if (d := _to_date(e.get("expired_at"))) and d >= week_ago]
    week_consumed = [c for c in consumed
                     if (d := _to_date(c.get("consumed_at"))) and d >= week_ago]

    return {
        "week_expired_count": len(week_expired),
        "week_consumed_count": len(week_consumed),
        "waste_cost": round(len(week_expired) * AVG_PRICE, 1),
        "saved_cost": round(len(week_consumed) * AVG_PRICE, 1),
        "saving_streak_days": _saving_streak(consumed),
        "total_in_fridge": len(storage.list_items()),
    }