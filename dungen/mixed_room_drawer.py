import math
import svg

from enum import Enum
from random import Random
from typing import Collection, List, Tuple

from .connections import Connections, Hallway
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
    def draw_rooms(
        rooms: Collection[Room], scale: int, fill: str, border: str, rng: Random, set_ids: bool = True
    ) -> List[svg.Element]:
        ret: List[svg.Element] = []
        for r in rooms:
            # TODO: chack if aspect ratio is close to square, make circle instead.
            if is_room_near_square(r):
                radius = int(((r.width + r.height) / 2) / 2)
                ret +=  [
                    svg.Circle(
                        cx = (r.location.x + radius) * scale,
                        cy = (r.location.y + radius) * scale,
                        r = radius * scale,
                        fill = fill,
                        stroke = border,
                        id = f"room-{r.id}" if set_ids else None,
                        class_ = (["room"] + r.tags) if set_ids else None,
                        stroke_width = scale,
                        paint_order = "stroke",
                    ),
                ]
            else: 
                ret +=  [
                    svg.Rect(
                        x = r.location.x * scale,
                        y = r.location.y * scale,
                        width = r.width * scale,
                        height = r.height * scale,
                        fill = fill,
                        stroke = border,
                        id = f"room-{r.id}" if set_ids else None,
                        class_ = (["room"] + r.tags) if set_ids else None,
                        stroke_width = scale,
                        paint_order = "stroke",
                    ),
                ]
        return ret

    @staticmethod
    def draw_hallways(
        hallways: Connections, scale: int, fill: str, width: int, rng: Random
    ) -> List[svg.Element]:
        ret:List[svg.Element] = []
        for hall in sorted(hallways, reverse=True):
            # pick sides
            room1_side = None
            room2_side = None
            if (
                hall.room1.location.x < hall.room2.location.x
                and hall.room1.location.y < hall.room2.location.y
            ):
                #hall.room1 upper left of hall.room2
                room1_side = rng.choice([Sides.RIGHT, Sides.BOTTOM])
                room2_side = rng.choice([Sides.LEFT, Sides.TOP])
            elif (
                hall.room1.location.x > hall.room2.location.x
                and hall.room1.location.y < hall.room2.location.y
            ):
                #hall.room1 upper right of hall.room2
                room1_side = rng.choice([Sides.LEFT, Sides.BOTTOM])
                room2_side = rng.choice([Sides.RIGHT, Sides.TOP])
            elif (
                hall.room1.location.x < hall.room2.location.x
                and hall.room1.location.y > hall.room2.location.y
            ):
                #hall.room1 lower left of hall.room2
                room1_side = rng.choice([Sides.RIGHT, Sides.TOP])
                room2_side = rng.choice([Sides.LEFT, Sides.BOTTOM])
            else:
                #hall.room1 lower right of hall.room2
                room1_side = rng.choice([Sides.LEFT, Sides.TOP])
                room2_side = rng.choice([Sides.RIGHT, Sides.BOTTOM])

            # generate points
            start = random_point(hall.room1, room1_side, rng)
            if is_room_near_square(hall.room1):
                radius = int(((hall.room1.width + hall.room1.height) / 2) / 2)
                start = Point(hall.room1.location.x + radius, hall.room1.location.y + radius)
            end = random_point(hall.room2, room2_side, rng)
            if is_room_near_square(hall.room2):
                radius = int(((hall.room2.width + hall.room2.height) / 2) / 2)
                end = Point(hall.room2.location.x + radius, hall.room2.location.y + radius)
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

            ret += [ 
                svg.Path(
                    d = path,  # type: ignore[arg-type]
                    fill = "transparent",
                    stroke = fill,
                    stroke_width = scale * width,
                    class_ = ["hall"],
                ),
            ]
        return ret
