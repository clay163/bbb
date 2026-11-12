import os
import sys
import base64
from pathlib import Path
from datetime import date, datetime, timedelta

ROOT = Path(__file__).resolve().parent
if not (ROOT / "app").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import streamlit as st
import altair as alt
import pandas as pd

try:
    for key in ["LLM_API_KEY", "LLM_BASE_URL", "LLM_VISION_MODEL", "LLM_TEXT_MODEL"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass

from app import storage, fridge, vision, recipe, stats

st.set_page_config(
    page_title="AI 冰箱管家",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
:root {
    --mint: #5a9e8f; --mint-dark: #3d7a6c; --mint-bg: #e8f5f0;
    --warn: #e8a838; --warn-bg: #fdf3e0;
    --danger: #e85d5d; --danger-bg: #fce8e8;
    --paper: #f7f6f3;
}
.stApp { background: var(--paper); }
.stApp h1 { color: var(--mint-dark); font-weight: 700; margin-bottom: 0.5rem; }

/* 压缩全局垂直间距 */
.stVerticalBlock { gap: 0.3rem !important; }
.stElementContainer { margin-bottom: 0.2rem !important; }
[data-testid="stVerticalBlock"] > div { margin-top: 0 !important; }

/* Tab */
.stTabs > div[data-baseweb="tab-list"] { gap: 4px; }
.stTabs > div[data-baseweb="tab-list"] > div[data-baseweb="tab"] {
    padding: 6px 16px; border-radius: 8px; background: white; border: 1px solid #e0ddd8;
}
.stTabs > div[data-baseweb="tab-list"] > div[data-baseweb="tab"][aria-selected="true"] {
    background: var(--mint); color: white; border-color: var(--mint);
}

/* 按钮 */
.stButton > button[kind="primary"] {
    background: var(--mint); border-color: var(--mint); border-radius: 6px;
    color: white; font-weight: 600; padding: 4px 12px;
}
.stButton > button[kind="primary"]:hover {
    background: var(--mint-dark); border-color: var(--mint-dark);
}
.stButton > button { padding: 4px 10px; border-radius: 6px; }

/* Metric */
div.stMetric {
    background: white; border-radius: 8px; padding: 6px 10px;
    border: 1px solid #e8e6e2;
}

/* 状态标签 */
.tag-fresh { background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.tag-expiring { background: #fdf3e0; color: #8a5a10; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.tag-expired { background: #fce8e8; color: #8a2020; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.tag-freeze { background: #d4ecfc; color: #0c4a8a; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }

/* 食材卡片 */
.food-card {
    background: white; border: 1px solid #e8e6e2; border-radius: 10px;
    padding: 10px 14px; margin-bottom: 6px;
}
.food-card .emoji { font-size: 36px; vertical-align: middle; }
.food-card .name { font-size: 17px; font-weight: 700; vertical-align: middle; }
.food-card .meta { color: #888; font-size: 12px; margin-top: 2px; }
.food-card .days { font-size: 13px; margin-top: 2px; }

.empty-state { text-align: center; padding: 40px 20px; color: #999; }
.empty-state .icon { font-size: 56px; margin-bottom: 12px; }

/* 压缩 markdown 段落间距 */
.stMarkdown p { margin-bottom: 2px !important; line-height: 1.5; }
.stMarkdown h3 { margin-top: 4px !important; margin-bottom: 2px !important; }
.stMarkdown h5 { margin-top: 4px !important; margin-bottom: 2px !important; }

/* 压缩 container 内边距 */
div[data-testid="stVerticalBlockBorderWrapper"] {
    padding: 8px 12px !important; border-radius: 10px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.title("🧊 AI 冰箱管家 + 剩菜改造师")


STATUS_MAP = {
    "expired":      ("已过期",   "tag-expired",   "🔴"),
    "expiring":     ("即将过期", "tag-expiring",  "🟠"),
    "freeze_suggested": ("建议冷冻", "tag-freeze", "🔵"),
    "fresh":        ("正常",     "tag-fresh",     "🟢"),
}

FOOD_ICONS = {
    "鸡蛋": "🥚", "鸭蛋": "🥚", "鹌鹑蛋": "🥚",
    "牛奶": "🥛", "酸奶": "🥛", "奶酪": "🧀", "黄油": "🧈",
    "西红柿": "🍅", "番茄": "🍅",
    "胡萝卜": "🥕", "萝卜": "🥕", "白萝卜": "🥕",
    "青菜": "🥬", "白菜": "🥬", "菠菜": "🥬", "生菜": "🥬", "油菜": "🥬",
    "芹菜": "🥬", "韭菜": "🥬", "空心菜": "🥬", "西兰花": "🥦", "花菜": "🥦",
    "米饭": "🍚", "剩米饭": "🍚", "粥": "🍚", "米": "🍚",
    "面包": "🍞", "馒头": "🍞", "吐司": "🍞",
    "面条": "🍜", "挂面": "🍜", "意面": "🍝", "米粉": "🍜",
    "鸡肉": "🍗", "鸡腿": "🍗", "鸡翅": "🍗", "鸡": "🍗",
    "猪肉": "🥓", "排骨": "🍖", "火腿": "🍖", "培根": "🥓",
    "牛肉": "🥩", "牛排": "🥩",
    "鱼": "🐟", "三文鱼": "🐟", "带鱼": "🐟", "鲈鱼": "🐟",
    "虾": "🦐", "大虾": "🦐", "基围虾": "🦐",
    "蟹": "🦀", "螃蟹": "🦀",
    "豆腐": "🧈", "豆干": "🧈", "腐竹": "🧈",
    "土豆": "🥔", "马铃薯": "🥔",
    "洋葱": "🧅", "大蒜": "🧄", "蒜": "🧄", "姜": "🫚",
    "玉米": "🌽", "青椒": "🫑", "辣椒": "🌶️", "彩椒": "🫑",
    "黄瓜": "🥒", "冬瓜": "🥒", "南瓜": "🎃", "丝瓜": "🥒",
    "茄子": "🍆", "蘑菇": "🍄", "香菇": "🍄", "金针菇": "🍄",
    "苹果": "🍎", "香蕉": "🍌", "柠檬": "🍋", "橙子": "🍊",
    "草莓": "🍓", "葡萄": "🍇", "西瓜": "🍉", "梨": "🍐", "桃": "🍑",
    "芒果": "🥭", "菠萝": "🍍", "猕猴桃": "🥝", "樱桃": "🍒",
    "饺子": "🥟", "包子": "🥟", "馄饨": "🥟",
    "月饼": "🥮", "蛋糕": "🍰", "饼干": "🍪",
    "坚果": "🥜", "花生": "🥜", "核桃": "🥜", "杏仁": "🥜",
    "蜂蜜": "🍯", "巧克力": "🍫", "糖果": "🍬",
    "可乐": "🥤", "果汁": "🧃", "茶": "🍵", "咖啡": "☕",
    "剩菜": "🍲", "剩饭": "🍚", "汤": "🍲",
}

CATEGORY_ICONS = {
    "叶菜类": "🥬", "根茎类": "🥕", "瓜果类": "🥒", "蛋奶类": "🥚",
    "肉类": "🥩", "水产类": "🐟", "主食类": "🍚", "熟食类": "🍲",
    "干货类": "🥜", "水果类": "🍎", "其他": "🍽️",
}


def get_food_icon(name: str, category: str = "") -> str:
    for key, emoji in FOOD_ICONS.items():
        if key in name:
            return emoji
    return CATEGORY_ICONS.get(category, "🍽️")
STATUS_FILTER_LIST = ["全部", "正常", "即将过期", "已过期", "建议冷冻"]
STORAGE_FILTER_LIST = ["全部", "冷藏", "冷冻", "常温"]
CATEGORY_LIST = ["全部", "叶菜类", "根茎类", "瓜果类", "蛋奶类", "肉类", "水产类", "主食类", "熟食类", "干货类", "水果类", "其他"]

tab_photo, tab_fridge, tab_cook, tab_stats = st.tabs(
    ["📷 拍照识别", "🧊 冰箱管理", "🍳 今天吃什么", "📊 浪费统计"]
)

# ============================================================
# Tab 1: 拍照识别
# ============================================================
with tab_photo:
    st.subheader("上传冰箱 / 餐桌 / 购物袋照片，AI 自动识别食材")

    upload_col, cam_col = st.columns(2)
    with upload_col:
        st.markdown("##### 📁 上传图片文件")
        uploaded = st.file_uploader(
            "拖拽图片到此处或点击选择",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            key="photo_upload",
            help="支持 JPG / PNG / WebP 格式",
        )
    with cam_col:
        st.markdown("##### 📷 拍照（需摄像头）")
        camera_img = st.camera_input("点击开启摄像头拍照", key="camera")

    img_bytes = None
    img_source = ""
    if uploaded is not None:
        img_bytes = uploaded.getvalue()
        img_source = "上传"
    elif camera_img is not None:
        img_bytes = camera_img.getvalue()
        img_source = "拍照"

    if img_bytes:
        st.markdown("---")
        preview_col, action_col = st.columns([1, 2])
        with preview_col:
            st.image(img_bytes, caption=f"📷 {img_source}的图片", width="stretch")
        with action_col:
            st.markdown("##### 确认后点击识别")
            if st.button("🔍 开始 AI 识别", type="primary", width="stretch"):
                with st.spinner("AI 正在识别食材…"):
                    try:
                        b64 = base64.b64encode(img_bytes).decode()
                        items = vision.recognize(b64)
                        if items:
                            st.session_state["recognized"] = items
                            st.session_state["recognize_ok"] = True
                        else:
                            st.session_state["recognize_ok"] = False
                            st.error("⚠️ 未识别到食材，请尝试换一张更清晰的照片")
                    except Exception as e:
                        st.session_state["recognize_ok"] = False
                        err_msg = str(e)
                        if "api_key" in err_msg.lower() or "401" in err_msg:
                            st.error("❌ API Key 无效，请检查 .env 或 Streamlit Secrets 配置")
                        elif "model" in err_msg.lower() or "404" in err_msg:
                            st.error(f"❌ 模型不可用: {err_msg[:200]}")
                        elif "timeout" in err_msg.lower():
                            st.error("❌ 请求超时，请重试")
                        elif "connection" in err_msg.lower():
                            st.error("❌ 网络连接失败，请检查网络后重试")
                        else:
                            st.error(f"❌ 识别失败: {err_msg[:300]}")

            if st.session_state.get("recognize_ok"):
                items = st.session_state.get("recognized", [])
                if items:
                    st.success(f"✅ 识别到 **{len(items)}** 种食材，请确认后加入冰箱：")
                    edited = []
                    for i, it in enumerate(items):
                        with st.container(border=True):
                            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                            name = c1.text_input("食材名称", it["name"], key=f"n{i}")
                            qty = c2.text_input("数量", it.get("quantity", "适量"), key=f"q{i}")
                            stor = c3.selectbox(
                                "存放", ["冷藏", "冷冻", "常温"],
                                index=["冷藏", "冷冻", "常温"].index(it.get("storage", "冷藏")),
                                key=f"s{i}",
                            )
                            opened = c4.checkbox("已开封", it.get("opened", False), key=f"o{i}")
                            edited.append({"name": name, "quantity": qty, "storage": stor, "opened": opened})

                    if st.button("✅ 全部加入冰箱", type="primary", width="stretch"):
                        ok = 0
                        for it in edited:
                            if it["name"].strip():
                                storage.add_item(it)
                                ok += 1
                        st.success(f"🎉 已加入 {ok} 种食材 → 前往「冰箱管理」查看")
                        st.session_state["recognized"] = []
                        st.session_state["recognize_ok"] = False
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">🧊</div>
            <p>上传一张冰箱照片，AI 帮你自动识别食材</p>
            <p style="font-size:13px;color:#bbb;">支持 JPG / PNG / WebP · 也可用摄像头拍照</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# Tab 2: 冰箱管理
# ============================================================
with tab_fridge:
    all_raw = storage.list_items()
    all_items = [fridge.compute_item(it) for it in all_raw] if all_raw else []

    # ---- 添加食材（顶部展开式表单）----
    with st.expander("➕ 添加食材", expanded=(len(all_items) == 0)):
        with st.form("add_form"):
            ac1, ac2, ac3, ac4, ac5 = st.columns([2, 1, 1, 1, 1])
            n = ac1.text_input("食材名称", placeholder="如：鸡蛋")
            q = ac2.text_input("数量", "适量")
            s = ac3.selectbox("存放位置", ["冷藏", "冷冻", "常温"])
            op = ac4.checkbox("已开封")
            purchase_date = ac5.date_input("购买日期", value=date.today())
            if st.form_submit_button("✅ 添加到冰箱", type="primary", width="stretch"):
                if n.strip():
                    storage.add_item({
                        "name": n.strip(), "quantity": q, "storage": s,
                        "opened": op, "purchase_date": purchase_date.isoformat()
                    })
                    st.rerun()
                else:
                    st.error("请输入食材名称")


    if all_items:
        # ---- 筛选器 + 排序 ----
        fc1, fc2, fc3, fc4 = st.columns(4)
        sf = fc1.selectbox("🔍 状态", STATUS_FILTER_LIST, key="status_filter")
        storf = fc2.selectbox("📦 存储", STORAGE_FILTER_LIST, key="storage_filter")
        catf = fc3.selectbox("🏷️ 分类", CATEGORY_LIST, key="category_filter")
        sortf = fc4.selectbox("↕️ 排序", ["剩余天数↑", "剩余天数↓", "热量↓", "名称"], key="sort_filter")

        filtered = all_items
        if sf != "全部":
            smap = {"正常": "fresh", "即将过期": "expiring", "已过期": "expired", "建议冷冻": "freeze_suggested"}
            filtered = [it for it in filtered if it["status"] == smap[sf]]
        if storf != "全部":
            filtered = [it for it in filtered if it["storage"] == storf]
        if catf != "全部":
            filtered = [it for it in filtered if it.get("category") == catf]

        if sortf == "剩余天数↑":
            filtered = sorted(filtered, key=lambda x: x["days_left"])
        elif sortf == "剩余天数↓":
            filtered = sorted(filtered, key=lambda x: -x["days_left"])
        elif sortf == "热量↓":
            filtered = sorted(filtered, key=lambda x: -x.get("calories", 0))
        elif sortf == "名称":
            filtered = sorted(filtered, key=lambda x: x["name"])

        st.markdown(f"##### 📋 食材列表（{len(filtered)} / {len(all_items)}）")

        if filtered:
            # ---- 3列卡片网格 ----
            grid = st.columns(3)
            for idx, it in enumerate(filtered):
                col = grid[idx % 3]
                with col:
                    label, tag_cls, icon = STATUS_MAP.get(
                        it["status"], ("未知", "tag-fresh", "❓")
                    )
                    food_emoji = get_food_icon(it["name"], it.get("category", ""))
                    dl = it["days_left"]
                    if dl < 0:
                        days_html = f"<span style='color:#e85d5d;font-weight:600'>⛔ 已过期 {-dl} 天</span>"
                    elif dl <= 1:
                        days_html = f"<span style='color:#e8a838;font-weight:600'>⚠️ 仅剩 {dl} 天</span>"
                    else:
                        days_html = f"<span style='color:#5a9e8f;font-weight:600'>✅ 剩余 {dl} 天</span>"
                    tip_html = f"<div style='color:#aaa;font-size:11px;margin-top:2px'>💡 {it['tip']}</div>" if it.get("tip") else ""
                    cal = it.get("calories", 0)
                    with st.container(border=True):
                        st.markdown(
                            f"<div class='food-card'>"
                            f"<span class='emoji'>{food_emoji}</span>&nbsp;"
                            f"<span class='name'>{it['name']}</span>&nbsp;"
                            f"<span class='{tag_cls}'>{label}</span>&nbsp;"
                            f"<span style='font-size:12px;color:#e8a838;font-weight:600'>🔥{cal}kcal</span>"
                            f"<div class='meta'>{it['quantity']} · {it.get('category','')} · 📦{it['storage']}</div>"
                            f"<div class='days'>{days_html} · 到期 {it['expire_date']}</div>"
                            f"{tip_html}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        b1, b2 = st.columns(2)
                        if b1.button("✅ 消耗", key=f"c{it['id']}", width="stretch"):
                            storage.consume_item(it["id"])
                            st.rerun()
                        if b2.button("🗑️ 删除", key=f"d{it['id']}", width="stretch"):
                            storage.remove_item(it["id"])
                            st.rerun()
        else:
            st.info("🔍 没有符合筛选条件的食材")
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">🧊</div>
            <p>冰箱空空如也～</p>
            <p style="font-size:14px;color:#aaa;">点击上方「➕ 添加食材」或去「拍照识别」添加吧</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# Tab 3: 今天吃什么
# ============================================================
with tab_cook:
    cook_sub1, cook_sub2, cook_sub3 = st.tabs(["🍳 生成菜谱", "📅 每日三餐", "⭐ 我的收藏"])
    all_items = [fridge.compute_item(it) for it in storage.list_items()]
    names = [it["name"] for it in all_items]

    with cook_sub1:
        if names:
            icon_line = "  ".join(
                f"{get_food_icon(n, fridge.match_category(n))} {n}" for n in names
            )
            st.markdown(f"##### 当前可用食材\n{icon_line}")
            chosen = st.multiselect("选择用于做菜的食材", names, default=names, key="cook_select")

            pref_col, cnt_col = st.columns([3, 1])
            with pref_col:
                pref = st.text_input("口味偏好", placeholder="如：清淡 / 快手10分钟 / 热食 / 一人份", key="pref")
            with cnt_col:
                cnt = st.slider("菜谱数量", 1, 6, 3, key="cnt")

            if st.button("🍳 生成菜谱", type="primary", width="stretch") and chosen:
                with st.spinner("AI 正在想做什么菜…"):
                    try:
                        recipes = recipe.generate_recipes(chosen, pref, cnt)
                    except Exception as e:
                        recipes = []
                        st.error(f"生成失败: {e}")

                if recipes:
                    all_extra = []
                    for r in recipes:
                        all_extra.extend(r.get("extra_needed", []))
                    if all_extra:
                        unique_extra = list(dict.fromkeys(all_extra))
                        with st.container(border=True):
                            st.markdown(f"##### 🛒 购物清单（共{len(unique_extra)}项）")
                            for item in unique_extra:
                                st.markdown(f"- ☐ {item}")

                    st.markdown(f"##### 🍽️ 为你推荐 {len(recipes)} 个菜谱")
                    for r in recipes:
                        rname = r.get("name", "未知菜名")
                        r_emoji = "🍽️"
                        for key, emoji in FOOD_ICONS.items():
                            if key in rname:
                                r_emoji = emoji
                                break
                        desc = r.get("description", "")
                        tag = r.get("tag", "")
                        tag_html = f"<span style='background:#e8f5f0;color:#3d7a6c;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600'>{tag}</span>" if tag else ""
                        with st.container(border=True):
                            st.markdown(
                                f"<span style='font-size:32px;line-height:1'>{r_emoji}</span>"
                                f" &nbsp; <span style='font-size:19px;font-weight:700;vertical-align:middle'>{rname}</span>"
                                f" &nbsp; {tag_html}"
                                f"<div style='color:#888;font-size:12px;margin-top:2px'>{desc}</div>",
                                unsafe_allow_html=True,
                            )

                            mc1, mc2, mc3, mc4 = st.columns(4)
                            mc1.metric("⏱️ 用时", f"{r.get('time_min', '?')}分")
                            mc2.metric("📊 难度", r.get("difficulty", "-"))
                            mc3.metric("🔥 热量", r.get("calories", "-"))
                            mc4.metric("📏 份量", r.get("servings", "-"))

                            used = r.get("ingredients_used", [])
                            if used:
                                st.markdown(f"**🥘 用料：** {'、'.join(used)}")
                            seasoning = r.get("seasoning", [])
                            if seasoning:
                                st.caption(f"🧂 调味：{'、'.join(seasoning)}")

                            extra = r.get("extra_needed", [])
                            if extra:
                                st.warning(f"🛒 还需购买：{'、'.join(extra)}")
                            else:
                                st.success("✅ 现有食材即可完成！")

                            steps = r.get("steps", [])
                            if steps:
                                steps_html = "<br>".join(f"**{j}.** {s}" for j, s in enumerate(steps, 1))
                                st.markdown(f"**📝 做法：**<br>{steps_html}", unsafe_allow_html=True)

                            tips = r.get("tips", "")
                            if tips:
                                st.caption(f"💡 {tips}")

                            bc1, bc2 = st.columns(2)
                            is_fav = storage.is_favorite(rname)
                            if bc1.button("⭐ 收藏" if not is_fav else "⭐ 已收藏", key=f"fav{rname}", width="stretch"):
                                if not is_fav:
                                    storage.add_favorite(r)
                                else:
                                    storage.remove_favorite(rname)
                                st.rerun()
                            if bc2.button("✅ 标记做过", key=f"cooked{rname}", width="stretch"):
                                storage.add_history(r)
                                st.success(f"已记录「{rname}」到做菜历史")
                else:
                    st.error("未能生成菜谱，请重试")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="icon">🍳</div>
                <p>冰箱里还没有食材</p>
                <p style="font-size:14px;color:#aaa;">先去添加食材，再来生成菜谱吧</p>
            </div>
            """, unsafe_allow_html=True)

    with cook_sub2:
        st.markdown("##### 📅 根据冰箱食材安排今日三餐")
        if names:
            st.markdown(f"当前食材：{'、'.join(names)}")
            meal_pref = st.text_input("饮食偏好", placeholder="如：清淡 / 减脂 / 家常 / 一人份", key="meal_pref")
            if st.button("📅 生成今日三餐", type="primary", width="stretch"):
                with st.spinner("AI 正在安排三餐…"):
                    plan = recipe.generate_meal_plan(names, meal_pref)
                if "error" in plan:
                    st.error(f"生成失败: {plan['error'][:200]}")
                else:
                    meals = [("🌅 早餐", "breakfast"), ("☀️ 午餐", "lunch"), ("🌙 晚餐", "dinner")]
                    for label, key in meals:
                        m = plan.get(key, {})
                        with st.container(border=True):
                            st.markdown(f"#### {label}：{m.get('name', '')}")
                            st.caption(m.get("description", ""))
                            items = m.get("items", [])
                            if items:
                                st.markdown(f"📋 {'、'.join(items)}")
                            mc1, mc2 = st.columns(2)
                            mc1.metric("⏱️ 用时", f"{m.get('time_min', '?')}分")
                            mc2.metric("🔥 热量", m.get("calories", "-"))
                    tips = plan.get("tips", "")
                    if tips:
                        st.info(f"💡 {tips}")
        else:
            st.info("冰箱里还没有食材，先去添加吧")

    with cook_sub3:
        favs = storage.list_favorites()
        history = storage.list_history()
        fc1, fc2 = st.columns([1, 1])
        with fc1:
            st.markdown(f"##### ⭐ 收藏菜谱（{len(favs)}）")
            if favs:
                for f in reversed(favs):
                    with st.container(border=True):
                        fname = f.get("name", "")
                        st.markdown(f"**{fname}**　{f.get('tag', '')}")
                        st.caption(f.get("description", ""))
                        if st.button("🗑️ 取消收藏", key=f"rmfav{fname}", width="stretch"):
                            storage.remove_favorite(fname)
                            st.rerun()
            else:
                st.caption("还没有收藏的菜谱")

        with fc2:
            st.markdown(f"##### 📖 做菜历史（{len(history)}）")
            if history:
                for h in reversed(history[-10:]):
                    d = h.get("cooked_at", "")[:10]
                    st.markdown(f"- **{h.get('name', '')}**　{d}")
            else:
                st.caption("还没有做菜记录")

# ============================================================
# Tab 4: 浪费统计
# ============================================================
with tab_stats:
    st.subheader("📊 本周浪费统计与环保反馈")
    s = stats.get_stats()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🗑️ 本周过期", f"{s['week_expired_count']} 份")
    m2.metric("✅ 成功消耗", f"{s['week_consumed_count']} 份")
    m3.metric("💸 预估浪费", f"¥{s['waste_cost']}")
    m4.metric("💰 预估节约", f"¥{s['saved_cost']}")

    m5, m6, m7 = st.columns(3)
    m5.metric("📅 连续节约", f"{s['saving_streak_days']} 天")
    m6.metric("🧊 冰箱现存", f"{s['total_in_fridge']} 份")
    carbon = round(s['week_consumed_count'] * 0.8, 1)
    m7.metric("🌱 减少碳排放", f"{carbon} kgCO₂")

    # ---- 图表 ----
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("##### 📈 近7天消耗/过期趋势")
        consumed_list = storage.get_consumed()
        expired_list = storage.get_expired_log()
        today = date.today()
        dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        chart_data = []
        for d in dates:
            dstr = d.isoformat()
            consumed_count = sum(1 for c in consumed_list if c.get("consumed_at", "")[:10] == dstr)
            expired_count = sum(1 for e in expired_list if e.get("expired_at", "")[:10] == dstr)
            chart_data.append({"日期": d.strftime("%m-%d"), "消耗": consumed_count, "过期": expired_count})
        df = pd.DataFrame(chart_data)
        df_melted = df.melt("日期", var_name="类型", value_name="数量")
        chart = alt.Chart(df_melted).mark_bar().encode(
            x=alt.X("日期:N", axis=alt.Axis(title="")),
            y=alt.Y("数量:Q", axis=alt.Axis(title="份数")),
            color=alt.Color("类型:N", scale=alt.Scale(range=["#5a9e8f", "#e85d5d"])),
            column=alt.Column("类型:N", title=None),
        ).properties(height=200)
        st.altair_chart(chart, width="stretch")

    with chart_col2:
        st.markdown("##### 🥧 冰箱食材分类分布")
        all_fridge = [fridge.compute_item(it) for it in storage.list_items()]
        if all_fridge:
            cat_counts = {}
            for it in all_fridge:
                cat = it.get("category", "其他")
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
            cat_data = [{"分类": k, "数量": v} for k, v in cat_counts.items()]
            cat_df = pd.DataFrame(cat_data)
            pie = alt.Chart(cat_df).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("数量:Q", stack=True),
                color=alt.Color("分类:N", legend=alt.Legend(title="分类", orient="right")),
                tooltip=["分类", "数量"],
            ).properties(height=200)
            st.altair_chart(pie, width="stretch")
        else:
            st.caption("冰箱空空如也")

    st.markdown("---")

    if s["week_expired_count"] == 0 and s["week_consumed_count"] > 0:
        st.balloons()
        st.success("🎉 本周零浪费，干得漂亮！")
    elif s["week_expired_count"] > 0:
        st.warning(f"⚠️ 本周有 {s['week_expired_count']} 份食材过期，注意及时消耗")
    else:
        st.info("💡 开始记录消耗和过期情况，统计会更丰富")

    if consumed_list:
        st.markdown("##### 📋 近期消耗记录")
        for it in consumed_list[-5:]:
            d = it.get("consumed_at", "")[:10]
            st.markdown(f"- **{it['name']}** {it.get('quantity', '')}　消耗于 {d}")