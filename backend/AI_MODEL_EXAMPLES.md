## AI Energy Model – Worked Examples

The `EnergyModel` in `backend/ai/energy_model.py` is responsible for:

- Detecting **anomalous power spikes** using simple statistics
- Generating **human-readable recommendations**
- Estimating **daily cost and potential savings**

Below are **two deterministic scenarios** you can show in your report or live demo.

---

### Example 1 – Normal, Stable Consumption

**Input readings (last few hours for one device):**

- 400 W, 420 W, 390 W, 410 W, 405 W

Conceptually, `EnergyModel.detect_anomalies()` will:

1. Compute the **average power** (mean) – roughly **405 W**
2. Compute the **standard deviation** – small, because readings are close together
3. Set an anomaly threshold at `mean + 2 × std_dev` – in this case, still near normal usage
4. Since all readings are under this threshold, **no anomalies** are returned

When you pass this into `generate_recommendation(anomalies, mean_power)`:

- `anomalies` is an empty list
- The model returns:
  - `message`: _"Energy consumption is normal. No action needed."_  
  - `estimated_savings`: `0`  
  - `confidence`: `"high"`  
  - `action`: `None`

This is useful to show that the AI does **not** over-react when usage is normal.

---

### Example 2 – Clear High-Usage Anomalies

**Input readings (last few hours):**

- 450 W, 460 W, 440 W, **1200 W**, **1300 W**

Conceptually, `detect_anomalies()` will:

1. Compute the average power – somewhere between normal and peaks (e.g. ~770 W)
2. Compute the standard deviation – larger now because of the two spikes
3. Any reading significantly above `mean + 2 × std_dev` is tagged as an anomaly  
   (in this example, the **1200 W** and **1300 W** points are treated as anomalies)
4. Each anomaly gets an `anomaly_score` and `threshold` attached

When these anomalies are passed into `generate_recommendation(anomalies, mean_power)`:

- The model:
  - Calculates an average anomaly power (roughly the average of 1200 W and 1300 W)
  - Targets a **30% reduction** in that peak usage
  - Converts the reduction into daily kWh and multiplies by the configured `ENERGY_PRICE_PER_UNIT`
- A typical output looks like:

```text
Message: "Anomaly detected in power consumption! Peak power: 1250W.
Suggest reducing runtime by 30%. Potential daily savings: PKR 500.00"
Estimated savings: ≈ PKR 500/day
Confidence: "high" (because there are multiple anomalies)
Action: "Reduce device runtime by 30%"
```

You can adjust the numbers in your presentation, but the **shape of the behavior** is:

- When there are frequent spikes far above normal, the model
  - Flags them as anomalies
  - Estimates how much money the user could save by cutting that peak usage

---

### How to Demonstrate in Swagger UI

1. Seed or simulate a few readings for a device via `POST /api/energy/data`
2. Call `GET /api/dashboard/recommendation/{device_id}`
3. Show:
   - For stable data, the model says **“Energy consumption is normal.”**
   - For spiky data, the model shows a **clear recommendation and estimated savings**.

