from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AlleanzaLuceGasAPI
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AlleanzaDataCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass: HomeAssistant,
        api: AlleanzaLuceGasAPI,
        update_interval_hours: int = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=update_interval_hours),
        )
        self.api = api

    async def _async_update_data(self) -> dict:
        try:
            return await self.api.fetch_all_data()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
