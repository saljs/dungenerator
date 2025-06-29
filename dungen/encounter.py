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

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "items": [
                {
                    "name": i.name,
                    "initiative": i.initiative,
                    "hp": i.hp,
                    "xp": i.xp,
                    "book": i.book,
                    "book_page": i.book_page,
                } for i in self.items
            ],
        }
