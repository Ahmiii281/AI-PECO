"""
AI/ML Energy Consumption Model
Features:
- Simple Moving Average for power forecasting
- Anomaly detection using IsolationForest
- Smart recommendations
"""
from typing import List, Dict, Any, Union
from datetime import datetime
import numpy as np
from sklearn.ensemble import IsolationForest
import logging

logger = logging.getLogger(__name__)

class DataNormalizer:
    @staticmethod
    def normalize_readings(energy_readings: List[Dict]) -> List[Dict]:
        """
        Validates, handles missing fields, and sorts data by timestamp.
        """
        valid_readings = []
        for r in energy_readings:
            try:
                power = float(r.get("power", 0.0))
                if power < 0:
                    power = 0.0
                r_copy = r.copy()
                r_copy["power"] = power
                valid_readings.append(r_copy)
            except (ValueError, TypeError):
                continue
        
        # Sort by timestamp strongly typed
        def _get_time(x):
            ts = x.get("timestamp")
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    return datetime.min
            elif isinstance(ts, datetime):
                return ts
            return datetime.min
            
        return sorted(valid_readings, key=_get_time)

class AnomalyDetector:
    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination

    def detect(self, valid_readings: List[Dict]) -> Dict[str, Any]:
        """
        Runs IsolationForest for anomaly detection without simple standard deviation heuristics.
        Returns a structured JSON/dict.
        """
        if not valid_readings:
            return {
                "anomalies": [],
                "mean_power": 0.0,
                "status": "error",
                "message": "No valid data provided."
            }

        powers = [r["power"] for r in valid_readings]
        try:
            mean_power = sum(powers) / len(powers)
        except ZeroDivisionError:
            mean_power = 0.0

        if len(valid_readings) < 5:
            return {
                "anomalies": [],
                "mean_power": mean_power,
                "status": "success",
                "message": "Dataset too small for reliable anomaly detection."
            }

        # Handle zero variance or identical readings
        if max(powers) == min(powers):
            return {
                "anomalies": [],
                "mean_power": mean_power,
                "status": "success",
                "message": "Zero variance in consumption data."
            }

        try:
            # IsolationForest model
            X = np.array(powers).reshape(-1, 1)
            model = IsolationForest(contamination=self.contamination, random_state=42)
            preds = model.fit_predict(X)
            scores = model.score_samples(X) 

            anomalies = []
            for i, val in enumerate(preds):
                if val == -1 and valid_readings[i]["power"] > mean_power:
                    anomaly = valid_readings[i].copy()
                    anomaly["anomaly_score"] = float(-scores[i])
                    anomalies.append(anomaly)
            
            return {
                "anomalies": anomalies,
                "mean_power": float(mean_power),
                "status": "success",
                "message": "Detection successful"
            }
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {
                "anomalies": [],
                "mean_power": mean_power,
                "status": "error",
                "message": f"Detection failed: {str(e)}"
            }

class RecommendationEngine:
    def __init__(self, energy_price_per_unit: float):
        self.energy_price_per_unit = energy_price_per_unit

    def generate(self, anomalies: List[Dict], mean_power: float) -> Dict:
        if not anomalies:
            return {
                "message": "Energy consumption is normal. No action needed.",
                "estimated_savings": 0.0,
                "confidence": "high",
                "action": None
            }

        anomaly_powers = [a["power"] for a in anomalies if "power" in a]
        avg_anomaly_power = sum(anomaly_powers) / len(anomaly_powers) if anomaly_powers else 0.0
        
        reduction_target = avg_anomaly_power * 0.30 
        estimated_reduction_kwh = (reduction_target / 1000) * 24 
        estimated_savings = estimated_reduction_kwh * self.energy_price_per_unit

        return {
            "message": f"Anomaly detected! Peak power: {avg_anomaly_power:.0f}W. Suggest reducing runtime by 30%. Potential daily savings: PKR {estimated_savings:.2f}",
            "estimated_savings": round(estimated_savings, 2),
            "confidence": "high" if len(anomalies) > 3 else "medium",
            "action": "Reduce device runtime by 30%",
            "details": {
                "peak_power": round(avg_anomaly_power, 2),
                "mean_power": round(mean_power, 2),
                "anomaly_count": len(anomalies),
                "reduction_target": round(reduction_target, 2),
            }
        }


class EnergyModel:
    def __init__(self, energy_price_per_unit: float = 50.0, anomaly_threshold_sigma: float = 2.0):
        self.energy_price_per_unit = energy_price_per_unit
        
        # Sub-modules
        self.normalizer = DataNormalizer()
        self.detector = AnomalyDetector()
        self.recommendation_engine = RecommendationEngine(energy_price_per_unit)

    def calculate_sma(self, energy_readings: List[Dict], window_size: int = 5) -> float:
        if not energy_readings:
            return 0.0

        recent = energy_readings[:window_size]
        powers = [float(r.get("power", 0)) for r in recent]
        if not powers:
            return 0.0
            
        return sum(powers) / len(powers)

    def detect_anomalies(self, energy_readings: List[Dict]) -> Dict:
        """
        Facade method for detection pipeline
        """
        valid_data = self.normalizer.normalize_readings(energy_readings)
        result = self.detector.detect(valid_data)
        
        # for backwards compatibility with parts expecting std_dev, though we removed it
        result["std_dev"] = 0.0 
        return result

    def generate_recommendation(self, anomalies: List[Dict], mean_power: float) -> Dict:
        return self.recommendation_engine.generate(anomalies, mean_power)

    def forecast_daily_cost(self, avg_power: float, usage_hours: float = 24) -> float:
        daily_kwh = (avg_power / 1000) * usage_hours
        daily_cost = daily_kwh * self.energy_price_per_unit
        return round(daily_cost, 2)
