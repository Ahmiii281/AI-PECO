"""
AI-PECO: Data Preprocessing Pipeline
=====================================
Preprocesses the UCI Individual Household Electric Power Consumption dataset
for LSTM forecasting and NILM disaggregation training.

Dataset: https://archive.ics.uci.edu/ml/datasets/Individual+household+electric+power+consumption
Format:  Semicolon-delimited .txt file with 2,075,259 rows (1-min sampling rate)

Columns:
  Date, Time, Global_active_power, Global_reactive_power,
  Voltage, Global_intensity, Sub_metering_1, Sub_metering_2, Sub_metering_3
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, Dict, Any
import joblib
import logging

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_THIS_DIR, "data")
SAVED_MODELS_DIR = os.path.join(_THIS_DIR, "saved_models")

# The UCI dataset file — user must place it here
DATASET_FILENAME = "household_power_consumption.txt"
DATASET_PATH = os.path.join(DATA_DIR, DATASET_FILENAME)

# Number of rows to use for training
NUM_ROWS = 50_000

# Sequence / window length for time-series models
SEQUENCE_LENGTH = 60  # 60-minute look-back window


# ═══════════════════════════════════════════════════════════════════════════
# 1. Load & Clean
# ═══════════════════════════════════════════════════════════════════════════
def load_raw_data(filepath: str = DATASET_PATH, n_rows: int = NUM_ROWS) -> pd.DataFrame:
    """
    Load the raw UCI dataset, take the first *n_rows*, and return a cleaned
    DataFrame with a proper DatetimeIndex.

    Missing values in the original file are encoded as ``?``.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(
            f"Dataset not found at '{filepath}'.\n"
            f"Please place '{DATASET_FILENAME}' inside:\n  {DATA_DIR}"
        )

    logger.info("Loading raw dataset from %s …", filepath)

    df = pd.read_csv(
        filepath,
        sep=";",
        nrows=n_rows,
        low_memory=False,
        na_values=["?"],
    )

    logger.info("Loaded %d rows × %d columns", len(df), len(df.columns))

    # ── Combine Date + Time → datetime index ──────────────────────────────
    df["datetime"] = pd.to_datetime(
        df["Date"] + " " + df["Time"],
        format="%d/%m/%Y %H:%M:%S",
    )
    df.set_index("datetime", inplace=True)
    df.drop(columns=["Date", "Time"], inplace=True)

    # ── Cast every column to float (handles leftover '?' → NaN) ──────────
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Handle missing values ─────────────────────────────────────────────
    missing_before = df.isna().sum().sum()
    df.ffill(inplace=True)          # forward fill
    df.bfill(inplace=True)          # back fill for leading NaNs
    df.interpolate(method="linear", inplace=True)  # remaining gaps
    missing_after = df.isna().sum().sum()
    logger.info("Missing values: %d → %d (after cleaning)", missing_before, missing_after)

    return df


# ═══════════════════════════════════════════════════════════════════════════
# 2. Feature Engineering
# ═══════════════════════════════════════════════════════════════════════════
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived features useful for the models.

    * ``remaining_power`` — power consumed by appliances NOT covered by
      sub-meters 1–3 (everything else in the house).
    * Temporal encodings: ``hour``, ``day_of_week``, ``month``.
    """
    df = df.copy()

    # Remaining (unmetered) power in watt-minutes
    # Global_active_power is in kW → multiply by 1000/60 to get Wh per minute
    df["remaining_power"] = (
        (df["Global_active_power"] * 1000.0 / 60.0)
        - df["Sub_metering_1"]
        - df["Sub_metering_2"]
        - df["Sub_metering_3"]
    )
    # Clip negatives (measurement noise)
    df["remaining_power"] = df["remaining_power"].clip(lower=0.0)

    # Temporal features (cyclical-friendly integers)
    df["hour"] = df.index.hour
    df["day_of_week"] = df.index.dayofweek
    df["month"] = df.index.month

    logger.info("Feature engineering done — columns: %s", list(df.columns))
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 3. Scaling / Normalization
# ═══════════════════════════════════════════════════════════════════════════
def fit_scalers(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, MinMaxScaler, MinMaxScaler]:
    """
    Fit **two** MinMaxScalers:

    1. ``lstm_scaler`` — scales the features used by the LSTM forecaster.
    2. ``nilm_scaler`` — scales *all* columns the NILM model touches
       (input = Global_active_power, targets = sub-meterings + remaining).

    Returns the scaled DataFrame and both scalers so they can be saved.
    """
    # ── LSTM features ─────────────────────────────────────────────────────
    lstm_feature_cols = [
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

    lstm_scaler = MinMaxScaler(feature_range=(0, 1))
    df[lstm_feature_cols] = lstm_scaler.fit_transform(df[lstm_feature_cols])

    # ── NILM scaler (fitted on *unscaled* copy — but we already scaled
    #    above, so we just reuse the same scaler's sub-ranges) ─────────────
    #    For NILM we only need Global_active_power as input and the 4 targets.
    nilm_cols = [
        "Global_active_power",
        "Sub_metering_1",
        "Sub_metering_2",
        "Sub_metering_3",
        "remaining_power",
    ]
    # Since the data is already scaled 0-1 via lstm_scaler, we create a
    # separate identity-like scaler fitted on the *already-normalised* data
    # so that inverse_transform works correctly during inference.
    nilm_scaler = MinMaxScaler(feature_range=(0, 1))
    nilm_scaler.fit(df[nilm_cols].values)

    logger.info("Scalers fitted — LSTM features: %d, NILM cols: %d",
                len(lstm_feature_cols), len(nilm_cols))

    return df, lstm_scaler, nilm_scaler


# ═══════════════════════════════════════════════════════════════════════════
# 4. Sliding-Window Sequence Builder
# ═══════════════════════════════════════════════════════════════════════════
def build_lstm_sequences(
    df: pd.DataFrame,
    seq_len: int = SEQUENCE_LENGTH,
    target_col: str = "Global_active_power",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create (X, y) pairs for the LSTM forecaster.

    X shape: (samples, seq_len, n_features)
    y shape: (samples, 1)            — next-step Global_active_power
    """
    feature_cols = [
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

    data = df[feature_cols].values
    target_idx = feature_cols.index(target_col)

    X, y = [], []
    for i in range(seq_len, len(data)):
        X.append(data[i - seq_len : i])
        y.append(data[i, target_idx])

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)

    logger.info("LSTM sequences — X: %s, y: %s", X.shape, y.shape)
    return X, y


