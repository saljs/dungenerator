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

from .dunspec import DunSpec
from .connections import Bound
from .encounter import Encounter
from .level import Level
from .level_drawer import LevelDrawer
from .room_generators import LevelSpec
from .rooms import Stairs, Room

# individual room drawers
from .rect_room_drawer import RectRoomDrawer
from .organic_room_drawer import OrganicRoomDrawer

# Map of shapes to drawers
drawer_map: Dict[str, LevelDrawer] = {
    "rect": cast(LevelDrawer, RectRoomDrawer()),
    "organic": cast(LevelDrawer, OrganicRoomDrawer()),
}


@dataclass
class DungenSave:
    """The savefile definition."""
    scale: int = 1
    levels: Dict[int, Tuple[Room, ...]] = field(default_factory=dict)
    images: Dict[int, svg.SVG] = field(default_factory=dict)
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
        help = "Export levels to svg file(s).",
    )
    args = parser.parse_args()
    spec = DunSpec.from_yaml(args.spec)

    savefile = DungenSave(scale = spec.scale)
    level:Optional[Level] = None
    level_specs: List[LevelSpec] = []
    for _ in range(spec.level_count):
        level_spec, = random.choices(spec.levels, weights=[ls.probability for ls in spec.levels])
        level_specs += [level_spec] * random.randint(level_spec.floors.lower, level_spec.floors.upper)

    for level_number in progressbar.progressbar(range(1, len(level_specs) + 1)):
        level_spec = level_specs[level_number - 1]
        level_textures = spec.textures[level_spec]
        if spec.entrances is not None and level_number == 1:
            level_spec = LevelSpec(
                name = level_spec.name,
                width = level_spec.width,
                height = level_spec.height,
                floors = level_spec.floors,
                rooms = level_spec.rooms,
                room_width = level_spec.room_width,
                room_height = level_spec.room_height,
                room_alg = level_spec.room_alg,
                room_shape = level_spec.room_shape,
                hall_density = level_spec.hall_density,
                hall_width = level_spec.hall_width,
                trap_chance = level_spec.trap_chance,
                monster_chance = level_spec.monster_chance,
                shop_chance = level_spec.shop_chance,
                treasure_chance = level_spec.treasure_chance,
                stairs_up = Bound(spec.entrances, spec.entrances),
                stairs_down = level_spec.stairs_down,
                probability = 0,
                extra = level_spec.extra,
            )
        level = Level(
            level_spec,
            [ r.location for r in level.rooms if r.stairs == Stairs.DOWN ] if level else None,
        )
        try:
            drawer = drawer_map[level_spec.room_shape]
        except KeyError:
            raise Exception(f"{level_spec.room_shape} is not a recognized room shape.")
        savefile.levels[level_number] = level.rooms
        savefile.images[level_number] = drawer.draw_level(
            level,
            level_textures,
            scale = spec.scale,
            hall_width = level_spec.hall_width,
        )
        savefile.room_notes.update({
            r.id: f"Room {i+1}:\n"
                + f"{'There are stairs up here.\n' if r.stairs == Stairs.UP else ''}"
                + f"{'There are stairs down here.\n' if r.stairs == Stairs.DOWN else ''}"
                + f"{'This room is a shop.\n' if r.shop else ''}"
                + f"{'This room contains monsters.\n' if r.monsters else ''}"
                + f"{'This room contains treasure.\n' if r.treasure else ''}"
                + f"{'There is a trap here.\n' if r.trap else ''}"
            for i, r in enumerate(level.rooms)
        })
        savefile.room_encounters.update({ r.id: Encounter() for r in level.rooms })
        savefile.level_notes[level_number] = f"Level {level_number}: {level_spec.name}"

        if args.svg_out is not None:
            args.svg_out.mkdir(exist_ok = True)
            svg_path = args.svg_out.joinpath(f"level_{level_number}.svg")
            svg_path.write_text(str(savefile.images[level_number]))
    
    with args.savefile.open("wb") as out:
        out.write(pickle.dumps(savefile))

if __name__ == "__main__":
    main_func()
