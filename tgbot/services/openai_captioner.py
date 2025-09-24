import base64
import json
import re
import os
import requests
from typing import Dict, Any, Optional
from ..config import OPENAI_API_KEY, DEFAULT_LANG

API_BASE = "https://api.openai.com/v1"

def _lang_prompt(lang: str) -> str:
    if (lang or "").lower() == "ru":
        return (
            "Сделай описание фотографии для фотостоков.\n"
            "- Напиши описание КРАТКО и ТОЛЬКО на русском языке (<=200 символов).\n"
            "- Не используй оценочных суждений.\n"
            "- Ключевые слова — на английском языке (8–14 существительных/кратких фраз, без #).\n"
            "- Хештеги — сгенерируй из keywords (#keyword).\n"
            "Верни ТОЛЬКО JSON с полями: title, description, keywords, hashtags."
        )
    return (
        "Create stock photo metadata.\n"
        "- Write a concise description in English (<=200 chars).\n"
        "- Keywords: 8–14 English nouns/short noun phrases (no #).\n"
        "- Hashtags: derive from keywords, prefixed with #.\n"
        "Return ONLY JSON with fields: title, description, keywords, hashtags."
    )


def _extract_json(text: str) -> Dict[str, Any]:
    # вырезаем JSON даже если модель обернула в кодовый блок
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError("Model did not return JSON")
    return json.loads(m.group(0))

def caption(image_bytes: bytes, lang: Optional[str] = None) -> Dict[str, Any]:
    """
    Возвращает словарь: { title, description, keywords[list[str]], hashtags[list[str]] }
    """
    lang = (lang or DEFAULT_LANG or "en").lower()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = _lang_prompt(lang)

    # готовим чат-запрос с vision через image_url data URI
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",  # доступная мультимодальная модель; при необходимости поменяй
        "messages": [
            {
                "role": "system",
                "content": "Output strictly valid JSON only. No code fences. No explanations.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            },
        ],
        "temperature": 0.2,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    text = data["choices"][0]["message"]["content"]
    result = _extract_json(text)

    # нормализация
    result.setdefault("title", "")

    # description ≤ 200
    desc = result.get("description", "")
    if isinstance(desc, str) and len(desc) > 200:
        result["description"] = desc[:197] + "…"

    # keywords 8–12
    kws = result.get("keywords", [])
    if isinstance(kws, list):
        result["keywords"] = [k.strip() for k in kws if isinstance(k, str) and k.strip()][:12]
    else:
        result["keywords"] = []

    # hashtags: если нет, генерим из keywords
    if not isinstance(result.get("hashtags"), list) or not result["hashtags"]:
        result["hashtags"] = [("#" + k.replace(" ", ""))[:30] for k in result["keywords"][:10]]
    else:
        clean = []
        for h in result["hashtags"]:
            if not isinstance(h, str):
                continue
            if not h.startswith("#"):
                h = "#" + h
            h = h.replace(" ", "")[:30]
            clean.append(h)
        result["hashtags"] = clean[:20]

    return result
