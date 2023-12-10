"""
Grohe session, using grohe app api
"""

import logging
from typing import Generator, Optional

import aiohttp

from grohe.appliance import Appliance

from grohe.location import Location
from grohe.room import Room

_LOGGER = logging.getLogger(__name__)


class Session:
    BASE_URL = "https://idp2-apigw.cloud.grohe.com/v3/iot/"
    """Grohe app session

    Args:
        refresh_token (str): Username used to login to verisure app

    """

    def __init__(self, refresh_token):
        self._refresh_token = refresh_token
        self._access_token = ""
        self._locations = []

    @property
    def access_token(self) -> str:
        return self._access_token

    @access_token.setter
    def access_token(self, access_token):
        self._access_token = access_token

    async def get_access_token(self):
        data = {"refresh_token": self._refresh_token}
        headers = {"Content-Type": "application/json"}
        url = self.BASE_URL + "oidc/refresh"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status not in (200, 201):
                    return False
                json = await response.json()
                self._access_token = json.get("access_token")
        return True

    async def appliance(self, id: str) -> Optional[Appliance]:
        async for appliance in self.appliances():
            if appliance.id == id:
                return appliance
        return None

    async def appliances(self) -> Generator[Appliance, None, None]:
        async for room in self.rooms():
            for appliance in await room.appliances():
                yield appliance

    async def discover(self) -> None:
        dashboard = await self.request("dashboard")
        for location_data in dashboard.get("locations", []):
            if "id" not in location_data:
                _LOGGER.warning(
                    "Grohe API returned location without an id: %s", location_data
                )
                continue
            location = self.location(location_data["id"])
            if location:
                location.update(location_data)
            else:
                self._locations.append(Location(location_data, self))

    def location(self, id: int) -> Optional[Location]:
        for location in self._locations:
            if location.id == id:
                return location
        return None

    async def locations(self) -> Generator[Location, None, None]:
        if not self._locations:
            for location in await self.request("locations"):
                self._locations.append(Location(location, self))
        for location in self._locations:
            yield location

    @property
    def refresh_token(self) -> str:
        return self._refresh_token

    async def request(self, path, data=None, method=None):
        """Make a request."""
        if not self._access_token:
            await self.get_access_token()
        method = method or "get"
        url = self.BASE_URL + path
        for _ in range(2):
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self._access_token,
            }
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, headers=headers, json=data
                ) as response:
                    if response.status == 401:
                        # Token expired, get new
                        _LOGGER.info("Token expired, fetch new")
                        if await self.get_access_token():
                            continue
                        else:
                            _LOGGER.info("Could not get access token")
                            break
                    if response.status not in (200, 201):
                        _LOGGER.error(f"Could not access API: {await response.text()}")
                        return []
                    return await response.json()

    async def room(self, id: int) -> Optional[Room]:
        async for room in self.rooms():
            if room.id == id:
                return room
        return None

    async def rooms(self) -> Generator[Room, None, None]:
        async for location in self.locations():
            for room in await location.rooms():
                yield room
