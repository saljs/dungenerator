import os
import imagesize
import svg
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

@dataclass
class Stamp:
    width: int
    height: int
    href: str
    name: str
    orig_path: Path

    def to_dict(self) -> Dict[str, Union[str, int, None]]:
        return {
            "width": self.width,
            "height": self.height,
            "href": self.href,
            "name": self.name,
        }

    @classmethod
    def from_file(cls, filepath: Union[Path, str], root: Path) -> "Stamp":
        w, h = imagesize.get(filepath)
        filepath = Path(filepath)
        return cls(
            w, h,
            href = str(filepath.relative_to(root)),
            name = os.path.basename(filepath),
            orig_path = filepath,
        )

@dataclass
class StampRepository:
    root: Path
    path: Path
    dirs: List["StampRepository"]
    stamps: List[Stamp]

    @property
    def relative_path(self) -> str:
        return str(self.path.relative_to(self.root))

    @property
    def parent(self) -> Optional[str]:
        if self.path.parent.is_relative_to(self.root):
            parent_path = str(self.path.parent.relative_to(self.root))
            if parent_path == ".":
                return ""
            return parent_path
        return None

    def get_stamps(self, path: str) -> Optional["StampRepository"]:
        """Gets metadata for a directory containing stamps"""
        if self.relative_path == path:
            return self
        for sr in self.dirs:
            child = sr.get_stamps(path)
            if child is not None:
                return child
        return None

    def get_stamp(self, path: str) -> Optional[Path]:
        """Gets a single stamp file from a relative path"""
        stamps = [s for s in self.stamps if s.href == path]
        if len(stamps) > 0:
            return stamps[0].orig_path
        for sr in self.dirs:
            child_stamp = sr.get_stamp(path)
            if child_stamp is not None:
                return child_stamp
        return None

    def search_stamps(self, key: str) -> List[Stamp]:
        """Search for term in all stamp directories, returns a flat list."""
        def match_stamp_name(s: Stamp) -> bool:
            if s.name.lower().find(key.lower()) > 0:
                return True
            return False
        stamps = [s for s in self.stamps if match_stamp_name(s)]
        for sr in self.dirs:
            stamps += sr.search_stamps(key)
        return stamps

    @classmethod
    def from_path(cls, path: Union[Path|str]) -> "StampRepository":
        path = Path(path).resolve()
        def walk_dirs(subdir: Path) -> "StampRepository":
            files = list(subdir.iterdir())
            return cls(
                root = path,
                path = Path(subdir),
                dirs = sorted([walk_dirs(d) for d in files if d.is_dir()], key=lambda d: d.path.name),
                stamps = sorted([Stamp.from_file(f, path) for f in files if f.is_file()], key=lambda f: f.name),
            )
        return walk_dirs(path)

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

def set_stamps(stamps: List[StampInfo], image: svg.SVG):
    if image.elements is None or len(image.elements) < 2:
        raise AttributeError("SVG is missing elements")
    g = image.elements[1]
    if g.elements is None:
        raise AttributeError("SVG inner container missing elements")
    stamp_container, = [el for el in g.elements if el.id == "stamps"]
    stamp_container.elements = [svg.Image(
        x = s.x,
        y = s.y,
        width = s.width,
        height = s.height,
        href = s.href,
        transform = s.transform,
    ) for s in stamps]
