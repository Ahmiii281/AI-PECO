# ML Model Training & Setup Guide

This guide explains how to train the LSTM forecasting and NILM disaggregation models used by AI-PECO, and what happens when they are not available.

---

## Model Architecture

| Model | Type | Purpose | Fallback |
|-------|------|---------|----------|
| **LSTM Forecaster** | LSTM (60-step window) | Predicts next power value | SMA (labeled `method: sma`) |
| **NILM Disaggregator** | CNN + LSTM | Breaks total power into appliance categories | Fixed household ratios (labeled `is_estimate: true`) |
| **RL Agent** | Tabular Q-learning | Suggests energy optimizations | Always ready — no pre-training needed |

---

## Required Files

After training, the following files must exist:

```
ml/
└── models/
    └── saved_models/
        ├── lstm_energy_forecaster.keras   ← LSTM model weights
        ├── lstm_scaler.pkl                ← Feature normalizer
        ├── nilm_disaggregator.keras       ← NILM model weights
        └── nilm_scaler.pkl                ← Power normalizer
```

---

## Graceful Fallback (No Training Required)

AI-PECO works **without trained models**. When model files are absent:

- **LSTM → SMA fallback**: Uses simple moving average of the last 10 readings. Response includes `"method": "sma"` and `"is_estimate": true`.
- **NILM → Ratio estimates**: Uses typical Pakistani household ratios (HVAC 35%, Kitchen 25%, etc.). Response includes `"method": "estimated"`, `"is_estimate": true`, and all breakdown keys end in `(estimated)`.
- **Health check** (`GET /health`) shows which models are ready.

---

## Step 1: Install Dependencies

```bash
cd ml
pip install -r requirements.txt
# Or with uv:
uv pip install -r requirements.txt
```

Required packages:
- `tensorflow >= 2.12`
- `scikit-learn`
- `pandas`
- `numpy`
- `joblib`

---

## Step 2: Download Training Data

The models were trained on the [UCI Household Electric Power Consumption dataset](https://archive.ics.uci.edu/ml/datasets/individual+household+electric+power+consumption).

```bash
# Download and place in:
# ml/data/raw/household_power_consumption.txt
```

Alternatively, use your own real sensor data exported from MongoDB:
```bash
# Export from MongoDB Atlas:
mongoexport --uri "your-mongodb-url" --collection energy_data --out ml/data/raw/energy_data.csv
```

---

## Step 3: Train LSTM Forecaster

```bash
cd ml/training
python train_lstm.py
```

This will:
1. Load and preprocess the household power dataset
2. Build a 60-step LSTM model
3. Train for 50 epochs with early stopping
4. Save `lstm_energy_forecaster.keras` and `lstm_scaler.pkl` to `ml/models/saved_models/`

Expected metrics (on UCI dataset): **R² ≈ 0.91**, RMSE ≈ 0.08 kW

---

## Step 4: Train NILM Disaggregator

```bash
cd ml/training
python train_nilm.py
```

This will:
1. Load submeter readings (Sub_metering_1/2/3 + remaining power)
2. Build a CNN + LSTM disaggregation model
3. Train for 30 epochs
4. Save `nilm_disaggregator.keras` and `nilm_scaler.pkl`

Expected metrics (on UCI dataset): **R² ≈ 0.74**

---

## Step 5: Verify at Startup

When the backend starts, it logs model status:

```
=======================================================
  AI-PECO — ML Model Availability Check
=======================================================
  ✅ LSTM Forecaster    → READY (real predictions)
  ✅ NILM Disaggregator → READY (real disaggregation)
  ✅ RL Q-Agent         → ALWAYS READY (tabular, no pre-training needed)
=======================================================
```

Or when models are missing:
```
  ⚠️  LSTM Forecaster    → NOT READY (missing: lstm_model, lstm_scaler)
     Fallback: SMA (simple moving average)
     Train with: python ml/training/train_lstm.py
```

---

## Step 6: Check via API

```bash
curl http://localhost:8000/health
```

Response includes:
```json
{
  "models": {
    "lstm": { "ready": true, "method_when_unavailable": "sma" },
    "nilm": { "ready": false, "method_when_unavailable": "estimated_ratios" },
    "rl_agent": { "ready": true, "method": "tabular_q_learning" }
  }
}
```

---

## Notes for FYP Submission

- The project is **fully functional without trained models** (fallbacks are properly labeled).
- Trained model files (`.keras`, `.pkl`) should be added to the repository or mounted as a volume if you want real predictions.
- Model files are excluded from Git by `.gitignore` because they can be large (>50 MB).
- To include them in submission, use Git LFS or upload separately to the academic submission portal.
