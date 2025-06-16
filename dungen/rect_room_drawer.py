import math
import svg

from enum import Enum
from random import Random

from .connections import Hallway
from .level import Level
from .level_drawer import LevelDrawer
from .rooms import Room, Point, Stairs

class Sides(Enum):
    LEFT = 0
    RIGHT = 1
    TOP = 2
    BOTTOM = 3

def random_point(room: Room, wall: Sides, rng: Random) -> Point:
    """Returns a random point near the edge of a room."""
    x = int(room.location.x + 1)
    y = int(room.location.y + 1)
    match wall:
        case Sides.LEFT:
            y = rng.randint(y, y + room.height - 2)
        case Sides.RIGHT:
            x += room.width - 2
            y = rng.randint(y, y + room.height - 2)
        case Sides.TOP:
            x = rng.randint(x, x + room.width - 2)
        case Sides.BOTTOM:
            x = rng.randint(x, x + room.width - 2)
            y += room.height - 2
    return Point(x, y)

class RectRoomDrawer(LevelDrawer):
    """Draws rectangular rooms and straight hallways."""

    @staticmethod
    def draw_room(
        room: Room, scale: int, fill: str, border: str, rng: Random
    ) -> svg.Element:
        return svg.Rect(
            x = room.location.x * scale,
            y = room.location.y * scale,
            width = room.width * scale,
            height = room.height * scale,
            fill = fill,
            stroke = border,
            stroke_width = scale,
            paint_order = "stroke",
        )

    @staticmethod
    def draw_hallway(
        hallway: Hallway, scale: int, fill: str, width: int, rng: Random
    ) -> svg.Element:
        # pick sides
        room1_side = None
        room2_side = None
        if (
            hallway.room1.location.x < hallway.room2.location.x
            and hallway.room1.location.y < hallway.room2.location.y
        ):
            #hallway.room1 upper left of hallway.room2
            room1_side = rng.choice([Sides.RIGHT, Sides.BOTTOM])
            room2_side = rng.choice([Sides.LEFT, Sides.TOP])
        elif (
            hallway.room1.location.x > hallway.room2.location.x
            and hallway.room1.location.y < hallway.room2.location.y
        ):
            #hallway.room1 upper right of hallway.room2
            room1_side = rng.choice([Sides.LEFT, Sides.BOTTOM])
            room2_side = rng.choice([Sides.RIGHT, Sides.TOP])
        elif (
            hallway.room1.location.x < hallway.room2.location.x
            and hallway.room1.location.y > hallway.room2.location.y
        ):
            #hallway.room1 lower left of hallway.room2
            room1_side = rng.choice([Sides.RIGHT, Sides.TOP])
            room2_side = rng.choice([Sides.LEFT, Sides.BOTTOM])
        else:
            #hallway.room1 lower right of hallway.room2
            room1_side = rng.choice([Sides.LEFT, Sides.TOP])
            room2_side = rng.choice([Sides.RIGHT, Sides.BOTTOM])

        # generate points
        start = random_point(hallway.room1, room1_side, rng)
        end = random_point(hallway.room2, room2_side, rng)
        middle = Point(
            int((start.x + end.x) / 2),
            int((start.y + end.y) / 2),
        )

        # create pathspec
        path = f"M {start.x * scale} {start.y * scale} "
        if room1_side in [Sides.LEFT, Sides.RIGHT]:
            # make horizontal line first
            path += f"H {middle.x * scale} V {middle.y * scale} "
        else:
            # make a vertical line first
            path += f"V {middle.y * scale} H {middle.x * scale} "
        if room2_side in [Sides.LEFT, Sides.RIGHT]:
            # make horizontal line last
            path += f"V {end.y * scale} H {end.x * scale}"
        else:
            # make a vertical line last
            path += f"H {end.x * scale} V {end.y * scale}"

        return svg.Path(
            d = path,  # type: ignore[arg-type]
            fill = "transparent",
            stroke = fill,
            stroke_width = scale * width,
            class_ = ["hall"],
        )
