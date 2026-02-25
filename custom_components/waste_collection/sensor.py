import logging
import json
import os
from datetime import date, datetime, timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

DOMAIN = "waste_collection"
STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 1

WASTE_TYPES = ["bio", "mixed", "plastic", "paper", "glass"]

WASTE_LABELS = {
    "bio": "Bio",
    "mixed": "Zmieszane",
    "plastic": "Plastik",
    "paper": "Papier",
    "glass": "Szkło",
}


def _days_until(date_str: str) -> int | None:
    """Return number of days until given ISO date string."""
    if not date_str:
        return None
    try:
        target = date.fromisoformat(date_str)
        today = date.today()
        return (target - today).days
    except Exception:
        return None


def _next_pickup(pickups: list, waste_type: str):
    """Find next upcoming pickup for given waste type."""
    today = date.today()
    future = [
        p for p in pickups
        if p.get("type") == waste_type
        and _parse_date(p.get("date")) is not None
        and _parse_date(p.get("date")) >= today
    ]
    if not future:
        return None
    future.sort(key=lambda p: _parse_date(p["date"]))
    return future[0]


def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str)
    except Exception:
        return None


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensors from config entry."""
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored_data = await store.async_load()
    pickups = stored_data.get("pickups", []) if stored_data else []

    sensors = []
    master = WasteCollectionMasterSensor(hass, store, pickups)
    sensors.append(master)

    for waste_type in WASTE_TYPES:
        sensors.append(WasteTypeSensor(hass, master, waste_type))

    async_add_entities(sensors, True)

    async def handle_update_schedule(call):
        new_pickups = call.data.get("pickups", [])
        await master.async_update_pickups(new_pickups)

    async def handle_add_pickup(call):
        pickup_type = call.data.get("type")
        pickup_date = call.data.get("date")
        if pickup_type and pickup_date:
            master._pickups.append({"type": pickup_type, "date": pickup_date})
            await master._store.async_save({"pickups": master._pickups})
            master.async_write_ha_state()
            for s in sensors:
                if isinstance(s, WasteTypeSensor):
                    s.async_write_ha_state()

    async def handle_remove_pickup(call):
        pickup_type = call.data.get("type")
        pickup_date = call.data.get("date")
        master._pickups = [
            p for p in master._pickups
            if not (p.get("type") == pickup_type and p.get("date") == pickup_date)
        ]
        await master._store.async_save({"pickups": master._pickups})
        master.async_write_ha_state()
        for s in sensors:
            if isinstance(s, WasteTypeSensor):
                s.async_write_ha_state()

    hass.services.async_register(DOMAIN, "update_schedule", handle_update_schedule)
    hass.services.async_register(DOMAIN, "add_pickup", handle_add_pickup)
    hass.services.async_register(DOMAIN, "remove_pickup", handle_remove_pickup)


class WasteCollectionMasterSensor(SensorEntity):
    """Master sensor holding all pickup data."""

    def __init__(self, hass, store, pickups):
        self._hass = hass
        self._store = store
        self._pickups = pickups
        self._attr_name = "Waste Collection Schedule"
        self._attr_unique_id = "waste_collection_master"
        self._attr_icon = "mdi:trash-can"

    @property
    def state(self):
        return len(self._pickups)

    @property
    def unit_of_measurement(self):
        return "pickups"

    @property
    def extra_state_attributes(self):
        return {"pickups": self._pickups}

    async def async_update_pickups(self, new_pickups):
        self._pickups = new_pickups
        await self._store.async_save({"pickups": self._pickups})
        self.async_write_ha_state()


class WasteTypeSensor(SensorEntity):
    """Sensor for a specific waste type showing days until next pickup."""

    def __init__(self, hass, master: WasteCollectionMasterSensor, waste_type: str):
        self._hass = hass
        self._master = master
        self._waste_type = waste_type
        self._attr_name = f"Waste Collection {WASTE_LABELS[waste_type]}"
        self._attr_unique_id = f"waste_collection_{waste_type}"
        self._attr_icon = "mdi:trash-can-outline"

    @property
    def state(self):
        pickup = _next_pickup(self._master._pickups, self._waste_type)
        if pickup is None:
            return None
        days = _days_until(pickup["date"])
        return days

    @property
    def unit_of_measurement(self):
        return "days"

    @property
    def extra_state_attributes(self):
        pickup = _next_pickup(self._master._pickups, self._waste_type)
        if pickup is None:
            return {"next_date": None, "waste_type": self._waste_type}
        return {
            "next_date": pickup["date"],
            "waste_type": self._waste_type,
            "label": WASTE_LABELS[self._waste_type],
        }
