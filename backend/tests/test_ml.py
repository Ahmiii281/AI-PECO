import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from ml.inference.energy_model import EnergyModel
from ml.inference.inference import LSTMForecaster, NILMDisaggregator

def test_energy_model_sma():
    model = EnergyModel(energy_price_per_unit=50.0)
    readings = [
        {"power": 100.0},
        {"power": 120.0},
        {"power": 110.0},
        {"power": 130.0},
        {"power": 115.0}
    ]
    sma = model.calculate_sma(readings, window_size=5)
    assert sma == 115.0

def test_energy_model_anomaly_detection():
    model = EnergyModel(energy_price_per_unit=50.0, anomaly_threshold_sigma=1.0)
    readings = [
        {"power": 100.0},
        {"power": 102.0},
        {"power": 101.0},
        {"power": 300.0} # Anomaly
    ]
    anomalies, mean, std = model.detect_anomalies(readings)
    assert len(anomalies) == 1
    assert anomalies[0]["power"] == 300.0

def test_energy_model_generate_recommendation():
    model = EnergyModel(energy_price_per_unit=50.0)
    anomalies = [{"power": 2000.0}]
    rec = model.generate_recommendation(anomalies, mean_power=100.0)
    assert rec["estimated_savings"] > 0
    assert "Anomaly detected!" in rec["message"]

def test_ml_forecaster_not_found_raises():
    forecaster = LSTMForecaster(model_path="nonexistent.keras", scaler_path="nonexistent.pkl")
    with pytest.raises(FileNotFoundError):
        forecaster._ensure_loaded()

def test_ml_disaggregator_not_found_raises():
    disagg = NILMDisaggregator(model_path="nonexistent.keras", scaler_path="nonexistent.pkl")
    with pytest.raises(FileNotFoundError):
        disagg._ensure_loaded()
