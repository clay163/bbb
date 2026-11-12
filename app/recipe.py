import json
import re

from .llm import chat

PROMPT_TEMPLATE = """你是一名经验丰富的家常菜厨师助手，擅长用冰箱里的现有食材做出贴近日常生活的美味菜肴。

现有食材：
{ingredients}

用户偏好：{preference}

请生成 {count} 个菜谱，要求贴近中国家庭日常饮食，涵盖不同烹饪方式（炒菜、汤品、凉拌、蒸菜、一锅出、主食改造等），尽量丰富多样。

返回 JSON 数组，每个菜谱格式：
{{
  "name": "菜名（如：番茄炒蛋、青菜豆腐汤）",
  "description": "一句话介绍这道菜的特点和口感",
  "ingredients_used": ["从现有食材中用到的，如：鸡蛋2个、西红柿1个"],
  "seasoning": ["需要的调味料，如：盐、生抽、葱花"],
  "steps": ["详细步骤1", "步骤2", ...],
  "tips": "烹饪小贴士，如火候、调味技巧或替代方案",
  "time_min": 预计总分钟数,
  "difficulty": "简单/中等/较难",
  "extra_needed": ["需要额外购买的食材，尽量少"],
  "calories": "热量估算如 约400千卡",
  "servings": "适合几人份如 2人份",
  "tag": "菜谱标签，从以下选一个：快手菜/家常炒菜/营养汤品/凉拌小菜/主食改造/一锅出/清炒时蔬/创意剩菜"
}}

要求：
1. 只返回 JSON 数组，不要 markdown 代码块，不要解释
2. 优先用完现有食材，extra_needed 尽量为空或少
3. 尊重用户偏好（清淡/快手/热食/一人份等）
4. 剩菜剩饭优先改造利用（如剩米饭做炒饭、剩菜做汤面）
5. 步骤要具体可操作，包含火候、时间、调味量等细节
6. 菜谱之间要有差异性，不要都是同一类型
7. 贴近生活：用常见调味料，不需要特殊食材或厨具"""


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

MEAL_PLAN_PROMPT = """你是一名家庭营养师兼家常菜厨师。根据冰箱现有食材，安排今日三餐，贴近中国家庭日常饮食习惯。

现有食材：
{ingredients}

用户偏好：{preference}

返回 JSON 对象，格式：
{{
  "breakfast": {{ "name": "早餐名", "items": ["食物1","食物2"], "description": "简述", "time_min": 分钟数, "calories": "约xxx千卡" }},
  "lunch": {{ "name": "午餐名", "items": ["菜品1","菜品2"], "description": "简述", "time_min": 分钟数, "calories": "约xxx千卡" }},
  "dinner": {{ "name": "晚餐名", "items": ["菜品1","菜品2"], "description": "简述", "time_min": 分钟数, "calories": "约xxx千卡" }},
  "tips": "今日饮食搭配建议"
}}

要求：
1. 只返回 JSON，不要 markdown 代码块
2. 早餐简单快捷（粥/面/蛋/奶），午餐丰盛饱腹，晚餐清淡适量
3. 优先用完即将过期的食材
4. 三餐总热量合理（成人约1800-2200千卡/天）"""


def generate_meal_plan(ingredients: list[str], preference: str = "") -> dict:
    ing_text = "\n".join(f"- {g}" for g in ingredients) or "- 暂无食材"
    pref = preference.strip() or "无特殊要求"
    raw = chat(
        [{"role": "user", "content": MEAL_PLAN_PROMPT.format(
            ingredients=ing_text, preference=pref
        )}],
        temperature=0.8,
    )
    try:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            raw = m.group(1)
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            raw = m.group(0)
        return json.loads(raw)
    except Exception:
        return {"error": raw[:200]}