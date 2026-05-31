"""
AI-PECO: LSTM Energy Forecasting Model
========================================
Two-layer LSTM network for next-step household power consumption forecasting.

Architecture:
    Input (60 timesteps × 11 features)
    → LSTM(128, return_sequences=True) + Dropout(0.2)
    → LSTM(64)                         + Dropout(0.2)
    → Dense(32, ReLU)
    → Dense(1, Linear)   →  predicted Global_active_power at t+1

Trained on the first 50 000 rows of the UCI Individual Household
Electric Power Consumption dataset.
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_MODELS_DIR = os.path.join(_THIS_DIR, "saved_models")
LSTM_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "lstm_energy_forecaster.keras")


# ═══════════════════════════════════════════════════════════════════════════
# Model Builder
# ═══════════════════════════════════════════════════════════════════════════
def build_lstm_model(
    seq_len: int,
    n_features: int,
    lstm_units_1: int = 128,
    lstm_units_2: int = 64,
    dense_units: int = 32,
    dropout_rate: float = 0.2,
    learning_rate: float = 1e-3,
) -> keras.Model:
    """
    Build and compile the LSTM forecasting model.

    Parameters
    ----------
    seq_len : int
        Number of timesteps in each input window (default 60).
    n_features : int
        Number of input features per timestep (default 11).
    lstm_units_1 : int
        Units in the first LSTM layer.
    lstm_units_2 : int
        Units in the second LSTM layer.
    dense_units : int
        Units in the fully-connected hidden layer.
    dropout_rate : float
        Dropout probability after each LSTM layer.
    learning_rate : float
        Initial learning rate for the Adam optimizer.

    Returns
    -------
    keras.Model
        Compiled Keras model ready for training.
    """
    model = keras.Sequential(name="LSTM_Energy_Forecaster")

    # ── First LSTM layer (returns full sequence) ──────────────────────────
    model.add(
        layers.LSTM(
            lstm_units_1,
            return_sequences=True,
            input_shape=(seq_len, n_features),
            name="lstm_1",
        )
    )
    model.add(layers.Dropout(dropout_rate, name="dropout_1"))

    # ── Second LSTM layer (returns last hidden state only) ────────────────
    model.add(
        layers.LSTM(
            lstm_units_2,
            return_sequences=False,
            name="lstm_2",
        )
    )
    model.add(layers.Dropout(dropout_rate, name="dropout_2"))

    # ── Dense head ────────────────────────────────────────────────────────
    model.add(layers.Dense(dense_units, activation="relu", name="dense_hidden"))
    model.add(layers.Dense(1, activation="linear", name="output"))

    # ── Compile ───────────────────────────────────────────────────────────
    optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(
        optimizer=optimizer,
        loss="mse",
        metrics=["mae"],
    )

    logger.info("LSTM model built — params: %s", f"{model.count_params():,}")
    return model


# ═══════════════════════════════════════════════════════════════════════════
# Training
# ═══════════════════════════════════════════════════════════════════════════
def train_lstm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 50,
    batch_size: int = 64,
    patience: int = 10,
) -> Tuple[keras.Model, Dict[str, Any]]:
    """
    Train the LSTM forecaster with early stopping and learning-rate
    reduction on plateau.

    Parameters
    ----------
    X_train, y_train : np.ndarray
        Training sequences and targets.
    X_val, y_val : np.ndarray
        Validation sequences and targets.
    epochs : int
        Maximum number of training epochs.
    batch_size : int
        Mini-batch size.
    patience : int
        Early-stopping patience (epochs without val-loss improvement).

    Returns
    -------
    (model, history_dict)
    """
    seq_len, n_features = X_train.shape[1], X_train.shape[2]
    model = build_lstm_model(seq_len=seq_len, n_features=n_features)

    model.summary(print_fn=logger.info)

    # ── Callbacks ─────────────────────────────────────────────────────────
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

    cb_list = [
        callbacks.EarlyStopping(
            monitor="val_loss",
            patience=patience,
            restore_best_weights=True,
            verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1,
        ),
        callbacks.ModelCheckpoint(
            filepath=LSTM_MODEL_PATH,
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
    ]

    logger.info("Starting LSTM training — %d epochs, batch=%d …", epochs, batch_size)

    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=cb_list,
        verbose=1,
    )

    logger.info(
        "LSTM training complete — best val_loss: %.6f",
        min(history.history["val_loss"]),
    )

    return model, history.history
