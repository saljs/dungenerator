import yaml

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .room_generators import LevelSpec
from .connections import Bound
from .level_drawer import FillPatterns, paths_to_patterns
from .rooms import Point


@dataclass(frozen=True)
class DunSpec:
    """A DunSpec provides the specification for how to generate an entire dungeon."""
    
    # Number of levels to create.
    level_count: int

    # Level Specs
    levels: List[LevelSpec]
    
    # Textures to use for the different levels.
    textures: Dict[LevelSpec, FillPatterns]

    # Scale of tiles. Set this to the size of patterns.
    scale: int = 1

    # Number of (top) entrances to the dungeon.
    # If unspecified, it is randomly chosen from the LevelSpec.
    entrances: Optional[int] = None

    @classmethod
    def from_yaml(cls, spec_file: Path) -> "DunSpec":
        with spec_file.open() as sf:
            spec = yaml.safe_load(sf)
        level_specs: Dict[str, LevelSpec] = {}
        dict_to_bound = lambda d: Bound(d["lower"], d["upper"])
        for name, level in spec["levels"].items():
            level_specs[name] = LevelSpec(
                name,
                spec["width"],
                spec["height"],
                floors = dict_to_bound(
                    level.get("floors", {"lower": 1, "upper": 1})
                ),
                rooms = dict_to_bound(level["rooms"]),
                room_width = dict_to_bound(level["room_width"]),
                room_height = dict_to_bound(level["room_height"]),
                room_alg = level["room_alg"],
                room_shape = level["room_shape"],
                hall_density = level["hall_density"],
                hall_width = level["hall_width"],
                trap_chance = level["trap_chance"],
                monster_chance = level["monster_chance"],
                shop_chance = level["shop_chance"],
                treasure_chance = level["treasure_chance"],
                stairs_up = dict_to_bound(level["stairs_up"]),
                stairs_down = dict_to_bound(level["stairs_down"]),
                probability = level["probability"],
                extra = level.get("extra", {}),
            )
        scale_factor = spec.get("scale", 1)
        return DunSpec(
            level_count = spec["level_count"],
            levels = list(level_specs.values()),
            textures = {
                level_specs[level]: paths_to_patterns(
                    Path(filepaths["background"]).absolute(),
                    Path(filepaths["room"]).absolute(),
                    Path(filepaths["hallway"]).absolute(),
                    Path(filepaths["room_wall"]).absolute(),
                    Path(filepaths["hall_wall"]).absolute(),
                    scale_factor,
                    filepaths.get("background_grid", False),
                    filepaths.get("room_grid", True),
                    filepaths.get("hall_grid", True),
                )
                for level, filepaths in spec["textures"].items()
            },
            scale = scale_factor,
            entrances = spec.get("entrances", None),
        )
