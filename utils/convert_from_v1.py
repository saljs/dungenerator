# Converts a v1 savefile to the new format

import argparse
import base64
import mimetypes
import pickle
import svg
import yaml
from dungen import DungenSave
from dungen.drawing import find_element, append_children
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

parser = argparse.ArgumentParser(description="Convert v1 savefiles to new format")
parser.add_argument(
    "old_save",
    help = "Savefile to convert",
    type = Path,
)
parser.add_argument(
    "new_save",
    help = "Location of new savefile",
    type = Path,
)
parser.add_argument(
    "textures",
    help = "YAML file containign a map of textures to update for each level number.",
    type = Path,
)
parser.add_argument(
    "--update-rooms",
    help = "Update room descriptions to new default values.",
    action = "store_true",
    default = False,
)
args = parser.parse_args()

if args.new_save.exists():
    raise Exception("new savefile already exists.")

with args.old_save.open("rb") as to_load:
    old_save = pickle.load(to_load)
scale = old_save.__dict__["scale"]
with args.textures.open() as tf:
    textures = yaml.load(tf, Loader=yaml.Loader)
new_save = DungenSave(args.new_save, scale)

for levelid, floors in old_save.__dict__["images"].items():
    images = {}
    for floorid, image in floors.items():
        # Add in new water editor defs
        width = image.width
        height = image.height
        append_children(image, "defs", [
            svg.Pattern(
                id = "water_pattern",
                width = scale, height = scale,
                patternUnits = "userSpaceOnUse",
                elements = [svg.Image(
                    x = 0, y = 0,
                    width = scale, height = scale,
                )],
            ),
            svg.Mask(
                id = "water_mask",
                width = width, height = height,
                elements = [
                    svg.Rect(
                        x = 0,
                        y = 0,
                        width = width,
                        height = height,
                        fill = "black",
                    ),
                ],
            ),
            svg.Filter(
                id = "water_filter",
                elements = [
                    svg.FeTurbulence(
                        type = "turbulence",
                        baseFrequency = "0.03",
                        numOctaves = 3,
                        stitchTiles = "stitch",
                        result = "turbulence",
                    ),
                    svg.FeDisplacementMap(
                        in_ = "SourceGraphic",
                        in2 = "turbulence",
                        scale = 35,
                        xChannelSelector = "R",
                        yChannelSelector = "G",
                    ),
                ],
            ),
        ])
        append_children(image, "fg-elements", [
            svg.G(
                elements = [
                    svg.Rect(
                        x = 0, y = 0,
                        width = width, height = height,
                        fill = "url(#water_pattern)",
                        mask = "url(#water_mask)",
                    ),
                ],
                id="water",
            ),
        ], before = "stamps")

        # Update textures
        for name, path in textures.get(levelid, {}).items():
            path = Path(path).resolve()
            text_def = find_element(image, f"{name}_pattern")
            if text_def is None or text_def.elements is None:
                raise Exception("Bad image defs!")
            elif len(text_def.elements) == 0 or not isinstance(img_el := text_def.elements[0], svg.Image):
                raise Exception("Bad image def, missing image!")
            mime, _ = mimetypes.guess_type(path)
            with path.open("rb") as f:
                data = f.read()
                data64 = base64.b64encode(data).decode("utf-8")
                img_el.href = f"data:{mime};base64,{data64}"
    
        # Insert room data
        rooms = find_element(image, "rooms")
        if rooms is None or rooms.elements is None:
            raise Exception("Image is missing room information!")
        for room in [r for r in rooms.elements if "room" in r.class_]:
            uid = UUID(room.id[5:])
            old_room,  = [r for r in old_save.__dict__["levels"][levelid][floorid] if r.id == uid]
            room.data = {
                "x": old_room.location.x,
                "y": old_room.location.y,
                "room-encounter": quote("{\"items\":[]}"),
            }
            if args.update_rooms:
                room.data["room-note"] = quote(old_room.note)
            else:
                room.data["room-note"]  = old_save.__dict__["room_notes"][uid]

        # Update organic levels with (some of the) new improvements
        organic_shapes = False
        for room in [r for r in rooms.elements if "room" in r.class_ and isinstance(r, svg.Path)]:
            room.stroke_linejoin = "bevel"
            organic_shapes = True
        if organic_shapes:
            halls = find_element(image, "hallways")
            if halls is None or halls.elements is None:
                raise Exception("Image is missing hall information!")
            for hall in [h for h in halls.elements if "hall" in h.class_ and isinstance(h, svg.Path)]:
                hall.stroke_linejoin = "bevel"

        images[floorid] = image
    new_save.add_level(levelid, images, old_save.__dict__["level_notes"][levelid])
