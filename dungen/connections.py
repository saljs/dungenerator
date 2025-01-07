import random

from dataclasses import dataclass
from typing import Collection, Iterator, Set, Tuple, cast

from .rooms import Room

@dataclass(frozen=True)
class Bound:
    """Represents a lower and upper integer bound on a value."""
    lower: int
    upper: int

@dataclass(frozen=True)
class Hallway:
    """Object that represents a hallway as an agenency between rooms."""
    room1: Room
    room2: Room

    @property
    def distance(self) -> int:
        """L1 distance between rooms."""
        return (int(
            abs(self.room1.location.x - self.room2.location.x)
            + abs(self.room1.location.y - self.room2.location.y)
        ))
        
    def __eq__(self, other) -> bool:
        return (
            self.room1 == other.room1
            or self.room1 == other.room2
            or self.room2 == other.room1
            or self.room2 == other.room2
        )

    def __lt__(self, other: "Hallway") -> bool:
        if not isinstance(other, Hallway):
            return False
        return self.distance < other.distance

    def __gt__(self, other: "Hallway") -> bool:
        return self.distance > other.distance

    def __hash__(self):
        return hash(self.room1) + hash(self.room2)

class Connections:
    """An adjency list of hallways between rooms"""

    def __init__(self, rooms: Collection[Room]):
        """Initializes the connection list by connecting all rooms 
        to each other."""
        self._rooms: Collection[Room] = rooms
        self._hallways: Set[Hallway] = {
            Hallway(s, e) for s in rooms for e in rooms if s != e
        }

    def room_hallways(self, room: Room) -> Set[Hallway]:
        return {x for x in self._hallways if x.room1.id == room.id or x.room2.id == room.id}

    def prune(self, density: float = 0.2):
        """Prunes the numbers of hallways between rooms"""
        if len(self._rooms) < 2:
            return
        mst_rooms: Set[Room] = { self._rooms[0] } # type: ignore[index]
        mst_edges: Set[Hallway] = set()
        adj_list = sorted(self._hallways)
        curr_room = self._rooms[0] # type: ignore[index]
        while len(mst_rooms) < len(self._rooms):
            for edge in adj_list:
                if edge.room1 == curr_room and edge.room2 not in mst_rooms:
                    mst_edges.add(edge)
                    mst_rooms.add(edge.room2)
                    curr_room = edge.room2
                    break
                elif edge.room2 == curr_room and edge.room1 not in mst_rooms:
                    mst_edges.add(edge)
                    mst_rooms.add(edge.room1)
                    curr_room = edge.room1
                    break
        self._hallways = mst_edges.union(
            random.choices(adj_list, k = int(len(mst_edges) * density)) # type: ignore[arg-type]
        )

    def __iter__(self) -> Iterator[Hallway]:
        return iter(self._hallways)

    def __next__(self):
        pass
