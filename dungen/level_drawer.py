import svg

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import base64
import mimetypes
from random import Random, random
from typing import Collection, List, Optional

from .connections import Connections, Hallway
from .drawing import append_children, find_element, remove_children, strip_ids
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
        walls_in_fg: bool = False,
    ) -> svg.SVG:
        width = level.width * scale
        height = level.height * scale
        rng_seed = random()

        defs: List[svg.Element] = [
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
        bg: List[svg.Element] = [
            svg.Rect(
                x = 0,
                y = 0,
                width = width,
                height = height,
                fill = "url(#background_pattern)",
                id = "background",
            ),
        ]
        walls: List[svg.Element] = [
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
                    "none",
                    "url(#room_wall_pattern)",
                    Random(rng_seed),
                    set_ids = False,
                ),
                id = "room_walls",
            ),
        ]
        fg: List[svg.Element] = [
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
                    "none",
                    Random(rng_seed),
                ),
                id = "rooms",
            ),
            svg.G(id = "stamps"),
        ]
        if walls_in_fg:
            fg = walls + fg
        else:
            bg = bg + walls

        return svg.SVG(
            width = level.width * scale,
            height = level.height * scale,
            elements = [
                svg.Defs(elements = defs, id = "defs"),
                svg.G(elements = [
                    svg.G(elements = bg, id = "bg-elements"),
                    svg.G(elements = fg, id = "fg-elements"),
                ]),
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

def create_pattern(fp: Path, scale: int, grid: bool = False) -> List[svg.Element]:
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
    return FillPatterns(
        create_pattern(background, scale, grid=background_grid),
        create_pattern(room, scale, grid=room_grid),
        create_pattern(hallway, scale, grid=hall_grid),
        create_pattern(room_wall, scale),
        create_pattern(hall_wall, scale),
    )

def handle_no_floors(
    imgs: List[svg.SVG],
    scale: int,
    opacity_inc: float = 0.2,
    max_trans_floors: int = 3,
    ground_floor_halls: bool = False,
    room_top_texture: Optional[str] = None,
):
    """Make floors transparent, showing levels below."""
    def set_texture(els, cls: str, texture: str, set_fill: bool = True):
        if els is not None:
            for el in els:
                if el.class_ is not None and cls in el.class_:
                    el.stroke = texture
                    if set_fill:
                        el.fill = texture
                set_texture(el.elements, cls, texture, set_fill)

    if not ground_floor_halls:
        # Remove hallways and their walls and replace them with background
        # texture for the lowest floor
        remove_children(imgs[-1], "hall_wall_pattern")
        remove_children(imgs[-1], "hall_walls")
        fg = find_element(imgs[-1], "fg-elements")
        if fg is not None:
            set_texture(fg.elements, "hall", "url(#background_pattern)", set_fill = False)

    if room_top_texture is not None:
        # Add a texture to all but the lowest floor with a roof pattern
        room_top = create_pattern(Path(room_top_texture).absolute(), scale)
        for img in imgs[:-1]:
            append_children(img, "defs", [
                svg.Pattern(
                    id = "room_top_pattern",
                    width = scale, height = scale,
                    patternUnits = "userSpaceOnUse",
                    elements = room_top,
                ),
            ])

    for i, img in enumerate(imgs):
        # For each level, starting from the topmost floor, add the lower
        # levels, starting with the bottommost, to the background
        floor_num = min(len(imgs) - 1, i + max_trans_floors)
        curr_opacity: float = (floor_num - i) * opacity_inc
        while floor_num > i:
            fg = find_element(imgs[floor_num], "fg-elements")
            if fg is None:
                continue
            fg_els = strip_ids(fg.elements)
            if fg_els is None:
                continue

            if room_top_texture is not None:
                set_texture(fg_els, "room", "url(#room_top_pattern)")
                if floor_num < len(imgs) - 1 or ground_floor_halls:
                    set_texture(fg_els, "hall", "url(#room_top_pattern)", set_fill = False)

            new_els: List[svg.Element] = [
                svg.G(
                    elements = fg_els,
                    id = f"bg_floor_{floor_num + 1}",
                ),
                svg.Rect(
                    x = 0, y = 0,
                    width = img.width, height = img.height,
                    fill = "black", opacity = curr_opacity,
                ),
            ]
            append_children(img, "bg-elements", new_els, before = "hall_walls")
            floor_num -= 1
            curr_opacity -= opacity_inc
