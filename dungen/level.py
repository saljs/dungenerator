import random
from typing import List, Optional

from .connections import Connections
from .rooms import Point, Stairs
from .room_generators import LevelSpec, RoomFactory

class Level:
    """A level is a collection of rooms and hallways."""
    
    def __init__(
        self,
        spec: LevelSpec,
        up: List[Point],
    ):
        self.width = spec.width
        self.height = spec.height

        # Create rooms and hallways
        self.rooms = tuple(RoomFactory(spec, up))
        self.hallways = Connections(self.rooms)
        self.hallways.prune(spec.hall_density)
    
    def __repr__(self) -> str:
        s = f"Level: {self.width}x{self.height} ({len(self.rooms)} rooms)\n"
        rc = 0
        for room in self.rooms:
            rc += 1
            status = [ ' ' for _ in range(5) ]
            if room.shop:
                status[0] = 'S'
            if room.monsters:
                status[1] = 'M'
            if room.treasure:
                status[2] = '$'
            if room.trap:
                status[3] = 'T'
            if room.stairs == Stairs.UP:
                status[4] = 'U'
            elif room.stairs == Stairs.DOWN:
                status[4] ='D'
            doors = len(self.hallways.room_hallways(room))
            s += f"  Room {rc:3} [{''.join(status)}] {doors} {room.id}\n"
        for hallway in self.hallways:
            r1 = self.rooms.index(hallway.room1) + 1
            r2 = self.rooms.index(hallway.room2) + 1
            s += f"    Room {r1:3} -- Room {r2:3}\n"
        return s
