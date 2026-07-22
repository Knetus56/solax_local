from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .coordinator import SolaxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Configuration au niveau de la plateforme."""
    hass.data.setdefault(DOMAIN, {})
    
    async def refresh_all_inverters(call: ServiceCall) -> None:
        """Service pour actualiser tous les onduleurs."""
        coordinators = hass.data.get(DOMAIN, {}).values()
        for coordinator in coordinators:
            if isinstance(coordinator, SolaxDataUpdateCoordinator):
                await coordinator.async_request_refresh()
        _LOGGER.info("Actualisation manuelle de tous les onduleurs")
    
    hass.services.async_register(DOMAIN, "refresh_all", refresh_all_inverters)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = SolaxDataUpdateCoordinator(hass, entry.data["host"], entry.data["serial"], entry.data.get("scan_interval", 60))
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "switch"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor", "switch"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
