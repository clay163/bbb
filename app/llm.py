import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("LLM_API_KEY", "")
BASE_URL = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
VISION_MODEL = os.getenv("LLM_VISION_MODEL", "glm-4v")
TEXT_MODEL = os.getenv("LLM_TEXT_MODEL", "glm-4-flash")

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    return _client


def chat(messages: list[dict], model: str | None = None, temperature: float = 0.7) -> str:
    resp = get_client().chat.completions.create(
        model=model or TEXT_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content


def chat_vision(image_base64: str, prompt: str, temperature: float = 0.2) -> str:
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
        model=VISION_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content