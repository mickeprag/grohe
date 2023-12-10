"""
Grohe Location
"""

import logging
from typing import Dict, List, Optional

from grohe.room import Room

_LOGGER = logging.getLogger(__name__)


class Location:
    def __init__(self, data: Dict, session) -> None:
        self._session = session
        self._rooms = []
        self._data = {}
        self.update(data)

    @property
    def id(self) -> int:
        return self._data.get("id", -1)

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    def room(self, id: int) -> Optional[Room]:
        for room in self._rooms:
            if room.id == id:
                return room
        return None

    async def rooms(self) -> List[Room]:
        if not self._rooms:
            for room in await self._session.call(f"locations/{self.id}/rooms"):
                self._rooms.append(Room(self.id, room, self._session))
        return self._rooms

    def update(self, data: Dict) -> None:
        self._data = data
        if "rooms" in self._data:
            for room_data in data["rooms"]:
                if "id" not in room_data:
                    _LOGGER.warning(
                        "Grohe API returned room without an id: %s", room_data
                    )
                    continue
                room = self.room(room_data["id"])
                if room:
                    room.update(room_data)
                else:
                    self._rooms.append(Room(self.id, room_data, self._session))
            # No need to keep the data in this object since the rooms have a copy of it
            del self._data["rooms"]
