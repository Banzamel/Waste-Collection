import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.loader import async_get_integration

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION, WASTE_TYPES
from .schedule import WasteCollectionData, WasteSchedule

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.CALENDAR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_UPDATE_SCHEDULE = "update_schedule"
SERVICE_ADD_PICKUP = "add_pickup"
SERVICE_REMOVE_PICKUP = "remove_pickup"

PICKUP_SCHEMA = vol.Schema(
    {
        vol.Required("type"): vol.In(WASTE_TYPES),
        vol.Required("date"): cv.date,
    }
)

# Entries are validated individually in WasteSchedule, so an import containing
# a single unknown waste type does not reject the whole schedule.
UPDATE_SCHEDULE_SCHEMA = vol.Schema(
    {vol.Required("pickups"): vol.All(cv.ensure_list, [dict])}
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Setup static paths and register Lovelace card."""
    from homeassistant.components.http import StaticPathConfig

    integration = await async_get_integration(hass, DOMAIN)
    version = str(integration.version or "1.0.0")

    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/waste_collection_local",
            hass.config.path("custom_components/waste_collection/www"),
            True,
        )
    ])

    url_with_version = f"/waste_collection_local/waste-card.js?v={version}"
    await _register_frontend_resource(hass, url_with_version)
    return True


async def _register_frontend_resource(hass: HomeAssistant, url: str):
    """Register JS card in Lovelace resources."""
    lovelace = hass.data.get("lovelace")
    if lovelace and hasattr(lovelace, "resources"):
        resources = lovelace.resources
        if not resources.loaded:
            await resources.async_load()

        items = resources.async_items()
        exists = any(url in r.get("url", "") for r in items)

        if not exists:
            for item in items:
                if "/waste_collection_local/waste-card.js" in item.get("url", ""):
                    await resources.async_delete_item(item.get("id"))

            await resources.async_create_item({
                "res_type": "module",
                "url": url,
            })


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup entry from UI."""
    integration = await async_get_integration(hass, DOMAIN)
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    schedule = await WasteSchedule.async_load(hass, store)
    entry.runtime_data = WasteCollectionData(
        schedule=schedule,
        version=str(integration.version or "1.0.0"),
    )

    # "Days until" values change at midnight even when the schedule does not.
    @callback
    def _midnight_refresh(_now) -> None:
        schedule.async_notify()

    entry.async_on_unload(
        async_track_time_change(hass, _midnight_refresh, hour=0, minute=0, second=0)
    )

    _register_services(hass, schedule)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        for service in (SERVICE_UPDATE_SCHEDULE, SERVICE_ADD_PICKUP, SERVICE_REMOVE_PICKUP):
            hass.services.async_remove(DOMAIN, service)
    return unloaded


def _register_services(hass: HomeAssistant, schedule: WasteSchedule) -> None:
    async def handle_update_schedule(call: ServiceCall) -> None:
        await schedule.async_set_pickups(call.data["pickups"])

    async def handle_add_pickup(call: ServiceCall) -> None:
        await schedule.async_add_pickup(call.data["type"], call.data["date"])

    async def handle_remove_pickup(call: ServiceCall) -> None:
        await schedule.async_remove_pickup(call.data["type"], call.data["date"])

    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_SCHEDULE, handle_update_schedule, schema=UPDATE_SCHEDULE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_PICKUP, handle_add_pickup, schema=PICKUP_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REMOVE_PICKUP, handle_remove_pickup, schema=PICKUP_SCHEMA
    )
