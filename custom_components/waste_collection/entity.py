from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, SIGNAL_SCHEDULE_UPDATED
from .schedule import WasteSchedule


class WasteCollectionEntity(Entity):
    """Base entity attached to the Waste Collection device."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, entity_id: str | None = None):
        self._schedule: WasteSchedule = entry.runtime_data.schedule
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Waste Collection",
            manufacturer="Banzamel",
            entry_type=DeviceEntryType.SERVICE,
            sw_version=entry.runtime_data.version,
        )
        # Keep stable, documented entity IDs regardless of the UI language.
        if entity_id:
            self.entity_id = entity_id

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_SCHEDULE_UPDATED, self.async_write_ha_state)
        )
