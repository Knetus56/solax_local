from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL
from .solax_protocol import fetch_inverter_state

_LOGGER = logging.getLogger(__name__)


class SolaxDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, host: str, serial: str, scan_interval: int = DEFAULT_SCAN_INTERVAL) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="solax_local",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self.serial = serial

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.hass.async_add_executor_job(fetch_inverter_state, self.host, self.serial)
            data["last_update"] = datetime.now(timezone.utc)
            return data
        except Exception as err:  # pragma: no cover - defensive path
            raise UpdateFailed(f"Unable to fetch SolaX data: {err}") from err
