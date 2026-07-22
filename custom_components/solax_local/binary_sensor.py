from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolaxDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SolaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SolaxBinarySensor(coordinator, entry.entry_id)])


class SolaxBinarySensor(CoordinatorEntity[SolaxDataUpdateCoordinator], BinarySensorEntity):
    def __init__(self, coordinator, entry_id) -> None:
        super().__init__(coordinator)
        self._attr_name = "Online"
        self._attr_unique_id = f"{entry_id}_online"
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        # Attach entity to inverter device by serial
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.serial)},
            "name": f"SolaX {coordinator.serial}",
            "manufacturer": "SolaX",
            "model": (coordinator.data or {}).get("model"),
            "connections": {("ip", coordinator.host)},
        }

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("online", False))

    @property
    def should_poll(self) -> bool:
        return False
