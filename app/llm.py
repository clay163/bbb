import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_api_key():
    key = os.getenv("LLM_API_KEY", "")
    if key and not key.startswith("your_"):
        return key
    try:
        import streamlit as st
        key = st.secrets.get("LLM_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return ""


def _get_config():
    return {
        "api_key": _get_api_key(),
        "base_url": os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
        "vision_model": os.getenv("LLM_VISION_MODEL", "glm-4v-plus"),
        "text_model": os.getenv("LLM_TEXT_MODEL", "glm-4-flash"),
    }


def get_client() -> OpenAI:
    global _client
    if _client is None:
        cfg = _get_config()
        _client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    return _client


def chat(messages: list[dict], model: str | None = None, temperature: float = 0.7) -> str:
    cfg = _get_config()
    resp = get_client().chat.completions.create(
        model=model or cfg["text_model"],
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content


def chat_vision(image_base64: str, prompt: str, temperature: float = 0.2) -> str:
    cfg = _get_config()
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        }
    ]
    resp = get_client().chat.completions.create(
        model=cfg["vision_model"],
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content