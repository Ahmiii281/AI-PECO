"""
AI-PECO: Demo Data Seeder
============================
Generates realistic demo data when the ESP32 hardware is not connected.
This runs as a background task that periodically inserts simulated
sensor readings into the database, so the entire system can be
demonstrated without any physical hardware.

The seeder creates:
- 4 demo devices (matching ESP32's device1-device4)
- Continuous sensor readings with realistic patterns
- Temperature/humidity variations based on time of day

Enable by setting DEMO_MODE=true in .env or environment variables.
"""

import asyncio
import random
import math
import logging
from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional
from services.hardware_status import is_hardware_connected

logger = logging.getLogger(__name__)

# Demo device configurations
DEMO_DEVICES = [
    {
        "name": "Living Room AC",
        "location": "Living Room",
        "relay_pin": 14,        # ESP32 GPIO 14 → Relay IN1
        "base_power": 1500,
        "power_variance": 300,
    },
    {
        "name": "Kitchen Appliances",
        "location": "Kitchen",
        "relay_pin": 27,        # ESP32 GPIO 27 → Relay IN2
        "base_power": 800,
        "power_variance": 200,
    },
    {
        "name": "Water Heater",
        "location": "Bathroom",
        "relay_pin": 26,        # ESP32 GPIO 26 → Relay IN3
        "base_power": 2000,
        "power_variance": 100,
    },
    {
        "name": "Bedroom Fan",
        "location": "Bedroom",
        "relay_pin": 25,        # ESP32 GPIO 25 → Relay IN4
        "base_power": 75,
        "power_variance": 15,
    },
]


async def seed_demo_devices(db, user_id: ObjectId) -> list:
    """
    Create demo devices if they don't already exist.
    Returns list of device documents.
    """
    devices = []
    for i, config in enumerate(DEMO_DEVICES):
        device_id_str = f"device{i + 1}"

        # Check if demo device already exists
        existing = await db.devices.find_one({
            "user_id": user_id,
            "name": config["name"],
        })

        if existing:
            devices.append(existing)
            continue

        device_doc = {
            "user_id": user_id,
            "name": config["name"],
            "location": config["location"],
            "relay_pin": config["relay_pin"],
            "status": "online",
            "is_relay_on": i < 2,  # First 2 devices start ON
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
        }

        result = await db.devices.insert_one(device_doc)
        device_doc["_id"] = result.inserted_id
        devices.append(device_doc)
        logger.info("Created demo device: %s (relay_pin=%d)", config["name"], config["relay_pin"])

    return devices


def generate_sensor_reading(
    device_config: dict,
    device_doc: dict,
    timestamp: datetime,
) -> dict:
    """
    Generate a realistic sensor reading for a demo device.
    Patterns:
    - Power varies with time of day (higher during day, lower at night)
    - Temperature follows a daily cycle
    - Humidity inversely correlates with temperature
    """
    hour = timestamp.hour

    # Time-of-day factor (0.0 to 1.0)
    # Higher during morning (8-10) and evening (18-22)
    tod_factor = 0.3 + 0.7 * (
        0.5 * math.exp(-((hour - 9) ** 2) / 8) +
        0.8 * math.exp(-((hour - 20) ** 2) / 10)
    )

    is_on = device_doc.get("is_relay_on", False)

    if is_on:
        base = device_config["base_power"]
        variance = device_config["power_variance"]
        power = base * tod_factor + random.uniform(-variance, variance)
        power = max(10, power)
    else:
        # Standby power
        power = random.uniform(1, 5)

    # Calculate current from power (P = V * I * PF)
    voltage = 220.0 + random.uniform(-5, 5)
    pf = 0.85 + random.uniform(0, 0.1)
    current = power / (voltage * pf) if voltage > 0 else 0

    # Temperature: base 25C, peaks at 14:00, min at 04:00
    temp_base = 25.0
    temp_variation = 8.0 * math.sin((hour - 4) * math.pi / 12)
    temperature = temp_base + temp_variation + random.uniform(-2, 2)

    # Humidity: inversely related to temperature
    humidity_base = 55.0
    humidity_variation = -10.0 * math.sin((hour - 4) * math.pi / 12)
    humidity = humidity_base + humidity_variation + random.uniform(-5, 5)
    humidity = max(20, min(95, humidity))

    return {
        "device_id": device_doc["_id"],
        "current": round(current, 3),
        "voltage": round(voltage, 1),
        "power": round(power, 2),
        "temperature": round(temperature, 1),
        "humidity": round(humidity, 1),
        "is_anomaly": False,
        "timestamp": timestamp,
    }


