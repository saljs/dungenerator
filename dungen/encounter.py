from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Enemy:
    name: str
    initiative: int
    hp: int
    xp: int
    book: str
    book_page: int

@dataclass
class Encounter:
    """Object that holds data representing a potential encounter."""
    items: List[Enemy] = field(default_factory=list)

    @classmethod
    def from_dict(cls, dictIn: Dict[str, Any]) -> "Encounter":
        items = [Enemy(**i) for i in dictIn["items"]]
        return cls(items)
