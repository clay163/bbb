import json
import re

from .llm import chat

PROMPT_TEMPLATE = """你是一名家常菜厨师助手。根据用户冰箱里的现有食材生成 {count} 个菜谱。

现有食材：
{ingredients}

用户偏好：{preference}

返回 JSON 数组，每个菜谱格式：
{{
  "name": "菜名",
  "description": "一句话介绍",
  "steps": ["步骤1", "步骤2", ...],
  "time_min": 预计分钟数,
  "difficulty": "简单/中等/较难",
  "extra_needed": ["需要额外购买的食材"],
  "calories": "热量估算如 约400千卡",
  "servings": "适合几人份如 1人份"
}}

要求：
1. 只返回 JSON 数组，不要 markdown 代码块，不要解释
2. 优先用完现有食材，extra_needed 尽量少
3. 尊重用户偏好（清淡/快手/热食等）
4. 剩菜剩饭优先改造利用"""


def _extract_json(text: str) -> list:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1)
    m = re.search(r"\[[\s\S]*\]", text)
    if m:
        text = m.group(0)
    return json.loads(text)


def generate_recipes(ingredients: list[str], preference: str = "", count: int = 3) -> list[dict]:
    ing_text = "\n".join(f"- {g}" for g in ingredients) or "- 暂无食材"
    pref = preference.strip() or "无特殊要求"
    raw = chat(
        [{"role": "user", "content": PROMPT_TEMPLATE.format(
            count=count, ingredients=ing_text, preference=pref
        )}],
        temperature=0.8,
    )
    try:
        recipes = _extract_json(raw)
    except Exception:
        return [{"name": "生成失败", "description": raw[:200], "steps": [], "time_min": 0,
                 "difficulty": "-", "extra_needed": [], "calories": "-", "servings": "-"}]
    return recipes