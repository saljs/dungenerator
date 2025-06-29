#!/bin/env python3

# This is the main runner for dungen
# It takes a DunSpec file and outputs a .dng file.

import argparse
import progressbar
import random
import svg
import sys

from pathlib import Path
from typing import Dict, List, Optional, Tuple, cast

from .dunspec import DunSpec
from .dungensave import DungenSave
from .connections import Bound
from .encounter import Encounter
from .level import Level
from .level_drawer import LevelDrawer, FillPatterns, handle_no_floors
from .room_generators import LevelSpec
from .rooms import Point, Stairs, Room

# individual room drawers
from .rect_room_drawer import RectRoomDrawer
from .mixed_room_drawer import MixedRoomDrawer
from .organic_room_drawer import OrganicRoomDrawer

# Map of shapes to drawers
drawer_map: Dict[str, LevelDrawer] = {
    "rect": cast(LevelDrawer, RectRoomDrawer()),
    "mixed": cast(LevelDrawer, MixedRoomDrawer()),
    "organic": cast(LevelDrawer, OrganicRoomDrawer()),
}


def create_level(
    spec: LevelSpec,
    entrances: List[Point],
    level_textures: FillPatterns,
    level_number: int,
    savefile: DungenSave,
    bottom_level: bool,
) -> Tuple[List[Point], List[svg.SVG]]:
    """Creates a level from a spec."""
    imgs = []
    stairs_up = entrances
    num_floors = random.randint(spec.floors.lower, spec.floors.upper)
    for floor_number in range(num_floors):
        stairs_bound = spec.stairs_down
        rooms_bound = spec.rooms
        if bottom_level and floor_number == num_floors - 1:
            # last level
            stairs_bound = Bound(0, 0)
        elif spec.towers:
            # if making towers, reduce number of rooms
            rooms_bound = Bound(
                int(spec.rooms.lower * (floor_number / (num_floors - 1))),
                int(spec.rooms.upper * (floor_number / (num_floors - 1))),
            )
        
        level = Level(
            spec.updated(rooms = rooms_bound, stairs_down = stairs_bound),
            stairs_up,
            towers = spec.towers and floor_number < num_floors - 1,
        )
        stairs_up = [r.location for r in level.rooms if Stairs.DOWN in r.stairs]

        try:
            drawer = drawer_map[spec.room_shape]
        except KeyError:
            raise Exception(f"{spec.room_shape} is not a recognized room shape.")
        imgs.append(drawer.draw_level(
            level,
            level_textures,
            scale = savefile.scale,
            hall_width = spec.hall_width,
            walls_in_fg = spec.extra.get("walls_in_fg", False),
        ))

    if "no_floors" in spec.extra:
        handle_no_floors(imgs, savefile.scale, **spec.extra["no_floors"])

    savefile.add_level(
        level_number,
        {i + 1: img for i, img in enumerate(imgs)},
        f"Level {level_number}: {spec.name}\nThis level contains {floor_number + 1} floors.",
    )

    return (stairs_up, imgs) 


def main_func():
    parser = argparse.ArgumentParser(description="DunGenerator: Dynamically generate dungeons")
    parser.add_argument(
        "spec",
        type = Path,
        help = "DunSpec YAML definition file.",
    )
    parser.add_argument(
        "savefile",
        type = Path,
        help = "Path to save output file.",
    )
    parser.add_argument(
        "--svg-out",
        type = Path,
        default = None,
        help = "Export levels to svg files.",
    )
    parser.add_argument(
        "-a",
        "--append",
        action = "store_true",
        default = False,
        help = "Append to existing Dungen savefile.",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        action = "store_true",
        default = False,
        help = "Overwrite existing Dungen savefile.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action = "store_true",
        default = False,
        help = "Print a summary.",
    )
    args = parser.parse_args()
    spec = DunSpec.from_yaml(args.spec)

    if args.savefile.exists() and not (args.overwrite or args.append):
        # Exit when we try to overwrite without flag
        print(f"File {args.savefile} already exists. Use -o to overwrite.", file = sys.stderr)
        sys.exit(2)
    elif args.overwrite and args.append:
        # Exit with incompatable args
        print(f"Cannot specify both --append and --override.", file = sys.stderr)
        sys.exit(2)
    elif args.overwrite:
        # Overwite existing file
        args.savefile.unlink()

    savefile = DungenSave(args.savefile, scale = spec.scale)
    stairs_up: Optional[List[Point]] = None

    if args.savefile.exists() and args.append:
        # Add stairs down
        last_level = savefile.levels
        last_floor_num = savefile.floor_count(last_level)
        last_floor = savefile.get_floor(last_level, last_floor_num)
        if last_floor is None:
            raise AttributeError("Error: cannot append to file, it is malformed")
        room_els = last_floor.room_elements()
        selected_rooms = random.choices(room_els, k = spec.entrances)
        for room in selected_rooms:
            # Edit classes to make stairs go down here
            room.class_.append("down") # type: ignore[attr-defined]
            if room.data is None:
                raise AttributeError("Error: cannot append to file, it is malformed")
            room.data["room-note"] += "There are stairs down here.\n"
        savefile.set_floor(last_level, last_floor_num, last_floor)
        stairs_up = [Point.from_dict(room.data) for r in selected_rooms] # type: ignore[arg-type]

    starting_levels = savefile.levels
    for i in progressbar.progressbar(range(1, spec.level_count + 1)):
        i += starting_levels
        level_spec, = random.choices(spec.levels, weights=[ls.probability for ls in spec.levels])
        if stairs_up is None:
            stairs_up = [
                Point(
                    random.randint(0, level_spec.width - level_spec.room_width.upper), 
                    random.randint(0, level_spec.height - level_spec.room_height.upper), 
                ) for _ in range(spec.entrances)
            ]
        stairs_up, imgs = create_level(
            level_spec,
            stairs_up,
            spec.textures[level_spec],
            i,
            savefile,
            i - starting_levels == spec.level_count,
        )

        if args.svg_out is not None:
            args.svg_out.mkdir(exist_ok = True)
            level_dir = args.svg_out.joinpath(f"level_{i}")
            level_dir.mkdir(exist_ok = True)
            for j, img in enumerate(imgs):
                svg_path = level_dir.joinpath(f"floor_{j + 1}.svg")
                svg_path.write_text(str(img))

    if args.verbose:
        print(f"Dungeon has {savefile.levels} levels:")
        for lvlid in range(1, savefile.levels + 1):
            print(f"  Level {lvlid}")
            for floorid in range(1, savefile.floor_count(lvlid) + 1):
                floor = savefile.get_floor(lvlid, floorid)
                if floor is None:
                    print(f"    Missing! Floor {floorid}")
                    continue
                down_c = len(floor.room_elements("down"))
                up_c = len(floor.room_elements("up"))
                print(f"    Floor {floorid}: {len(floor.room_elements())} Rooms [{up_c} U {down_c} D].")

if __name__ == "__main__":
    main_func()
