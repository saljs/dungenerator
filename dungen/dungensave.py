import json
import pickle
import sqlite3
import svg
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import cast, Dict, Iterator, List, Optional, Tuple, Union
from urllib.parse import quote, unquote
from uuid import UUID

from .drawing import append_children, find_element, remove_children
from .encounter import Encounter

@dataclass
class StampInfo:
    x: int
    y: int
    height: int
    width: int
    href: str
    angle: int

    @property
    def transform(self) -> Optional[List[svg.Transform]]:
        if self.angle == 0:
            return None
        centerX = self.x + (self.width / 2)
        centerY = self.y + (self.height / 2)
        return [ svg.Rotate(self.angle, centerX, centerY) ]

@dataclass
class WaterMaskElement:
    x: int
    y: int
    r: int


class FloorData:
    """Takes an `svg.SVG` and provides methods to access info from it."""
    def __init__(self, floor: svg.SVG):
        self.img = floor

    def __getroom(self, roomId: UUID) -> svg.Element:
        room = find_element(self.img, f"room-{roomId}")
        if room is None:
            raise AttributeError(f"Room {roomId} not found in floor")
        return room

    def __getitem__(self, roomId: UUID) -> Dict[str, Union[str, Encounter, List[str]]]:
        room = self.__getroom(roomId)
        if room.data is None:
            raise AttributeError(f"Room {roomId} is missing required attributes")
        return {
            "notes": unquote(room.data["room-note"]),
            "encounter": Encounter.from_dict(json.loads(unquote(room.data["room-encounter"]))),
            "attributes": [c for c in room.class_], # type: ignore[attr-defined]
        }

    def __setitem__(self, roomId: UUID, value: Dict[str, Union[str, Encounter, List[str]]]):
        notes = cast(str, value["notes"])
        encounter = cast(Encounter, value["encounter"])
        attributes = cast(List[str], value["attributes"])
        room = self.__getroom(roomId)
        if room.data is None:
            raise AttributeError(f"Room {roomId} is missing required attributes")
        room.data["room-note"] = quote(notes)
        room.data["room-encounter"] = quote(json.dumps(encounter.to_dict(), separators=(',', ':')))
        editable_attrs = ["monsters", "treasure", "trap", "shop"]
        room.class_ = [a for a in room.class_ if a not in editable_attrs] # type: ignore[attr-defined]
        room.class_ += [a for a in editable_attrs if a in attributes] # type: ignore[attr-defined]

    def room_elements(self, fltr: Optional[str] = None) -> List[svg.Element]:
        """Returns the SVG room elements, with optional class filter."""
        rooms = find_element(self.img, "rooms")
        if rooms is None:
            raise AttributeError(f"SVG is missing required rooms element")
        if rooms is not None and rooms.elements is not None:
            return [
                r for r in rooms.elements 
                if "room" in r.class_ and (fltr is None or fltr in r.class_) # type: ignore[attr-defined]
            ]
        return []

    def set_stamps(self, stamps: List[StampInfo]):
        """Sets all of the stamp object for the floor, overwriting current content."""
        if remove_children(self.img, "stamps"):
        	append_children(self.img, "stamps", [
        	    svg.Image(
        	        x = s.x,
        	        y = s.y,
        	        width = s.width,
        	        height = s.height,
        	        href = s.href,
        	        transform = s.transform,
        	    ) for s in stamps
        	]) 
        else:
            raise AttributeError("Stamps element not in floor image")

    def set_water_mask(self, circles: List[WaterMaskElement]):
        """Sets the water layer mask, overwriting current content."""
        if remove_children(self.img, "water_mask", "mask-element"):
        	append_children(self.img, "water_mask", [
        	    svg.Circle(
        	        cx = c.x,
        	        cy = c.y,
                    r = c.r,
                    fill = "white",
                    filter = "url(#water_filter)",
                    class_ = ["mask-element"],
        	    ) for c in circles
        	]) 
        else:
            raise AttributeError("Water element not in floor image")


