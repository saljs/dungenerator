import svg
from copy import copy
from typing import List, Optional, Sequence

def find_element(img: svg.SVG, id: str) -> Optional[svg.Element]:
    def find_from_list(
        elements: Optional[List[svg.Element]]
    ) -> Optional[svg.Element]:
        if elements is None:
            return None
        for el in elements:
            if el.id == id:
                return el
            match = find_from_list(el.elements)
            if match is not None:
                return match
        return None
    return find_from_list(img.elements)
        
def append_children(
    img: svg.SVG,
    id: str,
    elements: Sequence[svg.Element],
    before: Optional[str] = None,
) -> bool:
    parent = find_element(img, id)
    if parent is None:
        return False
    if parent.elements is None:
        parent.elements = []
    index = len(parent.elements)
    if before is not None:
        indeces = [i for i, el in enumerate(parent.elements) if el.id == before]
        if len(indeces) == 1:
            index, = indeces
    parent.elements[index:index] = elements
    return True

def remove_children(img: svg.SVG, id: str, clsfilt: Optional[str] = None) -> bool:
    parent = find_element(img, id)
    if parent is None:
        return False
    if clsfilt is not None and parent.elements is not None:
        parent.elements = [
            l for l in parent.elements if l.class_ is not None and clsfilt not in l.class_ # type: ignore[attr-defined]
        ]
    else:
        parent.elements = None
    return True

def strip_ids(elements: Optional[Sequence[svg.Element]]) -> Optional[List[svg.Element]]:
    if elements is None:
        return None
    final_els: List[svg.Element] = []
    for el in elements:
        el_copy = copy(el)
        el_copy.id = None
        el_copy.elements = strip_ids(el.elements)
        final_els.append(el_copy)
    return final_els
