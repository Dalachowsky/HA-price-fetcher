
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_URL, CONF_NAME
from homeassistant.components.sensor import (SensorEntity, PLATFORM_SCHEMA)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .price_fetcher import PriceFetcher, PriceEntity
from .const import DOMAIN

import voluptuous as vol
from typing import *

import logging
_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.string,
    vol.Required(CONF_NAME): cv.string,
})

PRICE_FETCHERS: List[PriceFetcher] = []

def setup(hass: HomeAssistant, config: dict) -> bool:

    async def handle_fetchPricesAsync(call):
        for fetcher in PRICE_FETCHERS:
            await fetcher.update_prices_async()

    hass.services.register(DOMAIN, "fetchPrices", handle_fetchPricesAsync)

    return True

async def async_setup_platform(hass, config: ConfigType, async_add_entities: AddEntitiesCallback, discovery_info=None):
    """Set up the sensor platform."""
    url = config[CONF_URL]
    name = config[CONF_NAME]

    _LOGGER.debug(f"Config: {config}")

    PRICE_FETCHERS.append(PriceFetcher(hass, config["name"], config["url"]))

    for fetcher in PRICE_FETCHERS:
        await fetcher.update_prices_async()
        await fetcher.createEntities()
        async_add_entities(fetcher.entities)

    return True

