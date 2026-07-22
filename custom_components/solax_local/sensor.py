from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolaxDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: SolaxDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        SolaxSensor(coordinator, entry.entry_id, "mptt1", "Puissance MPPT 1", UnitOfPower.WATT, "power"),
        SolaxSensor(coordinator, entry.entry_id, "mptt2", "Puissance MPPT 2", UnitOfPower.WATT, "power"),
        SolaxSensor(coordinator, entry.entry_id, "mptt_total", "Puissance totale", UnitOfPower.WATT, "power"),
        SolaxSensor(coordinator, entry.entry_id, "temp", "Température", UnitOfTemperature.CELSIUS, "temperature"),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "prod_auj",
            "Production du jour",
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "prod_total",
            "Production totale",
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "mode",
            "Mode",
            None,
            "enum",
            EntityCategory.DIAGNOSTIC,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "ip",
            "IP",
            None,
            "string",
            EntityCategory.DIAGNOSTIC,
        ),
        SolaxSensor(
            coordinator,
            entry.entry_id,
            "num_inverter",
            "Numéro de série",
            None,
            "string",
            EntityCategory.DIAGNOSTIC,
        ),
    ]
    async_add_entities(entities)


class SolaxSensor(CoordinatorEntity[SolaxDataUpdateCoordinator], SensorEntity):
    def __init__(
        self,
        coordinator,
        entry_id,
        key,
        name,
        unit,
        device_class,
        entity_category: EntityCategory | None = None,
        state_class: SensorStateClass | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_has_entity_name = True
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_entity_category = entity_category
        self._attr_state_class = state_class
        # Link this entity to a single device (the inverter) using its serial
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.serial)},
            "name": f"SolaX {coordinator.serial}",
            "manufacturer": "SolaX",
            "model": (coordinator.data or {}).get("model"),
            "connections": {("ip", coordinator.host)},
        }

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def should_poll(self) -> bool:
        return False
