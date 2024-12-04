from dataclasses import dataclass
from enum import Enum
from typing import List, Union
from uuid import UUID


class Stairs(Enum):
    NONE = 0
    UP = 1
    DOWN = 2

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
        if self.stairs == Stairs.UP:
            tags.append("up")
        elif self.stairs == Stairs.DOWN:
            tags.append("down")
        return tags