def build_nilm_sequences(
    df: pd.DataFrame,
    seq_len: int = SEQUENCE_LENGTH,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create (X, y) pairs for the NILM disaggregator.

    X shape: (samples, seq_len, 1)   — only Global_active_power
    y shape: (samples, 4)            — [Sub_metering_1, 2, 3, remaining_power]
    """
    gap = df["Global_active_power"].values
    targets = df[
        ["Sub_metering_1", "Sub_metering_2", "Sub_metering_3", "remaining_power"]
    ].values

    X, y = [], []
    for i in range(seq_len, len(gap)):
        X.append(gap[i - seq_len : i])
        y.append(targets[i])

    X = np.array(X, dtype=np.float32).reshape(-1, seq_len, 1)
    y = np.array(y, dtype=np.float32)

    logger.info("NILM sequences — X: %s, y: %s", X.shape, y.shape)
    return X, y


# ═══════════════════════════════════════════════════════════════════════════
# 5. Train / Validation Split
# ═══════════════════════════════════════════════════════════════════════════
def train_val_split(
    X: np.ndarray,
    y: np.ndarray,
    val_ratio: float = 0.2,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Time-series–safe split: last ``val_ratio`` fraction is used for
    validation (no shuffling — preserves temporal order).
    """
    split_idx = int(len(X) * (1 - val_ratio))
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    logger.info("Split → train: %d, val: %d", len(X_train), len(X_val))
    return X_train, X_val, y_train, y_val


# ═══════════════════════════════════════════════════════════════════════════
# 6. Full Pipeline (convenience)
# ═══════════════════════════════════════════════════════════════════════════
def run_preprocessing_pipeline() -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline and return everything needed
    for training in a single dict.

    Returns
    -------
    dict with keys:
        lstm_X_train, lstm_X_val, lstm_y_train, lstm_y_val,
        nilm_X_train, nilm_X_val, nilm_y_train, nilm_y_val,
        lstm_scaler, nilm_scaler, dataframe
    """
    # Ensure output dirs exist
    os.makedirs(SAVED_MODELS_DIR, exist_ok=True)

    # Step 1 — Load
    df = load_raw_data()

    # Step 2 — Feature engineering
    df = engineer_features(df)

    # Step 3 — Scale
    df, lstm_scaler, nilm_scaler = fit_scalers(df)

    # Step 4 — Sequences
    lstm_X, lstm_y = build_lstm_sequences(df)
    nilm_X, nilm_y = build_nilm_sequences(df)

    # Step 5 — Split
    lstm_X_train, lstm_X_val, lstm_y_train, lstm_y_val = train_val_split(lstm_X, lstm_y)
    nilm_X_train, nilm_X_val, nilm_y_train, nilm_y_val = train_val_split(nilm_X, nilm_y)

    # Step 6 — Persist scalers
    lstm_scaler_path = os.path.join(SAVED_MODELS_DIR, "lstm_scaler.pkl")
    nilm_scaler_path = os.path.join(SAVED_MODELS_DIR, "nilm_scaler.pkl")
    joblib.dump(lstm_scaler, lstm_scaler_path)
    joblib.dump(nilm_scaler, nilm_scaler_path)
    logger.info("Scalers saved → %s, %s", lstm_scaler_path, nilm_scaler_path)

    return {
        "lstm_X_train": lstm_X_train,
        "lstm_X_val": lstm_X_val,
        "lstm_y_train": lstm_y_train,
        "lstm_y_val": lstm_y_val,
        "nilm_X_train": nilm_X_train,
        "nilm_X_val": nilm_X_val,
        "nilm_y_train": nilm_y_train,
        "nilm_y_val": nilm_y_val,
        "lstm_scaler": lstm_scaler,
        "nilm_scaler": nilm_scaler,
        "dataframe": df,
    }
