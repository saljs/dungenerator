from dungen import DungenSave
from pathlib import Path
from typing import Dict, Optional, List

EXTENSION = ".dng"

class DungenList:
    """A wrapper around a lists of dungen save files, that handles loading
    automatically."""
    def __init__(self, search_directory: Path):
        self.search_directory = search_directory.resolve()
        self.__cached_dungens: Dict[str, DungenSave] = {}

    @property
    def names(self) -> List[str]:
        return [f.stem for f in self.search_directory.glob("*" + EXTENSION)]

    def __getitem__(self, dungen_name: str) -> Optional[DungenSave]:
        dungen_path = self.search_directory / (dungen_name + EXTENSION)
        if dungen_name in self.__cached_dungens:
            return self.__cached_dungens[dungen_name]
        elif dungen_path.exists():
            self.__cached_dungens[dungen_name] = DungenSave(dungen_path)
            return self.__cached_dungens[dungen_name]
        return None
