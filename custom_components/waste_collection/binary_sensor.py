from datetime import date, timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import WASTE_ICONS, WASTE_TYPES
from .entity import WasteCollectionEntity

# day key -> offset from today
DAYS = {"today": 0, "tomorrow": 1}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup binary sensors from config entry."""
    sensors = [AnyPickupBinarySensor(entry, day) for day in DAYS]
    sensors.extend(
        WasteTypePickupBinarySensor(entry, waste_type, day)
        for waste_type in WASTE_TYPES
        for day in DAYS
    )
    async_add_entities(sensors)


class _PickupBinarySensor(WasteCollectionEntity, BinarySensorEntity):
    def __init__(self, entry: ConfigEntry, day: str, entity_id: str):
        super().__init__(entry, entity_id)
        self._offset = DAYS[day]

    @property
    def _day(self) -> date:
        return self._schedule.today() + timedelta(days=self._offset)


class AnyPickupBinarySensor(_PickupBinarySensor):
    """On when any waste type is collected on the given day."""

    _attr_icon = "mdi:truck-alert"

    def __init__(self, entry: ConfigEntry, day: str):
        super().__init__(entry, day, f"binary_sensor.waste_collection_{day}")
        self._attr_unique_id = f"waste_collection_any_{day}"
        self._attr_translation_key = f"any_{day}"

    @property
    def is_on(self) -> bool:
        return bool(self._schedule.types_on(self._day))

    @property
    def extra_state_attributes(self):
        types = self._schedule.types_on(self._day)
        labels = [self._schedule.label(t) for t in types]
        return {
            "date": self._day.isoformat(),
            "types": types,
            "labels": labels,
            "description": ", ".join(labels),
        }


class WasteTypePickupBinarySensor(_PickupBinarySensor):
    """On when the given waste type is collected on the given day."""

    def __init__(self, entry: ConfigEntry, waste_type: str, day: str):
        super().__init__(entry, day, f"binary_sensor.waste_collection_{waste_type}_{day}")
        self._waste_type = waste_type
        self._attr_unique_id = f"waste_collection_{waste_type}_{day}"
        self._attr_translation_key = f"{waste_type}_{day}"
        self._attr_icon = WASTE_ICONS[waste_type]

    @property
    def is_on(self) -> bool:
        return self._waste_type in self._schedule.types_on(self._day)
