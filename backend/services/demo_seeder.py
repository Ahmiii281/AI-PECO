"""
AI-PECO: Demo Data Seeder
============================
Generates realistic demo data when the ESP32 hardware is not connected.
Runs as a background asyncio task.

Key safeguards:
- All seeder-created documents carry `is_demo: True` so they can be
  identified and filtered separately from real hardware data.
- The seeder auto-PAUSES when real ESP32 data is detected and RESUMES
  when hardware goes silent for >30 seconds.
- No hardcoded placeholder IDs — always uses real MongoDB ObjectIds.
"""

import asyncio
import random
import math
import logging
from datetime import datetime, timedelta
from bson import ObjectId
from typing import Optional, List
from services.hardware_status import is_hardware_connected

logger = logging.getLogger(__name__)

# ── Demo device configurations ────────────────────────────────────────────────

DEMO_DEVICES = [
    {
        "name": "Living Room AC",
        "location": "Living Room",
        "relay_pin": 14,       # ESP32 GPIO 14 → Relay IN1
        "base_power": 1500,
        "power_variance": 300,
    },
    {
        "name": "Kitchen Appliances",
        "location": "Kitchen",
        "relay_pin": 27,       # ESP32 GPIO 27 → Relay IN2
        "base_power": 800,
        "power_variance": 200,
    },
    {
        "name": "Water Heater",
        "location": "Bathroom",
        "relay_pin": 26,       # ESP32 GPIO 26 → Relay IN3
        "base_power": 2000,
        "power_variance": 100,
    },
    {
        "name": "Bedroom Fan",
        "location": "Bedroom",
        "relay_pin": 25,       # ESP32 GPIO 25 → Relay IN4
        "base_power": 75,
        "power_variance": 15,
    },
]


# ── Device seeding ─────────────────────────────────────────────────────────────

async def seed_demo_devices(db, user_id: ObjectId) -> List[dict]:
    """
    Create demo devices if they don't already exist.
    Returns the list of device documents (existing or newly created).
    All created documents carry `is_demo: True`.
    """
    devices = []
    for config in DEMO_DEVICES:
        # Look up by user + name (unique enough for demo purposes)
        existing = await db.devices.find_one({
            "user_id": user_id,
            "name": config["name"],
        })

        if existing:
            devices.append(existing)
            continue

        now = datetime.utcnow()
        device_doc = {
            "user_id": user_id,
            "name": config["name"],
            "location": config["location"],
            "relay_pin": config["relay_pin"],
            "status": "online",
            "is_relay_on": config["name"] in ("Living Room AC", "Kitchen Appliances"),
            "is_demo": True,        # Always mark demo devices
            "created_at": now,
            "updated_at": now,
            "last_seen": now,
        }

        result = await db.devices.insert_one(device_doc)
        device_doc["_id"] = result.inserted_id
        devices.append(device_doc)
        logger.info(
            "Created demo device: %s (relay_pin=%d, _id=%s)",
            config["name"],
            config["relay_pin"],
            result.inserted_id,
        )

    return devices


# ── Sensor reading generation ─────────────────────────────────────────────────

def generate_sensor_reading(
    device_config: dict,
    device_doc: dict,
    timestamp: datetime,
) -> dict:
    """
    Generate a realistic simulated sensor reading.

    Patterns:
    - Power varies with time of day (higher morning/evening)
    - Temperature follows a daily sinusoidal cycle
    - Humidity inversely correlates with temperature
    """
    hour = timestamp.hour

    # Time-of-day power factor (peaks at 09:00 and 20:00)
    tod_factor = 0.3 + 0.7 * (
        0.5 * math.exp(-((hour - 9) ** 2) / 8)
        + 0.8 * math.exp(-((hour - 20) ** 2) / 10)
    )

    is_on = device_doc.get("is_relay_on", False)
    if is_on:
        base = device_config["base_power"]
        variance = device_config["power_variance"]
        power = base * tod_factor + random.uniform(-variance, variance)
        power = max(10, power)
    else:
        power = random.uniform(1, 5)  # standby draw

    voltage = 220.0 + random.uniform(-5, 5)
    pf = 0.85 + random.uniform(0, 0.1)
    current = power / (voltage * pf) if voltage > 0 else 0.0

    # Temperature: peaks at 14:00, minimum at 04:00
    temperature = (
        25.0
        + 8.0 * math.sin((hour - 4) * math.pi / 12)
        + random.uniform(-2, 2)
    )

    # Humidity: inverse of temperature pattern
    humidity = max(20.0, min(95.0, 55.0 - 10.0 * math.sin((hour - 4) * math.pi / 12) + random.uniform(-5, 5)))

    return {
        "device_id": device_doc["_id"],
        "current": round(current, 3),
        "voltage": round(voltage, 1),
        "power": round(power, 2),
        "temperature": round(temperature, 1),
        "humidity": round(humidity, 1),
        "is_anomaly": False,
        "is_demo": True,            # Mark all demo readings
        "timestamp": timestamp,
    }


