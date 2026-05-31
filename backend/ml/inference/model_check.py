"""
AI-PECO: Model Availability Checker
=====================================
Checks whether trained ML models (LSTM, NILM) are present on disk.
Called at startup to log what AI features are available.

Usage:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from ml.inference.model_check import check_models, log_model_status
    status = check_models()
    log_model_status(status)
"""

import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Default paths (same as inference.py)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR = os.path.join(os.path.dirname(_THIS_DIR), "models", "saved_models")

_REQUIRED_FILES = {
    "lstm_model": os.path.join(_MODELS_DIR, "lstm_energy_forecaster.keras"),
    "lstm_scaler": os.path.join(_MODELS_DIR, "lstm_scaler.pkl"),
    "nilm_model": os.path.join(_MODELS_DIR, "nilm_disaggregator.keras"),
    "nilm_scaler": os.path.join(_MODELS_DIR, "nilm_scaler.pkl"),
}


def check_models() -> Dict[str, bool]:
    """
    Check which ML model files are present on disk.

    Returns a dict like:
        {
            "lstm_model": True,
            "lstm_scaler": True,
            "nilm_model": False,    # ← Not trained yet
            "nilm_scaler": False,
            "lstm_ready": True,     # Both LSTM files present
            "nilm_ready": False,    # NILM incomplete
        }
    """
    status: Dict[str, bool] = {}
    for name, path in _REQUIRED_FILES.items():
        status[name] = os.path.isfile(path)

    status["lstm_ready"] = status["lstm_model"] and status["lstm_scaler"]
    status["nilm_ready"] = status["nilm_model"] and status["nilm_scaler"]
    return status


def log_model_status(status: Dict[str, bool] | None = None) -> None:
    """
    Log the model availability status at startup.
    Call this during the FastAPI lifespan startup event.
    """
    if status is None:
        status = check_models()

    lines = ["", "=" * 55, "  AI-PECO — ML Model Availability Check", "=" * 55]

    if status["lstm_ready"]:
        lines.append("  ✅ LSTM Forecaster    → READY (real predictions)")
    else:
        missing = [k for k in ("lstm_model", "lstm_scaler") if not status[k]]
        lines.append(f"  ⚠️  LSTM Forecaster    → NOT READY (missing: {', '.join(missing)})")
        lines.append("     Fallback: SMA (simple moving average)")
        lines.append("     Train with: python ml/training/train_lstm.py")

    if status["nilm_ready"]:
        lines.append("  ✅ NILM Disaggregator → READY (real disaggregation)")
    else:
        missing = [k for k in ("nilm_model", "nilm_scaler") if not status[k]]
        lines.append(f"  ⚠️  NILM Disaggregator → NOT READY (missing: {', '.join(missing)})")
        lines.append("     Fallback: estimated household ratios (labeled as estimates)")
        lines.append("     Train with: python ml/training/train_nilm.py")

    lines.append("  ✅ RL Q-Agent         → ALWAYS READY (tabular, no pre-training needed)")
    lines.append("=" * 55)

    for line in lines:
        logger.info(line)


def get_model_status_dict() -> Dict:
    """
    Return a JSON-serialisable status object suitable for a health check endpoint.
    """
    status = check_models()
    return {
        "lstm": {
            "ready": status["lstm_ready"],
            "method_when_unavailable": "sma",
            "confidence_when_unavailable": "medium",
        },
        "nilm": {
            "ready": status["nilm_ready"],
            "method_when_unavailable": "estimated_ratios",
            "confidence_when_unavailable": "low",
        },
        "rl_agent": {
            "ready": True,
            "method": "tabular_q_learning",
            "note": "Pre-seeded with domain knowledge; improves online with sensor data.",
        },
    }
