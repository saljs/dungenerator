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

    @classmethod
    def from_dict(cls, info: dict) -> "Point":
        """Returns a point from a dict that contains x and y keys. If either
        key is not present, the corresponding value will be 0."""
        return Point(
            int(info.get("x", "0")),
            int(info.get("y", "0")),
        )

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

    @property
    def note(self) -> str:
        return (
            f"{'This room is a shop.\n' if self.shop else ''}"
            + f"{'This room contains monsters.\n' if self.monsters else ''}"
            + f"{'This room contains treasure.\n' if self.treasure else ''}"
            + f"{'There is a trap here.\n' if self.trap else ''}"
            + f"{'There are stairs up here.\n' if Stairs.UP in self.stairs else ''}"
            + f"{'There are stairs down here.\n' if Stairs.DOWN in self.stairs else ''}"
        )
