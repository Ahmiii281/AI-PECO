"""
AI-PECO: AI Service Layer
===========================
Unified service that wraps the LSTM forecaster, NILM disaggregator,
and RL agent. Provides high-level methods called by API routes.

Handles graceful fallback when models are unavailable.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class AIService:
    """
    Central service for all AI/ML functionality.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._lstm_forecaster = None
        self._nilm_disaggregator = None
        self._lstm_available = None
        self._nilm_available = None

    # ------------------------------------------------------------------
    # Lazy model loading
    # ------------------------------------------------------------------
    def _get_lstm(self):
        if self._lstm_available is False:
            return None
        if self._lstm_forecaster is None:
            try:
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

    # ------------------------------------------------------------------
    # LSTM Forecast
    # ------------------------------------------------------------------
    async def get_forecast(self, device_id: str) -> Dict[str, Any]:
        """
        Get LSTM-based power forecast for a device.
        Falls back to SMA if LSTM is not available.
        """
        # Fetch recent readings
        since = datetime.utcnow() - timedelta(hours=2)
        readings = await self.db.energy_data.find(
            {"device_id": ObjectId(device_id), "timestamp": {"$gte": since}}
        ).sort("timestamp", 1).to_list(120)

        if len(readings) < 5:
            return {
                "predicted_power_kw": 0.0,
                "method": "insufficient_data",
                "confidence": "low",
                "message": "Not enough data for forecasting. Need at least 5 readings.",
            }

        forecaster = self._get_lstm()
        if forecaster is not None and len(readings) >= 60:
            try:
                # Build feature dicts for LSTM
                feature_dicts = []
                for r in readings:
                    feature_dicts.append({
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
                    })

                predicted = forecaster.predict(feature_dicts)
                return {
                    "predicted_power_kw": round(predicted, 4),
                    "method": "lstm",
                    "confidence": "high",
                    "message": f"LSTM model predicts next power consumption: {predicted:.4f} kW",
                }
            except Exception as e:
                logger.warning("LSTM prediction failed: %s", e)

        # Fallback: Simple Moving Average
        powers = [r.get("power", 0) for r in readings[-10:]]
        avg = sum(powers) / len(powers) if powers else 0
        return {
            "predicted_power_kw": round(avg / 1000.0, 4),
            "method": "sma",
            "confidence": "medium",
            "message": f"SMA-based forecast: {avg / 1000.0:.4f} kW (LSTM model not available or insufficient data)",
        }

    # ------------------------------------------------------------------
    # NILM Disaggregation
    # ------------------------------------------------------------------
    async def get_disaggregation(self, device_id: str) -> Dict[str, Any]:
        """
        Get NILM-based power disaggregation for a device.
        Falls back to estimated proportions if NILM is not available.
        """
        since = datetime.utcnow() - timedelta(hours=2)
        readings = await self.db.energy_data.find(
            {"device_id": ObjectId(device_id), "timestamp": {"$gte": since}}
        ).sort("timestamp", 1).to_list(120)

        if len(readings) < 5:
            return {
                "breakdown": {},
                "method": "insufficient_data",
                "message": "Not enough data for disaggregation.",
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
                    "message": "NILM model disaggregation of appliance-level power.",
                }
            except Exception as e:
                logger.warning("NILM prediction failed: %s", e)

        # Fallback: Estimated proportions
        avg_power = sum(r.get("power", 0) for r in readings[-10:]) / max(len(readings[-10:]), 1)
        breakdown = {
            "Kitchen": round(avg_power * 0.25, 2),
            "Laundry": round(avg_power * 0.15, 2),
            "HVAC": round(avg_power * 0.35, 2),
            "Other": round(avg_power * 0.25, 2),
        }
        return {
            "breakdown": breakdown,
            "method": "estimated",
            "confidence": "low",
            "message": "Estimated breakdown (NILM model not available). Based on typical household ratios.",
        }

    # ------------------------------------------------------------------
    # RL Suggestion
    # ------------------------------------------------------------------
    async def get_rl_suggestion(self, user_id: str) -> Dict[str, Any]:
        """
        Get RL agent's optimization suggestion based on current state.
        """
        from ml.inference.rl_agent import get_rl_agent
        agent = get_rl_agent()

        # Gather current system state
        now = datetime.utcnow()
        hour = now.hour

        # Get user's devices
        devices = await self.db.devices.find(
            {"user_id": ObjectId(user_id)}
        ).to_list(100)
        device_ids = [d["_id"] for d in devices]
        devices_on = sum(1 for d in devices if d.get("is_relay_on", False))

        # Get recent power data
        since = now - timedelta(minutes=30)
        recent_data = await self.db.energy_data.find(
            {"device_id": {"$in": device_ids}, "timestamp": {"$gte": since}}
        ).sort("timestamp", -1).to_list(50)

        total_power = sum(r.get("power", 0) for r in recent_data[:5]) / max(len(recent_data[:5]), 1)
        avg_temp = sum(r.get("temperature", 25) for r in recent_data[:5]) / max(len(recent_data[:5]), 1)

        # If no data at all, use defaults
        if not recent_data:
            total_power = 0
            avg_temp = 25

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

        return suggestion

    # ------------------------------------------------------------------
    # Smart Analysis (for chat and analysis component)
    # ------------------------------------------------------------------
    async def process_smart_query(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Process a natural language query about energy consumption
        using a combination of data analysis and RL suggestions.
        """
        now = datetime.utcnow()
        query_lower = query.lower().strip()

        # Gather data
        devices = await self.db.devices.find(
            {"user_id": ObjectId(user_id)}
        ).to_list(100)
        device_ids = [d["_id"] for d in devices]

        since_24h = now - timedelta(hours=24)
        recent_data = await self.db.energy_data.find(
            {"device_id": {"$in": device_ids}, "timestamp": {"$gte": since_24h}}
        ).sort("timestamp", -1).to_list(500)

        # Calculate stats
        if recent_data:
            powers = [r.get("power", 0) for r in recent_data]
            temps = [r.get("temperature", 0) for r in recent_data if r.get("temperature")]
            humidities = [r.get("humidity", 0) for r in recent_data if r.get("humidity")]
            total_kwh = sum(powers) / 1000.0 / 60.0 * 5
            avg_power = sum(powers) / len(powers)
            max_power = max(powers)
            min_power = min(powers)
            avg_temp = sum(temps) / len(temps) if temps else 25.0
            avg_humidity = sum(humidities) / len(humidities) if humidities else 50.0
            # Time-based analysis
            hourly_power = {}
            for r in recent_data:
                h = r.get("timestamp", now).hour if hasattr(r.get("timestamp", now), "hour") else 0
                hourly_power.setdefault(h, []).append(r.get("power", 0))
            peak_hour = max(hourly_power, key=lambda h: sum(hourly_power[h]) / len(hourly_power[h])) if hourly_power else 14
            low_hour = min(hourly_power, key=lambda h: sum(hourly_power[h]) / len(hourly_power[h])) if hourly_power else 3
        else:
            total_kwh = avg_power = max_power = min_power = 0
            avg_temp = 25.0
            avg_humidity = 50.0
            peak_hour = 14
            low_hour = 3

        devices_on = sum(1 for d in devices if d.get("is_relay_on", False))
        devices_off = len(devices) - devices_on

        # Get RL suggestion
        rl_suggestion = await self.get_rl_suggestion(user_id)

        # ---------------------------------------------------------------
        # Intent matching — ordered from specific to general
        # ---------------------------------------------------------------

        # GREETINGS
        if query_lower in ("hi", "hello", "hey", "help", "start", "what can you do"):
            response = (
                "### Welcome to AI-PECO Assistant\n"
                "I can analyze your energy data in real time. Try asking:\n"
                "- \"What is my current power usage?\"\n"
                "- \"How can I reduce my bill?\"\n"
                "- \"Show me device status\"\n"
                "- \"What are my peak hours?\"\n"
                "- \"Give me a forecast\"\n"
                "- \"Analyze temperature trends\"\n"
                "- \"Any alerts or anomalies?\"\n"
                f"\n*Currently monitoring {len(devices)} device(s) with {len(recent_data)} data points in the last 24h.*"
            )

        # COST / BILLING
        elif any(kw in query_lower for kw in ("cost", "bill", "price", "expensive", "money", "spend", "charge", "tariff", "rate")):
            daily_cost = total_kwh * 50
            monthly_est = daily_cost * 30
            response = (
                f"### 💰 Cost Analysis\n"
                f"- Estimated daily consumption: **{total_kwh:.2f} kWh**\n"
                f"- Estimated daily cost: **PKR {daily_cost:.0f}**\n"
                f"- Projected monthly cost: **PKR {monthly_est:.0f}**\n"
                f"- Average power draw: {avg_power:.0f}W\n"
                f"- Peak power recorded: {max_power:.0f}W\n"
                f"\n### Tips to Reduce Cost\n"
                f"- Peak usage is around **{peak_hour}:00** — try shifting loads to **{low_hour}:00**\n"
                f"- {rl_suggestion['description']}\n"
                f"- Potential savings: **PKR {rl_suggestion['estimated_savings_pkr']}/month**"
            )

        # FORECAST / PREDICTION
        elif any(kw in query_lower for kw in ("forecast", "predict", "future", "upcoming", "next hour", "tomorrow")):
            if device_ids:
                try:
                    forecast = await self.get_forecast(str(device_ids[0]))
                    response = (
                        f"### 📈 Energy Forecast\n"
                        f"- Predicted next power: **{forecast['predicted_power_kw']:.4f} kW**\n"
                        f"- Method: {forecast['method']}\n"
                        f"- Confidence: {forecast['confidence']}\n"
                        f"\n### Current Baseline\n"
                        f"- Active devices: {devices_on}\n"
                        f"- Average power (24h): {avg_power:.0f}W\n"
                        f"- Peak hour: {peak_hour}:00 | Low hour: {low_hour}:00"
                    )
                except Exception:
                    response = (
                        f"### 📈 Forecast Estimate\n"
                        f"Based on your 24h pattern, usage is typically highest around **{peak_hour}:00** "
                        f"({max_power:.0f}W) and lowest around **{low_hour}:00** ({min_power:.0f}W).\n"
                        f"- Current avg: {avg_power:.0f}W\n"
                        f"- Trend: {'stable' if abs(max_power - min_power) < 200 else 'variable'}"
                    )
            else:
                response = "No devices registered yet. Add a device first to get forecasts."

        # DEVICES / APPLIANCES
        elif any(kw in query_lower for kw in ("device", "appliance", "relay", "switch", "turn on", "turn off", "status")):
            device_lines = []
            for d in devices:
                status = "🟢 ON" if d.get("is_relay_on") else "🔴 OFF"
                device_lines.append(f"- **{d['name']}** ({d.get('location', 'unknown')}): {status}")
            device_list = "\n".join(device_lines) if device_lines else "- No devices registered"
            response = (
                f"### 🔌 Device Status\n"
                f"{device_list}\n"
                f"\n**Summary:** {devices_on} ON, {devices_off} OFF out of {len(devices)} total\n"
                f"\n*Tip: You can control devices via the relay commands on the dashboard.*"
            )

        # SAVE / REDUCE / OPTIMIZE
        elif any(kw in query_lower for kw in ("save", "reduce", "optimize", "efficient", "lower", "cut", "conserve", "waste")):
            response = (
                f"### ⚡ Optimization Analysis\n"
                f"- Current avg power: **{avg_power:.0f}W**\n"
                f"- Peak power recorded: **{max_power:.0f}W** (at {peak_hour}:00)\n"
                f"- Devices online: {devices_on} / {len(devices)}\n"
                f"\n### AI Recommendation (RL Agent)\n"
                f"- **{rl_suggestion['title']}**\n"
                f"- {rl_suggestion['description']}\n"
                f"- Estimated savings: **PKR {rl_suggestion['estimated_savings_pkr']}/month**\n"
                f"- Confidence: {rl_suggestion['confidence']}\n"
                f"\n### Quick Wins\n"
                f"- Shift heavy loads from {peak_hour}:00 to {low_hour}:00\n"
                f"- Turn off {devices_on} idle device(s) when not needed\n"
                f"- Monitor standby power — devices consume 20-50W even when 'off'"
            )

        # TEMPERATURE
        elif any(kw in query_lower for kw in ("temperature", "temp", "hot", "cold", "cool", "warm", "heat")):
            response = (
                f"### 🌡️ Temperature Analysis\n"
                f"- Current average: **{avg_temp:.1f}°C**\n"
                f"- Avg humidity: {avg_humidity:.1f}%\n"
                f"- Data points analyzed: {len(recent_data)}\n"
                f"\n### Impact on Energy\n"
                f"- {'High temperature detected — cooling systems likely drawing extra power.' if avg_temp > 30 else 'Temperature is moderate — cooling load is normal.' if avg_temp > 22 else 'Cool conditions — heating may be contributing to usage.'}\n"
                f"- Each 1°C change in AC setpoint affects consumption by ~6-8%\n"
                f"- Consider setting AC to 25-26°C with a ceiling fan for optimal comfort vs cost"
            )

        # HUMIDITY
        elif any(kw in query_lower for kw in ("humidity", "moisture", "humid", "dry")):
            response = (
                f"### 💧 Humidity Analysis\n"
                f"- Current average humidity: **{avg_humidity:.1f}%**\n"
                f"- Average temperature: {avg_temp:.1f}°C\n"
                f"\n### Recommendations\n"
                f"- {'High humidity — consider using a dehumidifier or check AC drainage.' if avg_humidity > 70 else 'Humidity levels are comfortable.' if avg_humidity > 40 else 'Low humidity — a humidifier might improve comfort.'}\n"
                f"- Optimal indoor humidity: 40-60%"
            )

        # PEAK / PATTERN / USAGE TIMES
        elif any(kw in query_lower for kw in ("peak", "pattern", "when", "time", "hour", "schedule", "usage time", "high usage")):
            response = (
                f"### 📊 Usage Pattern Analysis\n"
                f"- **Peak hour:** {peak_hour}:00 (highest consumption)\n"
                f"- **Low hour:** {low_hour}:00 (lowest consumption)\n"
                f"- Average power: {avg_power:.0f}W\n"
                f"- Peak power: {max_power:.0f}W\n"
                f"- Min power: {min_power:.0f}W\n"
                f"\n### Recommendations\n"
                f"- Schedule washing machines, dryers, and heavy appliances at {low_hour}:00\n"
                f"- Avoid running multiple high-power devices simultaneously during {peak_hour}:00\n"
                f"- Use timer switches to automate off-peak scheduling"
            )

        # DATA INTEGRATION / TECHNICAL
        elif any(kw in query_lower for kw in ("data", "integrat", "api", "connect", "esp32", "sensor", "mqtt", "technical", "architecture")):
            response = (
                f"### 🔧 Data Integration Overview\n"
                f"AI-PECO uses a multi-layer data pipeline:\n"
                f"\n**1. Data Collection Layer**\n"
                f"- ESP32 microcontrollers read PZEM-004T sensors (voltage, current, power, energy)\n"
                f"- DHT22 sensors capture temperature & humidity\n"
                f"- Data is sent via HTTP POST to `/api/energy/data`\n"
                f"\n**2. Storage & Processing**\n"
                f"- MongoDB stores time-series energy data\n"
                f"- Currently: {len(devices)} device(s), {len(recent_data)} readings (24h)\n"
                f"\n**3. AI/ML Pipeline**\n"
                f"- **LSTM** (R²=0.91): Forecasts future power consumption\n"
                f"- **NILM CNN+LSTM** (R²=0.74): Disaggregates appliance-level usage\n"
                f"- **RL Q-Learning** ({rl_suggestion['episodes_trained']} episodes): Real-time optimization\n"
                f"\n**4. Frontend**\n"
                f"- React + Vite dashboard consumes `/api/predictions/*` endpoints\n"
                f"- Real-time charts, device control, and AI recommendations"
            )

        # ALERTS / ANOMALIES
        elif any(kw in query_lower for kw in ("alert", "anomal", "warning", "unusual", "spike", "problem", "issue")):
            high_power = max_power > avg_power * 2 if avg_power > 0 else False
            response = (
                f"### ⚠️ Alert Analysis\n"
                f"- Peak power: {max_power:.0f}W (avg: {avg_power:.0f}W)\n"
                f"- {'**ANOMALY DETECTED:** Peak is >2x average — possible device malfunction or unusual load.' if high_power else 'No significant anomalies detected in the last 24 hours.'}\n"
                f"- Active devices: {devices_on}\n"
                f"\n### Monitoring Tips\n"
                f"- Set energy limits per device to get automatic alerts\n"
                f"- Power spikes above {avg_power * 2:.0f}W should be investigated\n"
                f"- Check the Alerts page for historical anomaly reports"
            )

        # COMPARISON / BENCHMARKS
        elif any(kw in query_lower for kw in ("compar", "benchmark", "average household", "normal", "typical", "vs")):
            response = (
                f"### 📊 Your Usage vs Benchmarks\n"
                f"- Your avg power: **{avg_power:.0f}W**\n"
                f"- Your daily usage: **{total_kwh:.2f} kWh**\n"
                f"- Typical Pakistan household: ~8-12 kWh/day\n"
                f"- {'Your usage is above average — consider optimization.' if total_kwh > 12 else 'Your usage is within normal range.' if total_kwh > 5 else 'Your usage is below average — efficient!'}\n"
                f"\n### By Category (estimated)\n"
                f"- HVAC/Cooling: ~35% ({avg_power * 0.35:.0f}W)\n"
                f"- Kitchen: ~25% ({avg_power * 0.25:.0f}W)\n"
                f"- Laundry: ~15% ({avg_power * 0.15:.0f}W)\n"
                f"- Other: ~25% ({avg_power * 0.25:.0f}W)"
            )

        # DISAGGREGATION / BREAKDOWN
        elif any(kw in query_lower for kw in ("breakdown", "disaggregat", "which device", "how much each", "nilm", "split")):
            if device_ids:
                try:
                    disagg = await self.get_disaggregation(str(device_ids[0]))
                    breakdown_lines = [f"- **{k}**: {v:.1f}W" for k, v in disagg.get("breakdown", {}).items()]
                    breakdown_text = "\n".join(breakdown_lines)
                    response = (
                        f"### 🔍 Power Disaggregation\n"
                        f"{breakdown_text}\n"
                        f"- Method: {disagg.get('method', 'estimated')}\n"
                        f"- Confidence: {disagg.get('confidence', 'medium')}"
                    )
                except Exception:
                    response = (
                        f"### 🔍 Estimated Breakdown\n"
                        f"- HVAC/Cooling: ~{avg_power * 0.35:.0f}W (35%)\n"
                        f"- Kitchen: ~{avg_power * 0.25:.0f}W (25%)\n"
                        f"- Laundry: ~{avg_power * 0.15:.0f}W (15%)\n"
                        f"- Other: ~{avg_power * 0.25:.0f}W (25%)\n"
                        f"\n*For accurate disaggregation, the NILM model analyzes real-time load signatures.*"
                    )
            else:
                response = "No devices registered. Add a device to get power disaggregation analysis."

        # GENERAL / CATCH-ALL — give useful summary without repeating the same thing
        else:
            # Vary the response based on time of day and current conditions
            if now.hour < 6:
                time_context = "It's early morning — most devices should be in standby. Check for any unnecessary loads."
            elif now.hour < 12:
                time_context = "Morning hours typically see moderate usage as devices start up."
            elif now.hour < 17:
                time_context = "Afternoon peak — cooling loads are usually highest now."
            elif now.hour < 21:
                time_context = "Evening hours — multiple devices likely active (lighting, cooking, entertainment)."
            else:
                time_context = "Late evening — consider scheduling device shutdowns for the night."

            response = (
                f"### 📋 Current System Status\n"
                f"- Devices: {devices_on} active / {len(devices)} total\n"
                f"- Power: {avg_power:.0f}W avg, {max_power:.0f}W peak\n"
                f"- Temperature: {avg_temp:.1f}°C | Humidity: {avg_humidity:.1f}%\n"
                f"- Data points (24h): {len(recent_data)}\n"
                f"\n### 🕐 Time Context\n"
                f"{time_context}\n"
                f"\n### 💡 Quick Suggestion\n"
                f"- **{rl_suggestion['title']}**: {rl_suggestion['description']}\n"
                f"\n*Try asking about costs, forecasts, devices, patterns, temperature, or how to save energy.*"
            )

        return {
            "query": query,
            "response": response,
            "rl_suggestion": rl_suggestion,
            "data_points_analyzed": len(recent_data),
        }

    # ------------------------------------------------------------------
    # Online RL update (called when ESP32 sends data)
    # ------------------------------------------------------------------
    async def update_rl_from_reading(
        self,
        device_id: str,
        power: float,
        temperature: float,
    ) -> None:
        """
        Update the RL agent with a new sensor reading.
        Called from the energy data ingestion route.
        """
        try:
            from ml.inference.rl_agent import get_rl_agent
            agent = get_rl_agent()

            # Get device owner's energy limit
            device = await self.db.devices.find_one({"_id": ObjectId(device_id)})
            if not device:
                return

            user_id = device.get("user_id")
            user = await self.db.users.find_one({"_id": user_id}) if user_id else None
            energy_limit = (user.get("energy_limit", 50.0) * 1000 / 24) if user else 3000.0

            # Count active devices
            devices = await self.db.devices.find(
                {"user_id": user_id}
            ).to_list(100) if user_id else []
            devices_on = sum(1 for d in devices if d.get("is_relay_on", False))

            hour = datetime.utcnow().hour

            agent.online_update(
                hour=hour,
                power_watts=power,
                temperature=temperature,
                devices_on=devices_on,
                energy_limit_watts=energy_limit,
            )
        except Exception as e:
            logger.warning("RL online update failed: %s", e)
