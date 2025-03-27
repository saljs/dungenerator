import logging
import time

from dungen import DungenSave
from pathlib import Path
from typing import Optional, List

EXTENSION = ".dng"

class DungenList:
    """A wrapper around a lists of dungen save files, that handles loading
    automatically."""

    __current_open_file: Optional[Path] = None
    __current_open_dungen: Optional[DungenSave] = None

    def __init__(self, search_directory: Path, logger: Optional[logging.Logger] = None):
        if logger is None:
            logger = logging.getLogger("dungen_files")
        self.logger = logger
        self.search_directory = search_directory.resolve()
        
    @property
    def names(self) -> List[str]:
        return [f.stem for f in self.search_directory.glob("*" + EXTENSION)]

    def get(self, dungen_name: str) -> Optional[DungenSave]:
        dungen_path = self.search_directory / (dungen_name + EXTENSION)
        if dungen_path != self.__current_open_file:
            self.__load(dungen_path)
        return self.__current_open_dungen

    def save(self, dungen_name: str) -> bool:
        dungen_path = self.search_directory / (dungen_name + EXTENSION)
        if dungen_path == self.__current_open_file and self.__current_open_dungen is not None:
            start = time.time()
            self.__current_open_dungen.serialize(self.__current_open_file)
            end = time.time()
            self.logger.info(f"Saved {dungen_name} to {self.__current_open_file} ({end - start} seconds).")
            if end - start > 1:
                self.logger.warn(f"Saving dungen file {self.__current_open_file} took {end - start} seconds.")
            return True
        self.logger.warning(f"Cannot save {dungen_name} as it is not loaded.")
        return False

    def __load(self, filepath: Path):
        if self.__current_open_file is not None:
            self.logger.info(f"Unloading DunGen savefile {self.__current_open_file}")
            self.__current_open_file = None
            self.__current_open_dungen = None
        if filepath.exists():
            self.__current_open_file = filepath
            start = time.time()
            self.__current_open_dungen = DungenSave.deserialize(filepath)
            end = time.time()
            self.logger.info(f"Loading DunGen savefile {filepath} ({end - start} seconds).")
            if end - start > 1:
                self.logger.warn(f"Loading dungen file {filepath} took {end - start} seconds.")
