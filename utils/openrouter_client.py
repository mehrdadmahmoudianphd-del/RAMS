# -*- coding: utf-8 -*-
"""
کلاینت OpenRouter برای سامانه RAMS
کلید از .env یا Streamlit secrets خوانده می‌شود — هرگز در کد hardcode نشود.
"""

from __future__ import annotations

import os
import json
from typing import Optional, List, Dict, Any

try:
    from dotenv import load_dotenv
    # مسیر .env کنار ریشه پروژه
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_dotenv(os.path.join(_root, ".env"))
except ImportError:
    pass

import requests


def _get_api_key() -> Optional[str]:
    # اولویت: متغیر محیطی سیستم → .env → Streamlit secrets
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st
        key = st.secrets.get("OPENROUTER_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return None


def _get_model() -> str:
    model = os.environ.get("OPENROUTER_MODEL", "").strip()
    if model:
        return model
    try:
        import streamlit as st
        m = st.secrets.get("OPENROUTER_MODEL", "")
        if m:
            return str(m).strip()
    except Exception:
        pass
    return "openai/gpt-4o-mini"


def _get_base_url() -> str:
    return os.environ.get(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    ).rstrip("/")


def is_configured() -> bool:
    return bool(_get_api_key())


def chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1200,
) -> str:
    """
    ارسال پیام به OpenRouter و دریافت پاسخ متنی.
    در صورت خطا، پیام قابل‌نمایش برای کاربر برمی‌گرداند.
    """
    api_key = _get_api_key()
    if not api_key:
        return (
            "⚠️ کلید OpenRouter تنظیم نشده است.\n\n"
            "فایل `.env` را در ریشه پروژه با این محتوا بسازید:\n"
            "OPENROUTER_API_KEY=sk-or-v1-...\n"
        )

    url = f"{_get_base_url()}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://rams.local",
        "X-Title": "RAMS Power Distribution",
    }
    payload: Dict[str, Any] = {
        "model": model or _get_model(),
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 401:
            return "❌ احراز هویت ناموفق — کلید API نامعتبر است یا منقضی شده."
        if resp.status_code == 402:
            return "❌ اعتبار حساب OpenRouter کافی نیست."
        if resp.status_code != 200:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text[:300]
            return f"❌ خطای OpenRouter ({resp.status_code}): {detail}"

        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return "❌ پاسخ خالی از مدل دریافت شد."
        content = choices[0].get("message", {}).get("content", "")
        return content.strip() if content else "❌ متن پاسخ خالی بود."
    except requests.Timeout:
        return "❌ زمان انتظار برای پاسخ مدل به پایان رسید. دوباره تلاش کنید."
    except requests.RequestException as e:
        return f"❌ خطای شبکه در اتصال به OpenRouter: {e}"


def explain_decision(asset_info: dict, decision: str, confidence: float) -> str:
    """توضیح تصمیم موتور هوشمند به زبان کارشناس بهره‌برداری"""
    system = (
        "شما مشاور ارشد لجستیک معکوس در شرکت توزیع نیروی برق تهران هستید. "
        "پاسخ را به فارسی رسمی، مختصر و کاربردی بنویسید. "
        "از اصطلاحات فنی برق و نگهداری استفاده کنید. حداکثر ۸ خط."
    )
    user = (
        f"تجهیز با مشخصات زیر توسط مدل تصمیم‌یار به «{decision}» "
        f"با اطمینان {confidence*100:.0f}% پیشنهاد شده. توضیح بده چرا و چه اقدام عملی پیشنهاد می‌کنی.\n\n"
        f"{json.dumps(asset_info, ensure_ascii=False, indent=2)}"
    )
    return chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.25,
        max_tokens=800,
    )


def answer_ops_question(question: str, context: str = "") -> str:
    """پاسخ به سوال عملیاتی کاربر با زمینه سامانه RAMS"""
    system = (
        "شما دستیار هوشمند سامانه RAMS (مدیریت دارایی‌های بازگشتی) "
        "شرکت توزیع نیروی برق تهران هستید. به فارسی پاسخ بده. "
        "اگر داده دقیق نداری، شفاف بگو و مسیر پیشنهادی در سامانه را اشاره کن."
    )
    user = question
    if context:
        user = f"زمینه سامانه:\n{context}\n\nسوال کاربر:\n{question}"
    return chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.35,
        max_tokens=1000,
    )
