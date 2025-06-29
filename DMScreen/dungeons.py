from dungen import DungenSave
from pathlib import Path
from typing import Optional, List

EXTENSION = ".dng"

class DungenList:
    """A wrapper around a lists of dungen save files, that handles loading
    automatically."""
    def __init__(self, search_directory: Path):
        self.search_directory = search_directory.resolve()

    @property
    def names(self) -> List[str]:
        return [f.stem for f in self.search_directory.glob("*" + EXTENSION)]

    def __getitem__(self, dungen_name: str) -> Optional[DungenSave]:
        dungen_path = self.search_directory / (dungen_name + EXTENSION)
        if dungen_path.exists():
            return DungenSave(dungen_path)
        return None