async def seed_historical_data(db, devices: list, hours: int = 24) -> int:
    """
    Seed historical data for the last N hours.
    Returns the number of records inserted.
    """
    now = datetime.utcnow()
    count = 0

    for i, device_doc in enumerate(devices):
        config = DEMO_DEVICES[i] if i < len(DEMO_DEVICES) else DEMO_DEVICES[0]

        # Check if we already have recent data
        recent = await db.energy_data.find_one(
            {"device_id": device_doc["_id"]},
            sort=[("timestamp", -1)],
        )

        if recent:
            time_diff = (now - recent["timestamp"]).total_seconds()
            if time_diff < 60:
                continue  # Already have recent data

        # Generate data points every 5 minutes
        readings = []
        for minutes_ago in range(hours * 60, 0, -5):
            ts = now - timedelta(minutes=minutes_ago)
            reading = generate_sensor_reading(config, device_doc, ts)
            readings.append(reading)
            count += 1

        if readings:
            await db.energy_data.insert_many(readings)
            logger.info(
                "Seeded %d historical readings for %s",
                len(readings), device_doc["name"],
            )

    return count


async def demo_data_loop(db, devices: list, interval_seconds: int = 5):
    """
    Background loop that continuously generates demo sensor data.
    Simulates what the ESP32 would send in production.

    Automatically PAUSES when real ESP32 hardware is detected
    (i.e. POST /api/energy/data receives real sensor data).
    Resumes when hardware disconnects (no data for 30 seconds).
    """
    logger.info("Demo data loop started (interval=%ds)", interval_seconds)
    was_paused = False

    while True:
        try:
            # ── Check if real hardware is sending data ──
            if is_hardware_connected():
                if not was_paused:
                    logger.info("Demo data PAUSED — real ESP32 hardware is active")
                    was_paused = True
                await asyncio.sleep(interval_seconds)
                continue

            if was_paused:
                logger.info("Demo data RESUMED — no hardware detected")
                was_paused = False

            now = datetime.utcnow()
            for i, device_doc in enumerate(devices):
                config = DEMO_DEVICES[i] if i < len(DEMO_DEVICES) else DEMO_DEVICES[0]

                # Refresh device state from DB (relay might have been toggled)
                refreshed = await db.devices.find_one({"_id": device_doc["_id"]})
                if refreshed:
                    device_doc = refreshed

                reading = generate_sensor_reading(config, device_doc, now)
                await db.energy_data.insert_one(reading)

                # Update device status
                await db.devices.update_one(
                    {"_id": device_doc["_id"]},
                    {"$set": {
                        "status": "online",
                        "last_seen": now,
                        "updated_at": now,
                    }},
                )

                # Trigger RL update
                try:
                    from services.ai_service import AIService
                    ai_svc = AIService(db)
                    await ai_svc.update_rl_from_reading(
                        str(device_doc["_id"]),
                        reading["power"],
                        reading["temperature"],
                    )
                except Exception as e:
                    logger.debug("RL update in demo loop: %s", e)

            # Randomly toggle a device occasionally
            if random.random() < 0.05:
                toggle_idx = random.randint(0, len(devices) - 1)
                dev = devices[toggle_idx]
                current_state = dev.get("is_relay_on", False)
                await db.devices.update_one(
                    {"_id": dev["_id"]},
                    {"$set": {"is_relay_on": not current_state, "updated_at": now}},
                )

        except Exception as e:
            logger.error("Demo data loop error: %s", e)

        await asyncio.sleep(interval_seconds)


async def start_demo_mode(db) -> Optional[asyncio.Task]:
    """
    Initialize demo mode: seed devices, historical data, and start
    the continuous data generation loop.

    Returns the background task handle.
    """
    import os
    from utils.password import hash_password

    # Ensure demo user exists
    demo_email = "admin@aipeco.com"
    user = await db.users.find_one({"email": demo_email})

    if not user:
        admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "admin123")
        user_doc = {
            "name": "Demo Admin",
            "email": demo_email,
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "energy_limit": 100.0,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        result = await db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        user = user_doc
        logger.info("Created demo user: %s / admin123", demo_email)

    user_id = user["_id"]

    # Seed devices
    devices = await seed_demo_devices(db, user_id)
    logger.info("Demo mode: %d devices ready", len(devices))

    # Seed historical data (last 24 hours)
    count = await seed_historical_data(db, devices, hours=24)
    logger.info("Demo mode: seeded %d historical readings", count)

    # Start background data loop
    task = asyncio.create_task(demo_data_loop(db, devices, interval_seconds=5))
    logger.info("Demo mode: background data generation started")

    return task
