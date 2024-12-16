import svg

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import base64
import mimetypes
from random import Random, random
from typing import Collection, List, Optional

from .connections import Connections, Hallway
from .level import Level
from .rooms import Room

@dataclass
class FillPatterns:
    background: List[svg.Element]
    room: List[svg.Element]
    hallway: List[svg.Element]
    room_wall: List[svg.Element]
    hall_wall: List[svg.Element]

class LevelDrawer(ABC):
    """A LevelDrawer implements svg drawing for rooms and hallways."""

    @classmethod
    def draw_level(
        cls,
        level: Level,
        fill: FillPatterns,
        scale: int = 1,
        hall_width: int = 1,
    ) -> svg.SVG:
        width = level.width * scale
        height = level.height * scale
        rng_seed = random()

        defs:List[svg.Element] = [
            svg.Pattern(
                id = "background_pattern",
                width = scale, height = scale,
                patternUnits = "userSpaceOnUse",
                elements = fill.background,
            ),
            svg.Pattern(
                id = "room_pattern",
                width = scale, height = scale,
                patternUnits = "userSpaceOnUse",
                elements = fill.room,
            ),
            svg.Pattern(
                id = "hallway_pattern",
                width = scale, height = scale,
                patternUnits = "userSpaceOnUse",
                elements = fill.hallway,
            ),
            svg.Pattern(
                id = "room_wall_pattern",
                width = scale, height = scale,
                patternUnits = "userSpaceOnUse",
                elements = fill.room_wall,
            ),
            svg.Pattern(
                id = "hall_wall_pattern",
                width = scale, height = scale,
                patternUnits = "userSpaceOnUse",
                elements = fill.hall_wall,
            ),
        ]

        return svg.SVG(
            width = level.width * scale,
            height = level.height * scale,
            elements = [
                svg.Defs(elements = defs),
                svg.G(
                    elements = [
                        svg.Rect(
                            x = 0,
                            y = 0,
                            width = width,
                            height = height,
                            fill = "url(#background_pattern)",
                            id = "background",
                        ),
                        svg.G(
                            elements = cls.draw_hallways(
                                level.hallways,
                                scale,
                                "url(#hall_wall_pattern)",
                                hall_width + 1,
                                Random(rng_seed),
                            ),
                            id = "hall_walls",
                        ),
                        svg.G(
                            elements = cls.draw_rooms(
                                level.rooms,
                                scale,
                                "transparent",
                                "url(#room_wall_pattern)",
                                Random(rng_seed),
                                set_ids = False,
                            ),
                            id = "room_walls",
                        ),
                        svg.G(
                            elements = cls.draw_hallways(
                                level.hallways,
                                scale,
                                "url(#hallway_pattern)",
                                hall_width,
                                Random(rng_seed),
                            ),
                            id = "hallways",
                        ),
                        svg.G(
                            elements = cls.draw_rooms(
                                level.rooms,
                                scale,
                                "url(#room_pattern)",
                                "transparent",
                                Random(rng_seed),
                            ),
                            id = "rooms",
                        ),
                        svg.G(id = "stamps"),
                    ],
                ),
            ],
        )

    @staticmethod
    @abstractmethod
    def draw_rooms(
        rooms: Collection[Room], scale: int, fill: str, border: str, rng: Random, set_ids: bool = True
    ) -> List[svg.Element]:
        ...

    @staticmethod
    @abstractmethod
    def draw_hallways(
        hallways: Connections, scale: int, fill: str, width: int, rng: Random
    ) -> List[svg.Element]:
        ...

def paths_to_patterns(
    background: Path,
    room: Path,
    hallway: Path,
    room_wall: Path,
    hall_wall: Path,
    scale: int,
    background_grid: bool,
    room_grid: bool,
    hall_grid: bool,
) -> FillPatterns:
    """Creates fill patterns from file paths."""
    def create_pattern(fp: Path, grid: bool = False) -> List[svg.Element]:
        mime, _ = mimetypes.guess_type(fp)
        with fp.open("rb") as f:
            data = f.read()
            data64 = base64.b64encode(data).decode("utf-8")
        img: List[svg.Element] = [svg.Image(
            href = f"data:{mime};base64,{data64}",
            x = 0,
            y = 0,
            width = scale,
            height = scale,
        )]
        if grid:
            # Add a border to create a grid
            img.append(svg.Rect(
                x = 0,
                y = 0,
                width = scale,
                height = scale,
                stroke_width = int(scale / 50),
                stroke = "black",
                fill = "transparent",
            ))
        return img
    return FillPatterns(
        create_pattern(background, grid=background_grid),
        create_pattern(room, grid=room_grid),
        create_pattern(hallway, grid=hall_grid),
        create_pattern(room_wall),
        create_pattern(hall_wall),
    )
