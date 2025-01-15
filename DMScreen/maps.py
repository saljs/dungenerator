import copy
import svg

from typing import List
from dungen import find_element, append_children, remove_children

def render_as_map(orig_map: svg.SVG, scale: int) -> str:
    fg_filter = svg.Filter(
        id = "fg-filter",
        elements = [
            svg.FeColorMatrix(
                in_ = "SourceGraphic",
                type = "matrix",
                values = "0 0 1 0 0\n0 0 1 0 0\n0 0 1 0 0\n0 0 0 1 0",
                result = "black_and_white",
            ),
            svg.FeTurbulence(
                baseFrequency = "0.001",
                numOctaves = 2,
                type = "turbulence",
                result = "turbulence",
            ),
            svg.FeDisplacementMap(
                in2 = "turbulence",
                in_ = "black_and_white",
                scale = str(scale),
                xChannelSelector = "R",
                yChannelSelector = "G",
                result = "pencil",
            ),
        ],
    )

    map_copy = copy.deepcopy(orig_map)
    map_copy.viewBox = svg.ViewBoxSpec(0, 0, map_copy.width, map_copy.height) # type: ignore[arg-type]
    map_copy.width = None
    map_copy.height = None
    
    remove_children(map_copy, "background_pattern")
    remove_children(map_copy, "bg-elements")
    remove_children(map_copy, "stamps")

    fg_el = find_element(map_copy, "fg-elements")
    if fg_el is not None and isinstance(fg_el, svg.G):
        append_children(map_copy, "defs", [fg_filter])
        fg_el.filter = "url(#fg-filter)"

    return str(map_copy)
