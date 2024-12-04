import copy
import svg

from typing import List


MAP_EXPORT_BG = svg.Rect(x = 0, y = 0, width = 200, height = 200, fill = "white")
MAP_EXPORT_LINES = "/static/map_pattern.svg"

def find_node(elements: List[svg.Element], node_id: str) -> svg.Element:
    """Returns a node with the given id from a list of nodes."""
    node, = [el for el in elements if el.id == node_id]
    return node

def render_as_map(orig_map: svg.SVG) -> str:
    map_copy = copy.deepcopy(orig_map)
    if (
        map_copy.elements is None
        or len(map_copy.elements) < 1
        or map_copy.elements[0].elements is None
    ):
        raise AttributeError("Missing defs element in SVG.")
    defs = map_copy.elements[0].elements

    bg_pattern = find_node(defs, "background_pattern")
    room_pattern = find_node(defs, "room_pattern")
    hallway_pattern = find_node(defs, "hallway_pattern")
    room_wall_pattern = find_node(defs, "room_wall_pattern")
    hall_wall_pattern = find_node(defs, "hall_wall_pattern")

    def set_img_href(pattern, href):
        if (
            len(pattern.elements) < 1
            or not isinstance(pattern.elements[0], svg.Image)
        ):
            raise AttributeError("SVG pattern missing image element.")
        pattern.elements[0].href = href

    bg_pattern.elements = [ MAP_EXPORT_BG ]
    room_pattern.elements = [ MAP_EXPORT_BG ]
    hallway_pattern.elements = [ MAP_EXPORT_BG ]
    set_img_href(room_wall_pattern, MAP_EXPORT_LINES)
    set_img_href(hall_wall_pattern, MAP_EXPORT_LINES)

    return str(map_copy)
