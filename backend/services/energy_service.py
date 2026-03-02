"""
Energy data and analytics service
"""
from bson import ObjectId
from motor.motor_asyncio import AsyncDatabase
from datetime import datetime, timedelta
from typing import List
import statistics
from schemas import AlertResponse


class EnergyService:
    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.energy_collection = db.energy_data
        self.alerts_collection = db.alerts
        self.recommendations_collection = db.recommendations

    async def save_energy_data(self, device_id: str, energy_data: dict) -> dict:
        """
        Save energy reading from ESP32
        """
        doc = {
            "device_id": ObjectId(device_id),
            "current": energy_data["current"],
            "voltage": energy_data["voltage"],
            "power": energy_data["power"],
            "temperature": energy_data["temperature"],
            "humidity": energy_data["humidity"],
            "is_anomaly": False,
            "timestamp": datetime.utcnow(),
        }

        result = await self.energy_collection.insert_one(doc)
        doc["_id"] = result.inserted_id

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

        return {
            "total_power": stats.get("total_power", 0),
            "avg_temperature": round(stats.get("avg_temperature", 0), 2),
            "avg_humidity": round(stats.get("avg_humidity", 0), 2),
            "alert_count": alert_count,
            "device_count": len(devices),
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
