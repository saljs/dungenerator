import os
import imagesize
import re
import svg
from dataclasses import dataclass
from pathlib import Path
from rapidfuzz import fuzz
from typing import Dict, List, Optional, Union, Tuple

from dungen import append_children, find_element, remove_children

SEARCH_CUTOFF_RATIO = 90

@dataclass
class Stamp:
    href: str
    name: str
    orig_path: Path
    size: Optional[Tuple[int, int]] = None

    def to_dict(self) -> Dict[str, Union[str, int, None]]:
        if self.size is None:
            self.size = imagesize.get(self.orig_path)
        w, h = self.size
        return {
            "width": w,
            "height": h,
            "href": self.href,
            "name": self.name,
        }

    @classmethod
    def from_file(cls, filepath: Union[Path, str], root: Path) -> "Stamp":
        filepath = Path(filepath)
        return cls(
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
            ratio = fuzz.token_set_ratio(
                s.name,
                key,
                processor = lambda s: re.sub(r"[_\-\.]", " ",  s.lower()),
            )
            return ratio > SEARCH_CUTOFF_RATIO
        stamps = [s for s in self.stamps if match_stamp_name(s)]
        for sr in self.dirs:
            stamps += sr.search_stamps(key)
        return stamps

    def in_svg(self, img: svg.SVG) -> List[Stamp]:
        """Return a list of stamps used in a SVG image."""
        stamp_root = find_element(img, "stamps")
        if stamp_root is None or stamp_root.elements is None:
            return []
        # Remove the first 8 chars "/stamps/" from href
        hrefs = set([el.href[8:] for el in stamp_root.elements]) # type: ignore
        print(hrefs)
        def find_stamp_hrefs(sr: "StampRepository") -> List[Stamp]:
            m = [s for s in sr.stamps if s.href in hrefs]
            print(m)
            for sd in sr.dirs:
                m += find_stamp_hrefs(sd)
            return m
        return find_stamp_hrefs(self)

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
