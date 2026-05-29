"""
AI-PECO: Model Inference Module
=================================
Production-ready wrappers for the trained LSTM and NILM models.
These classes handle:
  • Loading saved Keras models and scikit-learn scalers
  • Normalizing raw input data
  • Running inference
  • Denormalizing predictions back to real units

Usage (after training):
    from ai.inference import LSTMForecaster, NILMDisaggregator

    forecaster = LSTMForecaster()
    predicted_kw = forecaster.predict(recent_readings)

    disaggregator = NILMDisaggregator()
    breakdown = disaggregator.predict(recent_power_values)
"""

import os
import numpy as np
import joblib
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_MODELS_DIR = os.path.join(os.path.dirname(_THIS_DIR), "models", "saved_models")

LSTM_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "lstm_energy_forecaster.keras")
NILM_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "nilm_disaggregator.keras")
LSTM_SCALER_PATH = os.path.join(SAVED_MODELS_DIR, "lstm_scaler.pkl")
NILM_SCALER_PATH = os.path.join(SAVED_MODELS_DIR, "nilm_scaler.pkl")

# Must match the preprocessing pipeline
SEQUENCE_LENGTH = 60

LSTM_FEATURE_COLS = [
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3",
    "remaining_power",
    "hour",
    "day_of_week",
    "month",
]

NILM_TARGET_NAMES = [
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3",
    "remaining_power",
]


_LSTM_FORECASTER_INSTANCE = None
_NILM_DISAGGREGATOR_INSTANCE = None


# ═══════════════════════════════════════════════════════════════════════════
# LSTM Forecaster
# ═══════════════════════════════════════════════════════════════════════════
class LSTMForecaster:
    """
    Wraps the trained LSTM model for single-step energy forecasting.

    Input : a list of the last 60 readings, each containing the 11 features
            used during training.
    Output: predicted Global_active_power (kW) for the next timestep.
    """

    def __init__(self, model_path: str = LSTM_MODEL_PATH, scaler_path: str = LSTM_SCALER_PATH):
        self.model = None
        self.scaler = None
        self._model_path = model_path
        self._scaler_path = scaler_path

    # ── Lazy-load (avoids TF import at module level) ──────────────────────
    def _ensure_loaded(self) -> None:
        global _LSTM_FORECASTER_INSTANCE
        
        if self.model is not None:
            return

        if _LSTM_FORECASTER_INSTANCE is not None:
            self.model = _LSTM_FORECASTER_INSTANCE.model
            self.scaler = _LSTM_FORECASTER_INSTANCE.scaler
            return

        if not os.path.isfile(self._model_path):
            raise FileNotFoundError(
                f"LSTM model not found at {self._model_path}. Run training first."
            )
        if not os.path.isfile(self._scaler_path):
            raise FileNotFoundError(
                f"LSTM scaler not found at {self._scaler_path}. Run training first."
            )

        from tensorflow import keras

        self.model = keras.models.load_model(self._model_path)
        self.scaler = joblib.load(self._scaler_path)
        _LSTM_FORECASTER_INSTANCE = self
        logger.info("LSTM forecaster loaded from %s (cached as singleton)", self._model_path)

    def predict(self, readings: List[Dict]) -> float:
        """
        Predict next-step Global_active_power.

        Parameters
        ----------
        readings : list[dict]
            At least 60 recent readings. Each dict must contain keys
            matching ``LSTM_FEATURE_COLS``.  If ``remaining_power`` is
            missing it will be computed from the other fields.

        Returns
        -------
        float
            Predicted Global_active_power in **kilowatts**.
        """
        self._ensure_loaded()

        if len(readings) < SEQUENCE_LENGTH:
            raise ValueError(
                f"Need at least {SEQUENCE_LENGTH} readings, got {len(readings)}."
            )

        # Take the most recent window
        window = readings[-SEQUENCE_LENGTH:]

        # Build feature matrix (seq_len × n_features)
        rows = []
        for r in window:
            row = []
            for col in LSTM_FEATURE_COLS:
                if col == "remaining_power" and col not in r:
                    # Compute on the fly
                    gap = r.get("Global_active_power", 0)
                    sm1 = r.get("Sub_metering_1", 0)
                    sm2 = r.get("Sub_metering_2", 0)
                    sm3 = r.get("Sub_metering_3", 0)
                    val = max(0.0, (gap * 1000.0 / 60.0) - sm1 - sm2 - sm3)
                else:
                    val = r.get(col, 0.0)
                row.append(float(val))
            rows.append(row)

        data = np.array(rows, dtype=np.float32)  # (60, 11)

        # Normalize with the saved scaler
        data_scaled = self.scaler.transform(data)

        # Reshape for model: (1, 60, 11)
        X = data_scaled.reshape(1, SEQUENCE_LENGTH, len(LSTM_FEATURE_COLS))

        # Predict (normalised)
        y_pred_scaled = self.model.predict(X, verbose=0)[0, 0]

        # Inverse-transform: we only need Global_active_power (column 0).
        # Create a dummy row filled with zeros and place prediction at col 0.
        dummy = np.zeros((1, len(LSTM_FEATURE_COLS)), dtype=np.float32)
        dummy[0, 0] = y_pred_scaled
        y_pred_real = self.scaler.inverse_transform(dummy)[0, 0]

        return float(max(0.0, y_pred_real))


