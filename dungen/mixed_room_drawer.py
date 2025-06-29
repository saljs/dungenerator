import math
import svg

from enum import Enum
from random import Random

from .connections import Hallway
from .level import Level
from .level_drawer import LevelDrawer
from .rooms import Room, Point, Stairs
from .rect_room_drawer import Sides, random_point

def is_room_near_square(room: Room) -> bool:
    """Returns true if the room is within 10% of square."""
    return (
        room.width / room.height >= 0.9
        and room.width / room.height <= 1.1
    )

class MixedRoomDrawer(LevelDrawer):
    """Draws rectangular and circular rooms and straight hallways."""
    @staticmethod
    def draw_room(
        room: Room, scale: int, fill: str, border: str, rng: Random
    ) -> svg.Element:
        if is_room_near_square(room):
            radius = int(((room.width + room.height) / 2) / 2)
            return svg.Circle(
                cx = (room.location.x + radius) * scale,
                cy = (room.location.y + radius) * scale,
                r = radius * scale,
                fill = fill,
                stroke = border,
                stroke_width = scale,
                paint_order = "stroke",
            )
        return  svg.Rect(
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
       if is_room_near_square(hallway.room1):
           radius = int(((hallway.room1.width + hallway.room1.height) / 2) / 2)
           start = Point(hallway.room1.location.x + radius, hallway.room1.location.y + radius)
       end = random_point(hallway.room2, room2_side, rng)
       if is_room_near_square(hallway.room2):
           radius = int(((hallway.room2.width + hallway.room2.height) / 2) / 2)
           end = Point(hallway.room2.location.x + radius, hallway.room2.location.y + radius)
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
       )
