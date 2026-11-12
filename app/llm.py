import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


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


def _get_base_url():
    return os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")


def _get_vision_model():
    return os.getenv("LLM_VISION_MODEL", "glm-4v-plus")


def _get_text_model():
    return os.getenv("LLM_TEXT_MODEL", "glm-4-flash")


def chat(messages: list[dict], model: str | None = None, temperature: float = 0.7) -> str:
    client = OpenAI(api_key=_get_api_key(), base_url=_get_base_url())
    resp = client.chat.completions.create(
        model=model or _get_text_model(),
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content


def chat_vision(image_base64: str, prompt: str, temperature: float = 0.2) -> str:
    client = OpenAI(api_key=_get_api_key(), base_url=_get_base_url())
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        }
    ]
    resp = client.chat.completions.create(
        model=_get_vision_model(),
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content