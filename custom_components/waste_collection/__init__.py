import logging
import json
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
DOMAIN = "waste_collection"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Setup static paths and register Lovelace card."""
    from homeassistant.components.http import StaticPathConfig

    manifest_path = hass.config.path("custom_components/waste_collection/manifest.json")
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        version = manifest.get("version", "1.0.0")
    except Exception as e:
        _LOGGER.error("Error reading manifest.json: %s", e)
        version = "1.0.0"

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
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    return await hass.config_entries.async_forward_entry_unload(entry, "sensor")
