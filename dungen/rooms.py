from dataclasses import dataclass
from enum import Flag, auto
from typing import List, Union
from uuid import UUID

class Stairs(Flag):
    NONE = 0
    UP = auto()
    DOWN = auto()

@dataclass(frozen=True)
class Point:
    """Object that holds a x, y coordinate."""
    x: Union[int, float]
    y: Union[int, float]

@dataclass(frozen=True)
class Room:
    """Object that holds data representing a room."""
    id: UUID
    location: Point
    width: int
    height: int
    monsters: bool
    treasure: bool
    trap: bool
    shop: bool
    stairs: Stairs

    @property
    def tags(self) -> List[str]:
        tags = []
        if self.monsters:
            tags.append("monsters")
        if self.treasure:
            tags.append("treasure")
        if self.trap:
            tags.append("trap")
        if self.shop:
            tags.append("shop")
        if Stairs.UP in self.stairs:
            tags.append("up")
        if Stairs.DOWN in self.stairs:
            tags.append("down")
        return tags
