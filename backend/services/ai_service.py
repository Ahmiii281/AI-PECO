"""
AI-PECO: AI Service Layer
===========================
Unified service that wraps the LSTM forecaster, NILM disaggregator,
and RL agent. Provides high-level methods called by API routes.

TRANSPARENCY POLICY
-------------------
Every response includes:
  - `method`      : what algorithm was used (lstm / sma / nilm / estimated / q_learning)
  - `confidence`  : high / medium / low
  - `is_estimate` : True when falling back to heuristic/rule-based values
  - `message`     : plain-English explanation of the result

This ensures the UI can clearly label estimated vs. real AI outputs.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Central service for all AI/ML functionality."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._lstm_forecaster = None
        self._nilm_disaggregator = None
        self._lstm_available: Optional[bool] = None
        self._nilm_available: Optional[bool] = None

    # ── Lazy model loading ────────────────────────────────────────────────────

    def _get_lstm(self):
        if self._lstm_available is False:
            return None
        if self._lstm_forecaster is None:
            try:
                import sys
                import os
                if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from ml.inference.inference import LSTMForecaster
                self._lstm_forecaster = LSTMForecaster()
                self._lstm_forecaster._ensure_loaded()
                self._lstm_available = True
                logger.info("LSTM forecaster loaded successfully")
            except Exception as e:
                logger.warning("LSTM forecaster not available: %s", e)
                self._lstm_available = False
                return None
        return self._lstm_forecaster

    def _get_nilm(self):
        if self._nilm_available is False:
            return None
        if self._nilm_disaggregator is None:
            try:
                import sys
                import os
                if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from ml.inference.inference import NILMDisaggregator
                self._nilm_disaggregator = NILMDisaggregator()
                self._nilm_disaggregator._ensure_loaded()
                self._nilm_available = True
                logger.info("NILM disaggregator loaded successfully")
            except Exception as e:
                logger.warning("NILM disaggregator not available: %s", e)
                self._nilm_available = False
                return None
        return self._nilm_disaggregator

    # ── LSTM Forecast ─────────────────────────────────────────────────────────

    async def get_forecast(self, device_id: str) -> Dict[str, Any]:
        """
        Get power forecast for a device.

        Returns LSTM prediction when the model is loaded and ≥60 readings
        are available. Falls back to Simple Moving Average (SMA) otherwise.
        """
        since = datetime.utcnow() - timedelta(hours=2)
        readings = await self.db.energy_data.find(
            {"device_id": ObjectId(device_id), "timestamp": {"$gte": since}}
        ).sort("timestamp", 1).to_list(120)

        min_readings_required = 60
        min_readings_sma = 5

        if len(readings) < min_readings_sma:
            return {
                "predicted_power_kw": 0.0,
                "method": "insufficient_data",
                "confidence": "low",
                "is_estimate": True,
                "message": (
                    f"Not enough data to forecast. Need at least {min_readings_sma} readings; "
                    f"only {len(readings)} found in the last 2 hours. "
                    "Keep the system running and check back later."
                ),
            }

        forecaster = self._get_lstm()
        lstm_unavailable_reason = None

        if forecaster is not None and len(readings) >= min_readings_required:
            try:
                feature_dicts = [
                    {
                        "Global_active_power": r.get("power", 0) / 1000.0,
                        "Global_reactive_power": 0.0,
                        "Voltage": r.get("voltage", 220.0),
                        "Global_intensity": r.get("current", 0.0),
                        "Sub_metering_1": 0.0,
                        "Sub_metering_2": 0.0,
                        "Sub_metering_3": 0.0,
                        "hour": r.get("timestamp", datetime.utcnow()).hour,
                        "day_of_week": r.get("timestamp", datetime.utcnow()).weekday(),
                        "month": r.get("timestamp", datetime.utcnow()).month,
                    }
                    for r in readings
                ]
                predicted = forecaster.predict(feature_dicts)
                return {
                    "predicted_power_kw": round(predicted, 4),
                    "method": "lstm",
                    "confidence": "high",
                    "is_estimate": False,
                    "message": (
                        f"LSTM model predicts next power: {predicted:.4f} kW "
                        f"(based on {len(readings)} readings, R²≈0.91 on training data)."
                    ),
                }
            except Exception as e:
                logger.warning("LSTM prediction failed, falling back to SMA: %s", e)
                lstm_unavailable_reason = f"LSTM runtime error: {e}"
        else:
            if forecaster is None:
                lstm_unavailable_reason = (
                    "LSTM model files not found. "
                    "Run ml/training/train_lstm.py to train the model, "
                    "then restart the server."
                )
            else:
                lstm_unavailable_reason = (
                    f"Insufficient readings for LSTM (need ≥{min_readings_required}, "
                    f"have {len(readings)}). Using SMA fallback."
                )

        # Fallback: Simple Moving Average over the last 10 readings
        powers = [r.get("power", 0) for r in readings[-10:]]
        avg = sum(powers) / len(powers) if powers else 0
        return {
            "predicted_power_kw": round(avg / 1000.0, 4),
            "method": "sma",
            "confidence": "medium",
            "is_estimate": True,
            "lstm_unavailable_reason": lstm_unavailable_reason,
            "message": (
                f"SMA fallback forecast: {avg / 1000.0:.4f} kW "
                f"(average of last {len(powers)} readings). "
                "Note: this is a simple average, not an LSTM prediction."
            ),
        }

    # ── NILM Disaggregation ───────────────────────────────────────────────────

    async def get_disaggregation(self, device_id: str) -> Dict[str, Any]:
        """
        Get power breakdown by appliance category.

        Uses trained NILM (CNN+LSTM) model when available.
        Falls back to fixed household ratio estimates when model is unavailable.
        Fallback values are clearly labeled as estimates.
        """
        since = datetime.utcnow() - timedelta(hours=2)
        readings = await self.db.energy_data.find(
            {"device_id": ObjectId(device_id), "timestamp": {"$gte": since}}
        ).sort("timestamp", 1).to_list(120)

        if len(readings) < 5:
            return {
                "breakdown": {},
                "method": "insufficient_data",
                "confidence": "low",
                "is_estimate": True,
                "message": "Not enough data for disaggregation (need ≥5 readings).",
            }

        disaggregator = self._get_nilm()
        if disaggregator is not None and len(readings) >= 60:
            try:
                power_values = [r.get("power", 0) / 1000.0 for r in readings]
                breakdown = disaggregator.predict(power_values)
                return {
                    "breakdown": breakdown,
                    "method": "nilm",
                    "confidence": "high",
                    "is_estimate": False,
                    "message": (
                        "NILM model (CNN+LSTM, R²≈0.74) disaggregated appliance-level power. "
                        "Values represent watt-hours per minute."
                    ),
                }
            except Exception as e:
                logger.warning("NILM prediction failed: %s", e)

        # Fallback: typical household ratios — ALWAYS labeled as estimated
        avg_power = sum(r.get("power", 0) for r in readings[-10:]) / max(len(readings[-10:]), 1)
        nilm_reason = (
            "NILM model files not found or insufficient data (need ≥60 readings). "
            "Run ml/training/train_nilm.py to train the model."
            if disaggregator is None
            else f"Only {len(readings)} readings available (need ≥60)."
        )
        breakdown = {
            "Kitchen (estimated)": round(avg_power * 0.25, 2),
            "Laundry (estimated)": round(avg_power * 0.15, 2),
            "HVAC (estimated)": round(avg_power * 0.35, 2),
            "Other (estimated)": round(avg_power * 0.25, 2),
        }
        return {
            "breakdown": breakdown,
            "method": "estimated",
            "confidence": "low",
            "is_estimate": True,
            "nilm_unavailable_reason": nilm_reason,
            "message": (
                "⚠️ Estimated breakdown based on typical Pakistani household ratios "
                "(HVAC 35%, Kitchen 25%, Other 25%, Laundry 15%). "
                "These are NOT measured values. Train the NILM model for real disaggregation."
            ),
        }

    # ── RL Suggestion ─────────────────────────────────────────────────────────

    async def get_rl_suggestion(self, user_id: str) -> Dict[str, Any]:
        """
        Get the RL agent's optimization suggestion for the current state.
        Uses tabular Q-learning, pre-seeded with domain knowledge.
        """
        from ml.inference.rl_agent import get_rl_agent
        agent = get_rl_agent()

        now = datetime.utcnow()
        hour = now.hour

        devices = await self.db.devices.find(
            {"user_id": ObjectId(user_id)}
        ).to_list(100)
        device_ids = [d["_id"] for d in devices]
        devices_on = sum(1 for d in devices if d.get("is_relay_on", False))

        since = now - timedelta(minutes=30)
        recent_data = await self.db.energy_data.find(
            {"device_id": {"$in": device_ids}, "timestamp": {"$gte": since}}
        ).sort("timestamp", -1).to_list(50)

        sample = recent_data[:5] if recent_data else []
        total_power = sum(r.get("power", 0) for r in sample) / max(len(sample), 1)
        avg_temp = sum(r.get("temperature", 25) for r in sample) / max(len(sample), 1)

        suggestion = agent.get_suggestion(
            hour=hour,
            power_watts=total_power,
            temperature=avg_temp,
            devices_on=devices_on,
        )

        suggestion["current_state_summary"] = {
            "hour": hour,
            "total_power_watts": round(total_power, 2),
            "avg_temperature": round(avg_temp, 1),
            "devices_on": devices_on,
            "total_devices": len(devices),
        }
        suggestion["method"] = "tabular_q_learning"
        suggestion["transparency"] = (
            "Rule-seeded Q-table with online updates from live sensor data. "
            "Confidence improves as the agent observes more of your usage patterns."
        )

        return suggestion

    # ── Smart Analysis ────────────────────────────────────────────────────────

    async def process_smart_query(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Process a natural language energy query and return a data-driven response.

        This is a RULE-BASED / DATA-BASED assistant, not a generative LLM.
        Responses are deterministic and grounded in actual sensor readings.
        The AI label refers to the RL-based optimization suggestions embedded
        in responses, not to language generation.
        """
        now = datetime.utcnow()
        query_lower = query.lower().strip()
        tariff = settings.ELECTRICITY_TARIFF_PKR

        # ── Gather context ────────────────────────────────────────────────────
        devices = await self.db.devices.find(
            {"user_id": ObjectId(user_id)}
        ).to_list(100)
        device_ids = [d["_id"] for d in devices]

        since_24h = now - timedelta(hours=24)
        recent_data = await self.db.energy_data.find(
            {"device_id": {"$in": device_ids}, "timestamp": {"$gte": since_24h}}
        ).sort("timestamp", -1).to_list(500)

        if recent_data:
            powers = [r.get("power", 0) for r in recent_data]
            temps = [r.get("temperature", 0) for r in recent_data if r.get("temperature")]
            humidities = [r.get("humidity", 0) for r in recent_data if r.get("humidity")]
            # kWh estimate: readings every ~5 min → multiply by 5/60
            total_kwh = sum(powers) / 1000.0 * (5 / 60)
            avg_power = sum(powers) / len(powers)
            max_power = max(powers)
            min_power = min(powers)
            avg_temp = sum(temps) / len(temps) if temps else 25.0
            avg_humidity = sum(humidities) / len(humidities) if humidities else 50.0
            hourly_power: Dict[int, list] = {}
            for r in recent_data:
                ts = r.get("timestamp", now)
                h = ts.hour if hasattr(ts, "hour") else 0
                hourly_power.setdefault(h, []).append(r.get("power", 0))
            peak_hour = max(hourly_power, key=lambda h: sum(hourly_power[h]) / len(hourly_power[h])) if hourly_power else 14
            low_hour = min(hourly_power, key=lambda h: sum(hourly_power[h]) / len(hourly_power[h])) if hourly_power else 3
        else:
            total_kwh = avg_power = max_power = min_power = 0.0
            avg_temp = 25.0
            avg_humidity = 50.0
            peak_hour, low_hour = 14, 3

        devices_on = sum(1 for d in devices if d.get("is_relay_on", False))
        devices_off = len(devices) - devices_on
        rl_suggestion = await self.get_rl_suggestion(user_id)

        # ── Intent routing ────────────────────────────────────────────────────

        if query_lower in ("hi", "hello", "hey", "help", "start", "what can you do"):
            response = (
                "### Welcome to AI-PECO Smart Assistant\n"
                "I analyze your real energy data and provide data-driven recommendations.\n\n"
                "**Note:** I am a rule-based assistant grounded in your sensor readings — "
                "not a generative AI. My suggestions come from actual consumption patterns "
                "and an RL agent trained on your data.\n\n"
                "Try asking:\n"
                "- \"What is my current power usage?\"\n"
                "- \"How can I reduce my bill?\"\n"
                "- \"Show me device status\"\n"
                "- \"What are my peak hours?\"\n"
                "- \"Give me a forecast\"\n"
                "- \"Any alerts or anomalies?\"\n"
                f"\n*Monitoring {len(devices)} device(s) with {len(recent_data)} readings in the last 24h.*"
            )

        elif any(kw in query_lower for kw in ("cost", "bill", "price", "expensive", "money", "spend", "charge", "tariff", "rate")):
            daily_cost = total_kwh * tariff
            monthly_est = daily_cost * 30
            response = (
                f"### 💰 Cost Analysis\n"
                f"- Estimated daily consumption: **{total_kwh:.2f} kWh**\n"
                f"- Tariff rate: **PKR {tariff:.0f}/kWh**\n"
                f"- Estimated daily cost: **PKR {daily_cost:.0f}**\n"
                f"- Projected monthly cost: **PKR {monthly_est:.0f}**\n"
                f"- Average power draw: {avg_power:.0f}W\n"
                f"- Peak power recorded: {max_power:.0f}W\n"
                f"\n### Tips to Reduce Cost\n"
                f"- Peak usage is around **{peak_hour}:00** — try shifting loads to **{low_hour}:00**\n"
                f"- {rl_suggestion['description']}\n"
                f"- Potential savings: **PKR {rl_suggestion['estimated_savings_pkr']}/month** *(RL estimate)*"
            )

        elif any(kw in query_lower for kw in ("forecast", "predict", "future", "upcoming", "next hour", "tomorrow")):
            if device_ids:
                try:
                    forecast = await self.get_forecast(str(device_ids[0]))
                    method_label = "LSTM model" if forecast["method"] == "lstm" else "SMA estimate"
                    response = (
                        f"### 📈 Energy Forecast\n"
                        f"- Predicted next power: **{forecast['predicted_power_kw']:.4f} kW**\n"
                        f"- Method: {method_label} ({'real AI model' if forecast['method'] == 'lstm' else 'statistical estimate'})\n"
                        f"- Confidence: {forecast['confidence']}\n"
                        f"- Is estimate: {'Yes' if forecast.get('is_estimate') else 'No'}\n"
                        f"\n{forecast['message']}\n"
                        f"\n### Current Baseline\n"
                        f"- Active devices: {devices_on}\n"
                        f"- Average power (24h): {avg_power:.0f}W\n"
                        f"- Peak: {peak_hour}:00 | Low: {low_hour}:00"
                    )
                except Exception:
                    response = (
                        f"### 📈 Forecast Estimate\n"
                        f"Based on 24h data: peak ~{peak_hour}:00 ({max_power:.0f}W), "
                        f"low ~{low_hour}:00 ({min_power:.0f}W), average {avg_power:.0f}W.\n"
                        f"*This is a simple pattern observation, not an LSTM prediction.*"
                    )
            else:
                response = "No devices registered yet. Add a device to get forecasts."

        elif any(kw in query_lower for kw in ("device", "appliance", "relay", "switch", "turn on", "turn off", "status")):
            device_lines = [
                f"- **{d['name']}** ({d.get('location', 'unknown')}): {'🟢 ON' if d.get('is_relay_on') else '🔴 OFF'}"
                for d in devices
            ]
            response = (
                f"### 🔌 Device Status\n"
                + ("\n".join(device_lines) if device_lines else "- No devices registered")
                + f"\n\n**Summary:** {devices_on} ON, {devices_off} OFF out of {len(devices)} total"
            )

        elif any(kw in query_lower for kw in ("save", "reduce", "optimize", "efficient", "lower", "cut", "conserve", "waste")):
            response = (
                f"### ⚡ Optimization Analysis\n"
                f"- Current avg power: **{avg_power:.0f}W**\n"
                f"- Peak power: **{max_power:.0f}W** (at {peak_hour}:00)\n"
                f"- Devices online: {devices_on}/{len(devices)}\n"
                f"\n### RL Agent Recommendation *(tabular Q-learning)*\n"
                f"- **{rl_suggestion['title']}**\n"
                f"- {rl_suggestion['description']}\n"
                f"- Estimated savings: **PKR {rl_suggestion['estimated_savings_pkr']}/month** *(estimate)*\n"
                f"- Confidence: {rl_suggestion['confidence']} ({rl_suggestion.get('episodes_trained', 0)} updates)\n"
                f"\n### Quick Wins\n"
                f"- Shift heavy loads from {peak_hour}:00 → {low_hour}:00\n"
                f"- Turn off {devices_on} idle device(s)\n"
                f"- Monitor standby power — devices draw 20-50W even when 'off'"
            )

        elif any(kw in query_lower for kw in ("temperature", "temp", "hot", "cold", "cool", "warm", "heat")):
            response = (
                f"### 🌡️ Temperature Analysis\n"
                f"- Average: **{avg_temp:.1f}°C** | Humidity: **{avg_humidity:.1f}%**\n"
                f"- Data points analyzed: {len(recent_data)}\n"
                f"\n### Energy Impact\n"
                f"- {'High temp — cooling systems likely drawing extra power.' if avg_temp > 30 else 'Moderate temp — cooling load is normal.' if avg_temp > 22 else 'Cool conditions — heating may be contributing.'}\n"
                f"- Each 1°C change in AC setpoint affects consumption by ~6-8%\n"
                f"- Optimal AC setpoint: 25-26°C with ceiling fan"
            )

        elif any(kw in query_lower for kw in ("humidity", "moisture", "humid", "dry")):
            response = (
                f"### 💧 Humidity Analysis\n"
                f"- Average: **{avg_humidity:.1f}%** | Temperature: {avg_temp:.1f}°C\n"
                f"\n### Recommendations\n"
                f"- {'High humidity — check AC drainage or use dehumidifier.' if avg_humidity > 70 else 'Comfortable humidity levels.' if avg_humidity > 40 else 'Low humidity — consider a humidifier.'}\n"
                f"- Optimal indoor range: 40-60%"
            )

        elif any(kw in query_lower for kw in ("peak", "pattern", "when", "time", "hour", "schedule", "usage time", "high usage")):
            response = (
                f"### 📊 Usage Pattern Analysis\n"
                f"- Peak hour: **{peak_hour}:00** | Low hour: **{low_hour}:00**\n"
                f"- Avg: {avg_power:.0f}W | Peak: {max_power:.0f}W | Min: {min_power:.0f}W\n"
                f"\n### Recommendations\n"
                f"- Schedule heavy appliances at {low_hour}:00\n"
                f"- Avoid stacking loads during {peak_hour}:00\n"
                f"- Use timer switches for off-peak automation"
            )

        elif any(kw in query_lower for kw in ("alert", "anomal", "warning", "unusual", "spike", "problem", "issue")):
            high_power = max_power > avg_power * 2 if avg_power > 0 else False
            response = (
                f"### ⚠️ Alert Analysis\n"
                f"- Peak: {max_power:.0f}W | Avg: {avg_power:.0f}W\n"
                f"- {'**ANOMALY DETECTED:** Peak is >2x average.' if high_power else 'No major anomalies in the last 24 hours.'}\n"
                f"\n### Monitoring\n"
                f"- Investigate any reading above {avg_power * 2:.0f}W\n"
                f"- Check the Alerts page for flagged readings"
            )

        elif any(kw in query_lower for kw in ("breakdown", "disaggregat", "which device", "how much each", "nilm", "split")):
            if device_ids:
                try:
                    disagg = await self.get_disaggregation(str(device_ids[0]))
                    is_est = disagg.get("is_estimate", True)
                    breakdown_lines = [f"- **{k}**: {v:.1f}W" for k, v in disagg.get("breakdown", {}).items()]
                    response = (
                        f"### 🔍 Power Disaggregation\n"
                        + "\n".join(breakdown_lines)
                        + f"\n- Method: {disagg.get('method', 'estimated')}\n"
                        + f"- Confidence: {disagg.get('confidence', 'low')}\n"
                        + (
                            "\n⚠️ **These are estimated values** based on typical household ratios, "
                            "not real appliance measurements. Train the NILM model for accuracy."
                            if is_est else
                            "\n✅ Values from trained NILM model."
                        )
                    )
                except Exception:
                    response = (
                        f"### 🔍 Estimated Breakdown *(not measured)*\n"
                        f"- HVAC/Cooling: ~{avg_power * 0.35:.0f}W (35%)\n"
                        f"- Kitchen: ~{avg_power * 0.25:.0f}W (25%)\n"
                        f"- Laundry: ~{avg_power * 0.15:.0f}W (15%)\n"
                        f"- Other: ~{avg_power * 0.25:.0f}W (25%)\n"
                        f"\n*These are estimates, not real measurements.*"
                    )
            else:
                response = "No devices registered. Add a device to get disaggregation."

        else:
            if now.hour < 6:
                time_context = "Early morning — most devices should be in standby."
            elif now.hour < 12:
                time_context = "Morning — moderate startup usage expected."
            elif now.hour < 17:
                time_context = "Afternoon — cooling loads are typically highest now."
            elif now.hour < 21:
                time_context = "Evening — multiple devices likely active."
            else:
                time_context = "Late evening — consider scheduling device shutdowns."

            response = (
                f"### 📋 Current System Status\n"
                f"- Devices: {devices_on} active / {len(devices)} total\n"
                f"- Power: {avg_power:.0f}W avg, {max_power:.0f}W peak\n"
                f"- Temperature: {avg_temp:.1f}°C | Humidity: {avg_humidity:.1f}%\n"
                f"- Readings (24h): {len(recent_data)}\n"
                f"\n### 🕐 Time Context\n{time_context}\n"
                f"\n### 💡 RL Suggestion *(Q-learning)*\n"
                f"- **{rl_suggestion['title']}**: {rl_suggestion['description']}\n"
                f"\n*Ask about costs, forecasts, devices, patterns, or savings.*"
            )

        return {
            "query": query,
            "response": response,
            "rl_suggestion": rl_suggestion,
            "data_points_analyzed": len(recent_data),
            "assistant_type": "rule_based_with_rl",  # transparency marker
        }

    # ── Online RL update ──────────────────────────────────────────────────────

    async def update_rl_from_reading(
        self,
        device_id: str,
        power: float,
        temperature: float,
    ) -> None:
        """
        Update the RL agent with a new sensor reading (called on every ESP32 POST).
        This is the online learning loop — the agent improves with each reading.
        """
        try:
            import sys
            import os
            if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import sys
            import os
            if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from ml.inference.rl_agent import get_rl_agent
            agent = get_rl_agent()

            device = await self.db.devices.find_one({"_id": ObjectId(device_id)})
            if not device:
                return

            user_id = device.get("user_id")
            user = await self.db.users.find_one({"_id": user_id}) if user_id else None
            energy_limit = (user.get("energy_limit", 50.0) * 1000 / 24) if user else 3000.0

            devices = (
                await self.db.devices.find({"user_id": user_id}).to_list(100)
                if user_id else []
            )
            devices_on = sum(1 for d in devices if d.get("is_relay_on", False))

            agent.online_update(
                hour=datetime.utcnow().hour,
                power_watts=power,
                temperature=temperature,
                devices_on=devices_on,
                energy_limit_watts=energy_limit,
            )
        except Exception as e:
            logger.warning("RL online update failed: %s", e)
