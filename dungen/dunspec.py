import yaml

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .room_generators import LevelSpec
from .connections import Bound
from .level_drawer import FillPatterns, paths_to_patterns
from .rooms import Point


class DunSpecLoader(yaml.SafeLoader):
    def __init__(self, stream):
        self.root = Path(stream.name).parent
        super().__init__(stream)

def construct_use(loader: DunSpecLoader, node: yaml.Node) -> Any:
    if not isinstance(node, yaml.ScalarNode):
        raise AttributeError(f"{node} is not a file path.")
    file = loader.root / loader.construct_scalar(node)
    with file.open() as sf:
        return yaml.load(sf, DunSpecLoader)

yaml.add_constructor("!use", construct_use, DunSpecLoader)

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
    entrances: int = 1

    @classmethod
    def from_yaml(cls, spec_file: Path) -> "DunSpec":
        with spec_file.open() as sf:
            spec = yaml.load(sf, DunSpecLoader)
        scale_factor = spec.get("scale", 1)
        level_specs: Dict[str, LevelSpec] = {}
        textures: Dict[LevelSpec, FillPatterns] = {}
        dict_to_bound = lambda d: Bound(d["lower"], d["upper"])
        for name, level in spec["floor_types"].items():
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
                stairs_down = dict_to_bound(level["stairs_down"]),
                probability = level["probability"],
                extra = level.get("extra", {}),
            )
            filepaths = level["textures"]
            textures[level_specs[name]] = paths_to_patterns(
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

        return DunSpec(
            level_count = spec["floor_count"],
            levels = list(level_specs.values()),
            textures = textures,
            scale = scale_factor,
            entrances = spec.get("entrances", None),
        )
