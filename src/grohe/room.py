"""
Grohe room
"""

import logging
from typing import Dict, List, Optional


from grohe.appliance import Appliance

_LOGGER = logging.getLogger(__name__)


class Room:
    def __init__(self, location_id: int, data: Dict, session) -> None:
        self._location_id = location_id
        self._session = session
        self._appliances = []
        self._data = {}
        self.update(data)

    def appliance(self, id: str) -> Optional[Appliance]:
        for appliance in self._appliances:
            if appliance.id == id:
                return appliance
        return None

    async def appliances(self) -> List[Appliance]:
        if not self._appliances:
            for appliance in await self._session.call(
                f"locations/{self._location_id}/rooms/{self.id}/appliances"
            ):
                self._appliances.append(
                    Appliance.get(self._location_id, self.id, appliance, self._session)
                )
        return self._appliances

    @property
    def id(self) -> int:
        return self._data.get("id", -1)

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def role(self) -> str:
        return self._data.get("role", -1)

    @property
    def room_type(self) -> int:
        return self._data.get("room_type", -1)

    @property
    def type(self) -> int:
        return self._data.get("type", -1)

    def update(self, data: Dict) -> None:
        self._data = data
        if "appliances" in self._data:
            for appliance_data in data["appliances"]:
                if "appliance_id" not in appliance_data:
                    _LOGGER.warning(
                        "Grohe API returned appliance without an appliance_id: %s",
                        appliance_data,
                    )
                    continue
                appliance = self.appliance(appliance_data["appliance_id"])
                if appliance:
                    appliance.update(appliance_data)
                else:
                    self._appliances.append(
                        Appliance.get(
                            self._location_id, self.id, appliance_data, self._session
                        )
                    )
            # No need to keep the data in this object since the appliance have a copy of it
            del self._data["appliances"]
