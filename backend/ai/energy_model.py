"""
AI/ML Energy Consumption Model
Features:
- Simple Moving Average for power forecasting
- Anomaly detection using IsolationForest
- Smart recommendations
"""
import statistics
from typing import List, Dict, Tuple
from datetime import datetime
import numpy as np
from sklearn.ensemble import IsolationForest


class EnergyModel:
    def __init__(self, energy_price_per_unit: float = 50.0, anomaly_threshold_sigma: float = 2.0):
        """
        Initialize the AI Energy Model
        
        Args:
            energy_price_per_unit: PKR per kWh
            anomaly_threshold_sigma: Standard deviations for anomaly detection
        """
        self.energy_price_per_unit = energy_price_per_unit
        self.anomaly_threshold_sigma = anomaly_threshold_sigma

    def calculate_sma(self, energy_readings: List[Dict], window_size: int = 5) -> float:
        """
        Calculate Simple Moving Average (SMA) of power consumption.
        
        Args:
            energy_readings: List of energy readings
            window_size: Number of recent readings to average
            
        Returns:
            Forecasted power in watts
        """
        if not energy_readings:
            return 0.0

        # Take the most recent `window_size` readings
        recent_readings = energy_readings[:window_size]
        powers = [r["power"] for r in recent_readings]
        
        if not powers:
            return 0.0
            
        return sum(powers) / len(powers)

    def detect_anomalies(self, energy_readings: List[Dict]) -> Tuple[List[Dict], float, float]:
        """
        Detect anomalous power consumption patterns using IsolationForest.
        
        Args:
            energy_readings: List of energy readings
            
        Returns:
            (anomalies_list, mean_power, std_dev)
        """
        if not energy_readings or len(energy_readings) < 2:
            return [], 0.0, 0.0

        # Sort readings by timestamp if available
        if all("timestamp" in r for r in energy_readings):
            energy_readings = sorted(
                energy_readings, 
                key=lambda x: datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00")) 
                if isinstance(x["timestamp"], str) else x["timestamp"]
            )

        powers = [r["power"] for r in energy_readings]

        # Calculate basic stats
        try:
            mean_power = statistics.mean(powers)
            std_dev = statistics.stdev(powers) if len(powers) > 1 else 0.0
        except (ValueError, statistics.StatisticsError):
            return [], 0.0, 0.0

        # If all powers are the same, or very small variance, no anomalies
        if std_dev < 1e-5:
            return [], mean_power, std_dev

        anomalies = []
        
        # Prepare data for IsolationForest
        X = np.array(powers).reshape(-1, 1)
        
        # Initialize and fit the model
        model = IsolationForest(contamination=0.1, random_state=42)
        preds = model.fit_predict(X)
        scores = model.decision_function(X) # lower score -> more anomalous

        for i, reading in enumerate(energy_readings):
            if preds[i] == -1 and reading["power"] > mean_power:
                anomalies.append({
                    **reading,
                    "anomaly_score": float(abs(scores[i])),
                    "threshold": mean_power + self.anomaly_threshold_sigma * std_dev
                })

        return anomalies, mean_power, std_dev

    def generate_recommendation(self, anomalies: List[Dict], mean_power: float) -> Dict:
        """
        Generate smart recommendations based on anomalies
        
        Args:
            anomalies: List of detected anomalies
            mean_power: Average power consumption
            
        Returns:
            Recommendation dictionary
        """
        if not anomalies:
            return {
                "message": "Energy consumption is normal. No action needed.",
                "estimated_savings": 0,
                "confidence": "high",
                "action": None
            }

        avg_anomaly_power = statistics.mean([a["power"] for a in anomalies])
        reduction_target = avg_anomaly_power * 0.30 

        estimated_reduction = (reduction_target / 1000) * 24 
        estimated_savings = estimated_reduction * self.energy_price_per_unit

        message = f"Anomaly detected! " \
                 f"Peak power: {avg_anomaly_power:.0f}W. " \
                 f"Suggest reducing runtime by 30%. " \
                 f"Potential daily savings: PKR {estimated_savings:.2f}"

        return {
            "message": message,
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

    def forecast_daily_cost(self, avg_power: float, usage_hours: float = 24) -> float:
        """
        Forecast daily energy cost based on SMA / Avg Power
        """
        daily_kwh = (avg_power / 1000) * usage_hours
        daily_cost = daily_kwh * self.energy_price_per_unit

        return round(daily_cost, 2)
