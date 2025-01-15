#!/bin/env python3

# This is the main runner for dungen
# It takes a DunSpec file and outputs a .dng file.

import argparse
import pickle
import progressbar
import random
import svg

from dataclasses import dataclass, field
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, cast
from uuid import UUID, uuid4

from .drawing import find_element
from .dunspec import DunSpec
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


@dataclass
class DungenSave:
    """The savefile definition."""
    scale: int = 1
    levels: Dict[int, Dict[int, Tuple[Room, ...]]] = field(default_factory=dict)
    images: Dict[int, Dict[int, svg.SVG]] = field(default_factory=dict)
    room_notes: Dict[UUID, str] = field(default_factory=dict)
    room_encounters: Dict[UUID, Encounter] = field(default_factory=dict)
    level_notes: Dict[int, str] = field(default_factory=dict)

    def serialize(self, path: Union[str, Path]):
        if not isinstance(path, Path):
            path = Path(path)
        with path.open("wb") as out:
            out.write(pickle.dumps(self))

    @classmethod
    def deserialize(cls, path: Union[str, Path]) -> "DungenSave":
        if not isinstance(path, Path):
            path = Path(path)
        with path.open("rb") as to_load:
            return pickle.load(to_load)


def create_level(
    spec: LevelSpec,
    entrances: List[Point],
    level_textures: FillPatterns,
    level_number: int,
    savefile: DungenSave,
    bottom_level: bool,
):
    """Creates a level from a spec."""
    rooms = []
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
        rooms.append(level.rooms)
        imgs.append(drawer.draw_level(
            level,
            level_textures,
            scale = savefile.scale,
            hall_width = spec.hall_width,
            walls_in_fg = spec.extra.get("walls_in_fg", False),
        ))
        savefile.room_notes.update({
            r.id: f"Room {i+1}:\n"
                + f"{'There are stairs up here.\n' if Stairs.UP in r.stairs else ''}"
                + f"{'There are stairs down here.\n' if Stairs.DOWN in r.stairs else ''}"
                + f"{'This room is a shop.\n' if r.shop else ''}"
                + f"{'This room contains monsters.\n' if r.monsters else ''}"
                + f"{'This room contains treasure.\n' if r.treasure else ''}"
                + f"{'There is a trap here.\n' if r.trap else ''}"
            for i, r in enumerate(level.rooms)
        })
        savefile.room_encounters.update({ r.id: Encounter() for r in level.rooms })

    if "no_floors" in spec.extra:
        handle_no_floors(imgs, savefile.scale, **spec.extra["no_floors"])

    savefile.level_notes[level_number] = f"Level {level_number}: {spec.name}i\nThis level contains {floor_number + 1} floors."
    savefile.levels[level_number] = {i + 1: rm for i, rm in enumerate(rooms)}
    savefile.images[level_number] = {i + 1: img for i, img in enumerate(imgs)}


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
        "--append",
        action = "store_true",
        default = False,
        help = "Append to existing Dungen savefile.",
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

    savefile = DungenSave(scale = spec.scale)
    if args.append:
        savefile = DungenSave.deserialize(args.savefile)
        # Add stairs down
        last_level = len(savefile.levels)
        last_floor = len(savefile.levels[last_level])
        selected_rooms = random.choices(
            savefile.levels[last_level][last_floor],
            k = spec.entrances,
        )
        savefile.levels[last_level][last_floor] = tuple(
            Room(
                r.id,
                r.location,
                r.width,
                r.height,
                r.monsters,
                r.treasure,
                r.trap,
                r.shop,
                (r.stairs | Stairs.DOWN) if r in selected_rooms else r.stairs,
            ) for r in savefile.levels[last_level][last_floor]
        )
           
        for room in savefile.levels[last_level][last_floor]:
            room_el = find_element(savefile.images[last_level][last_floor], f"room-{room.id}")
            if room_el is not None:
                room_el.class_ = ["room"] + room.tags # type: ignore[attr-defined] 
    starting_levels = len(savefile.levels)

    for i in progressbar.progressbar(range(1, spec.level_count + 1)):
        i += starting_levels
        level_spec, = random.choices(spec.levels, weights=[ls.probability for ls in spec.levels])
        stairs_up = []
        if i == 1:
            for _ in range(spec.entrances):
                stairs_up.append(
                    Point(
                        random.randint(0, level_spec.width - level_spec.room_width.upper), 
                        random.randint(0, level_spec.height - level_spec.room_height.upper), 
                    )
                )
        else:
            stairs_up = [ 
                r.location for r in savefile.levels[i - 1][len(savefile.levels[i - 1])] if Stairs.DOWN in r.stairs
            ]


        create_level(
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
            for j, img in enumerate(savefile.images[i]):
                svg_path = level_dir.joinpath(f"floor_{j + 1}.svg")
                svg_path.write_text(str(img))

    if args.verbose:
        print(f"Dungeon has {len(savefile.levels)} levels:")
        for lvl in savefile.levels:
            print(f"  Level {lvl}")
            for floor in savefile.levels[lvl]:
                down_c = len([r for r in savefile.levels[lvl][floor] if Stairs.DOWN in r.stairs])
                up_c = len([r for r in savefile.levels[lvl][floor] if Stairs.UP in r.stairs])
                print(f"    Floor {floor}: {len(savefile.levels[lvl][floor])} Rooms [{up_c} U {down_c} D].")

    with args.savefile.open("wb") as out:
        out.write(pickle.dumps(savefile))

if __name__ == "__main__":
    main_func()
