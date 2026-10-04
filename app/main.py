import base64
from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import storage, vision, fridge, recipe, stats

app = FastAPI(title="AI 冰箱管家", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class ItemIn(BaseModel):
    name: str
    quantity: str = "适量"
    storage: str = "冷藏"
    opened: bool = False
    purchase_date: str | None = None
    category: str | None = None


class ItemUpdate(BaseModel):
    name: str | None = None
    quantity: str | None = None
    storage: str | None = None
    opened: bool | None = None
    purchase_date: str | None = None
    category: str | None = None


class ImageIn(BaseModel):
    image_base64: str


class RecipeIn(BaseModel):
    ingredients: list[str]
    preference: str = ""
    count: int = 3


@app.get("/")
def root():
    return {"msg": "AI 冰箱管家 API", "docs": "/docs"}


@app.post("/vision/recognize")
def recognize(img: ImageIn):
    try:
        items = vision.recognize(img.image_base64)
    except Exception as e:
        raise HTTPException(400, f"识别失败: {e}")
    return {"items": items}


@app.get("/fridge/items")
def list_items():
    return {"items": [fridge.compute_item(it) for it in storage.list_items()]}


@app.get("/fridge/timeline")
def get_timeline():
    return fridge.timeline(storage.list_items())


@app.post("/fridge/items")
def add_item(item: ItemIn):
    data = item.model_dump()
    if not data.get("purchase_date"):
        data["purchase_date"] = date.today().isoformat()
    return storage.add_item(data)


@app.put("/fridge/items/{item_id}")
def update_item(item_id: str, upd: ItemUpdate):
    data = upd.model_dump(exclude_none=True)
    res = storage.update_item(item_id, data)
    if not res:
        raise HTTPException(404, "食材不存在")
    return res


@app.delete("/fridge/items/{item_id}")
def delete_item(item_id: str):
    if not storage.remove_item(item_id):
        raise HTTPException(404, "食材不存在")
    return {"ok": True}


@app.post("/fridge/items/{item_id}/consume")
def consume(item_id: str):
    if not storage.consume_item(item_id):
        raise HTTPException(404, "食材不存在")
    return {"ok": True}


@app.post("/recipe/generate")
def gen_recipe(req: RecipeIn):
    try:
        recipes = recipe.generate_recipes(req.ingredients, req.preference, req.count)
    except Exception as e:
        raise HTTPException(400, f"生成失败: {e}")
    return {"recipes": recipes}


@app.get("/stats")
def get_stats():
    return stats.get_stats()