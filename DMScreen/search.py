import rapidfuzz
from dungen import DungenSave
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class Note:
    roomId: str
    level: int
    floor: int
    note: str

search_cache_hash: int = -1
search_cache_notes: List[Note] = []

def search_room_notes(dungeon: DungenSave, query: Optional[str], cutoff: int) -> List[Tuple[Note, float, int]]:
    global search_cache_hash
    global search_cache_notes
    if query is None:
        return []
    notes: List[Note] = []
    if search_cache_hash == hash(dungeon):
        notes = search_cache_notes
    else:
        for level, floor, data in dungeon.all_floors:
            for roomId, room in data:
                notes.append(Note(roomId, level, floor, room.notes))
        search_cache_hash = hash(dungeon)
        search_cache_notes = notes

    def score_note(
        query: str, note: Note,
        score_cutoff: Optional[float] = None,
    ) -> float:
        return rapidfuzz.fuzz.token_set_ratio(
            query, note.note,
            score_cutoff = score_cutoff,
            processor = rapidfuzz.utils.default_process,
        )

    return rapidfuzz.process.extract(
        query.lower(),
        notes,
        score_cutoff = cutoff,
        limit = None,
        scorer = score_note, # type: ignore[call-overload]
    )