class DungenSave:
    """Savefile definition for DunGen files."""
    def __init__(self, file: Path, scale: Optional[int] = None):
        self.filepath = file
        self.__scale = scale
        self.__levels = None
        if not self.filepath.exists():
            if scale is None:
                raise AttributeError("Must supply scale when creating a new savefile")
            self.__create_tables(scale)
            self.__levels = 0

    @contextmanager
    def __open_tables(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(
            self.filepath,
            timeout = 20,
            autocommit = False,
        )
        try:
            yield conn
        finally:
            conn.close()

    def __create_tables(self, scale: int):
        with self.__open_tables() as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE meta(scale INT)")
            cur.execute("INSERT INTO meta VALUES(?)", (scale,))
            cur.execute("CREATE TABLE levels(lvlid INT PRIMARY KEY, note TEXT, floors INT)")
            cur.execute("CREATE TABLE floors(lvlid INT, floorid INT, img BLOB)")
            conn.commit()
            cur.execute("CREATE TRIGGER levels_trigger BEFORE UPDATE OF lvlid, floors ON levels BEGIN\n"
                + "SELECT RAISE(FAIL, 'Property is non-editable');\nEND"
            )
            cur.execute("CREATE TRIGGER floors_trigger BEFORE UPDATE OF lvlid, floorid ON floors BEGIN\n"
                + "SELECT RAISE(FAIL, 'Property is non-editable');\nEND"
            )
            conn.commit()

    @property
    def scale(self) -> int:
        if self.__scale is None:
            with self.__open_tables() as conn:
                cur = conn.cursor()
                cur.execute("SELECT scale FROM meta")
                self.__scale, = cur.fetchone()
        return self.__scale

    @property
    def levels(self) -> int:
        if self.__levels is None:
            with self.__open_tables() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM levels")
                self.__levels, = cur.fetchone()
        return self.__levels

    def add_level(self, lvlid: int, floors: Dict[int, svg.SVG], note: str):
        """Adds a new level to the table under the previous level."""
        with self.__open_tables() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO levels(lvlid, note, floors) VALUES(?, ?, ?)", (lvlid, note, len(floors)))
            for i, img in floors.items():
                cur.execute("INSERT INTO floors(lvlid, floorid, img) VALUES(?, ?, ?)", (lvlid, i, pickle.dumps(img)))
            conn.commit()
            self.__levels = None

    def floor_count(self, lvlid: int) -> int:
        """Returns the number of floors in the level."""
        with self.__open_tables() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM floors WHERE lvlid = ?", (lvlid,))
            c, = cur.fetchone()
        return c

    def get_floor(self, lvlid: int, floorid: int) -> Optional[FloorData]:
        """Returns a FloorData object wrapping the specified floor image."""
        with self.__open_tables() as conn:
            cur = conn.cursor()
            cur.execute("SELECT img FROM floors WHERE lvlid = ? AND floorid = ?", (lvlid, floorid))
            res = cur.fetchone()
            if len(res) != 1:
                return None
            img_pickle, = res
        img = pickle.loads(img_pickle)
        return FloorData(img)

    def set_floor(self, lvlid: int, floorid: int, floor: FloorData):
        """Sets the contents of the floor image."""
        with self.__open_tables() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE floors SET img = ? WHERE lvlid = ? AND floorid = ?",
                (pickle.dumps(floor.img), lvlid, floorid),
            )
            conn.commit()

    def set_level_note(self, lvlid: int, note: str):
        """Sets the level note for the level specified."""
        self.set_level_notes({ lvlid: note })

    def set_level_notes(self, notes: Dict[int, str]):
        """Sets level notes for all levels in the input."""
        with self.__open_tables() as conn:
            cur = conn.cursor()
            cur.executemany("UPDATE levels SET note = ? WHERE lvlid = ?", [
                (note, lvlid) for lvlid, note in notes.items()
            ])
            conn.commit()

    def get_level_notes(self) -> Dict[int, str]:
        """Gets all notes for each level."""
        with self.__open_tables() as conn:
            cur = conn.cursor()
            cur.execute("SELECT lvlid, note FROM levels")
            return { lvlid: note for lvlid, note in cur }
