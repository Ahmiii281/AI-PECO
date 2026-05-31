"""
AI-PECO: Master Training Script
=================================
Trains both the LSTM forecasting model and the NILM disaggregation model
on the first 50,000 rows of the UCI Individual Household Electric Power
Consumption dataset.

Usage:
    cd backend
    python -m ai.train

Outputs:
    saved_models/
    ├── lstm_energy_forecaster.keras   — trained LSTM model
    ├── nilm_disaggregator.keras       — trained NILM model
    ├── lstm_scaler.pkl                — MinMaxScaler for LSTM features
    ├── nilm_scaler.pkl                — MinMaxScaler for NILM features
    └── training_plots/
        ├── lstm_loss_curve.png
        └── nilm_loss_curve.png
"""

import os
import sys
import time
import logging
import numpy as np

# ── Setup logging before anything else ────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)
logger = logging.getLogger("ai.train")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_MODELS_DIR = os.path.join(_THIS_DIR, "saved_models")
PLOTS_DIR = os.path.join(SAVED_MODELS_DIR, "training_plots")


# ═══════════════════════════════════════════════════════════════════════════
# Plotting helper
# ═══════════════════════════════════════════════════════════════════════════
def save_loss_curve(history: dict, title: str, filename: str) -> None:
    """Save a training/validation loss curve as a PNG."""
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend
    import matplotlib.pyplot as plt

    os.makedirs(PLOTS_DIR, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ── Loss ──────────────────────────────────────────────────────────────
    axes[0].plot(history["loss"], label="Train Loss", linewidth=2)
    axes[0].plot(history["val_loss"], label="Val Loss", linewidth=2)
    axes[0].set_title(f"{title} — Loss (MSE)")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("MSE")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # ── MAE ───────────────────────────────────────────────────────────────
    axes[1].plot(history["mae"], label="Train MAE", linewidth=2)
    axes[1].plot(history["val_mae"], label="Val MAE", linewidth=2)
    axes[1].set_title(f"{title} — MAE")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("MAE")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Loss curve saved → %s", path)


# ═══════════════════════════════════════════════════════════════════════════
# Evaluation helper
# ═══════════════════════════════════════════════════════════════════════════
def evaluate_model(model, X_val, y_val, model_name: str) -> dict:
    """Compute RMSE, MAE, and R² on the validation set."""
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

    y_pred = model.predict(X_val, verbose=0)

    # Handle multi-output (NILM) vs single-output (LSTM)
    if y_val.ndim == 1:
        y_val_flat = y_val
        y_pred_flat = y_pred.flatten()
    else:
        y_val_flat = y_val.flatten()
        y_pred_flat = y_pred.flatten()

    rmse = float(np.sqrt(mean_squared_error(y_val_flat, y_pred_flat)))
    mae = float(mean_absolute_error(y_val_flat, y_pred_flat))
    r2 = float(r2_score(y_val_flat, y_pred_flat))

    logger.info(
        "%s Evaluation → RMSE: %.6f | MAE: %.6f | R²: %.4f",
        model_name, rmse, mae, r2,
    )

    return {"rmse": rmse, "mae": mae, "r2": r2}


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════
def main() -> None:
    """Run the full training pipeline for LSTM + NILM."""

    total_start = time.time()

    logger.info("=" * 70)
    logger.info("  AI-PECO  •  LSTM + NILM Training Pipeline")
    logger.info("=" * 70)

    # ── 1. Preprocessing ─────────────────────────────────────────────────
    logger.info("\n▶ Step 1/4 — Preprocessing …")
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from ml.training.preprocessing import run_preprocessing_pipeline

    data = run_preprocessing_pipeline()

    lstm_X_train = data["lstm_X_train"]
    lstm_X_val = data["lstm_X_val"]
    lstm_y_train = data["lstm_y_train"]
    lstm_y_val = data["lstm_y_val"]

    nilm_X_train = data["nilm_X_train"]
    nilm_X_val = data["nilm_X_val"]
    nilm_y_train = data["nilm_y_train"]
    nilm_y_val = data["nilm_y_val"]

    logger.info(
        "LSTM data shapes — X_train: %s, X_val: %s",
        lstm_X_train.shape, lstm_X_val.shape,
    )
    logger.info(
        "NILM data shapes — X_train: %s, X_val: %s",
        nilm_X_train.shape, nilm_X_val.shape,
    )

    # ── 2. Train LSTM Forecaster ─────────────────────────────────────────
    logger.info("\n▶ Step 2/4 — Training LSTM Energy Forecaster …")
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from ml.training.lstm_model import train_lstm

    t0 = time.time()
    lstm_model, lstm_history = train_lstm(
        lstm_X_train, lstm_y_train,
        lstm_X_val, lstm_y_val,
        epochs=50,
        batch_size=64,
        patience=10,
    )
    lstm_time = time.time() - t0
    logger.info("LSTM training took %.1f seconds", lstm_time)

    # ── 3. Train NILM Disaggregator ──────────────────────────────────────
    logger.info("\n▶ Step 3/4 — Training NILM Disaggregator …")
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from ml.training.nilm_model import train_nilm

    t0 = time.time()
    nilm_model, nilm_history = train_nilm(
        nilm_X_train, nilm_y_train,
        nilm_X_val, nilm_y_val,
        epochs=50,
        batch_size=64,
        patience=10,
    )
    nilm_time = time.time() - t0
    logger.info("NILM training took %.1f seconds", nilm_time)

    # ── 4. Evaluation & Plots ────────────────────────────────────────────
    logger.info("\n▶ Step 4/4 — Evaluation & Saving Plots …")

    lstm_metrics = evaluate_model(lstm_model, lstm_X_val, lstm_y_val, "LSTM")
    nilm_metrics = evaluate_model(nilm_model, nilm_X_val, nilm_y_val, "NILM")

    save_loss_curve(lstm_history, "LSTM Forecaster", "lstm_loss_curve.png")
    save_loss_curve(nilm_history, "NILM Disaggregator", "nilm_loss_curve.png")

    # ── Summary ──────────────────────────────────────────────────────────
    total_time = time.time() - total_start

    logger.info("\n" + "=" * 70)
    logger.info("  TRAINING COMPLETE")
    logger.info("=" * 70)
    logger.info("  LSTM Forecaster:")
    logger.info("    • RMSE : %.6f", lstm_metrics["rmse"])
    logger.info("    • MAE  : %.6f", lstm_metrics["mae"])
    logger.info("    • R²   : %.4f", lstm_metrics["r2"])
    logger.info("    • Time : %.1fs", lstm_time)
    logger.info("  NILM Disaggregator:")
    logger.info("    • RMSE : %.6f", nilm_metrics["rmse"])
    logger.info("    • MAE  : %.6f", nilm_metrics["mae"])
    logger.info("    • R²   : %.4f", nilm_metrics["r2"])
    logger.info("    • Time : %.1fs", nilm_time)
    logger.info("  Total    : %.1fs", total_time)
    logger.info("=" * 70)
    logger.info("  Saved models → %s", SAVED_MODELS_DIR)
    logger.info("  Loss plots   → %s", PLOTS_DIR)
    logger.info("=" * 70)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
