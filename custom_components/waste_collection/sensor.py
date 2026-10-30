from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import WASTE_ICONS, WASTE_TYPES
from .entity import WasteCollectionEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup sensors from config entry."""
    sensors = [
        WasteCollectionMasterSensor(entry),
        WasteCollectionNextSensor(entry),
    ]
    sensors.extend(WasteTypeSensor(entry, waste_type) for waste_type in WASTE_TYPES)
    async_add_entities(sensors)


class WasteCollectionMasterSensor(WasteCollectionEntity, SensorEntity):
    """Master sensor holding all pickup data (used by the Lovelace card)."""

    _attr_translation_key = "schedule"
    _attr_unique_id = "waste_collection_master"
    _attr_icon = "mdi:trash-can"
    _attr_native_unit_of_measurement = "pickups"

    def __init__(self, entry: ConfigEntry):
        super().__init__(entry, "sensor.waste_collection_schedule")

    @property
    def native_value(self) -> int:
        return len(self._schedule.pickups)

    @property
    def extra_state_attributes(self):
        return {"pickups": self._schedule.pickups}


class WasteCollectionNextSensor(WasteCollectionEntity, SensorEntity):
    """Date of the nearest collection day and all waste types picked up that day."""

    _attr_translation_key = "next_collection"
    _attr_unique_id = "waste_collection_next"
    _attr_icon = "mdi:truck"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, entry: ConfigEntry):
        super().__init__(entry, "sensor.waste_collection_next")

    @property
    def native_value(self):
        collection = self._schedule.next_collection()
        return collection[0] if collection else None

    @property
    def extra_state_attributes(self):
        collection = self._schedule.next_collection()
        if collection is None:
            return {"days": None, "types": [], "labels": [], "description": None}
        pickup_date, types = collection
        labels = [self._schedule.label(t) for t in types]
        return {
            "days": (pickup_date - self._schedule.today()).days,
            "types": types,
            "labels": labels,
            "description": ", ".join(labels),
        }


class WasteTypeSensor(WasteCollectionEntity, SensorEntity):
    """Sensor for a specific waste type showing days until next pickup."""

    _attr_native_unit_of_measurement = "days"

    def __init__(self, entry: ConfigEntry, waste_type: str):
        super().__init__(entry, f"sensor.waste_collection_{waste_type}")
        self._waste_type = waste_type
        self._attr_unique_id = f"waste_collection_{waste_type}"
        self._attr_icon = WASTE_ICONS[waste_type]
        self._attr_translation_key = waste_type

    @property
    def native_value(self) -> int | None:
        pickup_date = self._schedule.next_pickup(self._waste_type)
        if pickup_date is None:
            return None
        return (pickup_date - self._schedule.today()).days

    @property
    def extra_state_attributes(self):
        pickup_date = self._schedule.next_pickup(self._waste_type)
        return {
            "next_date": pickup_date.isoformat() if pickup_date else None,
            "waste_type": self._waste_type,
            "label": self._schedule.label(self._waste_type),
        }
