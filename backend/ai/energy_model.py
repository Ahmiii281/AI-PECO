"""
AI/ML Energy Consumption Model
Features:
- Linear Regression for power prediction
- Anomaly detection using statistical methods
- Smart recommendations
"""
import statistics
from typing import List, Dict, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import numpy as np
from datetime import datetime, timedelta


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
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_time_features(self, timestamps: List[datetime]) -> np.ndarray:
        """
        Convert timestamps to numeric features for regression
        """
        # Convert to hours since first timestamp
        if not timestamps:
            return np.array([]).reshape(-1, 1)

        first_time = timestamps[0]
        hours = np.array([
            (t - first_time).total_seconds() / 3600
            for t in timestamps
        ])

        return hours.reshape(-1, 1)

    def train_power_model(self, energy_readings: List[Dict]) -> bool:
        """
        Train linear regression model on historical data
        
        Args:
            energy_readings: List of {timestamp, power, ...}
            
        Returns:
            True if successfully trained, False otherwise
        """
        if len(energy_readings) < 3:
            return False

        timestamps = [r["timestamp"] if isinstance(r["timestamp"], datetime) 
                     else datetime.fromisoformat(r["timestamp"]) 
                     for r in energy_readings]
        powers = np.array([r["power"] for r in energy_readings]).reshape(-1, 1)

        X = self.prepare_time_features(timestamps)

        try:
            self.model.fit(X, powers)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"Training failed: {e}")
            return False

    def predict_power(self, hours_ahead: int = 1) -> float:
        """
        Predict power consumption N hours in advance
        
        Args:
            hours_ahead: Number of hours to predict ahead
            
        Returns:
            Predicted power in watts
        """
        if not self.is_trained:
            return 0.0

        X_pred = np.array([[hours_ahead]])
        prediction = self.model.predict(X_pred)[0][0]

        return max(0.0, prediction)  # Power cannot be negative

    def detect_anomalies(self, energy_readings: List[Dict]) -> Tuple[List[Dict], float, float]:
        """
        Detect anomalous power consumption patterns
        Using statistical method: if power > mean + 2*stddev
        
        Args:
            energy_readings: List of energy readings
            
        Returns:
            (anomalies_list, mean_power, std_dev)
        """
        if len(energy_readings) < 2:
            return [], 0, 0

        powers = [r["power"] for r in energy_readings]

        try:
            mean_power = statistics.mean(powers)
            std_dev = statistics.stdev(powers)
        except (ValueError, statistics.StatisticsError):
            return [], 0, 0

        anomalies = []
        threshold = mean_power + (self.anomaly_threshold_sigma * std_dev)

        for reading in energy_readings:
            if reading["power"] > threshold:
                anomalies.append({
                    **reading,
                    "anomaly_score": (reading["power"] - mean_power) / (std_dev + 0.001),
                    "threshold": threshold
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

        # Calculate average anomaly power
        avg_anomaly_power = statistics.mean([a["power"] for a in anomalies])
        reduction_target = avg_anomaly_power * 0.30  # 30% reduction

        # Estimate savings (assuming 50 PKR per kWh, and 5-second interval readings)
        # Rough estimate: readings are every 5 seconds, so ~288 readings per day
        estimated_daily_usage = (mean_power / 1000) * 24  # kWh per day
        estimated_reduction = (reduction_target / 1000) * 24  # kWh per day if consistently reduced
        estimated_savings = estimated_reduction * self.energy_price_per_unit

        message = f"Anomaly detected in power consumption! " \
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
        Forecast daily energy cost
        
        Args:
            avg_power: Average power in watts
            usage_hours: Daily usage hours
            
        Returns:
            Estimated daily cost in PKR
        """
        daily_kwh = (avg_power / 1000) * usage_hours
        daily_cost = daily_kwh * self.energy_price_per_unit

        return round(daily_cost, 2)
