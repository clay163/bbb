import base64
import json
import re
from pathlib import Path

from .llm import chat_vision

PROMPT = """识别图片中的所有食材，返回 JSON 数组。每个元素格式：
{"name": "食材名", "quantity": "数量或估计，如 3个/1碗/少量", "storage": "冷藏或冷冻或常温"}
要求：
1. 只返回 JSON 数组，不要 markdown 代码块，不要解释文字
2. 合并同类食材
3. 剩饭剩菜归为对应主食或熟食类
4. 数量不确定时用"少量""适量"等估计词"""


def encode_image(path_or_bytes) -> str:
    if isinstance(path_or_bytes, (str, Path)):
        return base64.b64encode(Path(path_or_bytes).read_bytes()).decode()
    return base64.b64encode(path_or_bytes).decode()


def _extract_json(text: str) -> list:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1)
    m = re.search(r"\[[\s\S]*\]", text)
    if m:
        text = m.group(0)
    return json.loads(text)


def recognize(image_base64: str) -> list[dict]:
    raw = chat_vision(image_base64, PROMPT)
    try:
        items = _extract_json(raw)
    except Exception:
        items = []
    result = []
    for it in items:
        if isinstance(it, dict) and it.get("name"):
            result.append({
                "name": it["name"],
                "quantity": it.get("quantity", "适量"),
                "storage": it.get("storage", "冷藏"),
                "opened": False,
            })
    return result