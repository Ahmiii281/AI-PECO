"""
Energy data and analytics service
"""
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
from typing import List
import statistics
from schemas import AlertResponse


class EnergyService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.energy_collection = db.energy_data
        self.alerts_collection = db.alerts
        self.recommendations_collection = db.recommendations

    async def save_energy_data(self, device_id: str, energy_data: dict) -> dict:
        """
        Save energy reading from ESP32 with deterministic calculation
        """
        # 1. Deterministic power calculation based on state
        device = await self.db.devices.find_one({"_id": ObjectId(device_id)})
        is_relay_on = device.get("is_relay_on", False) if device else False
        
        voltage = 220.0
        pf = 0.9
        relay_current = 0.8 if is_relay_on else 0.0
        calculated_power = voltage * relay_current * pf
        
        temp = energy_data.get("temperature", 0.0)
        humidity = energy_data.get("humidity", 0.0)
        
        doc = {
            "device_id": ObjectId(device_id),
            "current": relay_current,
            "voltage": voltage,
            "power": calculated_power,
            "temperature": temp,
            "humidity": humidity,
            "is_anomaly": False,
            "timestamp": datetime.utcnow(),
        }

        result = await self.energy_collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        # 2. Priority Logic / Automation based on User's devices
        if device and "user_id" in device:
            user_id = device["user_id"]
            
            # High Temperature -> Trigger Cooling
            if temp > 35.0:
                cooling_device = await self.db.devices.find_one({
                    "user_id": user_id, 
                    "name": {"$regex": "cooling|ac|fan|relay1", "$options": "i"}
                })
                if cooling_device and not cooling_device.get("is_relay_on"):
                    await self.db.devices.update_one(
                        {"_id": cooling_device["_id"]},
                        {"$set": {"is_relay_on": True, "updated_at": datetime.utcnow()}}
                    )
                    await self.create_alert(str(user_id), "High Temp: Auto-started cooling relay", "info")

            # High Humidity -> Trigger Ventilation
            if humidity > 70.0:
                vent_device = await self.db.devices.find_one({
                    "user_id": user_id, 
                    "name": {"$regex": "ventilation|exhaust|relay2", "$options": "i"}
                })
                if vent_device and not vent_device.get("is_relay_on"):
                    await self.db.devices.update_one(
                        {"_id": vent_device["_id"]},
                        {"$set": {"is_relay_on": True, "updated_at": datetime.utcnow()}}
                    )
                    await self.create_alert(str(user_id), "High Humidity: Auto-started ventilation relay", "info")

        return doc

    async def get_device_energy_data(self, device_id: str, hours: int = 24) -> List[dict]:
        """
        Get energy data for device in last N hours
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        data = await self.energy_collection.find({
            "device_id": ObjectId(device_id),
            "timestamp": {"$gte": since}
        }).sort("timestamp", -1).to_list(500)

        return data

    async def get_dashboard_stats(self, user_id: str) -> dict:
        """
        Get aggregated dashboard statistics for user
        """
        # Get user's devices
        from ai.energy_model import EnergyModel
        devices = await self.db.devices.find(
            {"user_id": ObjectId(user_id)}
        ).to_list(100)

        device_ids = [device["_id"] for device in devices]

        # Get latest energy readings
        since = datetime.utcnow() - timedelta(hours=1)

        pipeline = [
            {
                "$match": {
                    "device_id": {"$in": device_ids},
                    "timestamp": {"$gte": since}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_power": {"$sum": "$power"},
                    "avg_temperature": {"$avg": "$temperature"},
                    "avg_humidity": {"$avg": "$humidity"},
                    "avg_current": {"$avg": "$current"},
                }
            }
        ]

        result = await self.energy_collection.aggregate(pipeline).to_list(1)

        stats = result[0] if result else {
            "total_power": 0,
            "avg_temperature": 0,
            "avg_humidity": 0,
            "avg_current": 0,
        }

        # Get alert count
        alert_count = await self.alerts_collection.count_documents({
            "user_id": ObjectId(user_id),
            "resolved": False
        })

        # Calculate SMA Forecast
        recent_data = await self.energy_collection.find({
            "device_id": {"$in": device_ids[0:1] if device_ids else []},
            "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=24)}
        }).sort("timestamp", -1).to_list(10)
        
        model = EnergyModel()
        forecasted_power = model.calculate_sma(recent_data)
        
        return {
            "total_power": stats.get("total_power", 0),
            "avg_temperature": round(stats.get("avg_temperature", 0), 2),
            "avg_humidity": round(stats.get("avg_humidity", 0), 2),
            "alert_count": alert_count,
            "device_count": len(devices),
            "forecasted_power": round(forecasted_power, 2)
        }

    async def detect_anomalies(self, device_id: str, threshold_sigma: float = 2.0):
        """
        Detect anomalies in power consumption
        """
        # Get last 24 hours of data
        since = datetime.utcnow() - timedelta(hours=24)

        data = await self.energy_collection.find({
            "device_id": ObjectId(device_id),
            "timestamp": {"$gte": since}
        }).to_list(500)

        if len(data) < 3:
            return []

        # Calculate mean and std dev of power
        powers = [d["power"] for d in data]
        mean = statistics.mean(powers)
        std_dev = statistics.stdev(powers) if len(powers) > 1 else 0

        # Detect anomalies
        anomalies = []
        threshold = mean + (threshold_sigma * std_dev)

        for reading in data:
            is_anomaly = reading["power"] > threshold
            reading["is_anomaly"] = is_anomaly

            # Update in database
            await self.energy_collection.update_one(
                {"_id": reading["_id"]},
                {"$set": {"is_anomaly": is_anomaly}}
            )

            if is_anomaly:
                anomalies.append(reading)

        return anomalies

    async def create_alert(self, user_id: str, message: str, alert_type: str = "warning"):
        """
        Create an alert for user
        """
        alert_doc = {
            "user_id": ObjectId(user_id),
            "message": message,
            "alert_type": alert_type,
            "resolved": False,
            "created_at": datetime.utcnow(),
            "resolved_at": None,
        }

        result = await self.alerts_collection.insert_one(alert_doc)
        alert_doc["_id"] = result.inserted_id

        return alert_doc

    async def get_user_alerts(self, user_id: str, resolved: bool = False) -> List[dict]:
        """
        Get alerts for user
        """
        alerts = await self.alerts_collection.find({
            "user_id": ObjectId(user_id),
            "resolved": resolved
        }).sort("created_at", -1).to_list(100)

        return alerts

    async def resolve_alert(self, alert_id: str, user_id: str) -> dict:
        """
        Mark alert as resolved
        """
        alert = await self.alerts_collection.find_one_and_update(
            {"_id": ObjectId(alert_id), "user_id": ObjectId(user_id)},
            {
                "$set": {
                    "resolved": True,
                    "resolved_at": datetime.utcnow()
                }
            },
            return_document=True
        )

        if not alert:
            raise ValueError("Alert not found")

        return alert