# ═══════════════════════════════════════════════════════════════════════════
# NILM Disaggregator
# ═══════════════════════════════════════════════════════════════════════════
class NILMDisaggregator:
    """
    Wraps the trained CNN+LSTM NILM model for power disaggregation.

    Input : a list of the last 60 Global_active_power values (kW).
    Output: estimated power breakdown across 4 categories.
    """

    def __init__(self, model_path: str = NILM_MODEL_PATH, scaler_path: str = NILM_SCALER_PATH):
        self.model = None
        self.scaler = None
        self._model_path = model_path
        self._scaler_path = scaler_path

    def _ensure_loaded(self) -> None:
        global _NILM_DISAGGREGATOR_INSTANCE
        
        if self.model is not None:
            return

        if _NILM_DISAGGREGATOR_INSTANCE is not None:
            self.model = _NILM_DISAGGREGATOR_INSTANCE.model
            self.scaler = _NILM_DISAGGREGATOR_INSTANCE.scaler
            return

        if not os.path.isfile(self._model_path):
            raise FileNotFoundError(
                f"NILM model not found at {self._model_path}. Run training first."
            )
        if not os.path.isfile(self._scaler_path):
            raise FileNotFoundError(
                f"NILM scaler not found at {self._scaler_path}. Run training first."
            )

        from tensorflow import keras

        self.model = keras.models.load_model(self._model_path)
        self.scaler = joblib.load(self._scaler_path)
        _NILM_DISAGGREGATOR_INSTANCE = self
        logger.info("NILM disaggregator loaded from %s (cached as singleton)", self._model_path)

    def predict(self, power_values: List[float]) -> Dict[str, float]:
        """
        Disaggregate total power into per-appliance estimates.

        Parameters
        ----------
        power_values : list[float]
            Last 60 Global_active_power values in **kilowatts**.

        Returns
        -------
        dict
            Keys: Sub_metering_1, Sub_metering_2, Sub_metering_3,
                  remaining_power  — all in **watt-hours per minute**.
        """
        self._ensure_loaded()

        if len(power_values) < SEQUENCE_LENGTH:
            raise ValueError(
                f"Need at least {SEQUENCE_LENGTH} values, got {len(power_values)}."
            )

        window = power_values[-SEQUENCE_LENGTH:]
        data = np.array(window, dtype=np.float32).reshape(-1, 1)

        # Normalize using column 0 of the nilm_scaler (Global_active_power)
        # The nilm_scaler was fit on 5 columns: [GAP, SM1, SM2, SM3, remaining]
        # We only have GAP, so pad with zeros, transform, then take col 0.
        padded = np.zeros((len(data), 5), dtype=np.float32)
        padded[:, 0] = data[:, 0]
        padded_scaled = self.scaler.transform(padded)
        gap_scaled = padded_scaled[:, 0]

        X = gap_scaled.reshape(1, SEQUENCE_LENGTH, 1)

        # Predict (normalised 4-output)
        y_pred_scaled = self.model.predict(X, verbose=0)[0]  # (4,)

        # Inverse-transform: build a row with GAP=0 and targets filled
        dummy = np.zeros((1, 5), dtype=np.float32)
        dummy[0, 1:] = y_pred_scaled  # cols 1–4 are the targets
        y_real = self.scaler.inverse_transform(dummy)[0, 1:]

        result = {}
        for name, val in zip(NILM_TARGET_NAMES, y_real):
            result[name] = float(max(0.0, val))

        return result
