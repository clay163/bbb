import json
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE = DATA_DIR / "fridge.json"


def _load() -> dict:
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    return {"items": [], "consumed": [], "expired_log": []}


def _save(db: dict) -> None:
    DB_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def list_items() -> list[dict]:
    return _load()["items"]


def add_item(item: dict) -> dict:
    db = _load()
    if "id" not in item:
        item["id"] = f"f{len(db['items']) + 1}{int(datetime.now().timestamp()) % 100000}"
    if "added_at" not in item:
        item["added_at"] = datetime.now().isoformat()
    db["items"].append(item)
    _save(db)
    return item


def update_item(item_id: str, updates: dict) -> dict | None:
    db = _load()
    for it in db["items"]:
        if it["id"] == item_id:
            it.update(updates)
            _save(db)
            return it
    return None


def remove_item(item_id: str) -> bool:
    db = _load()
    before = len(db["items"])
    db["items"] = [it for it in db["items"] if it["id"] != item_id]
    _save(db)
    return len(db["items"]) < before


def consume_item(item_id: str) -> bool:
    db = _load()
    for it in db["items"]:
        if it["id"] == item_id:
            it["consumed_at"] = datetime.now().isoformat()
            db["consumed"].append(it)
            db["items"] = [x for x in db["items"] if x["id"] != item_id]
            _save(db)
            return True
    return False


def log_expired(item: dict) -> None:
    db = _load()
    item["expired_at"] = datetime.now().isoformat()
    db["expired_log"].append(item)
    _save(db)


def get_consumed() -> list[dict]:
    return _load()["consumed"]


def get_expired_log() -> list[dict]:
    return _load()["expired_log"]

RECIPE_FILE = DATA_DIR / "recipes.json"


def _load_recipes() -> dict:
    if RECIPE_FILE.exists():
        return json.loads(RECIPE_FILE.read_text(encoding="utf-8"))
    return {"favorites": [], "history": []}


def _save_recipes(data: dict) -> None:
    RECIPE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_favorite(recipe: dict) -> None:
    data = _load_recipes()
    name = recipe.get("name", "")
    data["favorites"] = [f for f in data["favorites"] if f.get("name") != name]
    recipe["saved_at"] = datetime.now().isoformat()
    data["favorites"].append(recipe)
    _save_recipes(data)


def remove_favorite(name: str) -> None:
    data = _load_recipes()
    data["favorites"] = [f for f in data["favorites"] if f.get("name") != name]
    _save_recipes(data)


def list_favorites() -> list[dict]:
    return _load_recipes()["favorites"]


def is_favorite(name: str) -> bool:
    return any(f.get("name") == name for f in _load_recipes()["favorites"])


def add_history(recipe: dict) -> None:
    data = _load_recipes()
    recipe["cooked_at"] = datetime.now().isoformat()
    data["history"].append(recipe)
    if len(data["history"]) > 50:
        data["history"] = data["history"][-50:]
    _save_recipes(data)


def list_history() -> list[dict]:
    return _load_recipes()["history"]