# سامانه RAMS — Reverse Asset Management System

**سامانه مدیریت هوشمند دارایی‌های بازگشتی شرکت توزیع نیروی برق**

نسخه تجاری ۳.۲.۱ | توسعه از سال ۱۴۰۱

---

## نصب و اجرا (ویندوز / لینوکس / مک)

### ۱. نصب وابستگی‌ها

```bash
cd rams_app
pip install -r requirements.txt
```

اگر `pip` کار نکرد:

```bash
python -m pip install -r requirements.txt
```

یا برای Python 3.9 مشخص:

```bash
py -3.9 -m pip install -r requirements.txt
```

### ۲. اجرای سامانه

```bash
streamlit run app.py
```

یا:

```bash
python -m streamlit run app.py
```

مرورگر به‌صورت خودکار باز می‌شود (معمولاً `http://localhost:8501`).

---

## حساب‌های آزمایشی

| کاربر     | رمز          | نقش              |
|-----------|--------------|------------------|
| admin     | rams@1404    | مدیر سیستم       |
| manager   | manager123   | مدیر بهره‌برداری |
| expert    | expert123    | کارشناس فنی      |
| warehouse | wh123        | اپراتور انبار    |

---

## رفع خطاهای رایج

### خطای `ModuleNotFoundError: No module named 'folium'`
```bash
pip install folium streamlit-folium
```
نقشه بدون این کتابخانه هم با نمودار جایگزین کار می‌کند.

### خطای `No module named 'sklearn'`
```bash
pip install scikit-learn joblib
```

### خطای `No module named 'reportlab'`
```bash
pip install reportlab
```
گزارش بدون این کتابخانه به‌صورت CSV دانلود می‌شود.

### خطای encoding در ویندوز
همه فایل‌های CSV با `utf-8-sig` ذخیره شده‌اند و در کد هم با همین encoding خوانده می‌شوند.

---

## ساختار پروژه

```
rams_app/
├── app.py                 # نقطه ورود اصلی
├── run.sh
├── requirements.txt
├── README.md
├── .streamlit/config.toml
├── data/                  # داده‌ها و خروجی PDF
├── models/                # مدل‌های آموزش‌دیده
└── utils/
    ├── data_generator.py
    ├── ml_engines.py
    └── styles.py
```

---

© شرکت توزیع نیروی برق | تمامی حقوق محفوظ است
