# -*- coding: utf-8 -*-
"""
موتورهای هوش مصنوعی سامانه RAMS
شبیه‌سازی حرفه‌ای مدل‌های RUL، تصمیم‌یار، ناهنجاری و ارزش باقیمانده
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error
import joblib
import os

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models"))
os.makedirs(MODELS_DIR, exist_ok=True)


class DecisionEngine:
    """موتور تصمیم‌یار: Random Forest + منطق تجاری"""
    
    def __init__(self):
        self.model = None
        self.le_decision = LabelEncoder()
        self.feature_cols = [
            "age_years", "health_score", "repair_cost", "residual_value",
            "cost_new", "num_repairs", "load_factor_avg", "temp_max_c",
            "voltage_deviation", "switching_ops"
        ]
    
    def train(self, df: pd.DataFrame):
        mask = df["decision"].notna()
        train_df = df[mask].copy()
        if len(train_df) < 50:
            return None
        
        X = train_df[self.feature_cols].fillna(0)
        y = self.le_decision.fit_transform(train_df["decision"])
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model = RandomForestClassifier(n_estimators=120, max_depth=10, random_state=42, n_jobs=-1)
        self.model.fit(X_train, y_train)
        acc = accuracy_score(y_test, self.model.predict(X_test))
        joblib.dump({"model": self.model, "le": self.le_decision}, os.path.join(MODELS_DIR, "decision_engine.joblib"))
        return acc
    
    def predict(self, row: dict) -> tuple:
        if self.model is None:
            try:
                saved = joblib.load(os.path.join(MODELS_DIR, "decision_engine.joblib"))
                self.model = saved["model"]
                self.le_decision = saved["le"]
            except:
                return "تعمیر", 0.75
        
        features = np.array([[row.get(c, 0) for c in self.feature_cols]])
        pred = self.model.predict(features)[0]
        proba = self.model.predict_proba(features)[0].max()
        decision = self.le_decision.inverse_transform([pred])[0]
        return decision, round(float(proba), 3)
    
    def feature_importance(self) -> dict:
        if self.model is None:
            return {}
        return dict(zip(self.feature_cols, self.model.feature_importances_.round(3)))


class RULEngine:
    """موتور پیش‌بینی عمر باقیمانده (شبیه‌سازی LSTM با Gradient Boosting)"""
    
    def __init__(self):
        self.model = None
        self.feature_cols = [
            "age_years", "health_score", "num_repairs", "load_factor_avg",
            "temp_max_c", "voltage_deviation", "switching_ops", "last_maintenance_days"
        ]
    
    def train(self, df: pd.DataFrame):
        X = df[self.feature_cols].fillna(0)
        y = df["rul_years"].fillna(5)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
        self.model.fit(X_train, y_train)
        mae = mean_absolute_error(y_test, self.model.predict(X_test))
        joblib.dump(self.model, os.path.join(MODELS_DIR, "rul_engine.joblib"))
        return mae
    
    def predict(self, row: dict) -> float:
        if self.model is None:
            try:
                self.model = joblib.load(os.path.join(MODELS_DIR, "rul_engine.joblib"))
            except:
                return 5.0
        features = np.array([[row.get(c, 0) for c in self.feature_cols]])
        pred = self.model.predict(features)[0]
        return round(max(0.3, float(pred)), 1)


class ResidualValueEngine:
    """موتور تخمین ارزش باقیمانده"""
    
    def __init__(self):
        self.model = None
        self.feature_cols = ["age_years", "health_score", "num_repairs", "cost_new", "load_factor_avg"]
    
    def train(self, df: pd.DataFrame):
        X = df[self.feature_cols].fillna(0)
        y = df["residual_value"]
        self.model = GradientBoostingRegressor(n_estimators=80, random_state=42)
        self.model.fit(X, y)
        joblib.dump(self.model, os.path.join(MODELS_DIR, "residual_value.joblib"))
    
    def predict(self, row: dict) -> int:
        if self.model is None:
            try:
                self.model = joblib.load(os.path.join(MODELS_DIR, "residual_value.joblib"))
            except:
                return int(row.get("cost_new", 1e8) * 0.4)
        features = np.array([[row.get(c, 0) for c in self.feature_cols]])
        return int(max(0, self.model.predict(features)[0]))


class AnomalyEngine:
    """موتور کشف ناهنجاری با Isolation Forest"""
    
    def __init__(self):
        self.model = None
    
    def fit(self, df: pd.DataFrame):
        cols = ["health_score", "repair_cost", "age_years", "residual_value"]
        X = df[cols].fillna(0)
        self.model = IsolationForest(contamination=0.08, random_state=42)
        self.model.fit(X)
        joblib.dump(self.model, os.path.join(MODELS_DIR, "anomaly_engine.joblib"))
    
    def score(self, row: dict) -> float:
        if self.model is None:
            try:
                self.model = joblib.load(os.path.join(MODELS_DIR, "anomaly_engine.joblib"))
            except:
                return 0.5
        cols = ["health_score", "repair_cost", "age_years", "residual_value"]
        X = np.array([[row.get(c, 0) for c in cols]])
        # IsolationForest: -1 anomaly, 1 normal → تبدیل به امتیاز 0-1
        raw = self.model.decision_function(X)[0]
        score = 1 / (1 + np.exp(raw * 3))  # sigmoid-like
        return round(float(score), 3)


def train_all_models(assets_df: pd.DataFrame):
    """آموزش تمام موتورها و ذخیره"""
    results = {}
    
    de = DecisionEngine()
    acc = de.train(assets_df)
    results["decision_accuracy"] = acc
    
    rul = RULEngine()
    mae = rul.train(assets_df)
    results["rul_mae"] = mae
    
    rv = ResidualValueEngine()
    rv.train(assets_df)
    results["residual_trained"] = True
    
    ae = AnomalyEngine()
    ae.fit(assets_df)
    results["anomaly_trained"] = True
    
    return results, de, rul, rv, ae
