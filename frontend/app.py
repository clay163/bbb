import os
import sys
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if not (ROOT / "app").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import streamlit as st

try:
    for key in ["LLM_API_KEY", "LLM_BASE_URL", "LLM_VISION_MODEL", "LLM_TEXT_MODEL"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass

from app import storage, fridge, vision, recipe, stats

st.set_page_config(page_title="AI 冰箱管家", page_icon="🧊", layout="wide")
st.title("🧊 AI 冰箱管家 + 剩菜改造师")

if not os.getenv("LLM_API_KEY") or os.getenv("LLM_API_KEY", "").startswith("your_"):
    st.warning("⚠️ 未检测到大模型 API Key，请在 .env 文件或 Streamlit secrets 中配置 LLM_API_KEY。拍照识别和菜谱生成将不可用。")

STATUS_STYLE = {
    "expired": ("🔴 已过期", "#ffcccc"),
    "expiring": ("🟠 即将过期", "#ffe0b2"),
    "freeze_suggested": ("🔵 建议冷冻", "#bbdefb"),
    "fresh": ("🟢 仍可存放", "#c8e6c9"),
}

tab_photo, tab_fridge, tab_cook, tab_stats = st.tabs(
    ["📷 拍照识别", "🧊 冰箱管理", "🍳 今天吃什么", "📊 浪费统计"]
)

with tab_photo:
    st.subheader("上传冰箱 / 餐桌 / 购物袋照片，AI 自动识别食材")
    uploaded = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"], key="photo")
    col1, col2 = st.columns([1, 2])
    if uploaded:
        img_bytes = uploaded.getvalue()
        col1.image(img_bytes, caption="已上传", use_container_width=True)
        if col2.button("🔍 开始识别", type="primary"):
            with st.spinner("AI 识别中…"):
                try:
                    b64 = base64.b64encode(img_bytes).decode()
                    items = vision.recognize(b64)
                    if items:
                        st.session_state["recognized"] = items
                    else:
                        col2.error("未识别到食材，请换一张照片")
                except Exception as e:
                    col2.error(f"识别失败: {e}")
        items = st.session_state.get("recognized", [])
        if items:
            col2.success(f"识别到 {len(items)} 种食材，请确认后加入冰箱：")
            edited = []
            for i, it in enumerate(items):
                c1, c2, c3, c4 = col2.columns([3, 2, 2, 1])
                name = c1.text_input("食材", it["name"], key=f"n{i}")
                qty = c2.text_input("数量", it.get("quantity", "适量"), key=f"q{i}")
                stor = c3.selectbox("存放", ["冷藏", "冷冻", "常温"],
                                    index=["冷藏", "冷冻", "常温"].index(it.get("storage", "冷藏")), key=f"s{i}")
                opened = c4.checkbox("已开封", it.get("opened", False), key=f"o{i}")
                edited.append({"name": name, "quantity": qty, "storage": stor, "opened": opened})
            if col2.button("✅ 全部加入冰箱", type="primary"):
                ok = 0
                for it in edited:
                    if it["name"]:
                        storage.add_item(it)
                        ok += 1
                col2.success(f"已加入 {ok} 种食材 → 前往「冰箱管理」查看")
                st.session_state["recognized"] = []
        elif uploaded and not st.session_state.get("recognized"):
            col2.info("点击「开始识别」")

with tab_fridge:
    c_left, c_right = st.columns([3, 2])
    with c_right:
        st.subheader("➕ 手动添加食材")
        with st.form("add_form"):
            n = st.text_input("食材名称")
            q = st.text_input("数量", "适量")
            s = st.selectbox("存放位置", ["冷藏", "冷冻", "常温"])
            op = st.checkbox("已开封")
            pd = st.date_input("购买日期")
            if st.form_submit_button("添加") and n:
                storage.add_item({
                    "name": n, "quantity": q, "storage": s,
                    "opened": op, "purchase_date": pd.isoformat()
                })
                st.rerun()

    with c_left:
        st.subheader("食材时间线")
        tl = fridge.timeline(storage.list_items())
        if tl.get("sections"):
            for sec in tl["sections"]:
                label, _ = STATUS_STYLE.get(sec["key"], (sec["label"], "#eeeeee"))
                st.markdown(f"### {label}")
                for it in sec["items"]:
                    with st.container(border=True):
                        mc, bc = st.columns([4, 2])
                        mc.markdown(
                            f"**{it['name']}**　{it['quantity']}　"
                            f"`{it.get('category','')}`　存放:{it['storage']}　"
                            f"剩余 **{it['days_left']}** 天　到期 {it['expire_date']}"
                        )
                        if it.get("tip"):
                            mc.caption(f"💡 {it['tip']}")
                        b1, b2 = bc.columns(2)
                        if b1.button("✅ 消耗", key=f"c{it['id']}"):
                            storage.consume_item(it["id"])
                            st.rerun()
                        if b2.button("🗑️ 删除", key=f"d{it['id']}"):
                            storage.remove_item(it["id"])
                            st.rerun()
        else:
            st.info("冰箱空空如也，去「拍照识别」添加食材吧")

with tab_cook:
    st.subheader("根据冰箱现有食材，AI 生成菜谱")
    all_items = [fridge.compute_item(it) for it in storage.list_items()]
    names = [it["name"] for it in all_items]
    if names:
        st.markdown("当前食材：" + "、".join(names))
        chosen = st.multiselect("选择用于做菜的食材", names, default=names)
    else:
        st.warning("冰箱里还没有食材，先去添加吧")
        chosen = []
    pref = st.text_input("偏好（如：清淡 / 快手10分钟 / 热食 / 一人份）", "")
    cnt = st.slider("推荐菜谱数量", 1, 5, 3)
    if st.button("🍳 生成菜谱", type="primary") and chosen:
        with st.spinner("AI 正在想做什么菜…"):
            try:
                recipes = recipe.generate_recipes(chosen, pref, cnt)
            except Exception as e:
                recipes = []
                st.error(f"生成失败: {e}")
        if recipes:
            for r in recipes:
                with st.container(border=True):
                    st.markdown(f"### 🍽️ {r.get('name','')}")
                    st.caption(r.get("description", ""))
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("用时", f"{r.get('time_min','?')} 分钟")
                    c2.metric("难度", r.get("difficulty", "-"))
                    c3.metric("热量", r.get("calories", "-"))
                    c4.metric("份量", r.get("servings", "-"))
                    extra = r.get("extra_needed", [])
                    if extra:
                        st.warning("还需购买：" + "、".join(extra))
                    else:
                        st.success("现有食材即可完成 ✅")
                    st.markdown("**做法：**")
                    for j, step in enumerate(r.get("steps", []), 1):
                        st.markdown(f"{j}. {step}")

with tab_stats:
    st.subheader("本周浪费统计与环保反馈")
    s = stats.get_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("本周过期食材", f"{s['week_expired_count']} 份")
    c2.metric("成功消耗", f"{s['week_consumed_count']} 份")
    c3.metric("预估浪费金额", f"¥{s['waste_cost']}")
    c4.metric("预估节约金额", f"¥{s['saved_cost']}")
    c5, c6, c7 = st.columns(3)
    c5.metric("连续节约天数", f"{s['saving_streak_days']} 天")
    c6.metric("冰箱现存食材", f"{s['total_in_fridge']} 份")
    carbon = round(s['week_consumed_count'] * 0.8, 1)
    c7.metric("预估减少碳排放", f"{carbon} kgCO₂")
    if s["week_expired_count"] == 0 and s["week_consumed_count"] > 0:
        st.balloons()
        st.success("本周零浪费，干得漂亮！🎉")