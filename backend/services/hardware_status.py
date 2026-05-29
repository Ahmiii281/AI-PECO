"""
Hardware connection tracker.

Tracks whether the ESP32 hardware is actively sending real sensor data.
When hardware is connected, the demo seeder automatically pauses.
When hardware disconnects (no data for TIMEOUT seconds), demo resumes.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# How long without ESP32 data before we consider hardware "disconnected"
HARDWARE_TIMEOUT_SECONDS = 30

# Internal state
_last_hardware_ping: datetime | None = None
_hardware_was_active: bool = False


def mark_hardware_active():
    """
    Called when real sensor data arrives from ESP32 via POST /api/energy/data.
    """
    global _last_hardware_ping, _hardware_was_active

    _last_hardware_ping = datetime.utcnow()

    if not _hardware_was_active:
        _hardware_was_active = True
        logger.info("🔌 ESP32 hardware CONNECTED — pausing demo data generation")


def is_hardware_connected() -> bool:
    """
    Returns True if ESP32 has sent data within the last HARDWARE_TIMEOUT_SECONDS.
    Used by the demo seeder to decide whether to generate fake data.
    """
    global _last_hardware_ping, _hardware_was_active

    if _last_hardware_ping is None:
        return False

    connected = (datetime.utcnow() - _last_hardware_ping) < timedelta(
        seconds=HARDWARE_TIMEOUT_SECONDS
    )

    if _hardware_was_active and not connected:
        _hardware_was_active = False
        logger.info("⚠️ ESP32 hardware DISCONNECTED (no data for %ds) — resuming demo data",
                     HARDWARE_TIMEOUT_SECONDS)

    return connected


def get_hardware_info() -> dict:
    """
    Returns current hardware connection status (for /health endpoint).
    """
    connected = is_hardware_connected()
    return {
        "hardware_connected": connected,
        "last_seen": _last_hardware_ping.isoformat() if _last_hardware_ping else None,
        "data_source": "esp32" if connected else "demo",
    }
