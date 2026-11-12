import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import streamlit as st

for key in ["LLM_API_KEY", "LLM_BASE_URL", "LLM_VISION_MODEL", "LLM_TEXT_MODEL"]:
    try:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
    except Exception:
        pass

os.environ.setdefault("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
os.environ.setdefault("LLM_VISION_MODEL", "glm-4v-plus")
os.environ.setdefault("LLM_TEXT_MODEL", "glm-4-flash")

app_file = ROOT / "frontend" / "app.py"
exec(compile(app_file.read_text(encoding="utf-8"), str(app_file), "exec"),
     {"__file__": str(app_file), "__name__": "__main__"})