"""
Grohe session, using grohe app api
"""

from enum import IntEnum
import logging
from typing import Dict

_LOGGER = logging.getLogger(__name__)


class Appliance:
    class Type(IntEnum):
        UNSUPPORTED = 0  # Unknown/Unsupported appliance type
        SENSE = 101  # Type identifier for the battery powered water detector
        SENSE_GUARD = 103  # Type identifier for sense guard, the water guard installed on your water pipe
        BLUE_HOME = 104  # Type identifier for Grohe Blue Home, chiled water tap

    def __init__(self, location_id: int, room_id: int, data: Dict, session) -> None:
        self._location_id = location_id
        self._room_id = room_id
        self._session = session
        self._data = {}
        self.update(data)

    async def command(self, data: Dict):
        command_response = await self._session.call(
            f"locations/{self._location_id}/rooms/{self._room_id}/appliances/{self.id}/command",
            data=data,
            method="post",
        )
        return command_response

    @property
    def id(self) -> str:
        return self._data.get("appliance_id", "")

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def type(self) -> Type:
        try:
            return Appliance.Type(self._data.get("type", 0))
        except ValueError:
            return Appliance.Type.UNSUPPORTED

    def update(self, data: Dict) -> None:
        self._data = data

    @staticmethod
    def get(location_id: int, room_id: int, data: Dict, session):
        types = {
            Appliance.Type.SENSE: GroheSenseSensor,
            Appliance.Type.SENSE_GUARD: GroheSenseGuardValve,
            Appliance.Type.BLUE_HOME: GroheBlueHomeTap,
        }
        Cls = types.get(data.get("type", 0), None)
        if not Cls:
            return None
        return Cls(location_id, room_id, data, session)


class GroheSenseSensor(Appliance):
    pass


class GroheSenseGuardValve(Appliance):
    pass


class GroheBlueHomeTap(Appliance):
    class WaterType(IntEnum):
        STILL_WATER = 1
        CARBONATED_WATER = 2

    def open_carbonated_water(self, amount_ml: int):
        pass

    async def open_water(self, type: WaterType, amount_ml: int):
        return await self.command(
            {"command": {"tap_type": type.value, "tap_amount": amount_ml}}
        )