# ── Historical data seeding ───────────────────────────────────────────────────

async def seed_historical_data(db, devices: List[dict], hours: int = 24) -> int:
    """
    Seed historical readings for the last N hours (one every 5 minutes).
    Skips devices that already have recent data to avoid duplicates.
    Returns the number of records inserted.
    """
    now = datetime.utcnow()
    total_inserted = 0

    for i, device_doc in enumerate(devices):
        config = DEMO_DEVICES[i] if i < len(DEMO_DEVICES) else DEMO_DEVICES[0]

        # Skip if recent real or demo data already exists
        recent = await db.energy_data.find_one(
            {"device_id": device_doc["_id"]},
            sort=[("timestamp", -1)],
        )
        if recent and (now - recent["timestamp"]).total_seconds() < 60:
            continue

        readings = []
        for minutes_ago in range(hours * 60, 0, -5):
            ts = now - timedelta(minutes=minutes_ago)
            reading = generate_sensor_reading(config, device_doc, ts)
            readings.append(reading)

        if readings:
            await db.energy_data.insert_many(readings)
            total_inserted += len(readings)
            logger.info(
                "Seeded %d historical readings for '%s'",
                len(readings),
                device_doc["name"],
            )

    return total_inserted


# ── Continuous data loop ──────────────────────────────────────────────────────

async def demo_data_loop(db, devices: List[dict], interval_seconds: int = 5) -> None:
    """
    Background loop: generates live demo readings every `interval_seconds`.
    Auto-pauses when real ESP32 hardware is detected.
    Auto-resumes when hardware goes silent.
    """
    logger.info("Demo data loop started (interval=%ds)", interval_seconds)
    was_paused = False

    while True:
        try:
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

                # Refresh device state to pick up relay toggles
                refreshed = await db.devices.find_one({"_id": device_doc["_id"]})
                if refreshed:
                    device_doc = refreshed

                reading = generate_sensor_reading(config, device_doc, now)
                await db.energy_data.insert_one(reading)

                await db.devices.update_one(
                    {"_id": device_doc["_id"]},
                    {"$set": {"status": "online", "last_seen": now, "updated_at": now}},
                )

                # Non-critical: update RL agent
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

            # Occasionally toggle a device to simulate usage changes
            if random.random() < 0.05 and devices:
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


# ── Entry point ───────────────────────────────────────────────────────────────

async def start_demo_mode(db) -> Optional[asyncio.Task]:
    """
    Initialize demo mode:
    1. Ensure the demo admin user exists.
    2. Seed demo devices (with real MongoDB ObjectIds, not placeholder strings).
    3. Seed 24h of historical data.
    4. Start the continuous data generation background task.

    Returns the asyncio.Task handle (cancel it to stop demo mode).
    """
    import os
    from utils.password import hash_password

    # Ensure demo user exists
    demo_email = "admin@aipeco.com"
    user = await db.users.find_one({"email": demo_email})

    if not user:
        admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "Admin123!")
        user_doc = {
            "name": "Demo Admin",
            "email": demo_email,
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "energy_limit": 100.0,
            "is_active": True,
            "is_demo": True,
            "created_at": datetime.utcnow(),
        }
        result = await db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        user = user_doc
        logger.info("Created demo user: %s (password from DEMO_ADMIN_PASSWORD env)", demo_email)

    user_id = user["_id"]

    # Seed devices using real ObjectIds
    devices = await seed_demo_devices(db, user_id)
    logger.info("Demo mode: %d devices ready", len(devices))

    # Seed historical data
    count = await seed_historical_data(db, devices, hours=24)
    logger.info("Demo mode: seeded %d historical readings", count)

    # Start background loop
    task = asyncio.create_task(demo_data_loop(db, devices, interval_seconds=5))
    logger.info("Demo mode: background data generation started")
    return task
