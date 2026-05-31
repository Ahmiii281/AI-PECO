"""
AI-PECO: NILM (Non-Intrusive Load Monitoring) Disaggregation Model
====================================================================
CNN + LSTM hybrid network that takes the *total* household power signal
and disaggregates it into four appliance-level components:

    1. Sub_metering_1 — Kitchen  (dishwasher, oven, microwave)
    2. Sub_metering_2 — Laundry  (washing machine, dryer, fridge, light)
    3. Sub_metering_3 — Water heater + air conditioner
    4. remaining_power — everything else

Architecture:
    Input (60 timesteps × 1 channel)
    → Conv1D(64,  k=5, ReLU) + MaxPool(2)
    → Conv1D(128, k=3, ReLU) + MaxPool(2)
    → LSTM(128)               + Dropout(0.3)
    → Dense(64, ReLU)         + Dropout(0.2)
    → Dense(4,  Sigmoid)

The Conv1D layers learn short-term consumption patterns (on/off edges,
duty cycles) while the LSTM captures longer temporal context.
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_MODELS_DIR = os.path.join(_THIS_DIR, "saved_models")
NILM_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "nilm_disaggregator.keras")

# Number of appliance-level outputs
NUM_APPLIANCES = 4


# ═══════════════════════════════════════════════════════════════════════════
# Model Builder
# ═══════════════════════════════════════════════════════════════════════════
def build_nilm_model(
    seq_len: int,
    n_input_features: int = 1,
    n_outputs: int = NUM_APPLIANCES,
    conv_filters_1: int = 64,
    conv_filters_2: int = 128,
    lstm_units: int = 128,
    dense_units: int = 64,
    dropout_cnn: float = 0.3,
    dropout_dense: float = 0.2,
    learning_rate: float = 1e-3,
) -> keras.Model:
    """
    Build and compile the CNN+LSTM NILM disaggregation model.

    Parameters
    ----------
    seq_len : int
        Input window length (default 60 minutes).
    n_input_features : int
        Channels per timestep — 1 (Global_active_power only).
    n_outputs : int
        Number of appliance targets (default 4).
    conv_filters_1 / conv_filters_2 : int
        Number of filters in the two Conv1D layers.
    lstm_units : int
        LSTM hidden units.
    dense_units : int
        Dense hidden layer units.
    dropout_cnn / dropout_dense : float
        Dropout rates after LSTM and Dense layers, respectively.
    learning_rate : float
        Initial learning rate for Adam.

    Returns
    -------
    keras.Model
    """
    model = keras.Sequential(name="NILM_Disaggregator")

    # ── CNN feature extractor ─────────────────────────────────────────────
    model.add(
        layers.Conv1D(
            conv_filters_1,
            kernel_size=5,
            activation="relu",
            padding="same",
            input_shape=(seq_len, n_input_features),
            name="conv1d_1",
        )
    )
    model.add(layers.MaxPooling1D(pool_size=2, name="maxpool_1"))

    model.add(
        layers.Conv1D(
            conv_filters_2,
            kernel_size=3,
            activation="relu",
            padding="same",
            name="conv1d_2",
        )
    )
    model.add(layers.MaxPooling1D(pool_size=2, name="maxpool_2"))

    # ── LSTM temporal encoder ─────────────────────────────────────────────
    model.add(
        layers.LSTM(
            lstm_units,
            return_sequences=False,
            name="lstm",
        )
    )
    model.add(layers.Dropout(dropout_cnn, name="dropout_lstm"))

    # ── Dense head ────────────────────────────────────────────────────────
    model.add(layers.Dense(dense_units, activation="relu", name="dense_hidden"))
    model.add(layers.Dropout(dropout_dense, name="dropout_dense"))

    # ── Output: 4 appliance power fractions (0-1 normalised) ──────────────
    model.add(layers.Dense(n_outputs, activation="sigmoid", name="output"))

    # ── Compile ───────────────────────────────────────────────────────────
    optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(
        optimizer=optimizer,
        loss="mse",
        metrics=["mae"],
    )

    logger.info("NILM model built — params: %s", f"{model.count_params():,}")
    return model


# ═══════════════════════════════════════════════════════════════════════════
# Training
# ═══════════════════════════════════════════════════════════════════════════
def train_nilm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 50,
    batch_size: int = 64,
    patience: int = 10,
) -> Tuple[keras.Model, Dict[str, Any]]:
    """
    Train the NILM disaggregation model.

    Parameters
    ----------
    X_train, y_train : np.ndarray
        Training sequences (total power) and targets (4 appliances).
    X_val, y_val : np.ndarray
        Validation data.
    epochs : int
        Maximum training epochs.
    batch_size : int
        Mini-batch size.
    patience : int
        Early-stopping patience.

    Returns
    -------
    (model, history_dict)
    """
    seq_len = X_train.shape[1]
    n_input_features = X_train.shape[2]
    n_outputs = y_train.shape[1]

    model = build_nilm_model(
        seq_len=seq_len,
        n_input_features=n_input_features,
        n_outputs=n_outputs,
    )

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
            filepath=NILM_MODEL_PATH,
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
    ]

    logger.info("Starting NILM training — %d epochs, batch=%d …", epochs, batch_size)

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
        "NILM training complete — best val_loss: %.6f",
        min(history.history["val_loss"]),
    )

    return model, history.history
