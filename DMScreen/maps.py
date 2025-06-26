import svg

from typing import List
from dungen import find_element, append_children, remove_children

def render_as_map(img: svg.SVG, scale: int) -> str:
    fg_filter = svg.Filter(
        id = "fg-filter",
        elements = [
            svg.FeColorMatrix(
                in_ = "SourceGraphic",
                type = "matrix",
                values = "0 0 1 0 0\n0 0 1 0 0\n0 0 1 0 0\n0 0 0 1 0",
                result = "black_and_white",
            ),
            svg.FeTurbulence(
                baseFrequency = "0.001",
                numOctaves = 2,
                type = "turbulence",
                result = "turbulence",
            ),
            svg.FeDisplacementMap(
                in2 = "turbulence",
                in_ = "black_and_white",
                scale = str(scale),
                xChannelSelector = "R",
                yChannelSelector = "G",
                result = "pencil",
            ),
        ],
    )

    img.viewBox = svg.ViewBoxSpec(0, 0, img.width, img.height) # type: ignore[arg-type]
    img.width = None
    img.height = None
    
    remove_children(img, "background_pattern")
    remove_children(img, "bg-elements")
    remove_children(img, "stamps")

    fg_el = find_element(img, "fg-elements")
    if fg_el is not None and isinstance(fg_el, svg.G):
        append_children(img, "defs", [fg_filter])
        fg_el.filter = "url(#fg-filter)"

    return str(img)


def render_for_viewer(img: svg.SVG, scale: int) -> str:
    shadow_filter = svg.Filter(
        id = "shadow_filter",
        elements = [
            svg.FeFlood(flood_color = "black"),
            svg.FeComposite(operator = "out", in2 = "SourceGraphic"),
            svg.FeGaussianBlur(stdDeviation = scale / 4),
            svg.FeOffset(dx = scale / 10, dy = scale / 10, result="drop-shadow"),
            svg.FeComposite(operator = "atop", in2="SourceGraphic"),
        ],
    )
    append_children(img, "defs", [shadow_filter])

    light_grad = svg.RadialGradient(
        id = "light_gradient",
        elements = [
            svg.Stop(offset=svg.Length(value=0, unit="%"),  stop_color="white"),
            svg.Stop(offset=svg.Length(value=80, unit="%"),  stop_color="white"),
            svg.Stop(offset=svg.Length(value=100, unit="%"),  stop_color="black"),
        ],
    )
    light_mask = svg.Mask(
        id = "light_mask",
        elements = [
            svg.Rect(
                x = 0, y = 0,
                width = svg.Length(value=120, unit="%"),
                height = svg.Length(value=120, unit="%"),
                fill = "black",
            ),
            svg.Rect(
                id = "light_mask_rect",
                x = 0, y = 0,
                width = img.width, height = img.height,
                fill = "white",
            ),
        ],
    )
    if img.elements is not None and len(img.elements) >= 2:
        g = img.elements[1]
        if isinstance(g, svg.G) and append_children(img, "defs", [light_grad, light_mask]):
            g.mask = "url(#light_mask)"

    return str(img)
