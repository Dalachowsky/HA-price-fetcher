
import re
import aiohttp
import asyncio
from typing import *
from bs4 import BeautifulSoup
import json
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

import logging
_LOGGER = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Connection': 'Keep-Alive'    
}

class PriceEntity(SensorEntity):

    def __init__(self, coordinator, name, volume):
        """Initialize the number entity."""
        self._name = name
        self._volume = volume
        self._coordinator = coordinator
        _LOGGER.debug(f"New PriceEntity {self._name} volume: {self._volume}")

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._coordinator._prices[self._volume]

    @property
    def unit_of_measurement(self):
        return "PLN"


class PriceFetcher:

    def __init__(self, hass: HomeAssistant, name, url):
        """Initialize the coordinator."""
        self._name = name
        self._url = url
        self._pricesFetched = asyncio.Event()
        self._prices = {}
        self.entities: List[PriceEntity] = []
        _LOGGER.debug(f"New PriceFetcher: {self._name}")
            
    async def createEntities(self):
        await self._pricesFetched.wait()
        self.entities = [PriceEntity(self, f"{self._name} {volume}", volume) for volume in self._prices.keys()]

    async def update_prices_async(self):
        self._prices = await self.fetchPrices()
        _LOGGER.debug(f"New Data: {self._prices}")
        self._pricesFetched.set()

        for volume, price in self._prices.items():
            for e in self.entities:
                if e._name == volume:
                    e._price = price

    async def fetchPrices(self):

        def getPrice(priceType: str, tag):
            try:
                text = tag.findChild("div", {"class": f"product-price__{priceType}"}).findChild("span", {"class", "product-price__price"}).text
                text = re.findall("\d+[,.]\d+", text)[0]
                text = text.replace(",", ".")
                return float(text)
            except Exception as e:
                return None

        retval = {}
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(self._url) as res:
                response = res

                if response.status != 200:
                    _LOGGER.error(f"Failed to fetch webpage. Status code: {response.status}. {await response.text()}")
                    return retval

                # Step 2: Parse the HTML content
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")

                product_tags = soup.find_all("div", {"class": "product-detail__variant"})
                for tag in product_tags:
                    name = ""
                    try:
                        name = tag.findChild("div", {"class": "product-detail__variant-name"}).text
                        original = getPrice('original', tag)
                        discount = getPrice('discount', tag)
                        prices = []
                        if original is not None:
                            prices.append(original)
                        if discount is not None:
                            prices.append(discount)
                        retval[name] = min(prices)
                    except Exception as e:
                        _LOGGER.debug(f"Error parsing {name}. {e}")

        return retval
            
