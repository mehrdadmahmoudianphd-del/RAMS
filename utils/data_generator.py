# -*- coding: utf-8 -*-
"""
RAMS - Reverse Asset Management System
مولد داده مصنوعی حرفه‌ای برای شبیه‌سازی دارایی‌های توزیع نیروی برق
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
try:
    import jdatetime
    HAS_JDATETIME = True
except ImportError:
    HAS_JDATETIME = False
import random
import string

np.random.seed(42)
random.seed(42)

# مناطق شرکت توزیع (نمونه استان‌های ایران)
REGIONS = {
    "تهران": {"lat": 35.6892, "lon": 51.3890, "code": "THR"},
    "اصفهان": {"lat": 32.6546, "lon": 51.6680, "code": "ISF"},
    "مشهد": {"lat": 36.2605, "lon": 59.6168, "code": "MSH"},
    "شیراز": {"lat": 29.5918, "lon": 52.5837, "code": "SHZ"},
    "تبریز": {"lat": 38.0962, "lon": 46.2738, "code": "TBZ"},
    "اهواز": {"lat": 31.3183, "lon": 48.6706, "code": "AHW"},
    "کرج": {"lat": 35.8400, "lon": 50.9391, "code": "KRJ"},
    "قم": {"lat": 34.6416, "lon": 50.8746, "code": "QOM"},
}

ASSET_TYPES = {
    "ترانسفورماتور توزیع": {"abbr": "TR", "avg_life": 25, "cost_new": 450_000_000},
    "کلید قدرت": {"abbr": "CB", "avg_life": 20, "cost_new": 180_000_000},
    "رله حفاظتی": {"abbr": "RL", "avg_life": 15, "cost_new": 45_000_000},
    "مقره": {"abbr": "IN", "avg_life": 30, "cost_new": 8_000_000},
    "کابل فشار متوسط": {"abbr": "CBM", "avg_life": 35, "cost_new": 25_000_000},
}

STATUSES = ["فعال", "بازگشتی", "در تعمیر", "بازسازی شده", "بازیافت شده", "امحا شده"]
DECISIONS = ["تعمیر", "بازسازی", "بازیافت", "امحا"]
FAULT_CODES = ["F01-حرارتی", "F02-عایق", "F03-مکانیکی", "F04-الکتریکی", "F05-رطوبت", "F06-پیری", "F00-بدون خطا"]

MANUFACTURERS = ["ایران ترانسفو", "پارس سوئیچ", "آریا رله", "فولاد مبارکه", "سیemens", "ABB", "Schneider"]


def generate_asset_id(asset_type: str, region_code: str, idx: int) -> str:
    abbr = ASSET_TYPES[asset_type]["abbr"]
    return f"{region_code}-{abbr}-{idx:05d}"


def generate_assets(n: int = 1200) -> pd.DataFrame:
    """تولید دیتاست دارایی‌های بازگشتی و فعال"""
    records = []
    for i in range(n):
        region = random.choice(list(REGIONS.keys()))
        region_info = REGIONS[region]
        asset_type = random.choices(
            list(ASSET_TYPES.keys()),
            weights=[0.45, 0.20, 0.15, 0.10, 0.10],
            k=1
        )[0]
        info = ASSET_TYPES[asset_type]
        
        install_year = random.randint(1375, 1402)  # شمسی تقریبی
        age = 1404 - install_year  # فرض سال جاری ۱۴۰۴
        status = random.choices(
            STATUSES,
            weights=[0.55, 0.18, 0.10, 0.08, 0.05, 0.04],
            k=1
        )[0]
        
        health_score = max(10, min(100, np.random.normal(75 - age * 1.8, 12)))
        residual_value_pct = max(5, min(90, 100 - age * 3.2 + np.random.normal(0, 8)))
        cost_new = info["cost_new"] * (1 + np.random.uniform(-0.15, 0.25))
        residual_value = cost_new * (residual_value_pct / 100)
        
        repair_cost = residual_value * np.random.uniform(0.15, 0.55) if status in ["بازگشتی", "در تعمیر"] else 0
        fault = random.choice(FAULT_CODES) if status in ["بازگشتی", "در تعمیر"] else "F00-بدون خطا"
        
        lat = region_info["lat"] + np.random.uniform(-0.15, 0.15)
        lon = region_info["lon"] + np.random.uniform(-0.15, 0.15)
        
        records.append({
            "asset_id": generate_asset_id(asset_type, region_info["code"], i + 1),
            "asset_type": asset_type,
            "region": region,
            "region_code": region_info["code"],
            "manufacturer": random.choice(MANUFACTURERS),
            "install_year": install_year,
            "age_years": age,
            "status": status,
            "health_score": round(health_score, 1),
            "residual_value": int(residual_value),
            "cost_new": int(cost_new),
            "repair_cost": int(repair_cost),
            "fault_code": fault,
            "num_repairs": random.randint(0, max(1, age // 3)),
            "last_maintenance_days": random.randint(10, 900),
            "load_factor_avg": round(np.random.uniform(0.4, 0.95), 2),
            "temp_max_c": round(np.random.uniform(45, 95), 1),
            "voltage_deviation": round(np.random.uniform(0.5, 8.5), 2),
            "switching_ops": random.randint(50, 2500),
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "return_date": (datetime.now() - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d") if status == "بازگشتی" else None,
            "decision": None,
            "decision_confidence": None,
            "rul_years": None,
        })
    
    df = pd.DataFrame(records)
    
    # محاسبه RUL ساده (شبیه‌سازی مدل LSTM)
    df["rul_years"] = np.clip(
        (df["health_score"] / 100) * (ASSET_TYPES[df["asset_type"].iloc[0]]["avg_life"] - df["age_years"]) 
        + np.random.normal(0, 1.5, len(df)),
        0.5, 20
    ).round(1)
    
    # تصمیم اولیه بر اساس منطق ساده (شبیه‌سازی Decision Engine)
    def decide(row):
        if row["status"] not in ["بازگشتی", "در تعمیر"]:
            return None, None
        h = row["health_score"]
        age = row["age_years"]
        repair_ratio = row["repair_cost"] / max(row["residual_value"], 1)
        if h > 70 and repair_ratio < 0.35:
            return "تعمیر", round(np.random.uniform(0.82, 0.96), 2)
        elif h > 45 and age < 18 and repair_ratio < 0.6:
            return "بازسازی", round(np.random.uniform(0.75, 0.92), 2)
        elif h > 25:
            return "بازیافت", round(np.random.uniform(0.70, 0.88), 2)
        else:
            return "امحا", round(np.random.uniform(0.78, 0.95), 2)
    
    decisions = df.apply(decide, axis=1)
    df["decision"] = [d[0] for d in decisions]
    df["decision_confidence"] = [d[1] for d in decisions]
    
    return df


def generate_kpi_history(months: int = 24) -> pd.DataFrame:
    """تولید تاریخچه KPIها برای داشبورد مدیریتی"""
    base = datetime(2024, 1, 1)
    records = []
    return_rate = 42.0
    cycle_days = 28.0
    repair_cost_idx = 100.0
    recycled_value = 1.2e9
    
    for m in range(months):
        dt = base + timedelta(days=30 * m)
        if HAS_JDATETIME:
            jdt = jdatetime.date.fromgregorian(date=dt.date())
            month_str = jdt.strftime("%Y/%m")
        else:
            month_str = dt.strftime("%Y-%m")
        return_rate = min(68, return_rate + np.random.uniform(0.3, 1.1))
        cycle_days = max(12, cycle_days - np.random.uniform(0.2, 0.8))
        repair_cost_idx = max(65, repair_cost_idx - np.random.uniform(0.4, 1.2))
        recycled_value *= (1 + np.random.uniform(0.01, 0.04))
        
        records.append({
            "month": month_str,
            "gregorian": dt.strftime("%Y-%m"),
            "return_to_grid_pct": round(return_rate, 1),
            "avg_cycle_days": round(cycle_days, 1),
            "emergency_repair_cost_idx": round(repair_cost_idx, 1),
            "recycled_value_rial": int(recycled_value),
            "assets_processed": random.randint(80, 220),
            "anomaly_alerts": random.randint(2, 18),
            "model_accuracy_pct": round(min(94, 78 + m * 0.6 + np.random.uniform(-1, 1)), 1),
        })
    return pd.DataFrame(records)


def generate_anomaly_events(n: int = 25) -> pd.DataFrame:
    """رویدادهای ناهنجاری کشف‌شده"""
    types = [
        "افزایش ناگهانی نرخ بازگشت ترانس در منطقه",
        "افزایش زمان چرخه لجستیک معکوس",
        "هزینه تعمیر بالاتر از حد آستانه",
        "کاهش غیرعادی امتیاز سلامت دسته‌ای",
        "تاخیر در تصمیم‌گیری بیش از SLA",
        "عدم تطابق موجودی انبار با سوابق",
    ]
    severities = ["بحرانی", "بالا", "متوسط", "پایین"]
    records = []
    for i in range(n):
        region = random.choice(list(REGIONS.keys()))
        records.append({
            "event_id": f"ANM-{i+1:04d}",
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 720))).strftime("%Y-%m-%d %H:%M"),
            "region": region,
            "anomaly_type": random.choice(types),
            "severity": random.choices(severities, weights=[0.15, 0.25, 0.35, 0.25])[0],
            "score": round(np.random.uniform(0.55, 0.98), 3),
            "status": random.choice(["جدید", "در حال بررسی", "حل شده", "در حال بررسی"]),
            "affected_assets": random.randint(3, 45),
        })
    return pd.DataFrame(records).sort_values("timestamp", ascending=False)


def generate_collection_points(n: int = 40) -> pd.DataFrame:
    """نقاط جمع‌آوری برای مسیریابی"""
    records = []
    for i in range(n):
        region = random.choice(list(REGIONS.keys()))
        info = REGIONS[region]
        records.append({
            "point_id": f"CP-{i+1:03d}",
            "region": region,
            "name": f"مرکز جمع‌آوری {region} - {i%5 + 1}",
            "lat": round(info["lat"] + np.random.uniform(-0.2, 0.2), 5),
            "lon": round(info["lon"] + np.random.uniform(-0.2, 0.2), 5),
            "pending_assets": random.randint(2, 25),
            "priority": random.choice(["بالا", "متوسط", "پایین"]),
            "window_start": "08:00",
            "window_end": "16:00",
        })
    return pd.DataFrame(records)


if __name__ == "__main__":
    assets = generate_assets(1200)
    assets.to_csv("/home/workdir/artifacts/rams_app/data/assets.csv", index=False, encoding="utf-8-sig")
    kpi = generate_kpi_history(24)
    kpi.to_csv("/home/workdir/artifacts/rams_app/data/kpi_history.csv", index=False, encoding="utf-8-sig")
    anomalies = generate_anomaly_events(30)
    anomalies.to_csv("/home/workdir/artifacts/rams_app/data/anomalies.csv", index=False, encoding="utf-8-sig")
    points = generate_collection_points(45)
    points.to_csv("/home/workdir/artifacts/rams_app/data/collection_points.csv", index=False, encoding="utf-8-sig")
    print("Data generated successfully.")
    print(assets.head())
    print(f"Total assets: {len(assets)}")
