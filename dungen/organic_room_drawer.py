import math
import svg

from enum import Enum
from typing import Collection, List
from random import Random

from .connections import Connections, Hallway
from .level import Level
from .level_drawer import LevelDrawer
from .rooms import Room, Point, Stairs

PATH_SEG_LEN = 1.5

def l2_dist(p1: Point, p2: Point) -> float:
    return math.sqrt(
        math.pow((p2.x - p1.x), 2) +
        math.pow((p2.y - p1.y), 2)
    )

def random_walk(start: Point, end: Point, vlen: float, rng: Random) -> List[Point]:
    """Draws a randomly walked path between start and end."""
    curr = start
    path: List[Point] = []
    rand_vec = 0.4
    while l2_dist(curr, end) > vlen:
        goal_vec_angle = math.atan2(end.y - curr.y, end.x - curr.x)
        rand_vec_angle = rng.uniform(0, 2*math.pi)

        next_point = Point(
            curr.x + (rand_vec * vlen * math.cos(rand_vec_angle)) + ((1 - rand_vec) * vlen * math.cos(goal_vec_angle)),
            curr.y + (rand_vec * vlen * math.sin(rand_vec_angle)) + ((1 - rand_vec) * vlen * math.sin(goal_vec_angle)),
        )
        path.append(curr)
        curr = next_point
    return path

def random_point_in_triangle(p1: Point, p2: Point, p3: Point, rng: Random) -> Point:
    """Chooses a random point in a triangular region."""
    x, y = sorted([rng.random(), rng.random()])
    s, t, u = x, y - x, 1 - y
    return Point(
        (p1.x * s) + (t * p2.x) + (u * p3.x),
        (p1.y * s) + (t * p2.y) + (u * p3.y),
    )

def random_point_on_ellipse(
    center: Point,
    width: int,
    height: int, 
    min_angle: float,
    max_angle: float,
    rng: Random,
) -> Point:
    """Chooses a random point along the edge of an elipse."""
    angle = rng.uniform(min_angle, max_angle)
    return Point(
        center.x + ((width / 2) * math.cos(angle)),
        center.y + ((height / 2) * math.sin(angle)),
    )

def points_to_pathstr(points: List[Point], scale: int, closed: bool = True) -> str:
    pathstr = f"M {points[0].x * scale} {points[0].y * scale} "
    for i in range(1, len(points)):
        pathstr += f"L {points[i].x * scale} {points[i].y * scale} "
    if closed:
        pathstr += "Z"
    return pathstr

class OrganicRoomDrawer(LevelDrawer):
    """Draws organic looking rooms and meandering hallways."""

    @staticmethod
    def draw_rooms(
        rooms: Collection[Room], scale: int, fill: str, border: str, rng: Random, set_ids: bool = True
    ) -> List[svg.Element]:
        ret: List[svg.Element] = []
        for r in rooms:
            center_point = Point(
                r.location.x + (r.width / 2),
                r.location.y + (r.height / 2),
            )
            num_int_points = 6
            points: List[Point] = []
            first_point = None
            last_point = None
            for i in range(num_int_points):
                p = random_point_on_ellipse(
                    center_point,
                    r.width,
                    r.height, 
                    ((2 * math.pi) / num_int_points) * i,
                    ((2 * math.pi) / num_int_points) * (i + 1),
                    rng,
                )
                if last_point is not None:
                    points += random_walk(last_point, p, PATH_SEG_LEN, rng)
                else:
                    first_point = p
                last_point = p
            points += random_walk(last_point, first_point, PATH_SEG_LEN, rng) # type: ignore[arg-type]

            ret +=  [
                svg.Path(
                    d = points_to_pathstr(points, scale), # type: ignore[arg-type]
                    fill = fill,
                    stroke = border,
                    id = f"room-{r.id}" if set_ids else None,
                    class_ = (["room"] + r.tags) if set_ids else None,
                    stroke_width = scale * 2,
                    paint_order = "stroke",
                ),
            ]
        return ret

    @staticmethod
    def draw_hallways(
        hallways: Connections, scale: int, fill: str, width: int, rng: Random
    ) -> List[svg.Element]:
        ret:List[svg.Element] = []
        for hall in hallways:
            start_point = Point(
                int(hall.room1.location.x + (hall.room1.width  / 2)),
                int(hall.room1.location.y + (hall.room1.height / 2)),
            )
            mid_point = random_point_in_triangle(
                hall.room1.location,
                Point(hall.room1.location.x, hall.room2.location.y) if rng.random() < 0.5
                else Point(hall.room2.location.x, hall.room1.location.y),
                hall.room2.location,
                rng,
            )
            end_point = Point(
                int(hall.room2.location.x + (hall.room2.width  / 2)),
                int(hall.room2.location.y + (hall.room2.height / 2)),
            )
            points = random_walk(start_point, mid_point, PATH_SEG_LEN, rng)
            points += random_walk(mid_point, end_point, PATH_SEG_LEN, rng)
            ret += [ 
                svg.Path(
                    d = points_to_pathstr(points, scale, closed=False), # type: ignore[arg-type]
                    fill = "transparent",
                    stroke = fill,
                    stroke_width = scale * width,
                    class_ = ["hall"],
                ),
            ]
        return ret
