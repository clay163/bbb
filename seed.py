import sys
from pathlib import Path
sys.path.insert(0, ".")

Path("data/fridge.json").unlink(missing_ok=True)

from app import storage, fridge

items = [
    {"name": "青菜", "quantity": "少量", "storage": "冷藏", "opened": False, "purchase_date": "2026-10-02"},
    {"name": "牛奶", "quantity": "1盒", "storage": "冷藏", "opened": True, "purchase_date": "2026-09-25"},
    {"name": "酸奶", "quantity": "1杯", "storage": "冷藏", "opened": True, "purchase_date": "2026-09-20"},
    {"name": "鸡蛋", "quantity": "3个", "storage": "冷藏", "opened": False, "purchase_date": "2026-09-28"},
    {"name": "剩米饭", "quantity": "1碗", "storage": "冷藏", "opened": False, "purchase_date": "2026-10-03"},
    {"name": "胡萝卜", "quantity": "半根", "storage": "冷藏", "opened": False, "purchase_date": "2026-09-25"},
    {"name": "西红柿", "quantity": "2个", "storage": "冷藏", "opened": False, "purchase_date": "2026-10-04"},
]

for it in items:
    storage.add_item(it)

tl = fridge.timeline(storage.list_items())
print(f"食材 {len(storage.list_items())} 种, 分组 {len(tl['sections'])} 个")
for sec in tl["sections"]:
    names = [x["name"] for x in sec["items"]]
    print(f"  {sec['label']}: {', '.join(names)}")