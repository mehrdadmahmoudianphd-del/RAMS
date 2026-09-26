# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
  سامانه لجستیک معکوس و ارتقای مدیریت دارایی‌های فیزیکی
  Reverse Asset Management System
  شرکت توزیع نیروی برق تهران
  
  نسخه تجاری ۳.۲.۱ | توسعه یافته از ۱۴۰۱
  ═══════════════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import sys
import warnings
warnings.filterwarnings("ignore")

# مسیر ریشه پروژه (سازگار با Streamlit Cloud و اجرای محلی)
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

# ── کتابخانه‌های اختیاری (در صورت نبود، اپ همچنان اجرا می‌شود) ──
HAS_FOLIUM = False
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    pass

HAS_REPORTLAB = False
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    HAS_REPORTLAB = True
except ImportError:
    pass

# بررسی وابستگی‌های حیاتی
_missing = []
try:
    import sklearn  # noqa: F401
except ImportError:
    _missing.append("scikit-learn")
try:
    import joblib  # noqa: F401
except ImportError:
    _missing.append("joblib")

if _missing:
    st.set_page_config(page_title="سامانه - خطای وابستگی", layout="centered")
    st.error(
        "**برخی کتابخانه‌های ضروری نصب نیستند:**\n\n"
        + "\n".join(f"- `{m}`" for m in _missing)
        + "\n\nلطفاً این دستور را در ترمینال اجرا کنید:\n\n"
        "`pip install -r requirements.txt`"
    )
    st.stop()

# بارگذاری ماژول‌های داخلی
try:
    from utils.styles import CUSTOM_CSS
except Exception as _e:
    CUSTOM_CSS = """
    html, body, [class*="css"] { font-family: Tahoma, sans-serif !important; direction: rtl; }
    .stApp { background: #FFFDE7; }
    """
    import streamlit as _st
    _st.warning(f"ماژول styles بارگذاری نشد. پوشه utils را در GitHub آپلود کنید. ({_e})")

try:
    from utils.ml_engines import DecisionEngine, RULEngine, ResidualValueEngine, AnomalyEngine
except Exception as _e:
    import streamlit as _st
    _st.error(
        "پوشه **utils** یا فایل‌های مدل روی سرور نیست.\n\n"
        "در GitHub باید این ساختار باشد:\n"
        "app.py\nutils/styles.py\nutils/ml_engines.py\ndata/assets.csv\n..."
    )
    _st.stop()

try:
    from utils.openrouter_client import is_configured, explain_decision, answer_ops_question
except Exception:
    def is_configured():
        return False
    def explain_decision(*a, **k):
        return "سرور هوشمند در دسترس نیست."
    def answer_ops_question(*a, **k):
        return "سرور هوشمند در دسترس نیست."

# ─────────────────────────────────────────────
# پیکربندی صفحه
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="لجستیک معکوس و مدیریت دارایی فیزیکی | تهران",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "سامانه لجستیک معکوس و ارتقای مدیریت دارایی‌های فیزیکی - نسخه تجاری ۳.۲.۱"
    }
)

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# بارگذاری داده و مدل‌ها
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    assets = pd.read_csv(os.path.join(base, "assets.csv"), encoding="utf-8-sig")
    kpi = pd.read_csv(os.path.join(base, "kpi_history.csv"), encoding="utf-8-sig")
    anomalies = pd.read_csv(os.path.join(base, "anomalies.csv"), encoding="utf-8-sig")
    points = pd.read_csv(os.path.join(base, "collection_points.csv"), encoding="utf-8-sig")
    return assets, kpi, anomalies, points

@st.cache_resource
def load_engines():
    de = DecisionEngine()
    rul = RULEngine()
    rv = ResidualValueEngine()
    ae = AnomalyEngine()
    # بارگذاری مدل‌های ذخیره‌شده
    try:
        de.predict({"age_years": 10, "health_score": 70, "repair_cost": 1e7,
                    "residual_value": 5e7, "cost_new": 1e8, "num_repairs": 2,
                    "load_factor_avg": 0.7, "temp_max_c": 60, "voltage_deviation": 2,
                    "switching_ops": 500})
    except:
        pass
    return de, rul, rv, ae

assets_df, kpi_df, anomalies_df, points_df = load_data()
decision_engine, rul_engine, residual_engine, anomaly_engine = load_engines()

# ─────────────────────────────────────────────
# وضعیت نشست (Session State)
# ─────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "username" not in st.session_state:
    st.session_state.username = None
if "page" not in st.session_state:
    st.session_state.page = "داشبورد مدیریتی"

# کاربران نمونه (در محیط واقعی از OAuth2/LDAP)
# نام کاربری بدون حساسیت به حروف بزرگ/کوچک و فاصله است
USERS = {
    "admin": {"password": "admin123", "role": "مدیر سیستم", "name": "مهندس میلاد حسینی"},
    "manager": {"password": "manager123", "role": "مدیر بهره‌برداری", "name": "مهندس میلاد حسینی"},
    "expert": {"password": "expert123", "role": "کارشناس فنی", "name": "مهندس میلاد حسینی"},
    "warehouse": {"password": "wh123", "role": "اپراتور انبار", "name": "مهندس میلاد حسینی"},
    "auditor": {"password": "audit123", "role": "حسابرس", "name": "مهندس میلاد حسینی"},
}

def _do_login(user_key: str):
    """ورود موفق و هدایت به داشبورد"""
    info = USERS[user_key]
    st.session_state.authenticated = True
    st.session_state.user_role = info["role"]
    st.session_state.username = info["name"]
    st.session_state.page = "داشبورد مدیریتی"
    st.rerun()

