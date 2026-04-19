"""
Device management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from services.device_service import DeviceService
from schemas import DeviceCreate, DeviceUpdate, DeviceResponse
from routes.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.post("", response_model=DeviceResponse)
async def create_device(
    device_data: DeviceCreate,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new device
    """
    device_service = DeviceService(db)

    try:
        device = await device_service.create_device(user_id, device_data.dict())
        return {
            "id": str(device["_id"]),
            "name": device["name"],
            "location": device["location"],
            "status": device["status"],
            "is_relay_on": device["is_relay_on"],
            "relay_pin": device["relay_pin"],
            "created_at": device["created_at"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list)
async def get_devices(user_id: str = Depends(get_current_user)):
    """
    Get all devices for current user
    """
    device_service = DeviceService(db)

    devices = await device_service.get_user_devices(user_id)

    return [
        {
            "id": str(device["_id"]),
            "name": device["name"],
            "location": device["location"],
            "status": device["status"],
            "is_relay_on": device.get("is_relay_on", False),
            "relay_pin": device.get("relay_pin", 5),
            "created_at": device["created_at"],
        }
        for device in devices
    ]


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get device details
    """
    device_service = DeviceService(db)

    try:
        device = await device_service.get_device(device_id, user_id)
        return {
            "id": str(device["_id"]),
            "name": device["name"],
            "location": device["location"],
            "status": device["status"],
            "is_relay_on": device.get("is_relay_on", False),
            "relay_pin": device.get("relay_pin", 5),
            "created_at": device["created_at"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_data: DeviceUpdate,
    user_id: str = Depends(get_current_user)
):
    """
    Update device information
    """
    device_service = DeviceService(db)

    try:
        device = await device_service.update_device(
            device_id,
            user_id,
            device_data.dict(exclude_unset=True)
        )
        return {
            "id": str(device["_id"]),
            "name": device["name"],
            "location": device["location"],
            "status": device["status"],
            "is_relay_on": device.get("is_relay_on", False),
            "relay_pin": device.get("relay_pin", 5),
            "created_at": device["created_at"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Delete a device
    """
    device_service = DeviceService(db)

    try:
        await device_service.delete_device(device_id, user_id)
        return {"message": "Device deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/admin/all", response_model=list)
async def get_all_devices_admin(admin_id: str = Depends(get_current_admin)):
    """
    Admin: Get all devices in the system
    """
    devices = await db.devices.find().to_list(1000)
    return [
        {
            "id": str(device["_id"]),
            "user_id": str(device.get("user_id", "")),
            "name": device["name"],
            "location": device["location"],
            "status": device["status"],
            "is_relay_on": device.get("is_relay_on", False),
            "relay_pin": device.get("relay_pin", 5),
            "created_at": device.get("created_at"),
        }
        for device in devices
    ]
