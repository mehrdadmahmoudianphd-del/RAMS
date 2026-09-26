# -*- coding: utf-8 -*-
"""استایل سازمانی — لجستیک معکوس و ارتقای مدیریت دارایی‌های فیزیکی"""

CUSTOM_CSS = """
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');

html, body, [class*="css"], .stApp, .stMarkdown, .stText, label, p, span, div,
button, input, textarea, select {
    font-family: 'Vazirmatn', Tahoma, 'Segoe UI', sans-serif !important;
}

/* پس‌زمینه زرد پررنگ با تکسچر نقطه‌ای حرفه‌ای */
.stApp {
    direction: rtl;
    text-align: right;
    background-color: #FFF8E1 !important;
    background-image:
        radial-gradient(ellipse at 15% 10%, rgba(255,255,255,0.55) 0%, transparent 45%),
        radial-gradient(ellipse at 85% 5%, rgba(255,249,196,0.45) 0%, transparent 40%),
        radial-gradient(circle at 50% 100%, rgba(255,236,179,0.35) 0%, transparent 50%),
        linear-gradient(180deg, #FFFDE7 0%, #FFF9C4 45%, #FFECB3 100%) !important;
    background-attachment: fixed;
}

/* مخفی‌سازی کامل کنترل جمع‌شدن سایدبار و متن Material Icons */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[kind="header"],
[data-testid="stHeader"],
.stAppDeployButton,
div[data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* هر عنصری که متن ligature آیکون نشان دهد */
[class*="keyboard_"],
[class*="material-icons"] {
    font-size: 0 !important;
    color: transparent !important;
}

/* سایدبار سرمه‌ای عریض و ثابت */
section[data-testid="stSidebar"] {
    background: linear-gradient(185deg, #0A1628 0%, #0D1B2A 40%, #152238 100%) !important;
    min-width: 300px !important;
    max-width: 320px !important;
    box-shadow: 6px 0 28px rgba(0,0,0,0.3) !important;
}

section[data-testid="stSidebar"] > div {
    background: transparent !important;
}

section[data-testid="stSidebar"] * {
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
}

section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #D6E0EA !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #FFD600 !important;
}

section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.05) !important;
    color: #E8EEF4 !important;
    border: 1px solid rgba(255,214,0,0.12) !important;
    border-radius: 10px !important;
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 0.9rem !important;
    justify-content: flex-start !important;
    box-shadow: none !important;
    width: 100% !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,214,0,0.15) !important;
    border-color: #FFD600 !important;
    color: #FFD600 !important;
}

h1, h2, h3, h4, h5 {
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    color: #0D1B2A !important;
    font-weight: 700 !important;
}

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.92);
    border-radius: 14px;
    padding: 16px 18px !important;
    box-shadow: 0 3px 14px rgba(13,27,42,0.1);
    border: 1px solid rgba(13,27,42,0.06);
    border-right: 4px solid #F9A825;
    backdrop-filter: blur(6px);
}

[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    color: #455A64 !important;
    font-weight: 600 !important;
}

[data-testid="stMetricValue"] {
    font-size: 1.55rem !important;
    color: #0D1B2A !important;
    font-weight: 800 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #FFD600 0%, #FFC107 100%) !important;
    color: #0D1B2A !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    font-weight: 700 !important;
    box-shadow: 0 3px 12px rgba(249,168,37,0.4) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #FFC107 0%, #FFB300 100%) !important;
    color: #0D1B2A !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(255,255,255,0.85);
    border-radius: 12px;
    padding: 5px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    font-weight: 600 !important;
    color: #546E7A !important;
}

.stTabs [aria-selected="true"] {
    background: #FFD600 !important;
    color: #0D1B2A !important;
}

.rams-card {
    background: rgba(255,255,255,0.93);
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 16px;
    box-shadow: 0 3px 16px rgba(13,27,42,0.08);
    border: 1px solid rgba(13,27,42,0.05);
    backdrop-filter: blur(8px);
}

.rams-card-title {
    font-size: 1.02rem;
    font-weight: 700;
    color: #0D1B2A;
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 2px solid #FFD600;
}

.rams-hint {
    font-size: 0.82rem;
    color: #546E7A;
    line-height: 1.7;
    margin-bottom: 12px;
    padding: 8px 12px;
    background: rgba(255,249,196,0.6);
    border-radius: 8px;
    border-right: 3px solid #F9A825;
}

.guide-box {
    background: linear-gradient(135deg, #0A1628 0%, #1B2838 100%);
    border-radius: 16px;
    padding: 24px 28px;
    color: #E8EEF4;
    margin-bottom: 20px;
    box-shadow: 0 8px 28px rgba(13,27,42,0.25);
    border-right: 5px solid #FFD600;
}

.guide-box h3 { color: #FFD600 !important; margin-bottom: 10px; }
.guide-box p, .guide-box li { color: #C8D6E5 !important; font-size: 0.92rem; line-height: 1.85; }

.decision-box {
    background: rgba(255,255,255,0.95);
    border: 2px solid #FFD600;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin: 14px 0;
    box-shadow: 0 4px 18px rgba(255,214,0,0.2);
}

.decision-box .decision-label { font-size: 0.95rem; color: #546E7A; }
.decision-box .decision-value {
    font-size: 2.1rem; font-weight: 800; color: #0D1B2A; margin: 8px 0;
}

.login-box {
    max-width: 560px;
    margin: 40px auto 16px;
    background: rgba(255,255,255,0.96);
    border-radius: 18px;
    padding: 32px 36px;
    box-shadow: 0 14px 44px rgba(13,27,42,0.15);
    border-top: 5px solid #FFD600;
}

.company-logo {
    text-align: center;
    margin-bottom: 8px;
}
.company-logo .logo-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 64px; height: 64px;
    border-radius: 50%;
    background: linear-gradient(145deg, #0D1B2A, #1B2838);
    border: 3px solid #FFD600;
    font-size: 1.8rem;
    margin-bottom: 8px;
    box-shadow: 0 4px 16px rgba(13,27,42,0.25);
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}

.stSelectbox label, .stTextInput label, .stNumberInput label,
.stSlider label, .stMultiSelect label, .stTextArea label {
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    color: #0D1B2A !important;
    font-weight: 600 !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.rams-footer {
    text-align: center;
    padding: 18px;
    color: #37474F;
    font-size: 0.84rem;
    margin-top: 28px;
    border-top: 1px solid rgba(13,27,42,0.1);
    line-height: 1.8;
}

.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1260px !important;
}

.js-plotly-plot .plotly text {
    font-family: Tahoma, Vazirmatn, sans-serif !important;
}

/* اکسپندر بدون آیکون خراب */
.streamlit-expanderHeader {
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    font-weight: 600 !important;
}
"""