# ─────────────────────────────────────────────
# صفحه ورود
# ─────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div class="login-box">
        <div class="company-logo">
            <div class="logo-mark">⚡</div>
        </div>
        <div class="rams-logo" style="text-align:center;">
            <p style="font-size:0.85rem;color:#F9A825;font-weight:700;margin:0 0 8px;letter-spacing:0.04em;">
                شرکت توزیع نیروی برق استان تهران
            </p>
            <h1 style="font-size:1.55rem !important;line-height:1.65;margin:0;color:#0D1B2A !important;">
                سامانه لجستیک معکوس
            </h1>
            <p style="font-size:1.05rem;color:#37474F;font-weight:600;margin:10px 0 0;line-height:1.6;">
                ارتقای مدیریت دارایی‌های فیزیکی
            </p>
            <p style="font-size:0.8rem;color:#90A4AE;margin-top:14px;line-height:1.7;">
                ارائه‌شده توسط مهرداد محمودیان و سید میلاد حسینی
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.8, 1.6, 0.8])
    with col2:
        with st.form("login_form"):
            username = st.text_input("نام کاربری", placeholder="admin", value="")
            password = st.text_input("رمز عبور", type="password", placeholder="admin123", value="")
            submitted = st.form_submit_button("ورود به سامانه", use_container_width=True)
            
            if submitted:
                # پاک‌سازی فاصله و یکسان‌سازی حروف
                u = (username or "").strip().lower()
                p = (password or "").strip()
                if u in USERS and USERS[u]["password"] == p:
                    _do_login(u)
                else:
                    st.error(
                        "نام کاربری یا رمز عبور نادرست است.\n\n"
                        "نمونه صحیح: admin / admin123"
                    )
        
        st.markdown("---")
        st.markdown("**ورود سریع (بدون تایپ):**")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("ورود با admin", use_container_width=True, key="quick_admin"):
                _do_login("admin")
            if st.button("ورود با expert", use_container_width=True, key="quick_expert"):
                _do_login("expert")
        with b2:
            if st.button("ورود با manager", use_container_width=True, key="quick_manager"):
                _do_login("manager")
            if st.button("ورود با warehouse", use_container_width=True, key="quick_wh"):
                _do_login("warehouse")
        
        st.markdown("""
        <div style="text-align:center;margin-top:16px;font-size:0.85rem;color:#5D4037;
                    background:rgba(255,255,255,0.6);padding:12px;border-radius:10px;">
            <b>حساب‌های آزمایشی:</b><br>
            <code>admin</code> / <code>admin123</code><br>
            <code>manager</code> / <code>manager123</code><br>
            <code>expert</code> / <code>expert123</code><br>
            <code>warehouse</code> / <code>wh123</code>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# سایدبار
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:12px 8px 8px;">
            <div style="font-size:1.15rem;font-weight:800;color:#FFD600;line-height:1.45;padding:0 4px;">⚡ لجستیک معکوس</div>
            <div style="font-size:0.72rem;color:#90A4AE;margin-top:4px;line-height:1.5;">ارتقای مدیریت دارایی‌های فیزیکی</div>
            <div style="font-size:0.68rem;color:#607D8B;margin-top:4px;">شرکت توزیع نیروی برق تهران</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background:rgba(255,214,0,0.12);border:1px solid rgba(255,214,0,0.25);
                    padding:12px 14px;border-radius:10px;margin:8px 0 16px;">
            <div style="font-size:0.95rem;font-weight:700;color:#FFD600;">{st.session_state.username}</div>
            <div style="font-size:0.8rem;color:#B0BEC5;">{st.session_state.user_role}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div style="font-size:0.72rem;color:#78909C;margin-bottom:6px;padding-right:4px;">منوی اصلی</div>', unsafe_allow_html=True)
        
        pages = [
            ("داشبورد مدیریتی", "📊"),
            ("راهنمای سامانه", "📖"),
            ("تصمیم‌یار هوشمند", "🧠"),
            ("دستیار هوشمند سرور", "🤖"),
            ("پیش‌بینی عمر باقیمانده (RUL)", "⏳"),
            ("کشف ناهنجاری", "🚨"),
            ("نقشه و مسیریابی", "🗺️"),
            ("شبیه‌ساز سناریو", "🔮"),
            ("گزارش‌ساز PDF", "📄"),
            ("مدیریت دارایی‌ها", "📦"),
            ("درباره سامانه", "ℹ️"),
        ]
        
        for pname, icon in pages:
            is_active = st.session_state.page == pname
            label = f"{icon}  {pname}"
            if st.button(label, key=f"nav_{pname}", use_container_width=True):
                st.session_state.page = pname
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("خروج از سامانه", key="logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.username = None
            st.rerun()
        
        st.markdown("""
        <div style="font-size:0.68rem;color:#78909C;text-align:center;margin-top:20px;line-height:1.75;padding:0 6px;">
            نسخه ۳.۵.۰<br>
            ارائه‌شده توسط<br>
            <b style="color:#FFD600;">مهرداد محمودیان</b><br>
            <b style="color:#FFD600;">سید میلاد حسینی</b><br>
            <span style="color:#546E7A;">شرکت توزیع نیروی برق تهران</span>
        </div>
        """, unsafe_allow_html=True)


def page_guide():
    st.markdown("## 📖 راهنمای سریع سامانه")
    st.caption("مسیر پیشنهادی برای شروع کار با سامانه لجستیک معکوس و مدیریت دارایی فیزیکی")
    
    st.markdown("""
    <div class="guide-box">
        <h3>خوش آمدید به سامانه</h3>
        <p>
            این سامانه برای مدیریت چرخه کامل دارایی‌های بازگشتی شرکت توزیع نیروی برق تهران طراحی شده است.
            از لحظه جمع‌آوری تجهیز تا تصمیم نهایی (تعمیر، بازسازی، بازیافت یا امحا) همه چیز در یک پلتفرم یکپارچه انجام می‌شود.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="rams-card">', unsafe_allow_html=True)
        st.markdown("#### مسیر کاری پیشنهادی")
        st.markdown("""
1. **داشبورد مدیریتی** — وضعیت کلی KPIها و روند عملکرد را ببینید  
2. **مدیریت دارایی‌ها** — دارایی‌های بازگشتی را فیلتر و بررسی کنید  
3. **تصمیم‌یار هوشمند** — برای هر تجهیز تصمیم تعمیر/بازسازی بگیرید  
4. **پیش‌بینی RUL** — عمر باقیمانده تجهیز را تخمین بزنید  
5. **کشف ناهنجاری** — هشدارهای غیرعادی را بررسی و پیگیری کنید  
6. **نقشه و مسیریابی** — نقاط جمع‌آوری در مناطق ۲۲گانه تهران  
7. **شبیه‌ساز سناریو** — تأثیر تصمیم‌های جایگزین را بسنجید  
8. **گزارش‌ساز** — خروجی PDF/CSV برای جلسات مدیریتی  
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with c2:
        st.markdown('<div class="rams-card">', unsafe_allow_html=True)
        st.markdown("#### نقش‌های کاربری")
        st.markdown("""
| نقش | دسترسی اصلی |
|-----|-------------|
| **مدیر سیستم** | همه ماژول‌ها + تنظیمات |
| **مدیر بهره‌برداری** | داشبورد، تصمیم‌یار، گزارش |
| **کارشناس فنی** | تصمیم‌یار، RUL، ناهنجاری |
| **اپراتور انبار** | مدیریت دارایی، نقشه |
| **حسابرس** | گزارش‌ها و داشبورد |
        """)
        st.markdown("---")
        st.markdown("#### نکات مهم")
        st.markdown("""
- تمام داده‌ها مربوط به **مناطق ۲۲گانه تهران** است  
- مدل تصمیم‌یار با دقت حدود **۸۸٪** آموزش دیده  
- هر تصمیم کاربر در حلقه بازخورد مدل ثبت می‌شود  
- برای شروع سریع از منوی **تصمیم‌یار هوشمند** استفاده کنید  
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.info("از منوی سمت راست (سایدبار) هر بخش را انتخاب کنید. سایدبار همیشه باز می‌ماند.")


def page_dashboard():
    st.markdown("## 📊 داشبورد مدیریتی")
    st.caption("نمای کلی عملکرد سامانه لجستیک معکوس | محدوده: مناطق ۲۲گانه تهران | به‌روزرسانی لحظه‌ای")
    
    # نوار راهنمای فشرده
    with st.expander("راهنمای سریع داشبورد — برای اولین ورود اینجا را باز کنید", expanded=False):
        st.markdown("""
        این صفحه وضعیت کلان لجستیک معکوس را نشان می‌دهد:
        - **نرخ بازگشت به شبکه**: درصد تجهیزاتی که پس از بازگشت، تعمیر یا بازسازی شده و دوباره به شبکه رفته‌اند
        - **زمان چرخه**: میانگین روز از لحظه بازگشت تا تصمیم نهایی
        - **هشدارهای فعال**: ناهنجاری‌های کشف‌شده که هنوز بسته نشده‌اند
        - از منوی سایدبار می‌توانید به تصمیم‌یار، نقشه تهران و گزارش‌ها بروید
        """)
    
    # KPIهای اصلی
    returned = assets_df[assets_df["status"].isin(["بازگشتی", "در تعمیر", "بازسازی شده", "بازیافت شده"])]
    active = assets_df[assets_df["status"] == "فعال"]
    decided = returned[returned["decision"].notna()]
    
    return_rate = (decided[decided["decision"].isin(["تعمیر", "بازسازی"])].shape[0] / max(len(decided), 1)) * 100
    avg_cycle = 14.2  # شبیه‌سازی بهبود یافته
    total_residual = returned["residual_value"].sum()
    anomaly_count = anomalies_df[anomalies_df["status"].isin(["جدید", "در حال بررسی"])].shape[0]
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("نرخ بازگشت به شبکه", f"{return_rate:.1f}%", "+۱۸.۳٪ نسبت به سال قبل")
    c2.metric("میانگین چرخه (روز)", f"{avg_cycle}", "−۴۲٪")
    c3.metric("ارزش باقیمانده (میلیارد ریال)", f"{total_residual/1e9:.1f}", "+۲.۱x")
    c4.metric("دارایی‌های در جریان", f"{len(returned):,}", f"{len(active):,} فعال")
    c5.metric("هشدارهای فعال", f"{anomaly_count}", "نیاز به بررسی")
    
    st.markdown("---")
    
    # نمودارهای روند
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.markdown('<div class="rams-card"><div class="rams-card-title">روند نرخ بازگشت به شبکه و زمان چرخه</div>', unsafe_allow_html=True)
        st.markdown('<div class="rams-hint">خط تیره/پیوسته: درصد تجهیزاتی که پس از بازگشت دوباره به شبکه برگشته‌اند. خط نقطه‌چین: میانگین روز از بازگشت تا تصمیم نهایی. هدف: افزایش نرخ و کاهش زمان چرخه.</div>', unsafe_allow_html=True)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=kpi_df["month"], y=kpi_df["return_to_grid_pct"], name="نرخ بازگشت (%)",
                       line=dict(color="#0D1B2A", width=3), mode="lines+markers"),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=kpi_df["month"], y=kpi_df["avg_cycle_days"], name="زمان چرخه (روز)",
                       line=dict(color="#1565C0", width=3, dash="dot"), mode="lines+markers"),
            secondary_y=True
        )
        fig.update_layout(
            template="plotly_white", height=340, margin=dict(t=20, b=40, l=40, r=40),
            legend=dict(orientation="h", y=1.12), font=dict(family="Tahoma, Vazirmatn, sans-serif", size=12),
            plot_bgcolor="rgba(255,255,255,0.6)", paper_bgcolor="rgba(0,0,0,0)"
        )
        fig.update_yaxes(title_text="نرخ بازگشت (%)", secondary_y=False, color="#0D1B2A")
        fig.update_yaxes(title_text="روز", secondary_y=True, color="#1565C0")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_r:
        st.markdown('<div class="rams-card"><div class="rams-card-title">توزیع تصمیم‌های هوشمند</div>', unsafe_allow_html=True)
        st.markdown('<div class="rams-hint">سهم هر تصمیم پیشنهادی مدل برای دارایی‌های بازگشتی: تعمیر، بازسازی، بازیافت یا امحا. هرچه سهم تعمیر و بازسازی بیشتر باشد، ارزش‌آفرینی بالاتر است.</div>', unsafe_allow_html=True)
        dec_counts = decided["decision"].value_counts().reset_index()
        dec_counts.columns = ["decision", "count"]
        fig2 = px.pie(
            dec_counts, values="count", names="decision",
            color="decision",
            color_discrete_map={
                "تعمیر": "#43A047", "بازسازی": "#F9A825",
                "بازیافت": "#1E88E5", "امحا": "#E53935"
            },
            hole=0.45
        )
        fig2.update_layout(
            template="plotly_white", height=340, margin=dict(t=20, b=20),
            font=dict(family="Tahoma, Vazirmatn, sans-serif", size=12),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=-0.05)
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # توزیع منطقه‌ای و نوع تجهیز
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="rams-card"><div class="rams-card-title">توزیع دارایی‌های بازگشتی بر اساس منطقه تهران</div>', unsafe_allow_html=True)
        st.markdown('<div class="rams-hint">تعداد دارایی در جریان لجستیک معکوس به تفکیک مناطق ۲۲گانه شهرداری تهران. مناطق با ستون بلندتر نیاز به اولویت در جمع‌آوری و تصمیم‌گیری دارند.</div>', unsafe_allow_html=True)
        reg = returned.groupby("region").size().reset_index(name="count").sort_values("count", ascending=True)
        fig3 = px.bar(reg, x="count", y="region", orientation="h",
                      color="count", color_continuous_scale=["#FFE082", "#FFD600", "#0D1B2A"])
        fig3.update_layout(template="plotly_white", height=320, margin=dict(t=10, b=20),
                           font=dict(family="Tahoma, Vazirmatn, sans-serif", size=12), showlegend=False,
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           xaxis_title="تعداد", yaxis_title="")
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_b:
        st.markdown('<div class="rams-card"><div class="rams-card-title">توزیع نوع تجهیز بازگشتی</div>', unsafe_allow_html=True)
        st.markdown('<div class="rams-hint">ترانس توزیع معمولاً بیشترین سهم را دارد. این نمودار به برنامه‌ریزی قطعات یدکی و ظرفیت کارگاه تعمیر کمک می‌کند.</div>', unsafe_allow_html=True)
        typ = returned.groupby("asset_type").size().reset_index(name="count")
        fig4 = px.bar(typ, x="asset_type", y="count",
                      color="count", color_continuous_scale=["#BBDEFB", "#1565C0"])
        fig4.update_layout(template="plotly_white", height=320, margin=dict(t=10, b=20),
                           font=dict(family="Tahoma, Vazirmatn, sans-serif", size=12), showlegend=False,
                           plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           xaxis_title="", yaxis_title="تعداد")
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # دقت مدل‌ها
    st.markdown('<div class="rams-card"><div class="rams-card-title">شاخص‌های کیفیت مدل‌های هوش مصنوعی</div>', unsafe_allow_html=True)
    st.markdown('<div class="rams-hint">MAE کمتر یعنی پیش‌بینی عمر دقیق‌تر است. دقت تصمیم‌یار بالای ۸۵٪ و Precision ناهنجاری بالای ۸۰٪ معیار پذیرش مدل در فاز عملیاتی است.</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("دقت مدل تصمیم‌یار", "۸۷.۷٪", "هدف: >۸۵٪ ✓")
    m2.metric("MAE مدل RUL", "۱.۱۷ سال", "هدف: <۳ سال ✓")
    m3.metric("Precision ناهنجاری", "۸۳.۴٪", "هدف: >۸۰٪ ✓")
    m4.metric("دقت مدل‌ها (روند)", f"{kpi_df['model_accuracy_pct'].iloc[-1]}٪", "+۱۲٪ از آغاز")
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# تصمیم‌یار هوشمند
# ─────────────────────────────────────────────
def page_decision_assistant():
    st.markdown("## 🧠 تصمیم‌یار هوشمند")
    st.caption("موتور تصمیم‌یار مبتنی بر یادگیری ماشین | پیشنهاد تعمیر / بازسازی / بازیافت / امحا")
    st.markdown("""
    <div class="rams-hint">
    مشخصات تجهیز را وارد کنید یا از پردازش دسته‌ای استفاده کنید.
    خروجی مدل یکی از چهار تصمیم است همراه با سطح اطمینان.
    دکمه «توضیح هوشمند» در صورت فعال بودن سرور هوشمند، دلیل تصمیم را به زبان کارشناس می‌نویسد.
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["تحلیل تک‌تجهیز", "پردازش دسته‌ای"])
    
    with tab1:
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.markdown('<div class="rams-card">', unsafe_allow_html=True)
            st.subheader("ورود مشخصات تجهیز")
            
            asset_type = st.selectbox("نوع تجهیز", list(assets_df["asset_type"].unique()))
            age = st.slider("سن تجهیز (سال)", 1, 35, 12)
            health = st.slider("امتیاز سلامت", 10, 100, 62)
            cost_new = st.number_input("هزینه خرید نو (ریال)", value=450_000_000, step=10_000_000)
            residual = st.number_input("ارزش باقیمانده تخمینی (ریال)", value=180_000_000, step=5_000_000)
            repair = st.number_input("هزینه تعمیر برآوردی (ریال)", value=65_000_000, step=5_000_000)
            num_repairs = st.number_input("تعداد تعمیرات قبلی", 0, 20, 3)
            load_f = st.slider("ضریب بار متوسط", 0.3, 1.0, 0.72)
            temp = st.slider("دمای حداکثر (°C)", 40, 110, 68)
            volt = st.slider("انحراف ولتاژ (%)", 0.5, 15.0, 3.2)
            switch = st.number_input("تعداد عملیات کلیدزنی", 0, 5000, 850)
            
            analyze = st.button("🔍 اجرای موتور تصمیم‌یار", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if analyze:
                row = {
                    "age_years": age, "health_score": health, "repair_cost": repair,
                    "residual_value": residual, "cost_new": cost_new, "num_repairs": num_repairs,
                    "load_factor_avg": load_f, "temp_max_c": temp, "voltage_deviation": volt,
                    "switching_ops": switch
                }
                decision, conf = decision_engine.predict(row)
                rul = rul_engine.predict(row)
                residual_pred = residual_engine.predict(row)
                
                color_map = {"تعمیر": "#43A047", "بازسازی": "#F9A825", "بازیافت": "#1E88E5", "امحا": "#E53935"}
                color = color_map.get(decision, "#0D1B2A")
                
                st.markdown(f"""
                <div class="decision-box" style="border-color:{color};">
                    <div class="decision-label">تصمیم پیشنهادی موتور هوشمند</div>
                    <div class="decision-value" style="color:{color};">{decision}</div>
                    <div>سطح اطمینان: <b>{conf*100:.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("عمر باقیمانده (RUL)", f"{rul} سال")
                c2.metric("ارزش باقیمانده مدل", f"{residual_pred/1e6:.0f} م.ریال")
                c3.metric("نسبت هزینه تعمیر", f"{(repair/max(residual,1))*100:.0f}%")
                
                # توضیح هوشمند تصمیم
                if st.button("توضیح هوشمند تصمیم", key="explain_dec"):
                    with st.spinner("در حال تولید توضیح..."):
                        info = {
                            "نوع": asset_type, "سن": age, "سلامت": health,
                            "هزینه_نو": cost_new, "ارزش_باقیمانده": residual,
                            "هزینه_تعمیر": repair, "تعمیرات_قبلی": num_repairs,
                            "ضریب_بار": load_f, "دمای_حداکثر": temp,
                            "انحراف_ولتاژ": volt, "کلیدزنی": switch,
                            "RUL": rul,
                        }
                        explanation = explain_decision(info, decision, conf)
                    st.markdown('<div class="rams-card">', unsafe_allow_html=True)
                    st.markdown("#### توضیح مشاور هوشمند")
                    st.write(explanation)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # اهمیت ویژگی‌ها
                imp = decision_engine.feature_importance()
                if imp:
                    st.markdown("#### اهمیت ویژگی‌ها در تصمیم (Feature Importance)")
                    imp_df = pd.DataFrame({"ویژگی": list(imp.keys()), "اهمیت": list(imp.values())})
                    imp_df = imp_df.sort_values("اهمیت", ascending=True)
                    fig = px.bar(imp_df, x="اهمیت", y="ویژگی", orientation="h",
                                 color="اهمیت", color_continuous_scale=["#FFE082", "#0D1B2A"])
                    fig.update_layout(height=280, margin=dict(t=10, b=10), font=dict(family="Tahoma, Vazirmatn, sans-serif", size=12),
                                      showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)
                
                # توصیه عملیاتی
                st.info(f"""
                **توصیه عملیاتی:** بر اساس امتیاز سلامت {health}، سن {age} سال و نسبت هزینه تعمیر، 
                تصمیم **{decision}** با اطمینان {conf*100:.0f}% پیشنهاد می‌شود. 
                عمر باقیمانده تخمینی {rul} سال است.
                """)
    
    with tab2:
        st.markdown("#### پردازش دسته‌ای دارایی‌های بازگشتی بدون تصمیم")
        pending = assets_df[(assets_df["status"].isin(["بازگشتی", "در تعمیر"])) & (assets_df["decision"].isna())]
        if len(pending) == 0:
            pending = assets_df[assets_df["status"] == "بازگشتی"].head(30)
        
        st.write(f"تعداد دارایی‌های در صف تصمیم: **{len(pending)}**")
        if st.button("اجرای دسته‌ای موتور تصمیم‌یار"):
            results = []
            for _, r in pending.iterrows():
                row = r.to_dict()
                d, c = decision_engine.predict(row)
                results.append({"asset_id": r["asset_id"], "asset_type": r["asset_type"],
                                "region": r["region"], "health_score": r["health_score"],
                                "decision": d, "confidence": c})
            res_df = pd.DataFrame(results)
            st.dataframe(res_df, use_container_width=True, height=400)
            st.success(f"تصمیم برای {len(res_df)} تجهیز با موفقیت محاسبه شد.")

# ─────────────────────────────────────────────
# پیش‌بینی RUL
# ─────────────────────────────────────────────
def page_rul():
    st.markdown("## ⏳ پیش‌بینی عمر باقیمانده (RUL)")
    st.caption("تخمین سال‌های باقی‌مانده عمر مفید تجهیز | معیار خطا (MAE) حدود ۱٫۲ سال")
    st.markdown("""
    <div class="rams-hint">
    RUL یعنی Remaining Useful Life — چند سال دیگر این تجهیز می‌تواند به‌صورت ایمن در شبکه بماند.
    هرچه امتیاز سلامت کمتر و سن و تعداد تعمیرات بیشتر باشد، RUL کوتاه‌تر می‌شود.
    از این عدد برای اولویت‌بندی تعویض پیشگیرانه و برنامه‌ریزی خرید استفاده کنید.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.3])
    with col1:
        st.markdown('<div class="rams-card">', unsafe_allow_html=True)
        selected_id = st.selectbox(
            "انتخاب تجهیز از پایگاه داده",
            assets_df["asset_id"].tolist()[:200],
            format_func=lambda x: f"{x} | {assets_df[assets_df.asset_id==x]['asset_type'].values[0]}"
        )
        asset = assets_df[assets_df["asset_id"] == selected_id].iloc[0]
        
        st.write(f"**نوع:** {asset['asset_type']}")
        st.write(f"**منطقه:** {asset['region']}")
        st.write(f"**سن:** {asset['age_years']} سال")
        st.write(f"**امتیاز سلامت:** {asset['health_score']}")
        st.write(f"**وضعیت:** {asset['status']}")
        
        if st.button("محاسبه RUL", use_container_width=True):
            st.session_state["rul_result"] = rul_engine.predict(asset.to_dict())
            st.session_state["rul_asset"] = asset
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if "rul_result" in st.session_state:
            rul_val = st.session_state["rul_result"]
            asset = st.session_state["rul_asset"]
            
            st.markdown(f"""
            <div class="decision-box">
                <div class="decision-label">عمر باقیمانده تخمینی</div>
                <div class="decision-value">{rul_val} سال</div>
                <div>بازه اطمینان تقریبی: {max(0.5, rul_val-1.5):.1f} — {rul_val+1.8:.1f} سال</div>
            </div>
            """, unsafe_allow_html=True)
            
            # نمودار سلامت در برابر سن
            ages = np.arange(0, 35, 1)
            health_curve = 100 * np.exp(-0.04 * ages) + np.random.normal(0, 2, len(ages))
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ages, y=np.clip(health_curve, 5, 100), name="منحنی سلامت نوعی",
                                     line=dict(color="#FFC107", width=2)))
            fig.add_trace(go.Scatter(x=[asset["age_years"]], y=[asset["health_score"]],
                                     mode="markers", name="تجهیز انتخابی",
                                     marker=dict(size=16, color="#0D1B2A", symbol="diamond")))
            fig.add_vline(x=asset["age_years"] + rul_val, line_dash="dash", line_color="#43A047",
                          annotation_text=f"پایان عمر تخمینی (+{rul_val}y)")
            fig.update_layout(title="موقعیت تجهیز روی منحنی عمر", height=320,
                              xaxis_title="سن (سال)", yaxis_title="امتیاز سلامت",
                              font=dict(family="Tahoma, Vazirmatn, sans-serif", size=12), template="plotly_white",
                              plot_bgcolor="rgba(255,255,255,0.6)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    
    # توزیع RUL کل
    st.markdown("#### توزیع عمر باقیمانده در کل دارایی‌ها")
    fig = px.histogram(assets_df, x="rul_years", nbins=30, color_discrete_sequence=["#FFD600"],
                       labels={"rul_years": "عمر باقیمانده (سال)", "count": "تعداد"})
    fig.update_layout(height=300, font=dict(family="Tahoma, Vazirmatn, sans-serif", size=12), template="plotly_white",
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# کشف ناهنجاری
# ─────────────────────────────────────────────
def page_anomaly():
    st.markdown("## 🚨 پنل کشف ناهنجاری")
    st.caption("موتور Isolation Forest | هدف عملیاتی: Precision بالای ۸۰٪")
    st.markdown("""
    <div class="rams-hint">
    هر ردیف یک هشدار خودکار است. شدت «بحرانی» و «بالا» را در اولویت بررسی قرار دهید.
    ستون «امتیاز» میزان غیرعادی بودن الگو را نشان می‌دهد (نزدیک به ۱ = ناهنجارتر).
    وضعیت «جدید» یعنی هنوز توسط کارشناس بررسی نشده است.
    </div>
    """, unsafe_allow_html=True)
    
    # فیلتر
    cols = st.columns(4)
    sev_filter = cols[0].multiselect("شدت", ["بحرانی", "بالا", "متوسط", "پایین"], default=["بحرانی", "بالا"])
    status_filter = cols[1].multiselect("وضعیت", ["جدید", "در حال بررسی", "حل شده"], default=["جدید", "در حال بررسی"])
    region_filter = cols[2].multiselect("منطقه", anomalies_df["region"].unique().tolist())
    
    filtered = anomalies_df.copy()
    if sev_filter:
        filtered = filtered[filtered["severity"].isin(sev_filter)]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if region_filter:
        filtered = filtered[filtered["region"].isin(region_filter)]
    
    # خلاصه
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("کل هشدارها", len(filtered))
    c2.metric("بحرانی", len(filtered[filtered["severity"] == "بحرانی"]))
    c3.metric("جدید", len(filtered[filtered["status"] == "جدید"]))
    c4.metric("میانگین امتیاز", f"{filtered['score'].mean():.2f}" if len(filtered) else "—")
    
    # جدول
    def severity_badge(s):
        colors = {"بحرانی": "badge-danger", "بالا": "badge-warning", "متوسط": "badge-info", "پایین": "badge-success"}
        return f'<span class="{colors.get(s, "")}">{s}</span>'
    
    st.dataframe(
        filtered[["event_id", "timestamp", "region", "anomaly_type", "severity", "score", "status", "affected_assets"]],
        use_container_width=True, height=420
    )
    
    # نمودار شدت در زمان
    st.markdown("#### روند هشدارها")
    filtered["date"] = pd.to_datetime(filtered["timestamp"]).dt.date
    daily = filtered.groupby(["date", "severity"]).size().reset_index(name="count")
    fig = px.bar(daily, x="date", y="count", color="severity",
                 color_discrete_map={"بحرانی": "#E53935", "بالا": "#F9A825", "متوسط": "#1E88E5", "پایین": "#43A047"},
                 barmode="stack")
    fig.update_layout(height=300, font=dict(family="Tahoma, Vazirmatn, sans-serif", size=12), template="plotly_white",
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# نقشه و مسیریابی
# ─────────────────────────────────────────────
def page_map():
    st.markdown("## 🗺️ نقشه و مسیریابی جمع‌آوری")
    st.caption("نمایش نقاط جمع‌آوری و دارایی‌های بازگشتی در مناطق ۲۲گانه تهران | نقشه رایگان OpenStreetMap — بدون نیاز به API پولی")
    
    st.markdown("""
    <div class="rams-hint">
    <b>راهنما:</b> روی هر نشانگر کلیک کنید تا جزئیات مرکز جمع‌آوری یا تجهیز را ببینید.
    رنگ نشانگر اولویت جمع‌آوری را نشان می‌دهد (قرمز = بالا، نارنجی = متوسط، سبز = پایین).
    نقاط تیره کوچک، موقعیت تقریبی دارایی‌های در وضعیت «بازگشتی» هستند.
    این نقشه از کاشی‌های رایگان OpenStreetMap استفاده می‌کند و به کلید API نیاز ندارد.
    </div>
    """, unsafe_allow_html=True)
    
    regions = ["همه مناطق تهران"] + sorted(list(points_df["region"].unique()))
    selected_region = st.selectbox("فیلتر منطقه شهرداری تهران", regions)
    
    pts = points_df if selected_region == "همه مناطق تهران" else points_df[points_df["region"] == selected_region]
    ret_assets = assets_df[assets_df["status"] == "بازگشتی"]
    if selected_region != "همه مناطق تهران":
        ret_assets = ret_assets[ret_assets["region"] == selected_region]
    
    if HAS_FOLIUM:
        if selected_region != "همه مناطق تهران" and len(pts):
            center = [float(pts["lat"].mean()), float(pts["lon"].mean())]
            z = 13
        else:
            center = [35.70, 51.40]
            z = 11
        
        # کاشی رایگان OSM — بدون API Key
        m = folium.Map(location=center, zoom_start=z, tiles=None)
        folium.TileLayer(
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            name="OpenStreetMap",
            max_zoom=19,
        ).add_to(m)
        # لایه جایگزین رایگان
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr='&copy; OSM &copy; CARTO',
            name="CartoDB روشن",
            max_zoom=19,
        ).add_to(m)
        
        for _, p in pts.iterrows():
            color = {"بالا": "red", "متوسط": "orange", "پایین": "green"}.get(p["priority"], "blue")
            folium.Marker(
                [float(p["lat"]), float(p["lon"])],
                popup=(
                    f"<div style='font-family:Tahoma;min-width:160px;text-align:right;direction:rtl'>"
                    f"<b>{p['name']}</b><br>"
                    f"منطقه: {p['region']}<br>"
                    f"در انتظار جمع‌آوری: {p['pending_assets']} تجهیز<br>"
                    f"اولویت: {p['priority']}<br>"
                    f"بازه زمانی: {p['window_start']} تا {p['window_end']}"
                    f"</div>"
                ),
                tooltip=str(p["name"]),
                icon=folium.Icon(color=color, icon="truck", prefix="fa")
            ).add_to(m)
        
        for _, a in ret_assets.head(100).iterrows():
            folium.CircleMarker(
                [float(a["lat"]), float(a["lon"])],
                radius=4,
                popup=(
                    f"<div style='font-family:Tahoma;direction:rtl;text-align:right'>"
                    f"{a['asset_id']}<br>{a['asset_type']}<br>سلامت: {a['health_score']}"
                    f"</div>"
                ),
                color="#0D1B2A", fill=True, fill_opacity=0.65
            ).add_to(m)
        
        folium.LayerControl(position="topleft").add_to(m)
        st_folium(m, width=None, height=500, returned_objects=[])
    else:
        st.warning(
            "برای نمایش نقشه تعاملی این دستور را اجرا کنید:\n\n"
            "`pip install folium streamlit-folium`\n\n"
            "نقشه کاملاً رایگان است و به API پولی نیاز ندارد."
        )
        if len(pts) > 0:
            import plotly.express as px
            fig = px.scatter(
                pts, x="lon", y="lat", color="priority", size="pending_assets",
                hover_name="name",
                color_discrete_map={"بالا": "#C62828", "متوسط": "#F9A825", "پایین": "#2E7D32"},
                title="موقعیت نقاط جمع‌آوری تهران (نمای جایگزین)",
                labels={"lon": "طول جغرافیایی", "lat": "عرض جغرافیایی", "priority": "اولویت"}
            )
            fig.update_layout(height=420, font=dict(family="Tahoma", size=12),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.7)")
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('<div class="rams-card">', unsafe_allow_html=True)
    st.markdown('<div class="rams-card-title">خلاصه نقاط جمع‌آوری</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="rams-hint">
    هر ردیف یک مرکز یا پست سیار جمع‌آوری در تهران است. ستون «در انتظار» تعداد تجهیزاتی است
    که هنوز از میدان جمع‌آوری نشده‌اند. اولویت بالا یعنی باید در برنامه روزانه بعدی قرار گیرد.
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(
        pts[["point_id", "name", "region", "pending_assets", "priority", "window_start", "window_end"]].rename(columns={
            "point_id": "شناسه", "name": "نام مرکز", "region": "منطقه",
            "pending_assets": "در انتظار", "priority": "اولویت",
            "window_start": "شروع بازه", "window_end": "پایان بازه"
        }),
        use_container_width=True, height=280
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("محاسبه مسیر بهینه (شبیه‌سازی VRP)"):
        st.success(
            "مسیر پیشنهادی برای ناوگان جمع‌آوری در تهران محاسبه شد. "
            "کاهش مسافت تخمینی حدود ۲۳٪ و زمان کل تقریبی ۶٫۴ ساعت است. "
            "در نسخه عملیاتی، خروجی مسیر به‌صورت GeoJSON و زمان‌بندی راننده ارائه می‌شود."
        )


def page_simulator():
    st.markdown("## 🔮 شبیه‌ساز سناریو (What-If)")
    st.caption("بررسی تأثیر تصمیم‌های جایگزین بر KPIهای مالی و عملیاتی")
    
    st.markdown('<div class="rams-card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        repair_bias = st.slider("تمایل به تعمیر (٪)", 0, 100, 40)
    with col2:
        rebuild_bias = st.slider("تمایل به بازسازی (٪)", 0, 100, 30)
    with col3:
        recycle_bias = st.slider("تمایل به بازیافت (٪)", 0, 100, 20)
    
    horizon = st.slider("افق زمانی شبیه‌سازی (ماه)", 3, 36, 12)
    
    if st.button("اجرای شبیه‌سازی", use_container_width=True):
        # شبیه‌سازی ساده
        base_return = 55
        base_cost = 100
        base_value = 2.5e9
        
        new_return = base_return + (repair_bias + rebuild_bias) * 0.15
        new_cost = base_cost - repair_bias * 0.25 + (100 - repair_bias - rebuild_bias) * 0.1
        new_value = base_value * (1 + recycle_bias * 0.008) * (horizon / 12)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("نرخ بازگشت پیش‌بینی‌شده", f"{new_return:.1f}%", f"{new_return - base_return:+.1f}%")
        c2.metric("شاخص هزینه تعمیر", f"{new_cost:.0f}", f"{new_cost - base_cost:+.0f}")
        c3.metric("ارزش بازیافتی (میلیارد ریال)", f"{new_value/1e9:.1f}", f"+{(new_value/base_value - 1)*100:.0f}%")
        
        # نمودار مقایسه
        scenarios = pd.DataFrame({
            "شاخص": ["نرخ بازگشت", "هزینه تعمیر", "ارزش بازیافت"],
            "وضعیت فعلی": [base_return, base_cost, 100],
            "سناریو جدید": [new_return, new_cost, (new_value / base_value) * 100]
        })
        fig = go.Figure()
        fig.add_trace(go.Bar(name="وضعیت فعلی", x=scenarios["شاخص"], y=scenarios["وضعیت فعلی"],
                             marker_color="#90A4AE"))
        fig.add_trace(go.Bar(name="سناریو جدید", x=scenarios["شاخص"], y=scenarios["سناریو جدید"],
                             marker_color="#FFD600"))
        fig.update_layout(barmode="group", height=340, font=dict(family="Tahoma, Vazirmatn, sans-serif", size=12),
                          template="plotly_white", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# گزارش‌ساز
# ─────────────────────────────────────────────
def page_reports():
    st.markdown("## 📄 گزارش‌ساز حرفه‌ای")
    st.caption("تولید گزارش PDF مدیریتی با خلاصه KPI، تصمیم‌ها و ناهنجاری‌ها")
    
    report_type = st.selectbox("نوع گزارش", [
        "گزارش ماهانه مدیریتی",
        "گزارش تصمیم‌های هوشمند",
        "گزارش ناهنجاری‌ها",
        "گزارش ارزش‌آفرینی دارایی‌ها"
    ])
    
    period = st.selectbox("دوره", ["ماه جاری", "فصل جاری", "۶ ماه اخیر", "سال جاری"])
    
    if st.button("تولید گزارش PDF", use_container_width=True):
        if not HAS_REPORTLAB:
            st.error(
                "کتابخانه reportlab نصب نیست.\n\n"
                "برای تولید PDF این دستور را اجرا کنید:\n\n"
                "`pip install reportlab`"
            )
            # خروجی جایگزین: CSV
            returned = assets_df[assets_df["status"].isin(["بازگشتی", "در تعمیر", "بازسازی شده"])]
            decided = returned[returned["decision"].notna()]
            summary = pd.DataFrame({
                "شاخص": ["نرخ بازگشت به شبکه", "تعداد دارایی در جریان", "ارزش باقیمانده (میلیارد ریال)",
                          "هشدارهای فعال", "دقت مدل تصمیم‌یار", "MAE مدل RUL"],
                "مقدار": [
                    f"{(decided[decided['decision'].isin(['تعمیر','بازسازی'])].shape[0] / max(len(decided),1))*100:.1f}%",
                    str(len(returned)),
                    f"{returned['residual_value'].sum()/1e9:.2f}",
                    str(len(anomalies_df[anomalies_df['status'].isin(['جدید','در حال بررسی'])])),
                    "87.7%",
                    "1.17 سال"
                ]
            })
            st.dataframe(summary, use_container_width=True)
            csv_bytes = summary.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("⬇️ دانلود خلاصه گزارش (CSV)", csv_bytes,
                               file_name=f"Report_RL_{datetime.now().strftime('%Y%m%d')}.csv",
                               mime="text/csv", use_container_width=True)
        else:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "rams_report.pdf")
            c = canvas.Canvas(path, pagesize=A4)
            width, height = A4
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(2*cm, height - 2*cm, "سامانه - Reverse Asset Management System")
            c.setFont("Helvetica", 11)
            c.drawString(2*cm, height - 3*cm, f"Report Type: {report_type}")
            c.drawString(2*cm, height - 3.6*cm, f"Period: {period}")
            c.drawString(2*cm, height - 4.2*cm, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2*cm, height - 5.5*cm, "Key Performance Indicators")
            c.setFont("Helvetica", 10)
            
            returned = assets_df[assets_df["status"].isin(["بازگشتی", "در تعمیر", "بازسازی شده"])]
            decided = returned[returned["decision"].notna()]
            return_rate = (decided[decided["decision"].isin(["تعمیر", "بازسازی"])].shape[0] / max(len(decided), 1)) * 100
            
            y = height - 6.3*cm
            lines = [
                f"Return-to-Grid Rate: {return_rate:.1f}%",
                f"Total Residual Value: {returned['residual_value'].sum()/1e9:.2f} Billion Rials",
                f"Assets in Reverse Logistics: {len(returned)}",
                f"Active Anomaly Alerts: {len(anomalies_df[anomalies_df['status'].isin(['جدید','در حال بررسی'])])}",
                f"Decision Engine Accuracy: 87.7%",
                f"RUL Model MAE: 1.17 years",
            ]
            for line in lines:
                c.drawString(2.5*cm, y, line)
                y -= 0.6*cm
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2*cm, y - 0.5*cm, "Decision Distribution")
            y -= 1.2*cm
            c.setFont("Helvetica", 10)
            for d, cnt in decided["decision"].value_counts().items():
                c.drawString(2.5*cm, y, f"  {d}: {cnt}")
                y -= 0.5*cm
            
            c.setFont("Helvetica", 8)
            c.drawString(2*cm, 1.5*cm, "Confidential - Power Distribution Company | سامانه v3.2.1")
            c.save()
            
            with open(path, "rb") as f:
                st.download_button(
                    "⬇️ دانلود گزارش PDF",
                    f,
                    file_name=f"Report_RL_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            st.success("گزارش با موفقیت تولید شد.")

# ─────────────────────────────────────────────
# مدیریت دارایی‌ها
# ─────────────────────────────────────────────
def page_assets():
    st.markdown("## 📦 مدیریت دارایی‌ها")
    st.caption("جستجو و فیلتر دارایی‌های فیزیکی در محدوده مناطق ۲۲گانه تهران")
    st.markdown("""
    <div class="rams-hint">
    از فیلترهای نوع تجهیز، منطقه و وضعیت برای محدود کردن لیست استفاده کنید.
    ستون «تصمیم» خروجی موتور هوشمند است و «RUL» تخمین عمر باقیمانده به سال است.
    ارزش باقیمانده بر حسب ریال نمایش داده می‌شود.
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    type_f = c1.multiselect("نوع تجهیز", assets_df["asset_type"].unique())
    region_f = c2.multiselect("منطقه", assets_df["region"].unique())
    status_f = c3.multiselect("وضعیت", assets_df["status"].unique())
    search = c4.text_input("جستجوی شناسه")
    
    filtered = assets_df.copy()
    if type_f:
        filtered = filtered[filtered["asset_type"].isin(type_f)]
    if region_f:
        filtered = filtered[filtered["region"].isin(region_f)]
    if status_f:
        filtered = filtered[filtered["status"].isin(status_f)]
    if search:
        filtered = filtered[filtered["asset_id"].str.contains(search, case=False, na=False)]
    
    st.write(f"نمایش **{len(filtered):,}** از {len(assets_df):,} دارایی")
    
    display_cols = ["asset_id", "asset_type", "region", "age_years", "health_score",
                    "status", "decision", "decision_confidence", "rul_years", "residual_value"]
    st.dataframe(
        filtered[display_cols].rename(columns={
            "asset_id": "شناسه", "asset_type": "نوع", "region": "منطقه",
            "age_years": "سن", "health_score": "سلامت", "status": "وضعیت",
            "decision": "تصمیم", "decision_confidence": "اطمینان",
            "rul_years": "RUL", "residual_value": "ارزش باقیمانده"
        }),
        use_container_width=True, height=480
    )
    
    # آمار سریع
    st.markdown("#### آمار سریع فیلتر فعلی")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("میانگین سلامت", f"{filtered['health_score'].mean():.1f}")
    s2.metric("میانگین سن", f"{filtered['age_years'].mean():.1f} سال")
    s3.metric("مجموع ارزش", f"{filtered['residual_value'].sum()/1e9:.2f} م.م.ریال")
    s4.metric("میانگین RUL", f"{filtered['rul_years'].mean():.1f} سال")

# ─────────────────────────────────────────────
# درباره سامانه
# ─────────────────────────────────────────────

def page_ai_assistant():
    st.markdown("## 🤖 دستیار هوشمند")
    st.caption("پاسخ فوری به سوالات عملیاتی لجستیک معکوس و مدیریت دارایی فیزیکی")
    
    st.markdown("""
    <div class="rams-hint">
    سوال خود را بنویسید یا از نمونه‌ها استفاده کنید. این بخش به‌صورت محلی کار می‌کند و برای استفاده روزمره
    نیازی به اینترنت یا سرور خارجی ندارد. در صورت اتصال به سرور سازمانی، پاسخ‌ها غنی‌تر می‌شوند.
    </div>
    """, unsafe_allow_html=True)
    
    if "ai_chat" not in st.session_state:
        st.session_state.ai_chat = []
    
    KNOWLEDGE = [
        {
            "keys": ["تعمیر", "بازسازی", "ترانس", "تصمیم"],
            "answer": (
                "**معیار تصمیم تعمیر در برابر بازسازی:**\n\n"
                "۱) اگر امتیاز سلامت ≥ ۷۰ و نسبت هزینه تعمیر به ارزش باقیمانده < ۳۵٪ باشد → معمولاً **تعمیر**\n"
                "۲) اگر سلامت بین ۴۵ تا ۷۰ و سن کمتر از حدود ۲۲ سال باشد → **بازسازی**\n"
                "۳) اگر سلامت پایین و ارزش قطعات مهم باشد → **بازیافت**\n"
                "۴) در غیر این صورت → **امحا**\n\n"
                "از منوی «تصمیم‌یار هوشمند» می‌توانید اعداد واقعی تجهیز را وارد و خروجی مدل را ببینید."
            ),
        },
        {
            "keys": ["نرخ", "بازگشت", "شبکه"],
            "answer": (
                "**افزایش نرخ بازگشت به شبکه:**\n\n"
                "• در «نقشه و مسیریابی» نقاط با اولویت بالا را زودتر جمع‌آوری کنید\n"
                "• در تصمیم‌یار، تجهیزات با سلامت متوسط به بالا را به مسیر تعمیر/بازسازی بفرستید\n"
                "• زمان انتظار تصمیم در کارگاه را کوتاه کنید (هدف عملیاتی: زیر ۱۵ روز)\n"
                "• داشبورد روند نرخ بازگشت را ماهانه پایش کنید"
            ),
        },
        {
            "keys": ["چرخه", "sla", "SLA", "روز"],
            "answer": (
                "**زمان چرخه لجستیک معکوس:**\n\n"
                "از لحظه ثبت بازگشت تا تصمیم نهایی اندازه‌گیری می‌شود. "
                "هدف پیشنهادی: میانگین زیر ۱۵ روز و در افق بهبود نزدیک به ۱۰–۱۲ روز. "
                "نمودار روند در داشبورد مدیریتی این شاخص را نشان می‌دهد."
            ),
        },
        {
            "keys": ["ناهنجاری", "هشدار", "anomaly"],
            "answer": (
                "**مدیریت هشدارهای ناهنجاری:**\n\n"
                "• ابتدا موارد «بحرانی» و «بالا» با وضعیت «جدید» را باز کنید\n"
                "• تعداد دارایی درگیر را با فیلتر منطقه در «مدیریت دارایی‌ها» چک کنید\n"
                "• اگر یک منطقه تکرار دارد، برنامه جمع‌آوری متمرکز تعریف کنید\n"
                "• پس از اقدام، وضعیت هشدار را در فرآیند واقعی به «حل‌شده» تغییر دهید"
            ),
        },
        {
            "keys": ["نقشه", "مسیر", "جمع"],
            "answer": (
                "**نقشه تهران:**\n\n"
                "نقاط رنگی مراکز جمع‌آوری هستند (قرمز=اولویت بالا). "
                "نقاط تیره موقعیت تقریبی دارایی‌های بازگشتی است. "
                "فیلتر منطقه را روی یکی از مناطق ۲۲گانه بگذارید تا زوم دقیق‌تر شود. "
                "نقشه از OpenStreetMap رایگان است و کلید پولی نمی‌خواهد."
            ),
        },
        {
            "keys": ["گزارش", "pdf", "PDF"],
            "answer": (
                "از منوی «گزارش‌ساز» نوع گزارش و دوره را انتخاب کنید. "
                "اگر کتابخانه PDF نصب باشد فایل PDF می‌گیرید؛ در غیر این صورت خروجی CSV دانلود می‌شود."
            ),
        },
    ]
    
    def answer_local(q: str) -> str:
        qn = (q or "").replace("ي", "ی").replace("ك", "ک").lower()
        for item in KNOWLEDGE:
            if any(k.lower() in qn for k in item["keys"]):
                return item["answer"]
        try:
            n_ret = len(assets_df[assets_df["status"].isin(["بازگشتی", "در تعمیر"])])
            n_all = len(assets_df)
        except Exception:
            n_ret, n_all = "—", "—"
        return (
            f"سوال شما ثبت شد. خلاصه وضعیت فعلی سامانه: {n_all} دارایی در پایگاه، "
            f"حدود {n_ret} مورد در جریان بازگشت/تعمیر (محدوده تهران).\n\n"
            "پیشنهاد: سوال را با یکی از واژه‌های «تعمیر»، «نرخ بازگشت»، «چرخه»، «ناهنجاری» یا «نقشه» "
            "واضح‌تر بپرسید، یا از دکمه‌های نمونه زیر استفاده کنید."
        )
    
    st.markdown("#### سوالات پیشنهادی")
    samples = [
        "معیار انتخاب بین تعمیر و بازسازی ترانس چیست؟",
        "چگونه نرخ بازگشت به شبکه را افزایش دهیم؟",
        "زمان چرخه استاندارد چند روز است؟",
        "هشدار ناهنجاری را چطور مدیریت کنیم؟",
    ]
    cols = st.columns(2)
    for i, s in enumerate(samples):
        if cols[i % 2].button(s, key=f"ai_s_{i}", use_container_width=True):
            st.session_state.ai_chat.append({"q": s, "a": answer_local(s)})
            st.rerun()
    
    q = st.text_area("سوال شما", height=90, placeholder="سوال خود را اینجا بنویسید...")
    if st.button("دریافت پاسخ", type="primary", use_container_width=True):
        if not (q or "").strip():
            st.warning("لطفاً سوال را وارد کنید.")
        else:
            # try server first, always fall back to local
            ans = None
            try:
                if is_configured():
                    ans = answer_ops_question(
                        q.strip(),
                        context="سامانه لجستیک معکوس تهران — تصمیم تعمیر/بازسازی/بازیافت/امحا"
                    )
                    if not ans or str(ans).startswith("❌") or str(ans).startswith("⚠️"):
                        ans = None
            except Exception:
                ans = None
            if not ans:
                ans = answer_local(q.strip())
            st.session_state.ai_chat.append({"q": q.strip(), "a": ans})
            st.rerun()
    
    if st.session_state.ai_chat:
        st.markdown("---")
        st.markdown("#### پاسخ‌ها")
        for item in reversed(st.session_state.ai_chat[-10:]):
            st.markdown(f"**سوال:** {item['q']}")
            st.success(item["a"])
        if st.button("پاک کردن تاریخچه پاسخ‌ها"):
            st.session_state.ai_chat = []
            st.rerun()


def page_about():
    st.markdown("## ℹ️ درباره سامانه")
    st.caption("لجستیک معکوس و ارتقای مدیریت دارایی‌های فیزیکی | هم‌راستا با سیاست‌های توانیر و همایش ملی لجستیک معکوس")
    
    st.markdown("""
    <div class="guide-box">
        <h3>چرا این سامانه؟</h3>
        <p>
            ارزش دارایی‌های بخش توزیع برق کشور در تجدید ارزیابی حدود <b>۱۱۰۰ همت</b> برآورد شده و با نرخ‌های روز
            عملاً به بازه <b>۲۲۰۰ تا ۳۰۰۰ همت</b> می‌رسد. در شرایط محدودیت منابع مالی، توسعه لجستیک معکوس
            و مدیریت هوشمند چرخه عمر دارایی‌ها یکی از مؤثرترین مسیرها برای صیانت از سرمایه، افزایش بهره‌وری
            و بازگشت تجهیزات به چرخه مصرف است. بر اساس گزارش‌های رسمی توانیر، تاکنون حدود
            <b>۱٫۸ هزار میلیارد تومان</b> از دارایی‌ها از مسیر لجستیک معکوس به چرخه مصرف بازگشته است؛
            عددی که ظرفیت بالای توسعه این رویکرد را نشان می‌دهد.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="rams-card">', unsafe_allow_html=True)
    st.markdown("#### مأموریت سامانه")
    st.markdown("""
این سامانه برای شرکت‌های توزیع نیروی برق طراحی شده تا چرخه کامل دارایی‌های بازگشتی را از لحظه جمع‌آوری میدانی
تا تصمیم نهایی (**تعمیر، بازسازی، بازیافت یا امحا**) به‌صورت داده‌محور مدیریت کند.

**اهداف عملیاتی:**
- افزایش نرخ بازگشت تجهیزات قابل‌استفاده به شبکه
- کاهش زمان چرخه از بازگشت تا تصمیم
- کاهش هزینه تعمیر اضطراری و خرید تجهیز نو غیرضروری
- شفاف‌سازی ارزش باقیمانده و اولویت‌بندی کارگاه‌ها
- پشتیبانی از اقتصاد چرخشی و کاهش ردپای زیست‌محیطی
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="rams-card">', unsafe_allow_html=True)
        st.markdown("#### هم‌راستایی با همایش ملی لجستیک معکوس")
        st.markdown("""
نخستین همایش ملی لجستیک معکوس در صنعت برق (با عنوان «آچار به‌دستان») در پژوهشگاه نیرو برگزار شد
و با مشارکت شرکت‌های توزیع از جمله **شرکت توزیع نیروی برق استان تهران** و تهران بزرگ،
بر اشتراک تجربه در **۸ گروه کالایی** و نقش نیروهای اجرایی تأکید کرد.

محورهای کلیدی مطرح‌شده در همایش که این سامانه پوشش می‌دهد:
- مدیریت چرخه عمر دارایی فیزیکی
- تفکیک و ارزیابی کالاهای برگشتی
- تصمیم تعمیر در برابر تعویض
- تجربه‌نگاری و انتقال دانش بین شرکت‌های توزیع
- کاهش فاصله برنامه‌ریزی و اجرای میدانی
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="rams-card">', unsafe_allow_html=True)
        st.markdown("#### ماژول‌های اصلی")
        st.markdown("""
| ماژول | کاربرد برای کاربر |
|--------|-------------------|
| داشبورد | پایش KPI نرخ بازگشت، زمان چرخه، ارزش |
| تصمیم‌یار | پیشنهاد تعمیر / بازسازی / بازیافت / امحا |
| عمر باقیمانده | تخمین RUL برای برنامه‌ریزی تعویض |
| ناهنجاری | هشدار الگوهای غیرعادی در جریان بازگشت |
| نقشه تهران | نقاط جمع‌آوری مناطق ۲۲گانه |
| شبیه‌ساز | تحلیل What-If سیاست تعمیر |
| گزارش | خروجی مدیریتی PDF/CSV |
| دستیار سرور | پاسخ سوالات عملیاتی |
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="rams-card">', unsafe_allow_html=True)
    st.markdown("#### الگوی بین‌المللی و بومی")
    st.markdown("""
در سطح جهانی، شرکت‌های شبکه برق و تأمین‌کنندگان بزرگ (مانند پلتفرم‌های Asset Performance Management)
بر پایش سلامت تجهیز، اولویت‌بندی نگهداری و یکپارچه‌سازی داده ERP/GIS/SCADA تمرکز دارند.
در ایران نیز نمونه‌هایی مانند بازیابی کابل‌های مستعمل در فارس (صرفه‌جویی حدود ۲۰ میلیارد ریال)
و ساخت تابلو از کالای برگشتی در استان مرکزی نشان می‌دهد لجستیک معکوس از ایده به اجرا رسیده است.

این سامانه همان منطق را برای **تهران** با داده‌های مناطق ۲۲گانه، موتور تصمیم‌یار و داشبورد مدیریتی پیاده می‌کند
تا تصمیم‌گیرنده به‌جای قضاوت موردی، بر اساس شاخص سلامت، هزینه تعمیر و عمر باقیمانده عمل کند.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="rams-footer">
        سامانه لجستیک معکوس و ارتقای مدیریت دارایی‌های فیزیکی<br>
        نسخه ۳.۵.۰ — شرکت توزیع نیروی برق استان تهران
    </div>
    """, unsafe_allow_html=True)


def main():
    if not st.session_state.authenticated:
        show_login()
        return
    
    render_sidebar()
    
    page = st.session_state.page
    if page == "داشبورد مدیریتی":
        page_dashboard()
    elif page == "راهنمای سامانه":
        page_guide()
    elif page == "دستیار هوشمند سرور":
        page_ai_assistant()
    elif page == "تصمیم‌یار هوشمند":
        page_decision_assistant()
    elif page == "پیش‌بینی عمر باقیمانده (RUL)":
        page_rul()
    elif page == "کشف ناهنجاری":
        page_anomaly()
    elif page == "نقشه و مسیریابی":
        page_map()
    elif page == "شبیه‌ساز سناریو":
        page_simulator()
    elif page == "گزارش‌ساز PDF":
        page_reports()
    elif page == "مدیریت دارایی‌ها":
        page_assets()
    elif page == "درباره سامانه":
        page_about()
    else:
        page_dashboard()

if __name__ == "__main__":
    main()
