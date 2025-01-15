import random

from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional, Union, Generator
from uuid import uuid4

from .connections import Bound
from .rooms import Point, Room, Stairs


@dataclass(frozen=True, eq=True)
class LevelSpec:
    """A level spec includes all the knobs to generate a level."""
    name: str
    width: int
    height: int
    floors: Bound
    rooms: Bound
    room_width: Bound
    room_height: Bound
    room_alg: str
    room_shape: str
    hall_density: float
    hall_width: int
    trap_chance: float
    monster_chance: float
    shop_chance: float
    treasure_chance: float
    stairs_down: Bound
    towers: bool
    probability: float
    extra: Dict[str, Any] = field(default_factory=dict, compare=False)

    def updated(self, **kwargs) -> "LevelSpec":
        """Returns a copy of the spec with fields in kwargs set to corresponding values."""
        curr = { f.name: getattr(self, f.name) for f in fields(self) }
        return LevelSpec(**(curr | kwargs))


def UniformRoomFactory(
    spec: LevelSpec,
    up: List[Point],
    use_towers: bool = False,
) -> Generator[Room, None, None]:
    """A generator that returns randomly created rooms."""
    stairs_up = len(up)
    stairs_down = random.randint(spec.stairs_down.lower, spec.stairs_down.upper)
    if use_towers:
        stairs_down = max(0, stairs_down - stairs_up)
 
    for _ in range(max(random.randint(spec.rooms.lower, spec.rooms.upper), stairs_up + stairs_down)):
        is_shop = random.random() < spec.shop_chance
        w = random.randint(spec.room_width.lower, spec.room_width.upper)
        h = random.randint(spec.room_height.lower, spec.room_height.upper)
        location = Point(
            random.randint(0, spec.width - w),
            random.randint(0, spec.height - h),
        )
        stair = Stairs.NONE
        if stairs_up > 0:
            stairs_up -= 1
            stair = Stairs.UP
            is_shop = False
            location = up[stairs_up]
        elif stairs_down > 0:
            stairs_down -= 1
            stair = Stairs.DOWN
            is_shop = False
        if use_towers:
            stair |= Stairs.DOWN
        yield Room(
            id = uuid4(),
            location = location,
            width = w,
            height = h,
            shop = is_shop,
            monsters = False if is_shop else random.random() < spec.monster_chance,
            treasure = False if is_shop else random.random() < spec.treasure_chance,
            trap = False if is_shop else random.random() < spec.trap_chance,
            stairs = stair,
        )

def ClusteredRoomFactory(
    spec: LevelSpec,
    up: List[Point],
    use_towers: bool = False,
) -> Generator[Room, None, None]:
    """A generator that returns randomly created rooms in connecting clusters."""
    std_mult = spec.extra.get("cluster_std", 2)
    start_count = spec.extra.get("cluster_starts", 5)
    uniform_gen = UniformRoomFactory(spec, up, use_towers)
    start_rooms: List[Room] = []
    while room := next(uniform_gen, None):
        if room.stairs == Stairs.NONE and len(start_rooms) >= start_count:
            break
        start_rooms.append(room)
        yield room
    for start in start_rooms:
        curr = start
        for _ in range(int(spec.rooms.lower / len(start_rooms)), int(spec.rooms.upper / len(start_rooms))):
            is_shop = random.random() < spec.shop_chance
            w = random.randint(spec.room_width.lower, spec.room_width.upper)
            h = random.randint(spec.room_height.lower, spec.room_height.upper)
            location = Point(
                int(random.gauss(curr.location.x, std_mult * spec.room_width.upper)),
                int(random.gauss(curr.location.y, std_mult *  spec.room_height.upper)),
            )
            while (
                location.x <= 0
                or location.y <= 0
                or location.x >= spec.width - w
                or location.y >= spec.height - h
            ):
                location = Point(
                    int(random.gauss(curr.location.x, std_mult * spec.room_width.upper)),
                    int(random.gauss(curr.location.y, std_mult *  spec.room_height.upper)),
                )

            curr = Room(
                id = uuid4(),
                location = location,
                width = w,
                height = h,
                shop = is_shop,
                monsters = False if is_shop else random.random() < spec.monster_chance,
                treasure = False if is_shop else random.random() < spec.treasure_chance,
                trap = False if is_shop else random.random() < spec.trap_chance,
                stairs = Stairs.DOWN if use_towers else Stairs.NONE,
            )
            yield curr

def LinearRoomFactory(
    spec: LevelSpec,
    up: List[Point],
    use_towers: bool = False,
) -> Generator[Room, None, None]:
    """A generator that returns randomly created rooms in linear rows."""
    block_width = spec.extra.get("block_width", 120)
    block_height = spec.extra.get("block_height", 120)
    empty_block_chance = spec.extra.get("empty_block_chance", 0.2)
    floor_area = spec.width * spec.height
    block_count = Bound(
        lower = int(floor_area / ((block_width + spec.room_width.upper) * (block_height + spec.room_height.upper))),
        upper = int(floor_area / ((block_width + spec.room_width.lower) * (block_height + spec.room_height.lower))),
    )

    # Get starting rooms
    uniform_gen = UniformRoomFactory(spec, up, use_towers)
    room_count = 0
    while room := next(uniform_gen, None):
        if room.stairs == Stairs.NONE or (use_towers and room_count < spec.rooms.lower):
            break
        room_count += 1
        yield room
    if spec.rooms.upper == 0:
        return
    total_rooms = (
        spec.rooms.lower if spec.rooms.upper - room_count > spec.rooms.lower
        else random.randint(spec.rooms.lower, spec.rooms.upper - room_count)
    )
    rooms_in_block = Bound(
        lower = int(total_rooms / block_count.upper),
        upper = int(total_rooms / block_count.lower),
    )

    # Generate rows of blocks
    curr_y = random.randint(spec.room_height.lower, spec.room_height.upper)
    while curr_y + block_height <= spec.height:
        curr_x = random.randint(spec.room_width.lower, spec.room_width.upper)
        while curr_x + block_width <= spec.width:
            # decide if we should skip and leave this an empty space
            if random.random() < empty_block_chance:
                curr_x += block_width + random.randint(spec.room_width.lower, spec.room_width.upper)
                continue
            rf = UniformRoomFactory(
                spec.updated(
                    width = block_width,
                    height = block_height,
                    rooms = rooms_in_block,
                    room_alg = "uniform",
                    stairs_down = Bound(0, 0),
                ),
                up = [],
                use_towers = use_towers,
            )

            while room := next(rf, None):
                yield Room(
                    id = room.id,
                    location = Point(
                        curr_x + room.location.x,
                        curr_y + room.location.y,
                    ),
                    width = room.width,
                    height = room.height,
                    monsters = room.monsters,
                    treasure = room.treasure,
                    trap = room.trap,
                    shop = room.shop,
                    stairs = room.stairs,
                )
            curr_x += block_width + random.randint(spec.room_width.lower, spec.room_width.upper)
        curr_y += block_height + random.randint(spec.room_height.lower, spec.room_height.upper)


# Mapping of names to generators
generator_map = {
    "uniform": UniformRoomFactory,
    "clustered": ClusteredRoomFactory,
    "linear": LinearRoomFactory,
}

def RoomFactory(
    spec: LevelSpec,
    up: List[Point],
    use_towers: bool = False,
) -> Generator[Room, None, None]:
    try:
        return generator_map[spec.room_alg](spec, up, use_towers)
    except KeyError:
        raise Exception(f"{spec.room_alg} is not a recognized room creation algorithm.")
